#!/usr/bin/env python3
"""Build LabOS Level 1 asset-understanding questions.

The pipeline uses the repository's benchmark inventory, rendered multiview
images, and protocol-to-inventory matches to build one multiple-choice question
per selected asset/protocol pair. OpenRouter credentials may be loaded from a
local ignored `.env` file, environment variables, stdin, or an interactive
prompt.
"""

from __future__ import annotations

import argparse
import ast
import getpass
import importlib.util
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = Path(__file__).with_name(".env")
DEFAULT_MULTIVIEW_MANIFEST = REPO_ROOT / "data/benchmark_inventory/multiview_manifest.json"
DEFAULT_CORE_INVENTORY = REPO_ROOT / "data/benchmark_inventory/benchmark_core_inventory.json"
DEFAULT_PROTOCOL_MATCHES = REPO_ROOT / "data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl"
DEFAULT_DEMO_TEMPLATE = REPO_ROOT / "data/benchmark_inventory/level-1-demo.md"
DEFAULT_OUTPUT = REPO_ROOT / "pipeline/level-1/generated/level1_questions_20.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_EVALUATOR_MODULE: Any | None = None
NONE_OF_ABOVE_CALL = "none_of_the_above()"
GROUPED_OPTION_TRIOS = (("A", "B", "C"), ("D", "E", "F"), ("G", "H", "I"))
QUESTION_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?(?:[–-]\d+(?:\.\d+)?)?\b")
QUESTION_SEQUENCE_CUES = (
    "already",
    "just",
    "after",
    "before",
    "previous",
    "prior",
    "then",
    "next",
)


def parse_dotenv_value(raw_value: str) -> str:
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_dotenv_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()
        if "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = parse_dotenv_value(raw_value)


def load_local_env() -> None:
    load_dotenv_file(REPO_ROOT / ".env")
    load_dotenv_file(DEFAULT_ENV_PATH)


load_local_env()

DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-5.4")
DEFAULT_VIEW_ORDER = ("front", "right", "left", "top", "free", "back", "bottom")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")
ZERO_VALUE_ARG_RE = re.compile(
    r"\b(?:duration_[a-z]+|volume_[a-z]+|force_[a-z]+)\s*=\s*(?:0\.0+|0(?!\.))\b"
)
SUSPICIOUS_DISTRACTOR_TOKENS = (
    "autoclave",
    "parafilm",
    "manipulator",
    "gripper",
    "robot",
    "wrist",
    "sonicate",
    "coverslip",
    "muffle_furnace",
)
PASSIVE_HOLDER_GROUPS = {"tube_rack", "pipette_rack", "tip_box"}
PASSIVE_CONTAINER_GROUPS = {
    "cell_dish",
    "microcentrifuge_tube_1_5ml",
    "centrifuge_tube_10ml",
    "centrifuge_tube_15ml",
    "centrifuge_tube_50ml",
    "cryovial",
    "pcr_plate",
    "beaker",
    "conical_bottle",
    "graduated_cylinder",
}
ACTIVE_DEVICE_GROUPS = {
    "centrifuge",
    "thermal_cycler",
    "thermal_mixer",
    "vortex_mixer",
    "drying_box",
    "heating_device",
    "muffle_furnace",
}
HARDER_PRIORITY_GROUPS = {
    "centrifuge",
    "thermal_cycler",
    "thermal_mixer",
    "vortex_mixer",
    "drying_box",
    "heating_device",
    "muffle_furnace",
    "pipette",
    "pcr_plate",
    "tip_box",
    "pipette_rack",
}
GENERIC_STEM_CUE_PHRASE_SOURCE = (
    "asset function",
    "asset's function",
    "container's capacity",
    "container capacity",
    "container's structural design",
    "container's physical design",
    "vessel's capacity",
    "vessel's dimensions",
    "device's rotational function",
    "volumetric measuring tool",
    "passive storage function",
    "gentle handling",
    "passive sample container",
    "visual features of this volumetric measuring tool",
)
DISALLOWED_ENTRY_IDS = {
    # This multi-well rack repeatedly invites unsupported magnetic-rack or
    # sealing distractors and is a weak Level 1 benchmark candidate.
    "autobio_centrifuge_plate_60well",
    # GPT-5.4 repeatedly leaks the asset family for active centrifuge devices in
    # the question stem even after targeted repair prompts. Excluding the
    # unstable device entries keeps the batch generator reliable without
    # removing the passive tube-style centrifuge consumables.
    "autobio_centrifuge_5430",
    "autobio_centrifuge_5910_ri",
    "autobio_centrifuge_tgear_mini",
}
SPECIALIZED_REVEAL_TERMS = {
    "beaker",
    "centrifuge",
    "cryovial",
    "graduated cylinder",
    "muffle furnace",
    "pipette",
    "pipette rack",
    "pcr plate",
    "thermal cycler",
    "thermal mixer",
    "thermocycler",
    "tip box",
    "tube rack",
    "vortex mixer",
}

