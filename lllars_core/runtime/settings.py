from __future__ import annotations

from dataclasses import is_dataclass, replace
from pathlib import Path

from lllars_core.config import (
    COMMAND_PROFILE_REGISTRY,
    DEFAULT_CONFIG_PATH,
    HarnessConfig,
    RunConfig,
    canonicalize_shell_command,
)
from lllars_core.runtime.models import HARNESS_RUN_SYNC_FIELDS
from lllars_core.runtime.models import RUN_CFG_OVERRIDE_FIELDS
from lllars_core.runtime.models import RunCommandSettings
from lllars_core.runtime_guard import resolve_project_root
from lllars_core.runtime.models import JobSpec


def resolve_config_path(spec: JobSpec) -> Path:
    if spec.config_path is None:
        return DEFAULT_CONFIG_PATH.resolve()
    return Path(spec.config_path).resolve()


def apply_job_run_settings(cfg: HarnessConfig, spec: JobSpec) -> HarnessConfig:
    if not hasattr(cfg, "mount_work_root"):
        return cfg

    project_root = _resolve_project_root(cfg, spec)
    commands = _resolve_run_commands(cfg, spec)
    run_cfg = _build_run_config(cfg, spec, project_root, commands)
    mcp_config_path = _resolve_and_validate_mcp_config(cfg, run_cfg)
    _validate_skills_config(run_cfg)

    if not is_dataclass(cfg):
        return cfg
    updates = _dataclass_updates(
        spec,
        project_root,
        commands,
        run_cfg,
        mcp_config_path,
    )
    return replace(cfg, **updates)


def _resolve_project_root(cfg: HarnessConfig, spec: JobSpec) -> Path:
    mount_root = cfg.mount_work_root.resolve()
    run_project_root = spec.run.project_root
    if run_project_root.is_absolute():
        resolved = run_project_root.resolve()
        try:
            resolved.relative_to(mount_root)
        except ValueError as exc:
            raise ValueError(
                "Invalid project_root: "
                f"{resolved} escapes mount_work_root"
            ) from exc
        return resolved
    return resolve_project_root(
        str(run_project_root),
        config_root=mount_root,
        mount_work_root=mount_root,
    )


def _resolve_run_commands(
    cfg: HarnessConfig,
    spec: JobSpec,
) -> RunCommandSettings:
    command_profile = _command_profile(cfg, spec)
    run_commands = spec.run.commands or {}
    test_raw = spec.run.test_command
    eval_raw = spec.run.eval_command
    if test_raw is None and isinstance(run_commands, dict):
        test_raw = run_commands.get("test")
    if eval_raw is None and isinstance(run_commands, dict):
        eval_raw = run_commands.get("eval")

    test_command = _normalize_command(test_raw)
    eval_command = _normalize_command(eval_raw)
    return RunCommandSettings(
        command_profile=command_profile,
        test_command=test_command,
        eval_command=eval_command,
        allowed_shell_commands=_allowed_commands(
            command_profile,
            test_command,
            eval_command,
        ),
    )


def _command_profile(cfg: HarnessConfig, spec: JobSpec) -> str:
    command_profile = (
        (spec.run.command_profile or "").strip().lower()
        or cfg.command_profile
    )
    if command_profile in COMMAND_PROFILE_REGISTRY:
        return command_profile

    available = ", ".join(sorted(COMMAND_PROFILE_REGISTRY))
    raise ValueError(
        "Unknown command_profile "
        f"{command_profile!r}. Available profiles: {available}"
    )


def _normalize_command(raw_value: object) -> str | None:
    return (raw_value.strip() or None) if isinstance(raw_value, str) else None


def _allowed_commands(
    command_profile: str, test_command: str | None, eval_command: str | None
) -> tuple[str, ...]:
    seen: set[str] = set()
    allowed: list[str] = []
    raw_commands = [
        test_command,
        eval_command,
        *COMMAND_PROFILE_REGISTRY[command_profile],
    ]
    for raw_command in raw_commands:
        canonical = canonicalize_shell_command(raw_command or "")
        if canonical and canonical not in seen:
            seen.add(canonical)
            allowed.append(canonical)
    return tuple(allowed)


def _build_run_config(
    cfg: HarnessConfig,
    spec: JobSpec,
    project_root: Path,
    commands: RunCommandSettings,
) -> RunConfig:
    command_map = {
        key: value
        for key, value in {
            "test": commands.test_command,
            "eval": commands.eval_command,
        }.items()
        if value is not None
    }
    return RunConfig(
        model=spec.run.model,
        provider_url=spec.run.provider_url,
        project_root=project_root,
        commands=command_map,
        test_command=commands.test_command,
        eval_command=commands.eval_command,
        command_profile=commands.command_profile,
        **_run_config_overrides(cfg, spec),
    )


def _run_config_overrides(
    cfg: HarnessConfig,
    spec: JobSpec,
) -> dict[str, object]:
    overrides: dict[str, object] = {}
    for field_name in RUN_CFG_OVERRIDE_FIELDS:
        override = getattr(spec.run, field_name)
        fallback = getattr(cfg, field_name)
        overrides[field_name] = fallback if override is None else override
    return overrides


def _resolve_and_validate_mcp_config(
    cfg: HarnessConfig,
    run_cfg: RunConfig,
) -> Path | None:
    mcp_config_path = run_cfg.mcp_config_path
    if mcp_config_path is not None and not mcp_config_path.is_absolute():
        mcp_config_path = (cfg.mount_config_root / mcp_config_path).resolve()
    if run_cfg.mcp_enabled and mcp_config_path is None:
        raise ValueError("mcp_enabled is true but mcp_config_path is empty")
    if run_cfg.mcp_enabled and mcp_config_path is not None:
        if not mcp_config_path.exists() or not mcp_config_path.is_file():
            raise ValueError(f"Invalid mcp_config_path: {mcp_config_path}")
    return mcp_config_path


def _validate_skills_config(run_cfg: RunConfig) -> None:
    if run_cfg.skills_enabled and not (run_cfg.skills_glob or "").strip():
        raise ValueError("skills_enabled is true but skills_glob is empty")


def _dataclass_updates(
    spec: JobSpec,
    project_root: Path,
    commands: RunCommandSettings,
    run_cfg: RunConfig,
    mcp_config_path: Path | None,
) -> dict[str, object]:
    updates: dict[str, object] = {
        "model": spec.run.model,
        "provider_url": spec.run.provider_url,
        "project_root": project_root,
        "test_command": commands.test_command,
        "eval_command": commands.eval_command,
        "command_profile": commands.command_profile,
        "allowed_shell_commands": commands.allowed_shell_commands,
        "mcp_config_path": mcp_config_path,
        "run": run_cfg,
    }
    for field_name in HARNESS_RUN_SYNC_FIELDS:
        value = getattr(run_cfg, field_name)
        if field_name == "skills_glob" and value is None:
            updates[field_name] = ""
        else:
            updates[field_name] = value
    return updates


__all__ = ["apply_job_run_settings", "resolve_config_path"]
