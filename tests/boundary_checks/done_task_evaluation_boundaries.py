from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_TASK_FILE_RE = re.compile(r"^T(\d+)-.*\.md$")
_KEY_RE = re.compile(r"^( *)([A-Za-z0-9_]+):(?:\s.*)?$")


@dataclass(frozen=True)
class DoneTaskEvaluationViolation:
    kind: str
    key: str
    reason: str


def load_boundaries(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _iter_done_task_files(
    root: Path,
    include: list[str],
    exclude: list[str],
) -> list[Path]:
    matched: set[Path] = set()
    for pattern in include:
        matched.update(root.glob(pattern))

    excluded = {root / pattern for pattern in exclude}
    results: list[Path] = []
    for file_path in sorted(matched):
        if file_path.suffix.lower() != ".md":
            continue
        if file_path in excluded:
            continue
        results.append(file_path)
    return results


def _task_number(file_path: Path) -> int | None:
    match = _TASK_FILE_RE.match(file_path.name)
    if match is None:
        return None
    return int(match.group(1))


def _extract_frontmatter(lines: list[str]) -> list[str] | None:
    if not lines or lines[0].strip() != "---":
        return None

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None


def _key_paths(frontmatter: list[str]) -> tuple[set[str], list[str]]:
    paths: set[str] = set()
    stack: list[str] = []
    issues: list[str] = []

    for line in frontmatter:
        if line.startswith("\t"):
            issues.append("tab indentation is not allowed")
            continue

        match = _KEY_RE.match(line)
        if match is None:
            continue

        spaces = len(match.group(1))
        if spaces % 2 != 0:
            issues.append("indentation must use multiples of two spaces")
            continue

        depth = spaces // 2
        if depth > len(stack):
            issues.append("indentation jump is not allowed")
            depth = len(stack)

        stack = stack[:depth]
        stack.append(match.group(2))
        paths.add(".".join(stack))

    return paths, issues


def _evaluate_file(
    *,
    root: Path,
    file_path: Path,
    required_fields: list[str],
) -> list[DoneTaskEvaluationViolation]:
    file_key = file_path.relative_to(root).as_posix()
    lines = file_path.read_text(encoding="utf-8").splitlines()
    frontmatter = _extract_frontmatter(lines)

    if frontmatter is None:
        return [
            DoneTaskEvaluationViolation(
                kind="frontmatter",
                key=file_key,
                reason="missing YAML frontmatter at file start",
            )
        ]

    paths, issues = _key_paths(frontmatter)
    violations: list[DoneTaskEvaluationViolation] = []

    for issue in issues:
        violations.append(
            DoneTaskEvaluationViolation(
                kind="format",
                key=file_key,
                reason=issue,
            )
        )

    for field in required_fields:
        if field in paths:
            continue
        violations.append(
            DoneTaskEvaluationViolation(
                kind="field",
                key=f"{file_key}::{field}",
                reason="missing required field",
            )
        )

    return violations


def evaluate_boundaries(
    root: Path,
    config: dict[str, Any],
) -> list[DoneTaskEvaluationViolation]:
    include = config.get("include", ["docs/workflow/done/T*.md"])
    exclude = config.get("exclude", [])
    required_fields = config.get("required_fields", [])
    min_task_number = int(config.get("enforce_from_task_number", 0))

    violations: list[DoneTaskEvaluationViolation] = []
    for file_path in _iter_done_task_files(root, include, exclude):
        task_number = _task_number(file_path)
        if task_number is None or task_number < min_task_number:
            continue

        violations.extend(
            _evaluate_file(
                root=root,
                file_path=file_path,
                required_fields=required_fields,
            )
        )

    return violations


def format_violations(violations: list[DoneTaskEvaluationViolation]) -> str:
    if not violations:
        return ""

    lines = ["Done-task evaluation boundary violations detected:"]
    for violation in violations:
        lines.append(
            f"- [{violation.kind}] {violation.key}: {violation.reason}"
        )
    return "\n".join(lines)
