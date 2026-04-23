#!/usr/bin/env python3
"""Build LabOS Level 1 asset-understanding questions.

The pipeline uses the repository's benchmark inventory, rendered multiview
images, and protocol-to-inventory matches to build one multiple-choice question
per selected asset/protocol pair. The OpenRouter API key is read only from an
environment variable, stdin, or an interactive prompt; it is never written to
disk.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MULTIVIEW_MANIFEST = REPO_ROOT / "data/benchmark_inventory/multiview_manifest.json"
DEFAULT_CORE_INVENTORY = REPO_ROOT / "data/benchmark_inventory/benchmark_core_inventory.json"
DEFAULT_PROTOCOL_MATCHES = REPO_ROOT / "data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl"
DEFAULT_DEMO_TEMPLATE = REPO_ROOT / "data/benchmark_inventory/level-1-demo.md"
DEFAULT_OUTPUT = REPO_ROOT / "pipeline/level-1/generated/level1_questions_20.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "qwen/qwen3.6-plus")
DEFAULT_VIEW_ORDER = ("front", "right", "left", "top", "free", "back", "bottom")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")

ENGLISH_DEMO_TEMPLATE = """
Example structure:

Question:
You are preparing a vector digestion reaction for a plant transformation protocol.
The reaction tube already contains the plasmid backbone, buffer, restriction
enzyme, and nuclease-free water, and the mixture has been gently mixed. The
asset shown in the three views is the equipment that may be used next. Based on
the asset function, the current reaction state, and the protocol temperature and
duration requirements, choose the most appropriate next operation.

Options:
A. centrifuge_sample(speed_xg=14000, duration_min=15, temperature_c=4)
B. incubate_in_thermal_cycler(temperature_c=37, duration_min=30)
C. vortex_sample(speed="maximum", duration_min=5)
D. seal_pcr_plate(seal_type="clear_adhesive_film")
E. sterilize_in_muffle_furnace(temperature_c=500, duration_h=5)
F. pipette_master_mix(destination="96_well_pcr_plate", volume_ul=20)
G. place_tube_on_magnetic_rack(duration_min=3)
H. incubate_on_roller(speed_rpm=20, duration_h=1, temperature_c=25)
I. wash_pellet(buffer="cold_70_percent_ethanol", volume_ul=400)
J. sonicate_coverslips(solvent="95_percent_ethanol", duration_min=15)

Answer: B

