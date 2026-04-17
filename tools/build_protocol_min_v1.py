#!/usr/bin/env python3
"""Build a benchmark-oriented minimal protocol schema from protocol_v1/all.jsonl.

Output schema:

{
  "id": "...",
  "title": "...",
  "background": "...",
  "materials": {
    "reagents": [{"name": "...", "vendor": "...", "identifier": "..."}],
    "equipment": [{"name": "...", "vendor": "...", "identifier": "..."}]
  },
  "procedure": {
    "steps": [{"idx": 1, "stage": "...", "description": "..."}],
    "troubleshooting": [{"problem": "...", "solution": "..."}]
  }
}

The script filters out records that do not satisfy the benchmark-oriented
minimum requirements after normalization. By default:

- id/title/background must be non-empty
- reagents >= 5
- equipment >= 2
- steps >= 20
- unique_stages >= 3

The thresholds are configurable from the command line.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def source_from_id(record_id: str) -> str:
    if ":" not in record_id:
        return "unknown"
    return record_id.split(":", 1)[0] or "unknown"


def dedupe_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for item in items:
        key = (
            normalize_text(item.get("name", "")).lower(),
            normalize_text(item.get("vendor", "")).lower(),
            normalize_text(item.get("identifier", "")).lower(),
        )
        if not key[0]:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def build_reagents(raw_items: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for raw in raw_items or []:
        name = normalize_text(raw.get("name"))
        if not name:
            continue
        items.append(
            {
                "name": name,
                "vendor": normalize_text(raw.get("vendor")),
                "identifier": normalize_text(raw.get("catalog_id")),
            }
        )
    return dedupe_items(items)


def build_equipment(raw_items: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for raw in raw_items or []:
        name = normalize_text(raw.get("name"))
        if not name:
            continue
        items.append(
            {
                "name": name,
                "vendor": normalize_text(raw.get("vendor")),
                "identifier": normalize_text(raw.get("model")),
            }
        )
    return dedupe_items(items)


def build_troubleshooting(
    raw_items: list[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for raw in raw_items or []:
        problem = normalize_text(raw.get("problem"))
        solution = normalize_text(raw.get("solution"))
        if not (problem or solution):
            continue
        items.append({"problem": problem, "solution": solution})
    return items


def build_steps(
    raw_items: list[dict[str, Any]] | None,
    title: str,
) -> tuple[list[dict[str, Any]], int, int]:
    steps: list[dict[str, Any]] = []
    current_stage = ""
    fallback_count = 0
    unique_stages: set[str] = set()

    for raw in raw_items or []:
        description = normalize_text(raw.get("text"))
        if not description:
            continue

        stage = normalize_text(raw.get("section"))
        if stage:
            current_stage = stage
        else:
            stage = current_stage or title
            fallback_count += 1

        if stage:
            unique_stages.add(stage)

        steps.append(
            {
                "idx": len(steps) + 1,
                "stage": stage,
                "description": description,
            }
        )

    return steps, fallback_count, len(unique_stages)


def build_min_record(raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    record_id = normalize_text(raw.get("id"))
    title = normalize_text(raw.get("title"))
    abstract = normalize_text(raw.get("abstract"))
    background = abstract or title

    reagents = build_reagents(raw.get("reagents"))
    equipment = build_equipment(raw.get("equipment"))
    troubleshooting = build_troubleshooting(raw.get("troubleshooting"))
    steps, stage_fallback_count, unique_stage_count = build_steps(
        raw.get("steps"), title=title
    )

    record = {
        "id": record_id,
        "title": title,
        "background": background,
        "materials": {
            "reagents": reagents,
            "equipment": equipment,
        },
        "procedure": {
            "steps": steps,
            "troubleshooting": troubleshooting,
        },
    }
    meta = {
        "stage_fallback_count": stage_fallback_count,
        "unique_stage_count": unique_stage_count,
    }
    return record, meta


def validate_min_record(
    record: dict[str, Any],
    *,
    min_reagents: int,
    min_equipment: int,
    min_steps: int,
    min_unique_stages: int,
    seen_ids: set[str],
    meta: dict[str, int],
) -> list[str]:
    reasons: list[str] = []

    if not record["id"]:
        reasons.append("empty_id")
    elif record["id"] in seen_ids:
        reasons.append("duplicate_id")

    if not record["title"]:
        reasons.append("empty_title")
    if not record["background"]:
        reasons.append("empty_background")

    if len(record["materials"]["reagents"]) < min_reagents:
        reasons.append(f"reagents<{min_reagents}")
    if len(record["materials"]["equipment"]) < min_equipment:
        reasons.append(f"equipment<{min_equipment}")
    if len(record["procedure"]["steps"]) < min_steps:
        reasons.append(f"steps<{min_steps}")
    if meta["unique_stage_count"] < min_unique_stages:
        reasons.append(f"unique_stages<{min_unique_stages}")

    return reasons


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build protocol_min_v1 from protocol_v1/all.jsonl"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/protocol_v1/all.jsonl"),
        help="Input JSONL file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/protocol_v1/protocol_min_v1.jsonl"),
        help="Output JSONL file",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/protocol_v1/protocol_min_v1.stats.json"),
        help="Output stats JSON file",
    )
    parser.add_argument(
        "--min-reagents",
        type=int,
        default=5,
        help="Minimum number of normalized reagents required",
    )
    parser.add_argument(
        "--min-equipment",
        type=int,
        default=2,
        help="Minimum number of normalized equipment items required",
    )
    parser.add_argument(
        "--min-steps",
        type=int,
        default=20,
        help="Minimum number of normalized steps required",
    )
    parser.add_argument(
        "--min-unique-stages",
        type=int,
        default=3,
        help="Minimum number of unique normalized stages required",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    kept = 0
    dropped = 0
    total = 0
    stage_fallback_steps = 0
    kept_unique_stage_total = 0

    keep_by_source: Counter[str] = Counter()
    drop_by_source: Counter[str] = Counter()
    drop_reasons: Counter[str] = Counter()

    with args.input.open("r", encoding="utf-8") as src, args.output.open(
        "w", encoding="utf-8"
    ) as dst:
        for line in src:
            if not line.strip():
                continue
            total += 1
            raw = json.loads(line)
            record, meta = build_min_record(raw)
            source = source_from_id(record["id"])
            reasons = validate_min_record(
                record,
                min_reagents=args.min_reagents,
                min_equipment=args.min_equipment,
                min_steps=args.min_steps,
                min_unique_stages=args.min_unique_stages,
                seen_ids=seen_ids,
                meta=meta,
            )

            if reasons:
                dropped += 1
                drop_by_source[source] += 1
                drop_reasons.update(reasons)
                continue

            seen_ids.add(record["id"])
            stage_fallback_steps += meta["stage_fallback_count"]
            kept_unique_stage_total += meta["unique_stage_count"]
            kept += 1
            keep_by_source[source] += 1
            dst.write(json.dumps(record, ensure_ascii=False) + "\n")

    report = {
        "schema": "protocol_min_v1",
        "input": str(args.input),
        "output": str(args.output),
        "total_input_records": total,
        "kept_records": kept,
        "dropped_records": dropped,
        "thresholds": {
            "min_reagents": args.min_reagents,
            "min_equipment": args.min_equipment,
            "min_steps": args.min_steps,
            "min_unique_stages": args.min_unique_stages,
        },
        "kept_by_source": dict(sorted(keep_by_source.items())),
        "dropped_by_source": dict(sorted(drop_by_source.items())),
        "drop_reasons": dict(drop_reasons.most_common()),
        "stage_fallback_steps": stage_fallback_steps,
        "kept_unique_stage_mean": round(kept_unique_stage_total / kept, 2) if kept else 0,
        "notes": [
            "background is normalized from abstract, falling back to title",
            "reagents.identifier comes from raw catalog_id",
            "equipment.identifier comes from raw model",
            "step.stage comes from raw section, falling back to the previous non-empty stage or title",
            "troubleshooting entries are kept when either problem or solution is non-empty",
            "benchmark filtering keeps longer and more structured protocols by requiring enough steps and unique stages",
        ],
    }

    with args.report.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
