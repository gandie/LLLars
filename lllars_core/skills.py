from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic_ai.capabilities import AbstractCapability, Capability

from lllars_core.config import HarnessConfig


def _parse_markdown_skill(
    path: Path,
    require_description: bool,
    defer_loading: bool,
) -> AbstractCapability[Any]:
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

    return Capability[Any](
        id=capability_id,
        description=description or None,
        instructions=instructions,
        defer_loading=defer_loading,
    )


def load_markdown_skill_capabilities(
    cfg: HarnessConfig,
) -> list[AbstractCapability[Any]]:
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

    capabilities: list[AbstractCapability[Any]] = []
    seen_ids: set[str] = set()

    for path in skill_paths:
        capability = _parse_markdown_skill(
            path=path,
            require_description=cfg.skills_require_description,
            defer_loading=cfg.skills_defer_loading,
        )
        capability_id = str(capability.id)
        if capability_id in seen_ids:
            raise ValueError(
                "Duplicate skill id found while loading markdown skills: "
                f"{capability_id}"
            )
        seen_ids.add(capability_id)
        capabilities.append(capability)

    return capabilities