Reasoning steps:
1. The three views show a PCR thermal cycler, which is used for controlled
temperature incubation or cycling of reactions in PCR tubes or plates.
2. The current task is not clarification, vortex mixing, plate sealing, or
high-temperature sterilization; it is an enzyme digestion reaction.
3. The protocol specifies incubation at 37 C for 30 min in a thermal cycler.
4. Therefore, the operation that matches both the asset and protocol evidence is
incubate_in_thermal_cycler(temperature_c=37, duration_min=30).
""".strip()


@dataclass(frozen=True)
class InventoryEntry:
    entry_id: str
    entry_name: str
    match_group: str
    aliases: tuple[str, ...]
    purpose: str
    source_project: str
    reference_kind: str
    views: dict[str, str]


@dataclass(frozen=True)
class ProtocolCandidate:
    protocol_id: str
    title: str
    matched_group: str
    background_excerpt: str
    relevant_steps: tuple[dict[str, Any], ...]
    score: int


@dataclass(frozen=True)
class QuestionJob:
    entry: InventoryEntry
    protocol: ProtocolCandidate
    selected_views: tuple[tuple[str, str], ...]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc


def compact_text(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def make_search_terms(entry: InventoryEntry) -> tuple[str, ...]:
    terms: list[str] = []
    terms.extend(entry.aliases)
    terms.append(entry.entry_name)
    terms.append(entry.match_group.replace("_", " "))
    terms.extend(entry.match_group.split("_"))

    normalized: list[str] = []
    seen: set[str] = set()
    for term in terms:
        cleaned = normalize_key(term)
        if not cleaned or cleaned in seen:
            continue
        if len(cleaned) < 4 and cleaned not in {"pcr"}:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return tuple(normalized)


def count_term_hits(text: str, terms: tuple[str, ...]) -> int:
    normalized = normalize_key(text)
    hits = 0
    for term in terms:
        if term in normalized:
            hits += 1
    return hits


def load_inventory_entries(
    inventory_path: Path,
    manifest_path: Path,
    *,
    include_scenes: bool,
) -> dict[str, InventoryEntry]:
    inventory_items = load_json(inventory_path)
    inventory_by_id = {item["entry_id"]: item for item in inventory_items}

    manifest = load_json(manifest_path)
    entries: dict[str, InventoryEntry] = {}
    for manifest_entry in manifest.get("entries", []):
        entry_id = manifest_entry.get("entry_id")
        inventory_entry = inventory_by_id.get(entry_id)
        if not inventory_entry:
            continue
        if not include_scenes and not inventory_entry.get("protocol_matchable", False):
            continue

        views = {}
        for view_name, relative_path in manifest_entry.get("views", {}).items():
            if (REPO_ROOT / relative_path).is_file():
                views[view_name] = relative_path
        if len(views) < 3:
            continue

        entries[entry_id] = InventoryEntry(
            entry_id=entry_id,
            entry_name=inventory_entry.get("entry_name", manifest_entry.get("entry_name", entry_id)),
            match_group=inventory_entry.get("match_group", ""),
            aliases=tuple(inventory_entry.get("aliases", [])),
            purpose=inventory_entry.get("purpose", ""),
            source_project=inventory_entry.get("source_project", manifest_entry.get("source_project", "")),
            reference_kind=inventory_entry.get("reference_kind", manifest_entry.get("reference_kind", "")),
            views=views,
        )
    return entries


def extract_relevant_steps(
    protocol_row: dict[str, Any],
    terms: tuple[str, ...],
    *,
    max_steps: int,
) -> tuple[dict[str, Any], ...]:
    steps = protocol_row.get("procedure", {}).get("steps", [])
    scored: list[dict[str, Any]] = []
    for step in steps:
        description = step.get("description", "")
        stage = step.get("stage", "")
        text = f"{stage} {description}"
        hit_count = count_term_hits(text, terms)
        if hit_count <= 0:
            continue
        scored.append(
            {
                "idx": step.get("idx"),
                "stage": compact_text(stage, 140),
                "description": compact_text(description, 850),
                "score": hit_count,
            }
        )

    scored.sort(key=lambda item: (-int(item["score"]), int(item.get("idx") or 10_000)))
    selected = scored[:max_steps]
    selected.sort(key=lambda item: int(item.get("idx") or 10_000))
    return tuple(selected)


def load_protocol_candidates(
    protocol_matches_path: Path,
    entries_by_id: dict[str, InventoryEntry],
    *,
    max_steps_per_protocol: int,
    max_protocols_per_entry: int,
) -> dict[str, list[ProtocolCandidate]]:
    protocols_by_entry: dict[str, list[ProtocolCandidate]] = {entry_id: [] for entry_id in entries_by_id}

    for protocol_row in iter_jsonl(protocol_matches_path):
        protocol_id = protocol_row.get("id", "")
        title = protocol_row.get("title", "")
        background_excerpt = compact_text(protocol_row.get("background", ""), 1400)
        for candidate in protocol_row.get("candidate_entries", []):
            entry_id = candidate.get("entry_id")
            entry = entries_by_id.get(entry_id)
            if entry is None:
                continue

            terms = make_search_terms(entry)
            relevant_steps = extract_relevant_steps(
                protocol_row,
                terms,
                max_steps=max_steps_per_protocol,
            )
            if not relevant_steps:
                continue

            step_score = sum(int(step.get("score") or 0) for step in relevant_steps)
            score = step_score + count_term_hits(background_excerpt, terms)
            protocols_by_entry[entry_id].append(
                ProtocolCandidate(
                    protocol_id=protocol_id,
                    title=title,
                    matched_group=candidate.get("match_group", entry.match_group),
                    background_excerpt=background_excerpt,
                    relevant_steps=relevant_steps,
                    score=score,
                )
            )

    for entry_id, candidates in protocols_by_entry.items():
        candidates.sort(key=lambda item: (-item.score, item.protocol_id))
        del candidates[max_protocols_per_entry:]
    return protocols_by_entry


def select_three_views(entry: InventoryEntry, rng: random.Random) -> tuple[tuple[str, str], ...]:
    preferred = [view for view in DEFAULT_VIEW_ORDER if view in entry.views]
    remainder = [view for view in entry.views if view not in preferred]
    available = preferred + sorted(remainder)
    if len(available) < 3:
        raise ValueError(f"{entry.entry_id} has fewer than three rendered views")
    selected = rng.sample(available, 3)
    return tuple((view_name, entry.views[view_name]) for view_name in selected)


def build_jobs(
    entries_by_id: dict[str, InventoryEntry],
    protocols_by_entry: dict[str, list[ProtocolCandidate]],
    *,
    count: int,
    seed: int,
) -> list[QuestionJob]:
    rng = random.Random(seed)
    eligible_entries = [
        entry
        for entry in entries_by_id.values()
        if protocols_by_entry.get(entry.entry_id)
    ]
    eligible_entries.sort(key=lambda item: item.entry_id)
    rng.shuffle(eligible_entries)

    jobs: list[QuestionJob] = []
    used_pairs: set[tuple[str, str]] = set()
    while len(jobs) < count:
        made_progress = False
        for entry in eligible_entries:
            available_protocols = [
                protocol
                for protocol in protocols_by_entry[entry.entry_id]
                if (entry.entry_id, protocol.protocol_id) not in used_pairs
            ]
            if not available_protocols:
                continue
            protocol = rng.choice(available_protocols[: min(12, len(available_protocols))])
            used_pairs.add((entry.entry_id, protocol.protocol_id))
            jobs.append(
                QuestionJob(
                    entry=entry,
                    protocol=protocol,
                    selected_views=select_three_views(entry, rng),
                )
            )
            made_progress = True
            if len(jobs) >= count:
                break
        if not made_progress:
            break

    if len(jobs) < count:
        raise RuntimeError(
            f"Only built {len(jobs)} jobs; requested {count}. "
            "Try lowering --count or --max-protocols-per-entry."
        )
    return jobs


def read_demo_template(path: Path, max_chars: int) -> str:
    """Return an English template derived from the repository's Chinese demos.

    The source demo file remains useful as the human reference, but the model
    prompt must stay English-only so generated benchmark items do not inherit
    Chinese wording from the demo document.
    """
    _ = path
    if max_chars <= 0:
        return ""
    return compact_text(ENGLISH_DEMO_TEMPLATE, max_chars)


def option_letters(count: int) -> list[str]:
    if count < 2 or count > 10:
        raise ValueError("--option-count must be between 2 and 10")
    return [chr(ord("A") + idx) for idx in range(count)]


def render_protocol_steps(protocol: ProtocolCandidate) -> str:
    lines = []
    for step in protocol.relevant_steps:
        lines.append(
            f"- Step {step.get('idx')} | {step.get('stage')}: {step.get('description')}"
        )
    return "\n".join(lines)


def make_messages(job: QuestionJob, demo_template: str, option_count: int) -> list[dict[str, str]]:
    letters = option_letters(option_count)
    schema = {
        "question": "English question stem. Include experiment context, current sample state, and ask for the best next operation based on the three-view asset.",
        "options": {letter: "Candidate operation, preferably a valid and concise Python function call." for letter in letters},
        "reasoning_steps": ["3-5 English reasoning steps."],
        "answer": letters[0],
        "protocol_alignment": {
            "protocol_id": job.protocol.protocol_id,
            "title": job.protocol.title,
            "step_indices": [step.get("idx") for step in job.protocol.relevant_steps[:2]],
            "explanation": "Explain in English how the correct answer aligns with the protocol step and visual asset."
        },
    }

    selected_images = "\n".join(
        f"- {view_name}: {image_path}" for view_name, image_path in job.selected_views
    )
    aliases = ", ".join(job.entry.aliases[:12]) if job.entry.aliases else "(none)"
    template_section = f"\n\nUse this English example as the style and structure template:\n{demo_template}" if demo_template else ""

    system = (
        "You are the LabOS benchmark Level 1 data builder. Build one "
        "multiple-choice asset-understanding question from the given lab asset, "
        "three-view image paths, and real protocol snippets. Output strict JSON "
        "only, with no markdown, no code fences, and no explanatory prefix or suffix. "
        "All generated natural-language fields must be in English."
    )
    user = f"""
