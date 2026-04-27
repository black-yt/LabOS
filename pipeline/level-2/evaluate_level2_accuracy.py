from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ast_utils import compare_program_steps, extract_python_program, parse_program_steps
from common import (
    DEFAULT_MODEL,
    compact_text,
    get_api_key,
    model_from_env,
    openrouter_chat_completion,
    repo_relative_display,
)

DEFAULT_QUESTIONS = SCRIPT_DIR / "generated" / "level2_tasks_20.json"


def build_user_prompt(record: dict[str, Any]) -> str:
    input_lines = [f"- {item['name']}: {item['description']}" for item in record["available_inputs"]]
    constraint_lines = [f"- {item}" for item in record["constraints"]]
    return (
        "Solve one LabOS Level 2 planning task. Produce Python code that completes the requested "
        "experimental subtask using only the provided action functions.\n\n"
        f"Background:\n{record['background']}\n\n"
        f"Goal:\n{record['goal']}\n\n"
        f"Constraints:\n{chr(10).join(constraint_lines)}\n\n"
        f"Available raw inputs:\n{chr(10).join(input_lines)}\n\n"
        f"Action pool:\n```python\n{record['action_pool_code']}```\n\n"
        "Requirements:\n"
        "- Use only the provided functions.\n"
        "- Use keyword arguments only.\n"
        "- Assign every call to a variable.\n"
        "- Do not redefine functions or import modules.\n"
        "- Stay at the protocol abstraction level implied by the action pool; do not add transport, setup, rotor-loading, or manipulation steps unless they are clearly required by the task and explicitly available in the pool.\n"
        "- Prefer a single ```python fenced block``` for the final program.\n"
    )


def partial_output_path(output_path: Path) -> Path:
    return output_path.with_suffix(".partial.jsonl")


def default_output_path(questions_path: Path, model: str) -> Path:
    suffix = model.replace("/", "_")
    return questions_path.with_name(f"{questions_path.stem}.eval.{suffix}.json")


def load_partial_results(path: Path) -> tuple[dict[str, dict[str, Any]], int]:
    if not path.is_file():
        return {}, 0
    cached: dict[str, dict[str, Any]] = {}
    skipped_invalid = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON in partial results at line {line_no}: {path}") from exc
            task_id = parsed.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise RuntimeError(f"Missing task_id in partial results at line {line_no}: {path}")
            if parsed.get("predicted_program") is None:
                skipped_invalid += 1
                continue
            cached[task_id] = parsed
    return cached, skipped_invalid


def append_partial_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False) + "\n")


def evaluate_record(
    *,
    record: dict[str, Any],
    api_key: str,
    model: str,
    timeout_s: float,
    retries: int,
    temperature: float | None,
    max_tokens: int | None,
) -> dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are solving a LabOS Level 2 long-horizon planning task. "
                "Return executable-looking Python code only when possible."
            ),
        },
        {"role": "user", "content": build_user_prompt(record)},
    ]

    gold_steps = parse_program_steps(record["gold_program"])
    raw_inputs = {item["name"] for item in record["available_inputs"]}
    started = time.time()
    last_error: Exception | None = None
    last_content: str | None = None
    for attempt in range(1, retries + 2):
        try:
            response = openrouter_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
                use_response_format=False,
            )
            content = response["choices"][0]["message"]["content"]
            last_content = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            predicted_program = extract_python_program(last_content)
            pred_steps = parse_program_steps(predicted_program)
            metrics = compare_program_steps(gold_steps, pred_steps, raw_inputs=raw_inputs)
            return {
                "task_id": record["task_id"],
                "protocol_id": record["protocol_id"],
                "gold_program": record["gold_program"],
                "predicted_program": predicted_program,
                "response_content": last_content,
                "action_sequence_similarity": metrics["action_sequence_similarity"],
                "parameter_accuracy": metrics["parameter_accuracy"],
                "final_score": metrics["final_score"],
                "relaxed_action_sequence_similarity": metrics["relaxed_action_sequence_similarity"],
                "relaxed_parameter_accuracy": metrics["relaxed_parameter_accuracy"],
                "relaxed_final_score": metrics["relaxed_final_score"],
                "error_count": metrics["error_count"],
                "details": metrics["details"],
                "relaxed_details": metrics["relaxed_details"],
                "relaxed_alignment_length": metrics["relaxed_alignment_length"],
                "relaxed_matched_parameter_count": metrics["relaxed_matched_parameter_count"],
                "relaxed_total_parameter_count": metrics["relaxed_total_parameter_count"],
                "model_requested": model,
                "model_returned": response["model"],
                "usage": response.get("usage"),
                "latency_s": round(time.time() - started, 3),
            }
        except Exception as exc:
            last_error = exc
            if attempt > retries:
                break
            messages = messages + [
                {"role": "assistant", "content": last_content or ""},
                {
                    "role": "user",
                    "content": (
                        "The previous response could not be parsed as a valid solution. "
                        f"Error: {compact_text(str(exc), 400)}. "
                        "Return a corrected solution, preferably as one ```python``` block, with no function redefinitions."
                    ),
                },
            ]

    return {
        "task_id": record["task_id"],
        "protocol_id": record["protocol_id"],
        "gold_program": record["gold_program"],
        "predicted_program": None,
        "response_content": last_content,
        "action_sequence_similarity": 0.0,
        "parameter_accuracy": 0.0,
        "final_score": 0.0,
        "relaxed_action_sequence_similarity": 0.0,
        "relaxed_parameter_accuracy": 0.0,
        "relaxed_final_score": 0.0,
        "error_count": None,
        "details": [],
        "relaxed_details": [],
        "relaxed_alignment_length": 0,
        "relaxed_matched_parameter_count": 0,
        "relaxed_total_parameter_count": 0,
        "model_requested": model,
        "model_returned": None,
        "usage": None,
        "latency_s": round(time.time() - started, 3),
        "error": str(last_error),
    }


