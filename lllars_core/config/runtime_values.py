from __future__ import annotations

from pathlib import Path

from lllars_core.config.models import (
    DEFAULT_MCP_INIT_TIMEOUT_SEC,
    DEFAULT_NETWORK_POLICY,
    DEFAULT_QUEUE_BACKEND,
    DEFAULT_SERVICE_HOST,
    DEFAULT_SERVICE_PORT,
    DEFAULT_SERVICE_WORKERS,
    ROOT,
    VALID_NETWORK_POLICIES,
    VALID_QUEUE_BACKENDS,
)
from lllars_core.config.runtime_section import (
    as_bool,
    optional_float,
    positive_int,
    resolve_mount_root,
    validate_choice,
)
from lllars_core.runtime_guard import resolve_project_root


def load_skills_settings(cfg: dict) -> tuple[bool, str, bool, bool]:
    skills_enabled = as_bool(cfg.get("skills_enabled", False), False)
    skills_glob = str(cfg.get("skills_glob", "")).strip()
    skills_defer_loading = as_bool(cfg.get("skills_defer_loading", True), True)
    skills_require_description = as_bool(
        cfg.get("skills_require_description", True),
        True,
    )
    if skills_enabled and not skills_glob:
        raise ValueError("skills_enabled is true but skills_glob is empty")
    return (
        skills_enabled,
        skills_glob,
        skills_defer_loading,
        skills_require_description,
    )


def load_mcp_settings(cfg: dict) -> tuple[bool, Path | None, float]:
    mcp_enabled = as_bool(cfg.get("mcp_enabled", False), False)
    mcp_config_raw = str(cfg.get("mcp_config_path", "")).strip()
    mcp_config_path: Path | None = None
    if mcp_config_raw:
        mcp_config_path = (ROOT / mcp_config_raw).resolve()

    mcp_timeout = optional_float(
        cfg,
        "mcp_init_timeout_sec",
        DEFAULT_MCP_INIT_TIMEOUT_SEC,
    )
    if mcp_timeout is None:
        mcp_timeout = DEFAULT_MCP_INIT_TIMEOUT_SEC

    if mcp_enabled:
        if mcp_config_path is None:
            raise ValueError(
                "mcp_enabled is true but mcp_config_path is empty"
            )
        if not mcp_config_path.exists() or not mcp_config_path.is_file():
            raise ValueError(f"Invalid mcp_config_path: {mcp_config_path}")

    return mcp_enabled, mcp_config_path, mcp_timeout


def load_service_settings(
    cfg: dict,
    *,
    config_root: Path,
    config_path: Path,
    project_root_raw: str,
) -> tuple[str, int, int, Path, Path, Path, str, str, Path]:
    service_host, service_port, service_workers = (
        _service_host_and_workers(cfg)
    )
    queue_backend, network_policy = _service_network_settings(cfg)
    mount_values = _service_mounts(
        cfg,
        config_root=config_root,
        config_path=config_path,
        project_root_raw=project_root_raw,
    )
    return (
        service_host,
        service_port,
        service_workers,
        mount_values[0],
        mount_values[1],
        mount_values[2],
        queue_backend,
        network_policy,
        mount_values[3],
    )


def _service_host_and_workers(cfg: dict) -> tuple[str, int, int]:
    service_host = (
        str(cfg.get("service_host", DEFAULT_SERVICE_HOST)).strip()
        or DEFAULT_SERVICE_HOST
    )
    service_port = positive_int(cfg, "service_port", DEFAULT_SERVICE_PORT)
    service_workers = positive_int(
        cfg,
        "service_workers",
        DEFAULT_SERVICE_WORKERS,
    )
    return service_host, service_port, service_workers


def _service_network_settings(cfg: dict) -> tuple[str, str]:
    queue_backend = validate_choice(
        cfg,
        "queue_backend",
        default=DEFAULT_QUEUE_BACKEND,
        valid_values=VALID_QUEUE_BACKENDS,
    )
    network_policy = validate_choice(
        cfg,
        "network_policy",
        default=DEFAULT_NETWORK_POLICY,
        valid_values=VALID_NETWORK_POLICIES,
    )
    return queue_backend, network_policy


def _service_mounts(
    cfg: dict,
    *,
    config_root: Path,
    config_path: Path,
    project_root_raw: str,
) -> tuple[Path, Path, Path, Path]:
    mount_work_root = _mount_work_root(
        cfg,
        config_root=config_root,
        project_root_raw=project_root_raw,
    )
    project_root = _project_root(
        project_root_raw,
        config_root=config_root,
        mount_work_root=mount_work_root,
    )
    mount_config_root = resolve_mount_root(
        cfg,
        "mount_config_root",
        config_root=config_root,
        default_path=config_path.parent.resolve(),
    )
    mount_artifacts_root = resolve_mount_root(
        cfg,
        "mount_artifacts_root",
        config_root=config_root,
        default_path=ROOT,
    )
    return (
        mount_work_root,
        mount_config_root,
        mount_artifacts_root,
        project_root,
    )


def _mount_work_root(
    cfg: dict,
    *,
    config_root: Path,
    project_root_raw: str,
) -> Path:
    default_path = (
        (config_root / project_root_raw).resolve()
        if project_root_raw
        else config_root
    )
    return resolve_mount_root(
        cfg,
        "mount_work_root",
        config_root=config_root,
        default_path=default_path,
    )


def _project_root(
    project_root_raw: str,
    *,
    config_root: Path,
    mount_work_root: Path,
) -> Path:
    if not project_root_raw:
        return mount_work_root
    return resolve_project_root(
        project_root_raw,
        config_root=config_root,
        mount_work_root=mount_work_root,
    )