Build 1 Level 1: Asset Understanding multiple-choice question.

Hard requirements:
1. Write all generated natural-language fields in English only.
2. The question must be grounded in the same asset or scene shown by the three
   image paths. Do not rewrite or invent image paths.
3. The correct option must be directly supported by the provided protocol steps.
   Preserve protocol parameters such as temperature, duration, speed, force, and
   volume when they matter.
4. Distractors should be plausible lab operations but incompatible with the
   asset, current sample state, or cited protocol step.
5. Options must be exactly {", ".join(letters)}, and answer must be one of those single letters.
6. reasoning_steps must contain 3-5 English strings explaining visual asset
   recognition, sample/protocol state, relevant parameters, and why distractors
   are less appropriate.
7. Do not reveal the correct answer in the question stem.
8. Output exactly one JSON object matching the schema below.

Output schema example:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Current asset:
- entry_id: {job.entry.entry_id}
- entry_name: {job.entry.entry_name}
- source_project: {job.entry.source_project}
- reference_kind: {job.entry.reference_kind}
- match_group: {job.entry.match_group}
- aliases: {aliases}
- purpose: {job.entry.purpose}

Selected three-view image paths:
{selected_images}

Relevant protocol:
- protocol_id: {job.protocol.protocol_id}
- title: {job.protocol.title}
- matched_group: {job.protocol.matched_group}
- background_excerpt: {job.protocol.background_excerpt}

