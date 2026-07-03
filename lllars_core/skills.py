from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic_ai.capabilities import AbstractCapability, Capability

from lllars_core.config import HarnessConfig


@dataclass(frozen=True)
class MarkdownSkillSpec:
    skill_id: str
    description: str | None
    instructions: str
    source_path: str


def _discover_skill_paths(cfg: HarnessConfig) -> list[Path]:
    if not cfg.skills_enabled:
        return []

    skill_paths = sorted(
        (
            path
            for path in cfg.project_root.glob(cfg.skills_glob)
            if path.is_file()
        ),
        key=lambda path: str(path.relative_to(cfg.project_root)).lower(),
    )
    if not skill_paths:
        raise ValueError(
            "No markdown skills matched skills_glob under project_root: "
            f"{cfg.skills_glob}"
        )
    return skill_paths


def _parse_markdown_skill(
    path: Path,
    require_description: bool,
) -> MarkdownSkillSpec:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise ValueError(
            f"Invalid skill file {path}: missing YAML frontmatter"
        )

    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(
            f"Invalid skill file {path}: malformed YAML frontmatter"
        )

    _, frontmatter, body = parts
    meta = yaml.safe_load(frontmatter)
    if not isinstance(meta, dict):
        raise ValueError(
            f"Invalid skill file {path}: frontmatter must be a mapping"
        )

    capability_id = str(meta.get("id", "")).strip()
    if not capability_id:
        raise ValueError(f"Invalid skill file {path}: missing id")

    description = str(meta.get("description", "")).strip()
    if require_description and not description:
        raise ValueError(
            f"Invalid skill file {path}: missing description"
        )

    instructions = body.strip()
    if not instructions:
        raise ValueError(
            f"Invalid skill file {path}: instructions body is empty"
        )

    return MarkdownSkillSpec(
        skill_id=capability_id,
        description=description or None,
        instructions=instructions,
        source_path=str(path),
    )


def load_markdown_skill_specs(cfg: HarnessConfig) -> list[MarkdownSkillSpec]:
    if not cfg.skills_enabled:
        return []

    skill_paths = _discover_skill_paths(cfg)
    specs: list[MarkdownSkillSpec] = []
    seen_ids: set[str] = set()

    for path in skill_paths:
        spec = _parse_markdown_skill(
            path=path,
            require_description=cfg.skills_require_description,
        )
        if spec.skill_id in seen_ids:
            raise ValueError(
                "Duplicate skill id found while loading markdown skills: "
                f"{spec.skill_id}"
            )
        seen_ids.add(spec.skill_id)
        specs.append(spec)

    return specs


def configured_markdown_skill_ids(cfg: HarnessConfig) -> tuple[str, ...]:
    if not cfg.skills_enabled:
        return ()
    return tuple(spec.skill_id for spec in load_markdown_skill_specs(cfg))


def load_markdown_skill_capabilities(
    cfg: HarnessConfig,
) -> list[AbstractCapability[Any]]:
    if not cfg.skills_enabled:
        return []

    capabilities: list[AbstractCapability[Any]] = []
    for spec in load_markdown_skill_specs(cfg):
        capabilities.append(
            Capability[Any](
                id=spec.skill_id,
                description=spec.description,
                instructions=spec.instructions,
                defer_loading=cfg.skills_defer_loading,
            )
        )

    return capabilities