ENGLISH_DEMO_TEMPLATE = """
Example structure:

Question:
You have already mixed the ligation reaction, quick-spun the tube, and kept the
sample on ice for 2 min. The pictured bench device is now used for the next
stage before transformation. According to the protocol, the reaction should be
held at 16 C for 30 min and then moved immediately to ice. Which operation is
the best match for this exact stage?

Options:
A. incubate_reaction(temperature_c=16, duration_min=20, post_step='move_to_ice')
B. incubate_reaction(temperature_c=16, duration_min=30, post_step='move_to_ice')
C. incubate_reaction(temperature_c=18, duration_min=30, post_step='move_to_ice')
D. centrifuge_sample(speed_xg=12000, duration_min=1, temperature_c=4)
E. centrifuge_sample(speed_xg=12000, duration_min=2, temperature_c=4)
F. centrifuge_sample(speed_xg=14000, duration_min=2, temperature_c=4)
G. add_competent_cells(volume_ul=50, temperature_c=0)
H. add_competent_cells(volume_ul=25, temperature_c=0)
I. add_competent_cells(volume_ul=50, temperature_c=4)
J. none_of_the_above()

Answer: B

Reasoning steps:
1. The stem already specifies the immediately preceding actions and two concrete
protocol numbers, so the decision is about the exact next operation rather than
a broad workflow category.
2. A-C form one action family with only subtle parameter changes, and only B
matches the required 16 C for 30 min before returning the sample to ice.
3. D-F are a nearby centrifugation family that could happen elsewhere in the
workflow but not at this stage.
4. G-I are a later transformation-loading family, again plausible in the same
protocol but not the next action here.
5. Because one of A-I exactly matches the target step, J is incorrect.
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
    nearby_steps: tuple[dict[str, Any], ...]
    score: int


@dataclass(frozen=True)
class QuestionJob:
    entry: InventoryEntry
    protocol: ProtocolCandidate
    selected_views: tuple[tuple[str, str], ...]
    target_answer_letter: str = "A"


def entry_difficulty_rank(entry: InventoryEntry) -> int:
    if entry.match_group in ACTIVE_DEVICE_GROUPS:
        return 0
    if entry.match_group in HARDER_PRIORITY_GROUPS:
        return 1
    if entry.match_group in PASSIVE_CONTAINER_GROUPS:
        return 3
    return 2


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_level1_evaluator_module() -> Any:
    global _EVALUATOR_MODULE
    if _EVALUATOR_MODULE is not None:
        return _EVALUATOR_MODULE
    evaluator_path = REPO_ROOT / "pipeline/level-1/evaluate_level1_accuracy.py"
    spec = importlib.util.spec_from_file_location("labos_level1_evaluator", evaluator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load evaluator module from {evaluator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _EVALUATOR_MODULE = module
    return module


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


GENERIC_STEM_CUE_PHRASES = tuple(normalize_key(value) for value in GENERIC_STEM_CUE_PHRASE_SOURCE)


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
        if entry_id in DISALLOWED_ENTRY_IDS:
            continue
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


def extract_nearby_steps(
    protocol_row: dict[str, Any],
    relevant_steps: tuple[dict[str, Any], ...],
    *,
    max_steps: int,
    distance_window: int = 2,
) -> tuple[dict[str, Any], ...]:
    if not relevant_steps:
        return ()

    relevant_indices = {
        int(step["idx"])
        for step in relevant_steps
        if step.get("idx") is not None
    }
    relevant_stages = {
        normalize_key(str(step.get("stage") or ""))
        for step in relevant_steps
        if step.get("stage")
    }

    scored: list[dict[str, Any]] = []
    for step in protocol_row.get("procedure", {}).get("steps", []):
        step_idx = step.get("idx")
        if step_idx is None:
            continue
        step_idx = int(step_idx)
        if step_idx in relevant_indices:
            continue

        stage = compact_text(step.get("stage", ""), 140)
        description = compact_text(step.get("description", ""), 850)
        normalized_stage = normalize_key(stage)
        min_distance = min(abs(step_idx - idx) for idx in relevant_indices)
        same_stage = normalized_stage in relevant_stages if normalized_stage else False
        if min_distance > distance_window:
            continue

        scored.append(
            {
                "idx": step_idx,
                "stage": stage,
                "description": description,
                "distance": min_distance,
                "same_stage": same_stage,
            }
        )

    scored.sort(key=lambda item: (item["distance"], not item["same_stage"], item["idx"]))
    selected = scored[:max_steps]
    selected.sort(key=lambda item: int(item["idx"]))
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
            nearby_steps = extract_nearby_steps(
                protocol_row,
                relevant_steps,
                max_steps=max_steps_per_protocol,
            )

            step_score = sum(int(step.get("score") or 0) for step in relevant_steps)
            score = step_score + count_term_hits(background_excerpt, terms)
            protocols_by_entry[entry_id].append(
                ProtocolCandidate(
                    protocol_id=protocol_id,
                    title=title,
                    matched_group=candidate.get("match_group", entry.match_group),
                    background_excerpt=background_excerpt,
                    relevant_steps=relevant_steps,
                    nearby_steps=nearby_steps,
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
    primary_entries = [
        entry for entry in eligible_entries if entry.match_group not in PASSIVE_CONTAINER_GROUPS
    ]
    fallback_entries = [
        entry for entry in eligible_entries if entry.match_group in PASSIVE_CONTAINER_GROUPS
    ]
    primary_entries.sort(key=lambda item: (entry_difficulty_rank(item), rng.random(), item.entry_id))
    fallback_entries.sort(key=lambda item: (entry_difficulty_rank(item), rng.random(), item.entry_id))
    ordered_entry_groups = [primary_entries]
    if fallback_entries:
        ordered_entry_groups.append(fallback_entries)

    jobs: list[QuestionJob] = []
    used_pairs: set[tuple[str, str]] = set()
    used_protocol_ids: set[str] = set()
    while len(jobs) < count:
        made_progress = False
        for entries in ordered_entry_groups:
            for entry in entries:
                available_protocols = [
                    protocol
                    for protocol in protocols_by_entry[entry.entry_id]
                    if (entry.entry_id, protocol.protocol_id) not in used_pairs
                ]
                if not available_protocols:
                    continue
                unseen_protocols = [
                    protocol for protocol in available_protocols if protocol.protocol_id not in used_protocol_ids
                ]
                candidate_pool = unseen_protocols or available_protocols
                protocol = rng.choice(candidate_pool[: min(12, len(candidate_pool))])
                used_pairs.add((entry.entry_id, protocol.protocol_id))
                used_protocol_ids.add(protocol.protocol_id)
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


def build_target_answer_letters(
    count: int,
    option_count: int,
    seed: int,
    *,
    none_above_rate: float,
) -> list[str]:
    letters = option_letters(option_count)
    rng = random.Random(seed + 97)
    none_letter = letters[-1]
    base_letters = letters[:-1]
    none_count = 0
    if none_above_rate > 0:
        none_count = max(1, round(count * none_above_rate))
        none_count = min(count, none_count)
    assigned = [none_letter] * none_count
    assigned.extend(base_letters[idx % len(base_letters)] for idx in range(count - none_count))
    rng.shuffle(assigned)
    return assigned


def render_steps(steps: tuple[dict[str, Any], ...]) -> str:
    lines = []
    for step in steps:
        lines.append(
            f"- Step {step.get('idx')} | {step.get('stage')}: {step.get('description')}"
        )
    return "\n".join(lines)


def render_protocol_steps(protocol: ProtocolCandidate) -> str:
    return render_steps(protocol.relevant_steps)


def render_nearby_steps(protocol: ProtocolCandidate) -> str:
    return render_steps(protocol.nearby_steps)


def build_affordance_guardrails(entry: InventoryEntry) -> str:
    generic = f"- Asset purpose: {entry.purpose or 'No purpose text available.'}"
    if entry.match_group in PASSIVE_HOLDER_GROUPS:
        constraint = (
            "- Treat the pictured asset as a passive holder or organizer. Do not invent "
            "powered, magnetic, heating, mixing, or centrifugation capabilities unless "
            "the asset metadata explicitly states them."
        )
    elif entry.match_group in PASSIVE_CONTAINER_GROUPS:
        constraint = (
            "- Treat the pictured asset as a passive vessel, measuring item, or sample "
            "container. Do not describe it as a powered instrument."
        )
    elif entry.match_group == "pipette":
        constraint = (
            "- Treat the pictured asset as a manual liquid-handling tool. Plausible "
            "operations should center on aspirating, dispensing, or transferring liquid."
        )
    elif entry.match_group == "pipette_tip":
        constraint = (
            "- Treat the pictured asset as a disposable consumable tip. Do not turn it "
            "into a storage rack, heater, mixer, or measurement device."
        )
    elif entry.match_group in ACTIVE_DEVICE_GROUPS:
        constraint = (
            "- Treat the pictured asset as a specialized powered device. The correct "
            "operation must fit the device's real function and the provided protocol."
        )
    else:
        constraint = (
            "- Stay within the explicit asset purpose and protocol evidence; do not invent "
            "specialized capabilities that are not supported by the metadata."
        )
    return "\n".join((generic, constraint))


def make_messages(job: QuestionJob, demo_template: str, option_count: int) -> list[dict[str, str]]:
    letters = option_letters(option_count)
    schema = {
        "question": (
            "English question stem. Include concrete protocol numbers, at least one or two prior actions already completed, "
            "the current sample state, and the next-step decision. Do not name the asset, brand, asset family, or aliases in the stem."
        ),
        "options": {letter: "Candidate operation as a valid Python function call." for letter in letters},
        "reasoning_steps": ["3-5 English reasoning steps."],
        "answer": job.target_answer_letter,
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
    affordance_guardrails = build_affordance_guardrails(job.entry)
    forbidden_stem_terms = forbidden_stem_terms_text(job.entry)
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
4. The question stem must include concrete protocol details: at least two numeric
   values and at least two prior or current workflow actions that have already
   happened before the decision point.
5. The question stem must NOT mention the asset's entry_name, brand, match_group,
   aliases, or obvious type labels such as "thermal cycler", "pipette", "centrifuge",
   "tube rack", "graduated cylinder", "beaker", or "muffle furnace". Refer to it
   only indirectly, for example "the item shown in the three views" or "the pictured lab object".
   Treat the forbidden stem terms list below as an exact banned vocabulary list for
   the stem. Do not use any of those words even as a generic noun.
6. The question must be hard because the protocol stage and parameter details are
   specific. Visual alignment is still required, but it does not need to be the
   only decisive signal.
7. Do NOT give away the answer direction by describing the object as a "volumetric
   measuring tool", "passive storage function", "rotational function", "container
   capacity", "vessel dimensions", or similar functional hints in the question stem.
   Forbidden stem terms for this asset: {forbidden_stem_terms}
8. Options A-I must follow a fixed blueprint:
   - A-C are one action family.
   - D-F are a second action family.
   - G-I are a third action family.
   - Within each 3-option family, use the same function name and the same keyword set;
     only the keyword values may change.
   - Across A-I, use exactly three distinct function names.
9. The three action families must mix two error types:
   - nearby-step families from immediately before or after the target step, ideally
     within about two protocol steps of the target decision point,
   - subtle parameter rewrites of the target or nearby steps.
   Do not make the wrong options obviously irrelevant.
10. If the answer is not J, exactly one of A-I must be the target step with the
   correct parameters. The other two options in that same 3-option family must be
   close parameter variants that are still wrong, and each wrong variant should
   differ from the correct target by only one keyword value, preferably a small
   numeric change such as one duration, one temperature, one volume, one speed,
   one cycle count, or one measured distance. The other two 3-option families
   must come from realistic nearby protocol actions.
11. If the answer is J, J must be exactly {NONE_OF_ABOVE_CALL}, and every option in
    A-I must be plausible but still wrong. In that case, include one 3-option family
    that is very close to the target step but has subtle wrong numbers differing
    by only one keyword value at a time, plus two 3-option nearby-step families
    from the same local protocol window.
12. Option J must always be exactly {NONE_OF_ABOVE_CALL}.
13. Do not use obviously irrelevant distractors such as autoclaving, parafilm sealing,
   robotic manipulation, sonication, or furnace operations unless those ideas are
   explicitly supported by the provided protocol context.
14. Respect the asset affordance guardrails below. Do not invent specialized functions
    that the pictured asset cannot perform.
15. Options must be exactly {", ".join(letters)}. The correct option must be placed at
    letter {job.target_answer_letter}, and the answer field must be exactly "{job.target_answer_letter}".
16. reasoning_steps must contain 3-5 English strings explaining the completed prior
    actions, the exact numeric protocol evidence, which 3-option family is the true
    target family, and why the nearby-step families or subtle parameter variants are wrong.
17. Output exactly one JSON object matching the schema below.

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

Nearby protocol context that can inspire realistic distractors:
{render_nearby_steps(job.protocol) or "- (none)"}

Asset affordance guardrails:
{affordance_guardrails}
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


def parse_python_call(expr: str) -> ast.Call:
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid Python call syntax: {expr}") from exc
    if not isinstance(tree.body, ast.Call):
        raise ValueError(f"Option is not a Python call: {expr}")
    if not isinstance(tree.body.func, ast.Name):
        raise ValueError(f"Option must call a simple function name: {expr}")
    return tree.body


def option_function_name(expr: str) -> str:
    return parse_python_call(expr).func.id


def stem_reveal_terms(entry: InventoryEntry) -> tuple[str, ...]:
    raw_terms = [entry.entry_name, entry.match_group.replace("_", " "), *entry.aliases]
    phrases: set[str] = set()
    for term in raw_terms:
        normalized = normalize_key(term)
        if not normalized:
            continue
        if " " in normalized or normalized in SPECIALIZED_REVEAL_TERMS:
            phrases.add(normalized)
    return tuple(sorted(phrases))


def forbidden_stem_terms_text(entry: InventoryEntry) -> str:
    return ", ".join(stem_reveal_terms(entry)[:16]) or "(none)"


def build_context_text(job: QuestionJob) -> str:
    parts = [
        job.entry.purpose,
        job.entry.entry_name,
        job.entry.match_group.replace("_", " "),
        " ".join(job.entry.aliases),
        job.protocol.background_excerpt,
        render_protocol_steps(job.protocol),
        render_nearby_steps(job.protocol),
    ]
    return normalize_key(" ".join(part for part in parts if part))


def validate_question_stem(question: str, entry: InventoryEntry) -> None:
    normalized_question = normalize_key(question)
    leaked = [term for term in stem_reveal_terms(entry) if term and term in normalized_question]
    if leaked:
        raise ValueError(f"question leaks asset identity: {', '.join(leaked[:4])}")
    leaked_cues = [phrase for phrase in GENERIC_STEM_CUE_PHRASES if phrase and phrase in normalized_question]
    if leaked_cues:
        raise ValueError(f"question leaks functional hint: {', '.join(leaked_cues[:3])}")
    if len(QUESTION_NUMBER_RE.findall(question)) < 2:
        raise ValueError("question must include at least two concrete protocol numbers")
    if not any(cue in normalized_question for cue in QUESTION_SEQUENCE_CUES):
        raise ValueError("question must mention prior-step or sequencing context")


def option_keyword_signature(expr: str) -> tuple[str, ...]:
    call = parse_python_call(expr)
    return tuple(sorted((keyword.arg or "") for keyword in call.keywords))


def option_keyword_node_map(expr: str) -> dict[str, ast.AST]:
    call = parse_python_call(expr)
    return {(keyword.arg or ""): keyword.value for keyword in call.keywords}


def ast_node_signature(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=False, include_attributes=False)


def ast_node_contains_numeric_literal(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Constant) and isinstance(child.value, (int, float))
        for child in ast.walk(node)
    )


def validate_target_family_precision(value: dict[str, Any]) -> None:
    answer_letter = value["answer"]
    if answer_letter == "J":
        return

    target_trio = next(
        trio for trio in GROUPED_OPTION_TRIOS if answer_letter in trio
    )
    options = value["options"]
    answer_nodes = option_keyword_node_map(options[answer_letter])
    for letter in target_trio:
        if letter == answer_letter:
            continue
        candidate_nodes = option_keyword_node_map(options[letter])
        changed_keys = [
            key
            for key in sorted(answer_nodes)
            if ast_node_signature(answer_nodes[key]) != ast_node_signature(candidate_nodes[key])
        ]
        if len(changed_keys) != 1:
            raise ValueError(
                "target family variants must differ from the correct option by exactly one keyword value"
            )
        changed_key = changed_keys[0]
        if not (
            ast_node_contains_numeric_literal(answer_nodes[changed_key])
            and ast_node_contains_numeric_literal(candidate_nodes[changed_key])
        ):
            raise ValueError(
                "target family variants must differ through a numeric parameter change"
            )


def validate_option_text(option_letter: str, option_text: str, job: QuestionJob) -> None:
    call = parse_python_call(option_text)
    function_name = call.func.id
    if option_letter == "J":
        if option_text.strip() != NONE_OF_ABOVE_CALL:
            raise ValueError(f"option J must be exactly {NONE_OF_ABOVE_CALL}")
        return
    if function_name == "none_of_the_above":
        raise ValueError("only option J may use none_of_the_above()")
    normalized_option = normalize_key(option_text)
    context_text = build_context_text(job)

    if ZERO_VALUE_ARG_RE.search(option_text):
        raise ValueError(f"option contains an implausible zero-valued operational parameter: {option_text}")

    for token in SUSPICIOUS_DISTRACTOR_TOKENS:
        if token in normalized_option and token not in context_text:
            raise ValueError(f"option introduces off-context distractor token '{token}': {option_text}")

    if job.entry.match_group in PASSIVE_HOLDER_GROUPS and "magnetic" in normalized_option:
        asset_text = normalize_key(" ".join((job.entry.entry_name, job.entry.purpose, *job.entry.aliases)))
        if "magnetic" not in asset_text:
            raise ValueError(f"option invents magnetic functionality for passive holder asset: {option_text}")

    if job.entry.match_group == "pipette_rack" and any(
        token in function_name for token in ("aspirat", "dispens", "aliquot", "transfer", "dispense")
    ):
        raise ValueError(f"option treats a pipette rack as the liquid-handling tool: {option_text}")


def validate_difficulty_structure(value: dict[str, Any]) -> None:
    options = value["options"]
    answer_letter = value["answer"]
    option_values = list(options.values())
    if len(set(option_values)) != len(option_values):
        raise ValueError("options contain duplicate candidate strings")
    if options.get("J", "").strip() != NONE_OF_ABOVE_CALL:
        raise ValueError(f"option J must be exactly {NONE_OF_ABOVE_CALL}")

    trio_functions: list[str] = []
    for trio in GROUPED_OPTION_TRIOS:
        trio_values = [options[letter] for letter in trio]
        trio_function_names = [option_function_name(text) for text in trio_values]
        if len(set(trio_function_names)) != 1:
            raise ValueError(f"options {trio[0]}-{trio[-1]} must share the same function name")
        trio_keyword_signatures = [option_keyword_signature(text) for text in trio_values]
        if len(set(trio_keyword_signatures)) != 1:
            raise ValueError(f"options {trio[0]}-{trio[-1]} must share the same keyword set")
        trio_functions.append(trio_function_names[0])

    if len(set(trio_functions)) != len(trio_functions):
        raise ValueError("A-I must contain exactly three distinct action families")

    if answer_letter == "J":
        return

    if answer_letter not in {letter for trio in GROUPED_OPTION_TRIOS for letter in trio}:
        raise ValueError("non-J answers must point to one of A-I")

    answer_function = option_function_name(options[answer_letter])
    answer_family_count = trio_functions.count(answer_function)
    if answer_family_count != 1:
        raise ValueError(
            f"answer family '{answer_function}' must occupy exactly one 3-option trio"
        )
    validate_target_family_precision(value)


def validate_generated_question(value: dict[str, Any], option_count: int, job: QuestionJob) -> None:
    required = {"question", "options", "reasoning_steps", "answer"}
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    if not isinstance(value["question"], str) or not value["question"].strip():
        raise ValueError("question must be a non-empty string")
    assert_english_text(value["question"], "question")
    validate_question_stem(value["question"], job.entry)
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
        validate_option_text(letter, value["options"][letter], job)

    answer = value["answer"]
    if not isinstance(answer, str) or answer.strip() not in letters:
        raise ValueError(f"answer must be one of {letters}")
    value["answer"] = answer.strip()
    if value["answer"] != job.target_answer_letter:
        raise ValueError(
            f"answer must be exactly '{job.target_answer_letter}' for this item, got '{value['answer']}'"
        )
    validate_difficulty_structure(value)

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
    source_nearby_step_indices = [step.get("idx") for step in job.protocol.nearby_steps]
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
        "source_protocol_nearby_step_indices": source_nearby_step_indices,
        "protocol_alignment": generated.get("protocol_alignment", {}),
    }


def partial_output_path(output_path: Path) -> Path:
    return output_path.with_suffix(".partial.jsonl")


def load_partial_records(path: Path) -> dict[int, dict[str, Any]]:
    if not path.is_file():
        return {}
    loaded: dict[int, dict[str, Any]] = {}
    for row in iter_jsonl(path):
        question_id = str(row.get("question_id", "")).strip()
        match = re.fullmatch(r"level1_q(\d{4})", question_id)
        if not match:
            continue
        loaded[int(match.group(1))] = row
    return loaded


def append_partial_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


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
    adversarial_eval_model: str,
    adversarial_eval_max_tokens: int,
    adversarial_eval_timeout_s: float,
    adversarial_eval_retries: int,
    adversarial_eval_rounds: int,
) -> dict[str, Any]:
    messages = make_messages(job, demo_template, option_count)
    banned_stem_terms = forbidden_stem_terms_text(job.entry)
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
            validate_generated_question(generated, option_count, job)
            if adversarial_eval_model:
                evaluator = load_level1_evaluator_module()
                candidate_record = build_record("preview", job, generated)
                for round_idx in range(1, adversarial_eval_rounds + 1):
                    solver_result = evaluator.evaluate_record(
                        record=candidate_record,
                        api_key=api_key,
                        model=adversarial_eval_model,
                        temperature=0.0,
                        max_tokens=adversarial_eval_max_tokens,
                        timeout_s=adversarial_eval_timeout_s,
                        retries=adversarial_eval_retries,
                    )
                    if solver_result["predicted_answer"] == candidate_record["answer"]:
                        raise ValueError(
                            "adversarial eval model solved the item correctly: "
                            f"{adversarial_eval_model} -> {solver_result['predicted_answer']} "
                            f"(round {round_idx}/{adversarial_eval_rounds})"
                        )
            return generated
        except Exception as exc:  # noqa: BLE001 - report model/API validation context.
            last_error = exc
            if attempt <= retries:
                error_text = str(exc)
                extra_feedback = ""
                if "adversarial eval model solved the item correctly" in error_text:
                    extra_feedback = (
                        " Increase the difficulty without making the item noisy: make the answer depend more on "
                        "a visible geometry, capacity, closure, format, slot-count, or parameter distinction from "
                        "the pictured asset, and tighten same-function distractors so multiple options remain "
                        "plausible until the final protocol detail is checked."
                    )
                elif "three distinct action families" in error_text or "share the same function name" in error_text:
                    extra_feedback = (
                        " Rebuild A-I strictly as three contiguous trios: A-C one function family, D-F a second "
                        "family, and G-I a third family. Each trio must use the same function name and keyword set, "
                        "changing only parameter values. The three trio function names must be different from each other."
                    )
                elif "option J must be exactly" in error_text:
                    extra_feedback = (
                        f" Set J to exactly {NONE_OF_ABOVE_CALL} with no arguments and do not use none_of_the_above() "
                        "in any other option."
                    )
                elif "question must include at least two concrete protocol numbers" in error_text:
                    extra_feedback = (
                        " Rewrite the stem to include at least two explicit numbers from the protocol, such as "
                        "volumes, durations, temperatures, rpm, xg, cycle counts, or distances."
                    )
                elif "question must mention prior-step or sequencing context" in error_text:
                    extra_feedback = (
                        " Rewrite the stem so it explicitly states one or two prior actions that have already "
                        "happened before the decision point."
                    )
                elif "target family variants must differ from the correct option by exactly one keyword value" in error_text:
                    extra_feedback = (
                        " Rebuild the correct 3-option target family so the two wrong variants each change only one "
                        "keyword value relative to the correct option."
                    )
                elif "target family variants must differ through a numeric parameter change" in error_text:
                    extra_feedback = (
                        " Rebuild the correct 3-option target family so the wrong variants change only one numeric "
                        "parameter such as a duration, temperature, volume, speed, cycle count, or distance."
                    )
                elif "magnetic functionality for passive holder asset" in error_text:
                    extra_feedback = (
                        " Do not use magnetic, magnet, magnetic_stand, or magnetic mode language for this passive "
                        "holder asset. Keep all three action families non-magnetic and consistent with an ordinary "
                        "bench holder or organizer."
                    )
                messages = messages + [
                    {
                        "role": "user",
                        "content": (
                            "The previous output was rejected by the pipeline validator. "
                            f"Validation error: {compact_text(error_text, 600)}. "
                            "Regenerate the full JSON object and fix this exact issue while "
                            "keeping all prior requirements. If the validation error mentions "
                            "question leakage, rewrite the stem from scratch and remove every "
                            "forbidden asset term or functional cue. "
                            f"For this asset, the stem must not use any of these terms: {banned_stem_terms}. "
                            f"Do not repeat the same invalid pattern.{extra_feedback}"
                        ),
                    }
                ]
                time.sleep(min(2.0 * attempt, 8.0))
    raise RuntimeError(f"Failed after {retries + 1} attempt(s): {last_error}")


def generate_record_for_job(
    *,
    idx: int,
    total: int,
    job: QuestionJob,
    api_key: str,
    model: str,
    demo_template: str,
    option_count: int,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
    retries: int,
    sleep_s: float,
    adversarial_eval_model: str,
    adversarial_eval_max_tokens: int,
    adversarial_eval_timeout_s: float,
    adversarial_eval_retries: int,
    adversarial_eval_rounds: int,
) -> tuple[int, dict[str, Any]]:
    question_id = f"level1_q{idx:04d}"
    print(
        f"[{idx}/{total}] generating {question_id}: "
        f"{job.entry.entry_id} x {job.protocol.protocol_id}",
        file=sys.stderr,
        flush=True,
    )
    generated = generate_question_for_job(
        job,
        api_key=api_key,
        model=model,
        demo_template=demo_template,
        option_count=option_count,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        retries=retries,
        adversarial_eval_model=adversarial_eval_model,
        adversarial_eval_max_tokens=adversarial_eval_max_tokens,
        adversarial_eval_timeout_s=adversarial_eval_timeout_s,
        adversarial_eval_retries=adversarial_eval_retries,
        adversarial_eval_rounds=adversarial_eval_rounds,
    )
    if sleep_s > 0:
        time.sleep(sleep_s)
    return idx, build_record(question_id, job, generated)


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
    parser.add_argument("--concurrency", type=int, default=4, help="Number of concurrent API requests.")
    parser.add_argument("--api-key-stdin", action="store_true", help="Read the API key from the first stdin line.")
    parser.add_argument("--include-scenes", action="store_true", help="Allow non-protocol-matchable scene entries if they have matches.")
    parser.add_argument("--dry-run", action="store_true", help="Print selected jobs without calling OpenRouter.")
    parser.add_argument("--template-max-chars", type=int, default=16000, help="Max chars from level-1-demo.md included in prompts.")
    parser.add_argument("--max-steps-per-protocol", type=int, default=8, help="Max protocol snippets sent to the model.")
    parser.add_argument("--max-protocols-per-entry", type=int, default=80, help="Max protocol candidates retained per entry.")
    parser.add_argument("--none-above-rate", type=float, default=0.2, help="Approximate fraction of items whose correct answer is J = none_of_the_above().")
    parser.add_argument("--adversarial-eval-model", default="", help="Optional evaluation model used to reject questions it can already answer correctly.")
    parser.add_argument("--adversarial-eval-max-tokens", type=int, default=256, help="Max tokens for adversarial self-play evaluation.")
    parser.add_argument("--adversarial-eval-timeout-s", type=float, default=90.0, help="HTTP timeout for adversarial self-play evaluation.")
    parser.add_argument("--adversarial-eval-retries", type=int, default=1, help="Retries for adversarial self-play evaluation.")
    parser.add_argument("--adversarial-eval-rounds", type=int, default=1, help="Number of independent self-play evaluation passes a candidate must survive.")
    parser.add_argument("--multiview-manifest", type=Path, default=DEFAULT_MULTIVIEW_MANIFEST)
    parser.add_argument("--core-inventory", type=Path, default=DEFAULT_CORE_INVENTORY)
    parser.add_argument("--protocol-matches", type=Path, default=DEFAULT_PROTOCOL_MATCHES)
    parser.add_argument("--demo-template", type=Path, default=DEFAULT_DEMO_TEMPLATE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    option_letters(args.option_count)
    if args.concurrency < 1:
        raise ValueError("--concurrency must be at least 1")

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
    target_answer_letters = build_target_answer_letters(
        len(jobs),
        args.option_count,
        args.seed,
        none_above_rate=args.none_above_rate,
    )
    jobs = [
        QuestionJob(
            entry=job.entry,
            protocol=job.protocol,
            selected_views=job.selected_views,
            target_answer_letter=target_answer_letters[idx],
        )
        for idx, job in enumerate(jobs)
    ]

    if args.dry_run:
        for idx, job in enumerate(jobs, 1):
            views = ", ".join(view for view, _ in job.selected_views)
            print(
                f"{idx:03d} {job.entry.entry_id} | {job.protocol.protocol_id} | "
                f"steps={list(step.get('idx') for step in job.protocol.relevant_steps[:4])} | "
                f"nearby={list(step.get('idx') for step in job.protocol.nearby_steps[:4])} | "
                f"answer={job.target_answer_letter} | views={views}"
            )
        return 0

    api_key = get_api_key(read_from_stdin=args.api_key_stdin)
    demo_template = read_demo_template(args.demo_template, args.template_max_chars)
    partial_path = partial_output_path(args.output)
    resumed_records = load_partial_records(partial_path)
    record_slots: list[dict[str, Any] | None] = [None] * len(jobs)
    for idx, record in resumed_records.items():
        if 1 <= idx <= len(record_slots):
            record_slots[idx - 1] = record
    resumed_count = sum(record is not None for record in record_slots)
    if resumed_count:
        print(
            f"Resuming from {resumed_count} existing record(s) in {partial_path}",
            file=sys.stderr,
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(
                generate_record_for_job,
                idx=idx,
                total=len(jobs),
                job=job,
                api_key=api_key,
                model=args.model,
                demo_template=demo_template,
                option_count=args.option_count,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout_s=args.timeout_s,
                retries=args.retries,
                sleep_s=args.sleep_s,
                adversarial_eval_model=args.adversarial_eval_model,
                adversarial_eval_max_tokens=args.adversarial_eval_max_tokens,
                adversarial_eval_timeout_s=args.adversarial_eval_timeout_s,
                adversarial_eval_retries=args.adversarial_eval_retries,
                adversarial_eval_rounds=args.adversarial_eval_rounds,
            ): idx
            for idx, job in enumerate(jobs, 1)
            if record_slots[idx - 1] is None
        }
        for completed_count, future in enumerate(as_completed(futures), 1):
            idx = futures[future]
            try:
                result_idx, record = future.result()
            except Exception as exc:
                for pending in futures:
                    pending.cancel()
                question_id = f"level1_q{idx:04d}"
                raise RuntimeError(f"Failed generating {question_id}") from exc
            record_slots[result_idx - 1] = record
            append_partial_record(partial_path, record)
            print(
                f"[{resumed_count + completed_count}/{len(jobs)}] completed level1_q{result_idx:04d}",
                file=sys.stderr,
                flush=True,
            )

    records = [record for record in record_slots if record is not None]
    if len(records) != len(jobs):
        raise RuntimeError(f"Generated {len(records)} records for {len(jobs)} jobs")

    metadata = {
        "count": len(records),
        "seed": args.seed,
        "model": args.model,
        "concurrency": args.concurrency,
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
