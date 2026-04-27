from __future__ import annotations

import ast
import math
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
RELAXED_NUMERIC_REL_TOL = 0.10
RELAXED_NUMERIC_ABS_TOL = 1e-6


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


def longest_common_action_alignment(gold_actions: list[str], pred_actions: list[str]) -> list[tuple[int, int]]:
    m = len(gold_actions)
    n = len(pred_actions)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            if gold_actions[i] == pred_actions[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

    alignment: list[tuple[int, int]] = []
    i = 0
    j = 0
    while i < m and j < n:
        if gold_actions[i] == pred_actions[j]:
            alignment.append((i, j))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return alignment


def relaxed_action_sequence_similarity(gold_actions: list[str], pred_actions: list[str]) -> float:
    denominator = max(len(gold_actions), len(pred_actions), 1)
    matched_positions = sum(1 for gold_action, pred_action in zip(gold_actions, pred_actions) if gold_action == pred_action)
    return matched_positions / denominator


def numeric_literals_compatible(gold_value: Any, pred_value: Any) -> bool:
    if isinstance(gold_value, bool) or isinstance(pred_value, bool):
        return gold_value == pred_value
    if isinstance(gold_value, (int, float)) and isinstance(pred_value, (int, float)):
        return math.isclose(
            float(gold_value),
            float(pred_value),
            rel_tol=RELAXED_NUMERIC_REL_TOL,
            abs_tol=RELAXED_NUMERIC_ABS_TOL,
        )
    return gold_value == pred_value


def relaxed_parameter_accuracy(
    gold_steps: list[ProgramStep],
    pred_steps: list[ProgramStep],
    *,
    raw_inputs: set[str],
    alignment: list[tuple[int, int]],
) -> tuple[float, dict[str, Any]]:
    gold_output_to_index = {step.output: idx for idx, step in enumerate(gold_steps) if step.output}
    pred_output_to_index = {step.output: idx for idx, step in enumerate(pred_steps) if step.output}
    aligned_pred_for_gold = {gold_idx: pred_idx for gold_idx, pred_idx in alignment}
    aligned_gold_for_pred = {pred_idx: gold_idx for gold_idx, pred_idx in alignment}

    var_map_pred_to_gold: dict[str, str] = {}
    for gold_idx, pred_idx in alignment:
        gold = gold_steps[gold_idx]
        pred = pred_steps[pred_idx]
        if gold.output and pred.output:
            var_map_pred_to_gold[pred.output] = gold.output

    correct_count = 0
    total_count = 0
    details: list[dict[str, Any]] = []

    for gold_idx, gold in enumerate(gold_steps):
        pred_idx = aligned_pred_for_gold.get(gold_idx)
        if pred_idx is None:
            total_count += len(gold.inputs)
            details.append(
                {
                    "step": gold_idx + 1,
                    "gold_action": gold.action,
                    "pred_action": None,
                    "status": "missing_step",
                    "matched_parameters": 0,
                    "total_parameters": len(gold.inputs),
                }
            )
            continue

        pred = pred_steps[pred_idx]
        matched = 0
        union_keys = set(gold.inputs) | set(pred.inputs)
        total_count += len(union_keys)

        for key in sorted(union_keys):
            gold_argument = gold.inputs.get(key)
            pred_argument = pred.inputs.get(key)
            if gold_argument is None or pred_argument is None:
                continue

            gold_kind, gold_value = classify_argument(
                gold_argument,
                step_index=gold_idx,
                raw_inputs=raw_inputs,
                output_to_index=gold_output_to_index,
            )
            pred_kind, pred_value = classify_argument(
                pred_argument,
                step_index=pred_idx,
                raw_inputs=raw_inputs,
                output_to_index=pred_output_to_index,
            )
            if gold_kind != pred_kind:
                continue
            if gold_kind == "generated_var":
                if var_map_pred_to_gold.get(str(pred_value)) == gold_value:
                    matched += 1
                continue
            if gold_kind == "literal":
                if numeric_literals_compatible(gold_value, pred_value):
                    matched += 1
                continue
            if gold_value == pred_value:
                matched += 1

        correct_count += matched
        details.append(
            {
                "step": gold_idx + 1,
                "gold_action": gold.action,
                "pred_action": pred.action,
                "status": "aligned",
                "matched_parameters": matched,
                "total_parameters": len(union_keys),
            }
        )

    for pred_idx, pred in enumerate(pred_steps):
        if pred_idx in aligned_gold_for_pred:
            continue
        total_count += len(pred.inputs)
        details.append(
            {
                "step": pred_idx + 1,
                "gold_action": None,
                "pred_action": pred.action,
                "status": "extra_step",
                "matched_parameters": 0,
                "total_parameters": len(pred.inputs),
            }
        )

    denominator = max(total_count, 1)
    return correct_count / denominator, {
        "matched_parameter_count": correct_count,
        "total_parameter_count": total_count,
        "alignment_length": len(alignment),
        "details": details,
    }


def compare_program_steps(
    gold_steps: list[ProgramStep],
    pred_steps: list[ProgramStep],
    *,
    raw_inputs: set[str],
) -> dict[str, Any]:
    gold_actions = [step.action for step in gold_steps]
    pred_actions = [step.action for step in pred_steps]
    order_similarity = kendall_tau_similarity_for_actions(gold_actions, pred_actions)
    relaxed_sequence_similarity = relaxed_action_sequence_similarity(gold_actions, pred_actions)
    relaxed_alignment = longest_common_action_alignment(gold_actions, pred_actions)

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
    relaxed_parameter, relaxed_meta = relaxed_parameter_accuracy(
        gold_steps,
        pred_steps,
        raw_inputs=raw_inputs,
        alignment=relaxed_alignment,
    )
    return {
        "action_sequence_similarity": order_similarity,
        "parameter_accuracy": parameter_accuracy,
        "final_score": (order_similarity + parameter_accuracy) / 2.0,
        "relaxed_action_sequence_similarity": relaxed_sequence_similarity,
        "relaxed_parameter_accuracy": relaxed_parameter,
        "relaxed_final_score": (relaxed_sequence_similarity + relaxed_parameter) / 2.0,
        "details": results,
        "error_count": error_count,
        "relaxed_details": relaxed_meta["details"],
        "relaxed_alignment_length": relaxed_meta["alignment_length"],
        "relaxed_matched_parameter_count": relaxed_meta["matched_parameter_count"],
        "relaxed_total_parameter_count": relaxed_meta["total_parameter_count"],
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
