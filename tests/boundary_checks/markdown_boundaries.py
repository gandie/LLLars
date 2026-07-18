from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_HEADING_RE = re.compile(r"^(#{1,6})\\s+(.*\\S)\\s*$")


@dataclass(frozen=True)
class MarkdownBoundaryViolation:
    kind: str
    key: str
    limit: int
    actual: int
    reason: str


def _iter_markdown_files(
    root: Path,
    include: list[str],
    exclude: list[str],
) -> list[Path]:
    matched: set[Path] = set()
    for pattern in include:
        matched.update(root.glob(pattern))

    excluded = {root / pattern for pattern in exclude}
    filtered: list[Path] = []
    for file_path in sorted(matched):
        if file_path.suffix.lower() != ".md":
            continue
        if file_path in excluded:
            continue
        filtered.append(file_path)

    return filtered


def _iter_sections(lines: list[str], file_key: str) -> list[tuple[str, int]]:
    headings: list[tuple[int, str]] = []
    for i, line in enumerate(lines, start=1):
        match = _HEADING_RE.match(line)
        if not match:
            continue
        headings.append((i, match.group(2)))

    sections: list[tuple[str, int]] = []
    if not headings:
        return sections

    for idx, (start_line, title) in enumerate(headings):
        end_line = (
            headings[idx + 1][0] - 1
            if idx + 1 < len(headings)
            else len(lines)
        )
        section_len = end_line - start_line + 1
        section_key = f"{file_key}::{title}"
        sections.append((section_key, section_len))

    return sections


def load_boundaries(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_boundaries(
    root: Path,
    config: dict[str, Any],
) -> list[MarkdownBoundaryViolation]:
    defaults = config["defaults"]
    file_limit_default = int(defaults["max_file_lines"])
    section_limit_default = int(defaults["max_section_lines"])

    waivers = config.get("waivers", {})
    file_waivers = waivers.get("files", {})
    section_waivers = waivers.get("sections", {})

    include = config.get("include", ["docs/*.md"])
    exclude = config.get("exclude", [])

    violations: list[MarkdownBoundaryViolation] = []
    for file_path in _iter_markdown_files(
        root,
        include=include,
        exclude=exclude,
    ):
        violations.extend(
            _evaluate_file_boundaries(
                root=root,
                file_path=file_path,
                file_waivers=file_waivers,
                section_waivers=section_waivers,
                file_limit_default=file_limit_default,
                section_limit_default=section_limit_default,
            )
        )
    return violations


def _evaluate_file_boundaries(
    *,
    root: Path,
    file_path: Path,
    file_waivers: dict[str, Any],
    section_waivers: dict[str, Any],
    file_limit_default: int,
    section_limit_default: int,
) -> list[MarkdownBoundaryViolation]:
    file_key = file_path.relative_to(root).as_posix()
    lines = file_path.read_text(encoding="utf-8").splitlines()
    file_waiver = file_waivers.get(file_key, {})
    file_limit = int(file_waiver.get("max_file_lines", file_limit_default))

    violations: list[MarkdownBoundaryViolation] = []
    if len(lines) > file_limit:
        violations.append(
            MarkdownBoundaryViolation(
                kind="file",
                key=file_key,
                limit=file_limit,
                actual=len(lines),
                reason=file_waiver.get("reason", "file exceeds limit"),
            )
        )
    violations.extend(
        _evaluate_section_boundaries(
            lines=lines,
            file_key=file_key,
            file_waiver=file_waiver,
            section_waivers=section_waivers,
            section_limit_default=section_limit_default,
        )
    )
    return violations


def _evaluate_section_boundaries(
    *,
    lines: list[str],
    file_key: str,
    file_waiver: dict[str, Any],
    section_waivers: dict[str, Any],
    section_limit_default: int,
) -> list[MarkdownBoundaryViolation]:
    violations: list[MarkdownBoundaryViolation] = []
    for section_key, section_len in _iter_sections(lines, file_key):
        section_limit = int(
            section_waivers.get(section_key, {}).get(
                "max_section_lines",
                file_waiver.get("max_section_lines", section_limit_default),
            )
        )
        if section_len > section_limit:
            violations.append(
                MarkdownBoundaryViolation(
                    kind="section",
                    key=section_key,
                    limit=section_limit,
                    actual=section_len,
                    reason=section_waivers.get(section_key, {}).get(
                        "reason",
                        file_waiver.get("reason", "section exceeds limit"),
                    ),
                )
            )
    return violations


def format_violations(violations: list[MarkdownBoundaryViolation]) -> str:
    if not violations:
        return ""

    lines = ["Markdown boundary violations detected:"]
    for violation in violations:
        lines.append(
            f"- [{violation.kind}] {violation.key}: "
            f"actual={violation.actual}, "
            f"limit={violation.limit}, reason={violation.reason}"
        )

    return "\\n".join(lines)
