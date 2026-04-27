from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from action_library import (
    ACTION_LIBRARY,
    LOW_LEVEL_ACTIONS,
    PROTOCOL_LEVEL_DISTRACTOR_ACTIONS,
    STEP_FAMILY_TO_ACTIONS,
    render_action_pool_code,
)
from ast_utils import numeric_literal_count, parse_program_steps
from common import (
    DEFAULT_MODEL,
    compact_text,
    get_api_key,
    model_from_env,
    openrouter_chat_completion,
    parse_json_object,
    repo_relative_display,
)

DEFAULT_PROTOCOLS = Path("data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl")
DEFAULT_OUTPUT = SCRIPT_DIR / "generated" / "level2_tasks_20.json"
FAMILY_PATTERNS: dict[str, tuple[str, ...]] = {
    "transfer": (
        r"\badd\b",
        r"\btransfer\b",
        r"\bpipett",
        r"\bdispens",
        r"\baliquot",
        r"\bload\b",
        r"\bapply\b",
        r"\bcombine\b",
    ),
    "mix": (r"\bmix\b", r"\bvortex\b", r"\bshake\b", r"\bstir\b", r"\brock\b", r"\binvert\b"),
    "incubate": (
        r"\bincubat",
        r"\bstore\b",
        r"\bleave\b",
        r"\bhold\b",
        r"\brest\b",
        r"\bstand\b",
        r"\bdry\b",
        r"\bovernight\b",
    ),
    "centrifuge": (r"centrifug", r"\bspin\b", r"\bx g\b", r"\brpm\b"),
    "wash": (r"\bwash\b", r"\brinse\b", r"\belut", r"\bpreclear"),
    "separate": (r"\bfilter\b", r"\bmagnet", r"\bpurif", r"\bcollect\b", r"\bseparat", r"\bpellet\b"),
    "measure": (r"\bmeasure\b", r"\bread\b", r"\bquantif", r"\bmonitor\b", r"\bnanodrop\b", r"\bscore\b"),
    "device": (r"\bopen\b", r"\bclose\b", r"\bbutton\b", r"\bpress\b", r"\blid\b", r"\bprogram\b", r"\bthermal cycler\b"),
}
GENERIC_STEP_PATTERNS = (
    r"^\s*cleaning\.?\s*$",
    r"^\s*preparation\.?\s*$",
    r"^\s*mouse preparation\.?\s*$",
    r"^\s*stereotaxic surgery\.?\s*$",
    r"^\s*injection cannulas circuit preparation\.?\s*$",
    r"^\s*apparatus preparation\.?\s*$",
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")


@dataclass(frozen=True)
class StepWindow:
    protocol_id: str
    title: str
    background: str
    matched_groups: tuple[str, ...]
    candidate_entries: tuple[dict[str, Any], ...]
    steps: tuple[dict[str, Any], ...]
    families: tuple[str, ...]
    score: float


def load_protocol_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def infer_step_families(text: str) -> set[str]:
    lowered = text.lower()
    matched: set[str] = set()
    for family, patterns in FAMILY_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            matched.add(family)
    return matched


def count_numeric_mentions(text: str) -> int:
    return len(re.findall(r"[-+]?\d+(?:\.\d+)?", text))


def is_generic_step(text: str) -> bool:
    lowered = text.strip().lower()
    if len(lowered) < 18:
        return True
    return any(re.match(pattern, lowered) for pattern in GENERIC_STEP_PATTERNS)


def score_window(steps: list[dict[str, Any]]) -> tuple[float, set[str]]:
    family_counter: Counter[str] = Counter()
    all_families: set[str] = set()
    numeric_score = 0
    generic_penalty = 0
    stage_counter: Counter[str] = Counter()

    for step in steps:
        description = str(step.get("description", "")).strip()
        families = infer_step_families(description)
        all_families.update(families)
        family_counter.update(families)
        numeric_score += min(4, count_numeric_mentions(description))
        if is_generic_step(description):
            generic_penalty += 1
        stage_counter[str(step.get("stage", "")).strip()] += 1

    repeated_bonus = sum(
        max(0, count - 1)
        for family, count in family_counter.items()
        if family in {"transfer", "incubate", "centrifuge", "wash", "separate", "mix"}
    )
    rich_family_bonus = sum(1 for count in family_counter.values() if count >= 2)
    repeated_core_family_bonus = sum(1 for family, count in family_counter.items() if family in {"transfer", "incubate", "centrifuge", "wash", "mix"} and count >= 2)
    stage_bonus = 2.0 if len([stage for stage in stage_counter if stage]) <= 2 else 0.0
    device_penalty = family_counter.get("device", 0) * 0.75
    score = (
        len(steps) * 1.5
        + len(all_families) * 2.0
        + repeated_bonus * 3.0
        + rich_family_bonus * 1.75
        + repeated_core_family_bonus * 2.5
        + numeric_score * 0.75
        + stage_bonus
        - device_penalty
        - generic_penalty * 2.0
    )
    return score, all_families


def window_family_counter(window: StepWindow) -> Counter[str]:
    counter: Counter[str] = Counter()
    for step in window.steps:
        counter.update(infer_step_families(str(step.get("description", "")).strip()))
    return counter


def is_hard_compatible_window(window: StepWindow) -> bool:
    family_counter = window_family_counter(window)
    repeated_core_families = sum(
        1
        for family, count in family_counter.items()
        if family in {"transfer", "mix", "incubate", "centrifuge", "wash", "separate"} and count >= 2
    )
    total_numeric_mentions = sum(count_numeric_mentions(str(step.get("description", ""))) for step in window.steps)
    return repeated_core_families >= 2 and total_numeric_mentions >= 5 and len(window.steps) >= 8


def build_candidate_windows(
    record: dict[str, Any],
    *,
    min_steps: int,
    max_steps: int,
) -> list[StepWindow]:
    procedure = record.get("procedure") or {}
    steps = procedure.get("steps") or []
    if not isinstance(steps, list):
        return []

    protocol_id = str(record.get("id", "")).strip()
    title = str(record.get("title", "")).strip()
    background = str(record.get("background", "")).strip()
    matched_groups = tuple(record.get("matched_groups") or [])
    candidate_entries = tuple(record.get("candidate_entries") or [])
    windows: list[StepWindow] = []
    candidate_lengths = sorted(
        {
            min_steps,
            max_steps,
            max(min_steps, min(max_steps, (min_steps + max_steps) // 2)),
        }
    )

    for length in candidate_lengths:
        if length > len(steps):
            continue
        for start in range(0, len(steps) - length + 1):
            window_steps = steps[start : start + length]
            score, families = score_window(window_steps)
            if score < 18 or len(families) < 2:
                continue
            windows.append(
                StepWindow(
                    protocol_id=protocol_id,
                    title=title,
                    background=background,
                    matched_groups=matched_groups,
                    candidate_entries=candidate_entries,
                    steps=tuple(window_steps),
                    families=tuple(sorted(families)),
                    score=score,
                )
            )
    windows.sort(key=lambda item: item.score, reverse=True)
    return windows[:5]


def steps_text(window: StepWindow) -> str:
    return "\n".join(str(step.get("description", "")).strip().lower() for step in window.steps)


def needs_low_level_actions(window: StepWindow) -> bool:
    text = steps_text(window)
    low_level_patterns = (
        r"\bopen the lid\b",
        r"\bclose the lid\b",
        r"\bpress\b",
        r"\bload .*?(?:rotor|bucket|slot)\b",
        r"\bbalance\b",
        r"\bseal\b",
    )
    return any(re.search(pattern, text) for pattern in low_level_patterns)


def select_action_pool(window: StepWindow, *, hardness: str) -> list[str]:
    selected: list[str] = []
    protocol_families = [family for family in window.families if family != "manipulate"]
    for family in protocol_families:
        for action_name in STEP_FAMILY_TO_ACTIONS.get(family, ()):
            if action_name not in selected:
                selected.append(action_name)

    if "transfer" in protocol_families and "wash" not in protocol_families:
        for action_name in STEP_FAMILY_TO_ACTIONS["wash"]:
            if action_name not in selected:
                selected.append(action_name)
    if "wash" in protocol_families and "transfer" not in protocol_families:
        for action_name in STEP_FAMILY_TO_ACTIONS["transfer"]:
            if action_name not in selected:
                selected.append(action_name)
    if "incubate" in protocol_families and "device" not in protocol_families:
        for action_name in ("seal_plate",):
            if action_name in ACTION_LIBRARY and action_name not in selected:
                selected.append(action_name)
    if "centrifuge" in protocol_families:
        for action_name in ("wash_pellet", "discard_supernatant", "resuspend_pellet"):
            if action_name not in selected:
                selected.append(action_name)
    if "mix" in protocol_families:
        for action_name in ("incubate_sample", "cool_sample"):
            if action_name not in selected:
                selected.append(action_name)
    if "measure" in protocol_families:
        for action_name in ("store_sample", "mix_sample"):
            if action_name not in selected:
                selected.append(action_name)

    for action_name in PROTOCOL_LEVEL_DISTRACTOR_ACTIONS:
        if action_name not in selected:
            selected.append(action_name)

    if needs_low_level_actions(window):
        for action_name in LOW_LEVEL_ACTIONS:
            if action_name in ACTION_LIBRARY and action_name not in selected:
                selected.append(action_name)

    max_size = 12 if hardness == "baseline" else 14
    return selected[:max_size]


def summarize_steps(steps: tuple[dict[str, Any], ...]) -> str:
    lines = []
    for step in steps:
        idx = step.get("idx")
        stage = str(step.get("stage", "")).strip()
        description = str(step.get("description", "")).strip()
        lines.append(f"- Step {idx} [{stage}] {description}")
    return "\n".join(lines)


def background_excerpt(text: str, max_chars: int = 1800) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3] + "..."


def partial_output_path(output_path: Path) -> Path:
    return output_path.with_suffix(".partial.jsonl")


def load_partial_records(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    cached: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"invalid JSON in partial file at line {line_no}: {path}") from exc
            task_id = record.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise RuntimeError(f"missing task_id in partial file at line {line_no}: {path}")
            cached[task_id] = record
    return cached


def append_partial_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def validate_english_text(text: str, field_name: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if CJK_RE.search(text):
        raise ValueError(f"{field_name} must be English-only")


def validate_task(
    task: dict[str, Any],
    *,
    task_id: str,
    action_pool_names: list[str],
    hardness: str,
) -> dict[str, Any]:
    validate_english_text(task.get("background", ""), "background")
    validate_english_text(task.get("goal", ""), "goal")

    constraints = task.get("constraints")
    max_constraints = 6 if hardness == "baseline" else 10
    if not isinstance(constraints, list) or not (3 <= len(constraints) <= max_constraints):
        raise ValueError(f"constraints must be a list with 3-{max_constraints} items")
    for idx, item in enumerate(constraints, 1):
        validate_english_text(item, f"constraints[{idx}]")

    raw_inputs = task.get("available_inputs")
    if not isinstance(raw_inputs, list) or not (3 <= len(raw_inputs) <= 8):
        raise ValueError("available_inputs must be a list with 3-8 items")
    raw_input_names: list[str] = []
    for idx, item in enumerate(raw_inputs, 1):
        if not isinstance(item, dict):
            raise ValueError(f"available_inputs[{idx}] must be an object")
        name = item.get("name")
        description = item.get("description")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_]\w*", name):
            raise ValueError(f"available_inputs[{idx}].name must be a valid Python identifier")
        validate_english_text(str(description or ""), f"available_inputs[{idx}].description")
        raw_input_names.append(name)
    if len(raw_input_names) != len(set(raw_input_names)):
        raise ValueError("available_inputs names must be unique")

    gold_program = task.get("gold_program")
    if not isinstance(gold_program, str) or not gold_program.strip():
        raise ValueError("gold_program must be a non-empty string")
    if "```" in gold_program:
        raise ValueError("gold_program must not contain markdown fences")
    steps = parse_program_steps(gold_program)
    min_program_steps = 6 if hardness == "baseline" else 7
    max_program_steps = 12 if hardness == "baseline" else 13
    if not (min_program_steps <= len(steps) <= max_program_steps):
        raise ValueError(
            f"gold_program must contain {min_program_steps}-{max_program_steps} top-level function-call steps"
        )

    used_actions = [step.action for step in steps]
    if any(action not in action_pool_names for action in used_actions):
        unknown_actions = sorted(set(action for action in used_actions if action not in action_pool_names))
        raise ValueError(f"gold_program uses actions outside the action pool: {unknown_actions}")

    counts = Counter(used_actions)
    repeated_action_names = [action for action, count in counts.items() if count >= 2]
    if max(counts.values(), default=0) < 2:
        raise ValueError("gold_program must reuse at least one action name more than once")
    min_numeric_literals = 3 if hardness == "baseline" else 5
    if numeric_literal_count(gold_program) < min_numeric_literals:
        raise ValueError(f"gold_program must include at least {min_numeric_literals} numeric literals")

    available_input_set = set(raw_input_names)
    generated_outputs: set[str] = set()
    generated_reference_count = 0
    for step_index, step in enumerate(steps, 1):
        if step.output is None or not re.fullmatch(r"[A-Za-z_]\w*", step.output):
            raise ValueError(f"step {step_index} must assign its function call to a valid output variable")
        for key, argument in step.inputs.items():
            if argument.kind == "expression":
                raise ValueError(f"step {step_index} parameter '{key}' uses an unsupported expression")
            if argument.kind == "name":
                name = str(argument.value)
                if name not in available_input_set and name not in generated_outputs:
                    raise ValueError(f"step {step_index} parameter '{key}' references unknown variable '{name}'")
                if name in generated_outputs:
                    generated_reference_count += 1
        generated_outputs.add(step.output)
    if hardness != "baseline" and generated_reference_count < max(4, len(steps) // 2):
        raise ValueError("hard tasks must include a longer generated-variable dependency chain")

    return {
        "task_id": task_id,
        "background": task["background"].strip(),
        "goal": task["goal"].strip(),
        "constraints": [item.strip() for item in constraints],
        "available_inputs": [{"name": item["name"], "description": item["description"].strip()} for item in raw_inputs],
        "gold_program": gold_program.strip(),
        "gold_step_count": len(steps),
        "gold_action_counts": dict(sorted(counts.items())),
    }


def build_generation_prompt(window: StepWindow, *, action_pool_names: list[str], action_pool_code: str, hardness: str) -> list[dict[str, Any]]:
    hard_rules = ""
    if hardness != "baseline":
        hard_rules = (
            "\nHardness requirements:\n"
            "- Prefer repeated transfer / wash / centrifuge / incubate / resuspend cycles.\n"
            "- Make at least two different action names recur multiple times.\n"
            "- At least one repeated action family must differ only by one or two critical numeric arguments.\n"
            "- Favor long dependency chains where later steps consume outputs from earlier steps instead of restarting from raw inputs.\n"
            "- Prefer local-stage procedural segments rather than far-apart protocol jumps.\n"
            "- Keep the task correct, but avoid turning the constraints into an explicit ordered checklist.\n"
        )

    user_prompt = (
        "Construct one LabOS Level 2 planning item from the private protocol segment below. "
        "Return strict JSON only.\n\n"
        f"Protocol ID: {window.protocol_id}\n"
        f"Title: {window.title}\n"
        f"Matched asset groups: {', '.join(window.matched_groups) if window.matched_groups else 'none'}\n"
        f"Background excerpt:\n{background_excerpt(window.background)}\n\n"
        f"Private source steps:\n{summarize_steps(window.steps)}\n\n"
        f"Available action pool names:\n{', '.join(action_pool_names)}\n\n"
        f"Available action pool code:\n```python\n{action_pool_code}```\n\n"
        "Return a JSON object with exactly these keys:\n"
        "- background: string\n"
        "- goal: string\n"
        "- constraints: list[string]\n"
        "- available_inputs: list[{name, description}]\n"
        "- gold_program: string\n\n"
        "Requirements:\n"
        "- English only.\n"
        "- background should summarize the experiment and current stage without copying the source steps verbatim.\n"
        "- goal should tell the model what subtask to complete, but it must not list the exact gold order.\n"
        "- constraints must encode critical numeric values, intermediate-state requirements, and device conditions without turning into a full step-by-step solution.\n"
        "- available_inputs must contain 3-8 raw variables with valid Python identifiers.\n"
        "- gold_program must be valid Python and must not contain markdown fences.\n"
        "- gold_program must use only the provided action-pool functions.\n"
        "- gold_program must use keyword arguments only.\n"
        "- gold_program must assign every function call to a variable.\n"
        "- Every argument value in gold_program must be either a literal, a raw input variable, or a previously assigned variable; do not use f-strings, concatenation, or other Python expressions.\n"
        "- gold_program must contain 6-12 top-level steps.\n"
        "- Same operation must reuse the same function name; do not invent aliases or near-synonym functions.\n"
        "- Stay at the protocol abstraction level implied by the action pool; do not add robot transport, pick/place, rotor-loading, or device-opening steps unless the source steps explicitly require them and such functions are present in the pool.\n"
        "- Reuse at least one action name more than once.\n"
        "- Include at least 3 numeric literals copied or normalized from the source steps.\n"
        "- Do not redefine functions or import modules.\n"
        f"{hard_rules}"
    )
    return [
        {
            "role": "system",
            "content": (
                "You are constructing a Level 2 long-horizon planning benchmark item for LabOS. "
                "Return strict JSON only."
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def generate_task_for_window(
    *,
    task_id: str,
    window: StepWindow,
    action_pool_names: list[str],
    api_key: str,
    model: str,
    timeout_s: float,
    retries: int,
    hardness: str,
) -> dict[str, Any]:
    action_pool_code = render_action_pool_code(action_pool_names)
    messages = build_generation_prompt(
        window,
        action_pool_names=action_pool_names,
        action_pool_code=action_pool_code,
        hardness=hardness,
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            response = openrouter_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                timeout_s=timeout_s,
                use_response_format=True,
            )
            content = response["choices"][0]["message"]["content"]
            parsed = parse_json_object(content)
            validated = validate_task(
                parsed,
                task_id=task_id,
                action_pool_names=action_pool_names,
                hardness=hardness,
            )
            validated.update(
                {
                    "protocol_id": window.protocol_id,
                    "protocol_title": window.title,
                    "matched_groups": list(window.matched_groups),
                    "candidate_entries": list(window.candidate_entries),
                    "action_pool_names": action_pool_names,
                    "action_pool_code": action_pool_code,
                    "source_step_indices": [step["idx"] for step in window.steps],
                    "source_steps": list(window.steps),
                    "window_score": round(window.score, 3),
                    "window_families": list(window.families),
                    "model_requested": model,
                    "model_returned": response["model"],
                    "usage": response.get("usage"),
                }
            )
            return validated
        except Exception as exc:
            last_error = exc
            if attempt > retries:
                break
            messages = messages + [
                {
                    "role": "assistant",
                    "content": content if "content" in locals() else "",
                },
                {
                    "role": "user",
                    "content": (
                        "The previous JSON was invalid. "
                        f"Validation error: {compact_text(str(exc), 400)}. "
                        "Return a corrected JSON object with the same required keys and no markdown fences."
                    ),
                },
            ]
    raise RuntimeError(f"{task_id} generation failed: {last_error}")


def write_outputs(output_path: Path, metadata: dict[str, Any], tasks: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_path.with_suffix(".jsonl").write_text(
        "\n".join(json.dumps(task, ensure_ascii=False) for task in tasks) + "\n",
        encoding="utf-8",
    )
    output_path.with_name(output_path.stem + ".metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocols", type=Path, default=DEFAULT_PROTOCOLS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--model", default=model_from_env(DEFAULT_MODEL))
    parser.add_argument("--timeout-s", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--min-steps", type=int, default=6)
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--hardness", choices=("baseline", "hard"), default="baseline")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--api-key-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    random.seed(args.seed)
    records = load_protocol_records(args.protocols)
    random.shuffle(records)

    candidate_windows: list[StepWindow] = []
    minimum_candidate_pool = max(args.count * 4, 200 if args.count <= 50 else 800)
    minimum_unique_protocols = max(args.count * 2, 80 if args.count <= 50 else 400)
    for record in records:
        candidate_windows.extend(
            build_candidate_windows(
                record,
                min_steps=args.min_steps,
                max_steps=args.max_steps,
            )
        )
        if (
            len(candidate_windows) >= minimum_candidate_pool
            and len({window.protocol_id for window in candidate_windows}) >= minimum_unique_protocols
        ):
            break
    candidate_windows.sort(key=lambda item: item.score, reverse=True)

    jobs: list[tuple[str, StepWindow, list[str]]] = []
    per_protocol_limit = 1 if args.count <= 50 else 2
    protocol_counts: Counter[str] = Counter()
    seen_job_keys: set[tuple[str, tuple[int, ...]]] = set()
    for window in candidate_windows:
        key = (window.protocol_id, tuple(step["idx"] for step in window.steps))
        if key in seen_job_keys:
            continue
        if protocol_counts[window.protocol_id] >= per_protocol_limit:
            continue
        if args.hardness == "hard" and not is_hard_compatible_window(window):
            continue
        action_pool_names = select_action_pool(window, hardness=args.hardness)
        task_id = f"level2_q{len(jobs) + 1:04d}"
        jobs.append((task_id, window, action_pool_names))
        seen_job_keys.add(key)
        protocol_counts[window.protocol_id] += 1
        if len(jobs) >= args.count:
            break

    if len(jobs) < args.count:
        raise RuntimeError(f"only found {len(jobs)} candidate jobs for requested count={args.count}")

    if args.dry_run:
        for task_id, window, action_pool_names in jobs:
            print(
                json.dumps(
                    {
                        "task_id": task_id,
                        "protocol_id": window.protocol_id,
                        "title": window.title,
                        "step_indices": [step["idx"] for step in window.steps],
                        "families": list(window.families),
                        "score": window.score,
                        "action_pool_names": action_pool_names,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    api_key = get_api_key(read_from_stdin=args.api_key_stdin)
    output_path = args.output
    partial_path = partial_output_path(output_path)
    cached = load_partial_records(partial_path)

    results: list[dict[str, Any] | None] = [None] * len(jobs)
    pending: list[tuple[int, str, StepWindow, list[str]]] = []
    restored = 0
    for idx, (task_id, window, action_pool_names) in enumerate(jobs):
        if task_id in cached:
            results[idx] = cached[task_id]
            restored += 1
        else:
            pending.append((idx, task_id, window, action_pool_names))

    if restored:
        print(
            f"restored {restored} tasks from {repo_relative_display(partial_path)}",
            file=sys.stderr,
            flush=True,
        )

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(
                generate_task_for_window,
                task_id=task_id,
                window=window,
                action_pool_names=action_pool_names,
                api_key=api_key,
                model=args.model,
                timeout_s=args.timeout_s,
                retries=args.retries,
                hardness=args.hardness,
            ): idx
            for idx, task_id, window, action_pool_names in pending
        }
        completed_count = restored
        for future in as_completed(futures):
            idx = futures[future]
            task_id = jobs[idx][0]
            try:
                task = future.result()
            except Exception as exc:
                failures.append(f"{task_id}: {exc}")
                print(
                    f"[error] {task_id} -> {compact_text(str(exc), 240)}",
                    file=sys.stderr,
                    flush=True,
                )
                continue
            results[idx] = task
            append_partial_record(partial_path, task)
            completed_count += 1
            print(
                f"[{completed_count}/{len(jobs)}] {task['task_id']} -> "
                f"{task['protocol_id']} ({task['gold_step_count']} steps)",
                file=sys.stderr,
                flush=True,
            )

    if failures:
        raise RuntimeError(
            "generation incomplete; failed tasks:\n" + "\n".join(failures[:10])
        )

    tasks = [task for task in results if task is not None]
    metadata = {
        "count": len(tasks),
        "protocols_path": repo_relative_display(args.protocols),
        "model": args.model,
        "seed": args.seed,
        "hardness": args.hardness,
        "concurrency": args.concurrency,
        "min_steps": args.min_steps,
        "max_steps": args.max_steps,
        "unique_protocol_count": len({task["protocol_id"] for task in tasks}),
        "unique_title_count": len({task["protocol_title"] for task in tasks}),
    }
    write_outputs(output_path, metadata, tasks)
    print(
        json.dumps(
            {
                "output_path": repo_relative_display(output_path),
                "count": len(tasks),
                "unique_protocol_count": metadata["unique_protocol_count"],
                "hardness": args.hardness,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
