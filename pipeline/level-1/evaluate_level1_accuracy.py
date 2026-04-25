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
ANSWER_TAG_RE = re.compile(r"<answer>\s*([A-Z])\s*</answer>", re.IGNORECASE)
STEP_TAG_RE = re.compile(r"<step>\s*(.*?)\s*</step>", re.IGNORECASE | re.DOTALL)
REASONING_TAG_RE = re.compile(r"<reasoning>\s*(.*?)\s*</reasoning>", re.IGNORECASE | re.DOTALL)
FINAL_ANSWER_LINE_RE = re.compile(r"^\s*Final\s+Answer\s*:\s*([A-Z])\s*$", re.IGNORECASE)
FREEFORM_ANSWER_PATTERNS = (
    re.compile(r"<final_answer>\s*([A-Z])\s*</final_answer>", re.IGNORECASE),
    re.compile(r"(?is)(?:final\s+answer|answer|correct\s+answer|correct\s+option)\s*(?:is|:|=)\s*([A-Z])\b"),
    re.compile(r"(?is)\boption\s*([A-Z])\s+is\s+correct\b"),
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


def build_user_content(record: dict[str, Any], *, output_format: str) -> list[dict[str, Any]]:
    option_lines = [f"{letter}. {text}" for letter, text in sorted(record["options"].items())]
    if output_format == "json":
        prompt = (
            "Solve one LabOS Level 1 multiple-choice question using the three images and the "
            "question text. Return strict JSON only in the format "
            "{\"reasoning_steps\": [\"...\"], \"answer\": \"A\"}. "
            "The answer must be exactly one capital letter from the provided options. "
            "reasoning_steps must be a list of 2-5 concise English strings grounded in the "
            "images, the protocol context implied by the stem, and the option differences.\n\n"
            f"Question:\n{record['question']}\n\n"
            f"Options:\n" + "\n".join(option_lines)
        )
    else:
        prompt = (
            "Solve one LabOS Level 1 multiple-choice question using the three images and the "
            "question text. Answer in your normal style. Put the final answer on the LAST non-empty "
            "line in exactly this format: Final Answer: X where X is one capital letter from the "
            "provided options.\n\n"
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
    temperature: float | None,
    max_tokens: int | None,
    timeout_s: float,
    use_response_format: bool,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if use_response_format:
        payload["response_format"] = {"type": "json_object"}
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


def normalize_reasoning_chunks(chunks: list[str]) -> list[str]:
    cleaned: list[str] = []
    for chunk in chunks:
        normalized = re.sub(r"\s+", " ", chunk).strip()
        if normalized:
            cleaned.append(normalized)
    if not cleaned:
        return []
    return cleaned[:6]


def split_reasoning_text(text: str) -> list[str]:
    parts: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•\d.)\s]+", "", line).strip()
        if line:
            parts.append(line)
    if len(parts) >= 2:
        return normalize_reasoning_chunks(parts)
    sentence_parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return normalize_reasoning_chunks(sentence_parts)


def extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text)
        return "\n".join(text_parts)
    if content is None:
        return ""
    return str(content)


def parse_tagged_answer(text: str, valid_letters: set[str]) -> tuple[list[str], str]:
    matches = [match.group(1).upper() for match in ANSWER_TAG_RE.finditer(text)]
    if not matches:
        raise ValueError(f"Response missing <answer> tag: {compact_text(text, 200)}")
    unique_answers = sorted(set(matches))
    if len(unique_answers) != 1:
        raise ValueError(f"Response contains conflicting <answer> tags: {compact_text(text, 200)}")
    answer = unique_answers[0]
    if answer not in valid_letters:
        raise ValueError(f"Invalid answer letter: {answer}")

    step_chunks = normalize_reasoning_chunks([match.group(1) for match in STEP_TAG_RE.finditer(text)])
    if step_chunks:
        return step_chunks, answer

    reasoning_blocks = normalize_reasoning_chunks([match.group(1) for match in REASONING_TAG_RE.finditer(text)])
    if reasoning_blocks:
        return reasoning_blocks, answer

    stripped = ANSWER_TAG_RE.sub("", text)
    stripped = REASONING_TAG_RE.sub(lambda match: match.group(1), stripped)
    stripped = STEP_TAG_RE.sub(lambda match: match.group(1), stripped)
    reasoning_steps = split_reasoning_text(stripped)
    return reasoning_steps, answer