Available protocol step snippets:
{render_protocol_steps(job.protocol)}
{template_section}
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def get_api_key(*, read_from_stdin: bool) -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    if read_from_stdin:
        key = sys.stdin.readline().strip()
        if key:
            return key
    if sys.stdin.isatty():
        key = getpass.getpass("OpenRouter API key: ").strip()
        if key:
            return key
    raise RuntimeError("Set OPENROUTER_API_KEY or pass --api-key-stdin and provide the key on stdin.")


def openrouter_chat_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/InternScience/LabOS",
            "X-Title": "LabOS Level 1 Pipeline",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {compact_text(body, 1200)}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

    data = json.loads(body)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected OpenRouter response: {compact_text(body, 1200)}") from exc


def parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Model output is not a JSON object")
    return value


def contains_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def assert_english_text(value: Any, field_path: str) -> None:
    if isinstance(value, str):
        if contains_cjk(value):
            raise ValueError(f"{field_path} contains CJK text")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            assert_english_text(item, f"{field_path}[{idx}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_english_text(item, f"{field_path}.{key}")


def validate_generated_question(value: dict[str, Any], option_count: int) -> None:
    required = {"question", "options", "reasoning_steps", "answer"}
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    if not isinstance(value["question"], str) or not value["question"].strip():
        raise ValueError("question must be a non-empty string")
    assert_english_text(value["question"], "question")
    if not isinstance(value["options"], dict):
        raise ValueError("options must be an object")

    letters = option_letters(option_count)
    option_keys = sorted(value["options"].keys())
    if option_keys != letters:
        raise ValueError(f"options must contain exactly {letters}, got {option_keys}")
    for letter in letters:
        if not isinstance(value["options"][letter], str) or not value["options"][letter].strip():
            raise ValueError(f"option {letter} must be a non-empty string")
        assert_english_text(value["options"][letter], f"options.{letter}")

    answer = value["answer"]
    if not isinstance(answer, str) or answer.strip() not in letters:
        raise ValueError(f"answer must be one of {letters}")
    value["answer"] = answer.strip()

    reasoning_steps = value["reasoning_steps"]
    if not isinstance(reasoning_steps, list) or not (2 <= len(reasoning_steps) <= 6):
        raise ValueError("reasoning_steps must be a list with 2-6 items")
    for idx, step in enumerate(reasoning_steps, 1):
        if not isinstance(step, str) or not step.strip():
            raise ValueError(f"reasoning_steps[{idx}] must be a non-empty string")
        assert_english_text(step, f"reasoning_steps[{idx}]")

    if "protocol_alignment" in value:
        assert_english_text(value["protocol_alignment"], "protocol_alignment")


def build_record(question_id: str, job: QuestionJob, generated: dict[str, Any]) -> dict[str, Any]:
    source_step_indices = [step.get("idx") for step in job.protocol.relevant_steps]
    return {
        "question_id": question_id,
        "entry_id": job.entry.entry_id,
        "entry_name": job.entry.entry_name,
        "asset_family": job.entry.match_group,
        "source_project": job.entry.source_project,
        "image_paths": [image_path for _, image_path in job.selected_views],
        "views": [
            {"view": view_name, "path": image_path}
            for view_name, image_path in job.selected_views
        ],
        "question": generated["question"].strip(),
        "options": {
            letter: generated["options"][letter].strip()
            for letter in sorted(generated["options"])
        },
        "reasoning_steps": [step.strip() for step in generated["reasoning_steps"]],
        "answer": generated["answer"].strip(),
        "source_protocol_id": job.protocol.protocol_id,
        "source_protocol_title": job.protocol.title,
        "source_protocol_step_indices": source_step_indices,
        "protocol_alignment": generated.get("protocol_alignment", {}),
    }


def generate_question_for_job(
    job: QuestionJob,
    *,
    api_key: str,
    model: str,
    demo_template: str,
    option_count: int,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
    retries: int,
) -> dict[str, Any]:
    messages = make_messages(job, demo_template, option_count)
    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            content = openrouter_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
            )
            generated = parse_json_object(content)
            validate_generated_question(generated, option_count)
            return generated
        except Exception as exc:  # noqa: BLE001 - report model/API validation context.
            last_error = exc
            if attempt <= retries:
                time.sleep(min(2.0 * attempt, 8.0))
    raise RuntimeError(f"Failed after {retries + 1} attempt(s): {last_error}")


