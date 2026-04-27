from __future__ import annotations

import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_ENV_PATH = SCRIPT_DIR / ".env"
LEVEL1_ENV_PATH = SCRIPT_DIR.parent / "level-1" / ".env"
ROOT_ENV_PATH = REPO_ROOT / ".env"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-5.4"


def parse_dotenv_value(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return ""
    if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_from_paths(
    paths: list[Path] | tuple[Path, ...] = (DEFAULT_ENV_PATH, LEVEL1_ENV_PATH, ROOT_ENV_PATH)
) -> None:
    for path in paths:
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, raw_value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = parse_dotenv_value(raw_value)


def get_api_key(*, read_from_stdin: bool = False) -> str:
    load_env_from_paths()
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    if read_from_stdin:
        line = sys.stdin.readline().strip()
        if line:
            return line
    prompt = "Enter OPENROUTER_API_KEY: "
    return getpass.getpass(prompt).strip()


def model_from_env(default: str = DEFAULT_MODEL) -> str:
    load_env_from_paths()
    return os.environ.get("OPENROUTER_MODEL", default)


def repo_relative_display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def compact_text(text: str, max_len: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("expected a JSON object")
    return parsed


def openrouter_chat_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout_s: float = 120.0,
    use_response_format: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
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
            "HTTP-Referer": "https://github.com/black-yt/LabOS",
            "X-Title": "LabOS Level 2 Pipeline",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter request failed: {exc.code} {exc.reason}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc}") from exc
    return json.loads(body)