def parse_final_answer_line(text: str, valid_letters: set[str]) -> tuple[list[str], str]:
    non_empty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not non_empty_lines:
        raise ValueError("Response is empty")
    last_line = non_empty_lines[-1]
    match = FINAL_ANSWER_LINE_RE.fullmatch(last_line)
    if not match:
        raise ValueError(f"Response missing final line 'Final Answer: X': {compact_text(text, 200)}")
    answer = match.group(1).upper()
    if answer not in valid_letters:
        raise ValueError(f"Invalid answer letter: {answer}")
    reasoning_text = "\n".join(non_empty_lines[:-1]).strip()
    return split_reasoning_text(reasoning_text), answer


def parse_flexible_answer(text: str, valid_letters: set[str]) -> tuple[list[str], str]:
    tail = text[-600:]
    for pattern in FREEFORM_ANSWER_PATTERNS:
        matches = [match.group(1).upper() for match in pattern.finditer(tail)]
        if not matches:
            continue
        answer = matches[-1]
        if answer not in valid_letters:
            raise ValueError(f"Invalid answer letter: {answer}")
        stripped = tail
        for cleanup_pattern in FREEFORM_ANSWER_PATTERNS:
            stripped = cleanup_pattern.sub("", stripped)
        reasoning_steps = split_reasoning_text(stripped)
        return reasoning_steps, answer
    raise ValueError(f"Response missing parseable final answer marker: {compact_text(text, 200)}")


def parse_reasoning_answer(content: Any, valid_letters: set[str]) -> tuple[list[str], str]:
    text = extract_message_text(content).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    if FINAL_ANSWER_LINE_RE.search(text):
        return parse_final_answer_line(text, valid_letters)
    if ANSWER_TAG_RE.search(text):
        return parse_tagged_answer(text, valid_letters)
    if any(pattern.search(text[-600:]) for pattern in FREEFORM_ANSWER_PATTERNS):
        return parse_flexible_answer(text, valid_letters)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError(f"Response is not valid JSON: {compact_text(text, 200)}")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Response is not valid JSON: {compact_text(text, 200)}") from exc
    if not isinstance(parsed, dict) or "answer" not in parsed:
        raise ValueError(f"Response JSON missing answer: {compact_text(text, 200)}")

    answer = str(parsed["answer"]).strip()
    if answer not in valid_letters:
        raise ValueError(f"Invalid answer letter: {answer}")
    reasoning_steps_raw = parsed.get("reasoning_steps")
    if isinstance(reasoning_steps_raw, list):
        reasoning_steps = normalize_reasoning_chunks([step for step in reasoning_steps_raw if isinstance(step, str)])
        return reasoning_steps, answer
    reasoning_text = parsed.get("reasoning")
    if isinstance(reasoning_text, str):
        return split_reasoning_text(reasoning_text), answer
    return [], answer


def evaluate_record(
    *,
    record: dict[str, Any],
    api_key: str,
    model: str,
    temperature: float | None,
    max_tokens: int | None,
    timeout_s: float,
    retries: int,
    use_response_format: bool,
    output_format: str,
) -> dict[str, Any]:
    valid_letters = set(record["options"])
    messages = [
        {
            "role": "system",
            "content": (
                "You are evaluating a LabOS Level 1 asset-understanding item. "
                "Use the images and question text to choose the correct option. "
                + (
                    "Return strict JSON only with fields reasoning_steps and answer. "
                    "The reasoning steps must be concise English strings; scoring will still use the answer field."
                    if output_format == "json"
                    else "Answer in your normal style. Put the final answer on the last non-empty line exactly as "
                    "'Final Answer: X'. Scoring will use only that final line."
                )
            ),
        },
        {"role": "user", "content": build_user_content(record, output_format=output_format)},
    ]

    last_error: Exception | None = None
    last_content: str | None = None
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
                use_response_format=use_response_format,
            )
            content = response["choices"][0]["message"]["content"]
            last_content = extract_message_text(content)
            reasoning_steps, answer = parse_reasoning_answer(content, valid_letters)
            elapsed_s = round(time.time() - started, 3)
            return {
                "question_id": record["question_id"],
                "entry_id": record["entry_id"],
                "gold_answer": record["answer"],
                "reasoning_steps": reasoning_steps,
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
                            + (
                                "Return only strict JSON in the form "
                                "{\"reasoning_steps\": [\"...\"], \"answer\": \"<LETTER>\"}. "
                                "Keep 2-5 concise English reasoning steps and one valid option letter."
                                if output_format == "json"
                                else "Please try again and put the answer on the last non-empty line exactly as "
                                "'Final Answer: A'."
                            )
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
        "response_content": last_content,
        "latency_s": elapsed_s,
    }


