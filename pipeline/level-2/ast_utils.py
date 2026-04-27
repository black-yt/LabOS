from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from itertools import combinations
from typing import Any


@dataclass(frozen=True)
class ParsedArgument:
    kind: str
    value: Any


@dataclass(frozen=True)
class ProgramStep:
    action: str
    inputs: dict[str, ParsedArgument]
    output: str | None


CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*([\s\S]*?)```", re.IGNORECASE)


def normalize_literal(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 8)
    return value


def parse_argument_node(node: ast.AST) -> ParsedArgument:
    if isinstance(node, ast.Constant):
        return ParsedArgument("literal", normalize_literal(node.value))
    if isinstance(node, ast.Name):
        return ParsedArgument("name", node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
        operand = node.operand.value
        if isinstance(operand, (int, float)):
            return ParsedArgument("literal", normalize_literal(-operand))
    return ParsedArgument("expression", ast.unparse(node))


def extract_steps_from_ast(tree: ast.AST) -> list[ProgramStep]:
    steps: list[ProgramStep] = []
    for node in tree.body:
        call: ast.Call | None = None
        output: str | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if isinstance(node.value, ast.Call):
                output = node.targets[0].id
                call = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and isinstance(node.value, ast.Call):
            output = node.target.id
            call = node.value
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
        elif isinstance(node, ast.FunctionDef):
            continue
        elif isinstance(node, (ast.Import, ast.ImportFrom, ast.Pass)):
            continue
        else:
            raise ValueError(f"unsupported top-level statement: {ast.dump(node, include_attributes=False)}")

        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
            raise ValueError("only direct function calls are supported")
        if call.args:
            raise ValueError("positional arguments are not allowed; use keyword arguments only")
        if any(keyword.arg is None for keyword in call.keywords):
            raise ValueError("**kwargs are not allowed")
        inputs = {keyword.arg: parse_argument_node(keyword.value) for keyword in call.keywords if keyword.arg is not None}
        steps.append(ProgramStep(action=call.func.id, inputs=inputs, output=output))
    return steps


def parse_program_steps(code: str) -> list[ProgramStep]:
    tree = ast.parse(code)
    return extract_steps_from_ast(tree)


def extract_python_program(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError("empty response")

    for match in CODE_BLOCK_RE.finditer(text):
        candidate = match.group(1).strip()
        if not candidate:
            continue
        try:
            steps = parse_program_steps(candidate)
        except Exception:
            continue
        if steps:
            return candidate

    try:
        steps = parse_program_steps(text)
    except Exception:
        pass
    else:
        if steps:
            return text

    lines = [line for line in text.splitlines() if line.strip()]
    for start in range(len(lines)):
        candidate = "\n".join(lines[start:]).strip()
        if not candidate:
            continue
        try:
            steps = parse_program_steps(candidate)
        except Exception:
            continue
        if steps:
            return candidate

    raise ValueError("unable to extract a parsable Python program from response")


def classify_argument(
    argument: ParsedArgument,
    *,
    step_index: int,
    raw_inputs: set[str],
    output_to_index: dict[str, int],
) -> tuple[str, Any]:
    if argument.kind == "literal":
        return "literal", argument.value
    if argument.kind != "name":
        return argument.kind, argument.value
    name = str(argument.value)
    if name in output_to_index:
        if output_to_index[name] < step_index:
            return "generated_var", name
        return "future_generated_var", name
    if name in raw_inputs:
        return "raw_var", name
    return "unknown_var", name


def label_action_occurrences(actions: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    labeled: list[str] = []
    for action in actions:
        counts[action] = counts.get(action, 0) + 1
        labeled.append(f"{action}#{counts[action]}")
    return labeled


def kendall_tau_similarity_for_actions(gold_actions: list[str], pred_actions: list[str]) -> float:
    if len(gold_actions) != len(pred_actions):
        return 0.0
    labeled_gold = label_action_occurrences(gold_actions)
    labeled_pred = label_action_occurrences(pred_actions)
    if sorted(labeled_gold) != sorted(labeled_pred):
        return 0.0
    gold_positions = {token: idx for idx, token in enumerate(labeled_gold)}
    ranked_pred = [gold_positions[token] for token in labeled_pred]
    n = len(ranked_pred)
    if n <= 1:
        return 1.0
    inversions = 0
    for i, j in combinations(range(n), 2):
        if ranked_pred[i] > ranked_pred[j]:
            inversions += 1
    max_inversions = n * (n - 1) / 2
    return 1.0 - inversions / max_inversions


def compare_program_steps(
    gold_steps: list[ProgramStep],
    pred_steps: list[ProgramStep],
    *,
    raw_inputs: set[str],
) -> dict[str, Any]:
    gold_actions = [step.action for step in gold_steps]
    pred_actions = [step.action for step in pred_steps]
    order_similarity = kendall_tau_similarity_for_actions(gold_actions, pred_actions)

    gold_output_to_index = {step.output: idx for idx, step in enumerate(gold_steps) if step.output}
    pred_output_to_index = {step.output: idx for idx, step in enumerate(pred_steps) if step.output}

    results: list[dict[str, Any]] = []
    error_count = 0
    var_map_pred_to_gold: dict[str, str] = {}
    min_len = min(len(gold_steps), len(pred_steps))

    for idx in range(min_len):
        gold = gold_steps[idx]
        pred = pred_steps[idx]
        detail = {
            "step": idx + 1,
            "gold_action": gold.action,
            "pred_action": pred.action,
            "status": "ok",
            "errors": [],
        }

        if gold.action != pred.action:
            detail["status"] = "error"
            detail["errors"].append("action_mismatch")
            error_count += 1
            results.append(detail)
            continue

        gold_keys = set(gold.inputs)
        pred_keys = set(pred.inputs)
        if gold_keys != pred_keys:
            detail["status"] = "error"
            detail["errors"].append("parameter_keys_mismatch")
            error_count += 1
            results.append(detail)
            continue

        if (gold.output is None) != (pred.output is None):
            detail["status"] = "error"
            detail["errors"].append("output_assignment_mismatch")
            error_count += 1
            results.append(detail)
            continue

        step_error = False
        for key in sorted(gold_keys):
            gold_kind, gold_value = classify_argument(
                gold.inputs[key],
                step_index=idx,
                raw_inputs=raw_inputs,
                output_to_index=gold_output_to_index,
            )
            pred_kind, pred_value = classify_argument(
                pred.inputs[key],
                step_index=idx,
                raw_inputs=raw_inputs,
                output_to_index=pred_output_to_index,
            )

            if gold_kind != pred_kind:
                detail["status"] = "error"
                detail["errors"].append(f"{key}:type:{gold_kind}!={pred_kind}")
                step_error = True
                continue

            if gold_kind == "generated_var":
                mapped = var_map_pred_to_gold.get(str(pred_value))
                if mapped != gold_value:
                    detail["status"] = "error"
                    detail["errors"].append(f"{key}:generated_ref:{gold_value}!={mapped or pred_value}")
                    step_error = True
                continue

            if gold_kind in {"raw_var", "literal", "expression", "unknown_var", "future_generated_var"}:
                if gold_value != pred_value:
                    detail["status"] = "error"
                    detail["errors"].append(f"{key}:value:{gold_value}!={pred_value}")
                    step_error = True

        if step_error:
            error_count += 1
        elif gold.output and pred.output:
            var_map_pred_to_gold[pred.output] = gold.output
        results.append(detail)

    if len(gold_steps) != len(pred_steps):
        gap = abs(len(gold_steps) - len(pred_steps))
        error_count += gap
        longer = "pred" if len(pred_steps) > len(gold_steps) else "gold"
        for idx in range(min_len, max(len(gold_steps), len(pred_steps))):
            results.append(
                {
                    "step": idx + 1,
                    "gold_action": gold_steps[idx].action if idx < len(gold_steps) else None,
                    "pred_action": pred_steps[idx].action if idx < len(pred_steps) else None,
                    "status": "error",
                    "errors": ["extra_step" if longer == "pred" else "missing_step"],
                }
            )

    denominator = max(len(gold_steps), len(pred_steps), 1)
    parameter_accuracy = max(0.0, 1.0 - error_count / denominator)
    return {
        "action_sequence_similarity": order_similarity,
        "parameter_accuracy": parameter_accuracy,
        "final_score": (order_similarity + parameter_accuracy) / 2.0,
        "details": results,
        "error_count": error_count,
    }


def numeric_literal_count(code: str) -> int:
    tree = ast.parse(code)
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            count += 1
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            if isinstance(node.operand.value, (int, float)):
                count += 1
    return count