def write_outputs(records: list[dict[str, Any]], output_path: Path, metadata: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    jsonl_path = output_path.with_suffix(".jsonl")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    metadata_path = output_path.with_name(output_path.stem + ".metadata.json")
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=20, help="Number of questions to generate.")
    parser.add_argument("--seed", type=int, default=20260423, help="Random seed for entry/protocol/view selection.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSON path.")
    parser.add_argument("--option-count", type=int, default=10, help="Number of answer options, 2-10.")
    parser.add_argument("--temperature", type=float, default=0.35, help="Generation temperature.")
    parser.add_argument("--max-tokens", type=int, default=2200, help="Max output tokens per question.")
    parser.add_argument("--timeout-s", type=float, default=90.0, help="HTTP timeout per API call.")
    parser.add_argument("--retries", type=int, default=2, help="Retries per question after API/validation failure.")
    parser.add_argument("--sleep-s", type=float, default=0.2, help="Sleep between successful API calls.")
    parser.add_argument("--api-key-stdin", action="store_true", help="Read the API key from the first stdin line.")
    parser.add_argument("--include-scenes", action="store_true", help="Allow non-protocol-matchable scene entries if they have matches.")
    parser.add_argument("--dry-run", action="store_true", help="Print selected jobs without calling OpenRouter.")
    parser.add_argument("--template-max-chars", type=int, default=16000, help="Max chars from level-1-demo.md included in prompts.")
    parser.add_argument("--max-steps-per-protocol", type=int, default=8, help="Max protocol snippets sent to the model.")
    parser.add_argument("--max-protocols-per-entry", type=int, default=80, help="Max protocol candidates retained per entry.")
    parser.add_argument("--multiview-manifest", type=Path, default=DEFAULT_MULTIVIEW_MANIFEST)
    parser.add_argument("--core-inventory", type=Path, default=DEFAULT_CORE_INVENTORY)
    parser.add_argument("--protocol-matches", type=Path, default=DEFAULT_PROTOCOL_MATCHES)
    parser.add_argument("--demo-template", type=Path, default=DEFAULT_DEMO_TEMPLATE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    option_letters(args.option_count)

    entries_by_id = load_inventory_entries(
        args.core_inventory,
        args.multiview_manifest,
        include_scenes=args.include_scenes,
    )
    protocols_by_entry = load_protocol_candidates(
        args.protocol_matches,
        entries_by_id,
        max_steps_per_protocol=args.max_steps_per_protocol,
        max_protocols_per_entry=args.max_protocols_per_entry,
    )
    jobs = build_jobs(
        entries_by_id,
        protocols_by_entry,
        count=args.count,
        seed=args.seed,
    )

    if args.dry_run:
        for idx, job in enumerate(jobs, 1):
            views = ", ".join(view for view, _ in job.selected_views)
            print(
                f"{idx:03d} {job.entry.entry_id} | {job.protocol.protocol_id} | "
                f"steps={list(step.get('idx') for step in job.protocol.relevant_steps[:4])} | views={views}"
            )
        return 0

    api_key = get_api_key(read_from_stdin=args.api_key_stdin)
    demo_template = read_demo_template(args.demo_template, args.template_max_chars)
    records: list[dict[str, Any]] = []

    for idx, job in enumerate(jobs, 1):
        question_id = f"level1_q{idx:04d}"
        print(
            f"[{idx}/{len(jobs)}] generating {question_id}: "
            f"{job.entry.entry_id} x {job.protocol.protocol_id}",
            file=sys.stderr,
            flush=True,
        )
        generated = generate_question_for_job(
            job,
            api_key=api_key,
            model=args.model,
            demo_template=demo_template,
            option_count=args.option_count,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout_s=args.timeout_s,
            retries=args.retries,
        )
        records.append(build_record(question_id, job, generated))
        if args.sleep_s > 0:
            time.sleep(args.sleep_s)

    metadata = {
        "count": len(records),
        "seed": args.seed,
        "model": args.model,
        "option_count": args.option_count,
        "multiview_manifest": str(args.multiview_manifest.relative_to(REPO_ROOT)),
        "core_inventory": str(args.core_inventory.relative_to(REPO_ROOT)),
        "protocol_matches": str(args.protocol_matches.relative_to(REPO_ROOT)),
        "demo_template": str(args.demo_template.relative_to(REPO_ROOT)),
    }
    write_outputs(records, args.output, metadata)
    print(f"Wrote {len(records)} questions to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
