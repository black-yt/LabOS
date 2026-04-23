#!/usr/bin/env python3
"""Evaluate Level 1 answer accuracy with an OpenRouter model."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_ENV_PATH = SCRIPT_DIR / ".env"
DEFAULT_QUESTIONS = SCRIPT_DIR / "generated/level1_questions_20.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


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


def compact_text(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


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
    raise RuntimeError("Set OPENROUTER_API_KEY, provide pipeline/level-1/.env, or pass --api-key-stdin.")


def guess_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    raise ValueError(f"Unsupported image type: {path}")


def image_to_data_url(path: Path) -> str:
    mime_type = guess_mime_type(path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_user_content(record: dict[str, Any]) -> list[dict[str, Any]]:
    option_lines = [f"{letter}. {text}" for letter, text in sorted(record["options"].items())]
    prompt = (
        "Solve one LabOS Level 1 multiple-choice question using the three images and the "
        "question text. Return strict JSON only in the format {\"answer\": \"A\"}. "
        "The answer must be exactly one capital letter from the provided options.\n\n"
        f"Question:\n{record['question']}\n\n"
        f"Options:\n" + "\n".join(option_lines)
    )

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for view in record["views"]:
        image_path = REPO_ROOT / view["path"]
        content.append({"type": "text", "text": f"View: {view['view']}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_to_data_url(image_path),
                },
            }
        )
    return content


def openrouter_chat_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
    timeout_s: float,
) -> dict[str, Any]:
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
            "X-Title": "LabOS Level 1 Evaluator",
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
    return json.loads(body)


def parse_answer(content: str, valid_letters: set[str]) -> str:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\b([A-J])\b", text)
        if not match:
            raise ValueError(f"Could not parse answer from response: {compact_text(text, 200)}")
        answer = match.group(1)
    else:
        if not isinstance(parsed, dict) or "answer" not in parsed:
            raise ValueError(f"Response JSON missing answer field: {compact_text(text, 200)}")
        answer = str(parsed["answer"]).strip()

    if answer not in valid_letters:
        raise ValueError(f"Invalid answer letter: {answer}")
    return answer


def evaluate_record(
    *,
    record: dict[str, Any],
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
    retries: int,
) -> dict[str, Any]:
    valid_letters = set(record["options"])
    messages = [
        {
            "role": "system",
            "content": (
                "You are evaluating a LabOS Level 1 asset-understanding item. "
                "Use the images and question text to choose the correct option. "
                "Return strict JSON only with a single field named answer."
            ),
        },
        {"role": "user", "content": build_user_content(record)},
    ]

    last_error: Exception | None = None
    started = time.time()
    for attempt in range(1, retries + 2):
        try:
            response = openrouter_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
            )
            content = response["choices"][0]["message"]["content"]
            answer = parse_answer(content, valid_letters)
            elapsed_s = round(time.time() - started, 3)
            return {
                "question_id": record["question_id"],
                "entry_id": record["entry_id"],
                "gold_answer": record["answer"],
                "predicted_answer": answer,
                "correct": answer == record["answer"],
                "response_content": content,
                "model_returned": response.get("model"),
                "usage": response.get("usage", {}),
                "latency_s": elapsed_s,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt <= retries:
                messages = messages + [
                    {
                        "role": "user",
                        "content": (
                            "The previous response was invalid. "
                            f"Validation error: {compact_text(str(exc), 400)}. "
                            "Return only {\"answer\": \"<LETTER>\"} with one valid option letter."
                        ),
                    }
                ]
                time.sleep(min(2.0 * attempt, 8.0))

    elapsed_s = round(time.time() - started, 3)
    return {
        "question_id": record["question_id"],
        "entry_id": record["entry_id"],
        "gold_answer": record["answer"],
        "predicted_answer": None,
        "correct": False,
        "error": str(last_error),
        "latency_s": elapsed_s,
    }


def sanitize_model_id(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model)


def default_output_path(questions_path: Path, model: str) -> Path:
    suffix = sanitize_model_id(model)
    return questions_path.with_name(f"{questions_path.stem}.eval.{suffix}.json")


def write_outputs(output_path: Path, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary,
        "results": results,
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    jsonl_path = output_path.with_suffix(".jsonl")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS, help="Question JSON file to evaluate.")
    parser.add_argument("--output", type=Path, help="Evaluation output JSON path.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature.")
    parser.add_argument("--max-tokens", type=int, default=128, help="Max output tokens per question.")
    parser.add_argument("--timeout-s", type=float, default=120.0, help="HTTP timeout per API call.")
    parser.add_argument("--retries", type=int, default=2, help="Retries per question after invalid output or request failure.")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent evaluation requests.")
    parser.add_argument("--limit", type=int, help="Optional limit on the number of questions evaluated.")
    parser.add_argument("--api-key-stdin", action="store_true", help="Read the API key from the first stdin line.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.concurrency < 1:
        raise ValueError("--concurrency must be at least 1")

    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    if args.limit is not None:
        questions = questions[: args.limit]
    if not questions:
        raise RuntimeError("No questions selected for evaluation")

    api_key = get_api_key(read_from_stdin=args.api_key_stdin)
    output_path = args.output or default_output_path(args.questions, args.model)

    started = time.time()
    results: list[dict[str, Any] | None] = [None] * len(questions)
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(
                evaluate_record,
                record=record,
                api_key=api_key,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout_s=args.timeout_s,
                retries=args.retries,
            ): idx
            for idx, record in enumerate(questions)
        }
        for completed_count, future in enumerate(as_completed(futures), 1):
            idx = futures[future]
            result = future.result()
            results[idx] = result
            print(
                f"[{completed_count}/{len(questions)}] {result['question_id']} -> "
                f"{result.get('predicted_answer') or 'ERROR'} | correct={result['correct']}",
                file=sys.stderr,
                flush=True,
            )

    finalized_results = [result for result in results if result is not None]
    correct_count = sum(1 for result in finalized_results if result["correct"])
    invalid_count = sum(1 for result in finalized_results if result.get("predicted_answer") is None)
    total_cost = 0.0
    model_returns: set[str] = set()
    for result in finalized_results:
        usage = result.get("usage", {})
        cost = usage.get("cost")
        if isinstance(cost, (float, int)):
            total_cost += float(cost)
        if result.get("model_returned"):
            model_returns.add(str(result["model_returned"]))

    elapsed_s = round(time.time() - started, 3)
    summary = {
        "questions_path": str(args.questions),
        "output_path": str(output_path),
        "count": len(finalized_results),
        "model_requested": args.model,
        "model_returned": sorted(model_returns),
        "concurrency": args.concurrency,
        "correct_count": correct_count,
        "invalid_count": invalid_count,
        "answer_accuracy": correct_count / len(finalized_results),
        "total_cost": round(total_cost, 8),
        "elapsed_s": elapsed_s,
    }
    write_outputs(output_path, summary, finalized_results)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
