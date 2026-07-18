from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BoundaryViolation:
    kind: str
    key: str
    limit: int
    actual: int
    reason: str


def _iter_python_files(root: Path, include: list[str], exclude: list[str]) -> list[Path]:
    matched: set[Path] = set()
    for pattern in include:
        matched.update(root.glob(pattern))

    filtered: list[Path] = []
    excluded = {root / pattern for pattern in exclude}
    for file_path in sorted(matched):
        if file_path.suffix != ".py":
            continue
        if file_path in excluded:
            continue
        filtered.append(file_path)
    return filtered


def _line_count(text: str) -> int:
    return len(text.splitlines())


def _function_id(file_key: str, node: ast.AST, class_name: str | None) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise TypeError("Expected function node")
    if class_name:
        return f"{file_key}::{class_name}.{node.name}"
    return f"{file_key}::{node.name}"


def _function_line_count(node: ast.AST) -> int | None:
    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", None)
    if not start or not end:
        return None
    return end - start + 1


def _iter_functions(tree: ast.Module, file_key: str) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = _function_line_count(node)
            if size is not None:
                result.append((_function_id(file_key, node, None), size))
            continue

        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    size = _function_line_count(child)
                    if size is not None:
                        result.append((_function_id(file_key, child, node.name), size))

    return result


def load_boundaries(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _default_limits(config: dict[str, Any]) -> tuple[int, int]:
    defaults = config["defaults"]
    return int(defaults["max_file_lines"]), int(defaults["max_function_lines"])


def _waivers(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    waivers = config.get("waivers", {})
    return waivers.get("files", {}), waivers.get("functions", {})


def _function_limit(
    *,
    fn_id: str,
    file_waiver: dict[str, Any],
    fn_waivers: dict[str, Any],
    fn_limit_default: int,
) -> tuple[int, str]:
    fn_waiver = fn_waivers.get(fn_id, {})
    limit = int(fn_waiver.get("max_function_lines", file_waiver.get("max_function_lines", fn_limit_default)))
    reason = fn_waiver.get("reason", file_waiver.get("reason", "function exceeds limit"))
    return limit, reason


def _function_violations(
    *,
    tree: ast.Module,
    file_key: str,
    file_waiver: dict[str, Any],
    fn_waivers: dict[str, Any],
    fn_limit_default: int,
) -> list[BoundaryViolation]:
    violations: list[BoundaryViolation] = []
    for fn_id, fn_lines in _iter_functions(tree, file_key=file_key):
        fn_limit, reason = _function_limit(
            fn_id=fn_id,
            file_waiver=file_waiver,
            fn_waivers=fn_waivers,
            fn_limit_default=fn_limit_default,
        )
        if fn_lines > fn_limit:
            violations.append(
                BoundaryViolation(
                    kind="function",
                    key=fn_id,
                    limit=fn_limit,
                    actual=fn_lines,
                    reason=reason,
                )
            )
    return violations


def _evaluate_file(
    *,
    root: Path,
    file_path: Path,
    file_limit_default: int,
    fn_limit_default: int,
    file_waivers: dict[str, Any],
    fn_waivers: dict[str, Any],
) -> list[BoundaryViolation]:
    file_key = file_path.relative_to(root).as_posix()
    source = file_path.read_text(encoding="utf-8")
    file_waiver = file_waivers.get(file_key, {})
    file_limit = int(file_waiver.get("max_file_lines", file_limit_default))

    violations: list[BoundaryViolation] = []
    file_lines = _line_count(source)
    if file_lines > file_limit:
        violations.append(
            BoundaryViolation(
                kind="file",
                key=file_key,
                limit=file_limit,
                actual=file_lines,
                reason=file_waiver.get("reason", "file exceeds limit"),
            )
        )

    tree = ast.parse(source)
    violations.extend(_function_violations(tree=tree, file_key=file_key, file_waiver=file_waiver, fn_waivers=fn_waivers, fn_limit_default=fn_limit_default))
    return violations


def evaluate_boundaries(root: Path, config: dict[str, Any]) -> list[BoundaryViolation]:
    file_limit_default, fn_limit_default = _default_limits(config)
    file_waivers, fn_waivers = _waivers(config)
    include = config.get("include", ["lllars_core/*.py"])
    exclude = config.get("exclude", [])

    violations: list[BoundaryViolation] = []
    for file_path in _iter_python_files(root, include=include, exclude=exclude):
        violations.extend(
            _evaluate_file(
                root=root,
                file_path=file_path,
                file_limit_default=file_limit_default,
                fn_limit_default=fn_limit_default,
                file_waivers=file_waivers,
                fn_waivers=fn_waivers,
            )
        )

    return violations


def format_violations(violations: list[BoundaryViolation]) -> str:
    if not violations:
        return ""
    lines = ["Refactor boundary violations detected:"]
    for v in violations:
        lines.append(
            f"- [{v.kind}] {v.key}: actual={v.actual}, limit={v.limit}, reason={v.reason}"
        )
    return "\n".join(lines)