def sanitize_model_id(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model)


def default_output_path(questions_path: Path, model: str) -> Path:
    suffix = sanitize_model_id(model)
    return questions_path.with_name(f"{questions_path.stem}.eval.{suffix}.json")


def partial_output_path(output_path: Path) -> Path:
    return output_path.with_suffix(".partial.jsonl")


def repo_relative_display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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
            question_id = parsed.get("question_id")
            if not isinstance(question_id, str) or not question_id:
                raise RuntimeError(f"Missing question_id in partial results at line {line_no}: {path}")
            if parsed.get("predicted_answer") is None:
                skipped_invalid += 1
                continue
            cached[question_id] = parsed
    return cached, skipped_invalid


def append_partial_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS, help="Question JSON file to evaluate.")
    parser.add_argument("--output", type=Path, help="Evaluation output JSON path.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id.")
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Optional sampling temperature. Omit to use the provider default.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Optional max output tokens per question. Omit to use the provider default.",
    )
    parser.add_argument("--timeout-s", type=float, default=120.0, help="HTTP timeout per API call.")
    parser.add_argument("--retries", type=int, default=2, help="Retries per question after invalid output or request failure.")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent evaluation requests.")
    parser.add_argument("--limit", type=int, help="Optional limit on the number of questions evaluated.")
    parser.add_argument("--api-key-stdin", action="store_true", help="Read the API key from the first stdin line.")
    parser.add_argument(
        "--output-format",
        choices=("tagged", "json"),
        default="tagged",
        help="Model output contract. 'tagged' allows freeform reasoning but requires the last non-empty line to be 'Final Answer: X'.",
    )
    parser.add_argument(
        "--disable-response-format",
        action="store_true",
        help="Do not request OpenRouter response_format=json_object; useful for models with weak JSON-mode compatibility.",
    )
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
    partial_path = partial_output_path(output_path)
    cached_results, skipped_invalid_cache = load_partial_results(partial_path)

    started = time.time()
    results: list[dict[str, Any] | None] = [None] * len(questions)
    pending_questions: list[tuple[int, dict[str, Any]]] = []
    restored_count = 0
    for idx, record in enumerate(questions):
        cached = cached_results.get(record["question_id"])
        if cached is None:
            pending_questions.append((idx, record))
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

    use_response_format = args.output_format == "json" and not args.disable_response_format
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
                use_response_format=use_response_format,
                output_format=args.output_format,
            ): idx
            for idx, record in pending_questions
        }
        completed_count = restored_count
        for future in as_completed(futures):
            idx = futures[future]
            result = future.result()
            results[idx] = result
            append_partial_result(partial_path, result)
            completed_count += 1
            print(
                f"[{completed_count}/{len(questions)}] {result['question_id']} -> "
                f"{result.get('predicted_answer') or 'ERROR'} | correct={result['correct']}",
                file=sys.stderr,
                flush=True,
            )

    finalized_results = [result for result in results if result is not None]
    if len(finalized_results) != len(questions):
        missing = len(questions) - len(finalized_results)
        raise RuntimeError(f"Evaluation incomplete: missing {missing} results")
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
        "questions_path": repo_relative_display(args.questions),
        "output_path": repo_relative_display(output_path),
        "partial_output_path": repo_relative_display(partial_path),
        "count": len(finalized_results),
        "model_requested": args.model,
        "model_returned": sorted(model_returns),
        "concurrency": args.concurrency,
        "output_format": args.output_format,
        "use_response_format": use_response_format,
        "restored_valid_cache_count": restored_count,
        "retried_invalid_cache_count": skipped_invalid_cache,
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