def write_outputs(output_path: Path, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_path.with_suffix(".jsonl").write_text(
        "\n".join(json.dumps(result, ensure_ascii=False) for result in results) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default=model_from_env(DEFAULT_MODEL))
    parser.add_argument("--timeout-s", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--api-key-stdin", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    if args.limit:
        questions = questions[: args.limit]

    api_key = get_api_key(read_from_stdin=args.api_key_stdin)
    output_path = args.output or default_output_path(args.questions, args.model)
    partial_path = partial_output_path(output_path)
    cached_results, skipped_invalid_cache = load_partial_results(partial_path)

    started = time.time()
    results: list[dict[str, Any] | None] = [None] * len(questions)
    pending_records: list[tuple[int, dict[str, Any]]] = []
    restored_count = 0
    for idx, record in enumerate(questions):
        cached = cached_results.get(record["task_id"])
        if cached is None:
            pending_records.append((idx, record))
            continue
        results[idx] = cached
        restored_count += 1

    if restored_count:
        print(
            f"restored {restored_count} completed evaluations from {repo_relative_display(partial_path)}",
            file=sys.stderr,
            flush=True,
        )
    if skipped_invalid_cache:
        print(
            f"ignored {skipped_invalid_cache} cached invalid result(s); they will be retried",
            file=sys.stderr,
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(
                evaluate_record,
                record=record,
                api_key=api_key,
                model=args.model,
                timeout_s=args.timeout_s,
                retries=args.retries,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            ): idx
            for idx, record in pending_records
        }
        completed_count = restored_count
        for future in as_completed(futures):
            idx = futures[future]
            result = future.result()
            results[idx] = result
            append_partial_result(partial_path, result)
            completed_count += 1
            print(
                f"[{completed_count}/{len(questions)}] {result['task_id']} -> "
                f"seq={result['action_sequence_similarity']:.3f} param={result['parameter_accuracy']:.3f}",
                file=sys.stderr,
                flush=True,
            )

    finalized_results = [result for result in results if result is not None]
    if len(finalized_results) != len(questions):
        raise RuntimeError(f"evaluation incomplete: {len(finalized_results)} / {len(questions)} results")

    model_returns = {result["model_returned"] for result in finalized_results if result.get("model_returned")}
    invalid_count = sum(1 for result in finalized_results if result.get("predicted_program") is None)
    average_sequence = sum(result["action_sequence_similarity"] for result in finalized_results) / len(finalized_results)
    average_parameter = sum(result["parameter_accuracy"] for result in finalized_results) / len(finalized_results)
    average_final = sum(result["final_score"] for result in finalized_results) / len(finalized_results)
    average_relaxed_sequence = sum(result.get("relaxed_action_sequence_similarity", 0.0) for result in finalized_results) / len(finalized_results)
    average_relaxed_parameter = sum(result.get("relaxed_parameter_accuracy", 0.0) for result in finalized_results) / len(finalized_results)
    average_relaxed_final = sum(result.get("relaxed_final_score", 0.0) for result in finalized_results) / len(finalized_results)
    total_cost = 0.0
    for result in finalized_results:
        usage = result.get("usage") or {}
        if isinstance(usage, dict) and isinstance(usage.get("cost"), (int, float)):
            total_cost += float(usage["cost"])

    summary = {
        "questions_path": repo_relative_display(args.questions),
        "output_path": repo_relative_display(output_path),
        "partial_output_path": repo_relative_display(partial_path),
        "count": len(finalized_results),
        "model_requested": args.model,
        "model_returned": sorted(model_returns),
        "concurrency": args.concurrency,
        "restored_valid_cache_count": restored_count,
        "retried_invalid_cache_count": skipped_invalid_cache,
        "average_action_sequence_similarity": average_sequence,
        "average_parameter_accuracy": average_parameter,
        "average_final_score": average_final,
        "average_relaxed_action_sequence_similarity": average_relaxed_sequence,
        "average_relaxed_parameter_accuracy": average_relaxed_parameter,
        "average_relaxed_final_score": average_relaxed_final,
        "invalid_count": invalid_count,
        "total_cost": round(total_cost, 6),
        "elapsed_s": round(time.time() - started, 3),
    }
    write_outputs(output_path, summary, finalized_results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
