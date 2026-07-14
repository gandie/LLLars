from __future__ import annotations

from pathlib import Path


def resolve_mount_directory(
    raw_value: str,
    *,
    config_root: Path,
    default_path: Path,
    field_name: str,
) -> Path:
    path = default_path if not raw_value else Path(raw_value)
    if not path.is_absolute():
        path = config_root / path
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"Invalid {field_name}: {resolved}")
    return resolved


def resolve_project_root(
    project_root_raw: str,
    *,
    config_root: Path,
    mount_work_root: Path,
) -> Path:
    raw = project_root_raw.strip()
    candidate_path = Path(raw)

    if candidate_path.is_absolute():
        raise ValueError(
            "Invalid project_root: absolute paths are not allowed"
        )
    if ".." in candidate_path.parts:
        raise ValueError(
            "Invalid project_root: parent traversal is not allowed"
        )

    resolved = (config_root / candidate_path).resolve()
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError(f"Invalid project_root: {resolved}")

    work_root_resolved = mount_work_root.resolve()
    try:
        resolved.relative_to(work_root_resolved)
    except ValueError as exc:
        raise ValueError(
            f"Invalid project_root: {resolved} escapes mount_work_root"
        ) from exc
    return resolved
