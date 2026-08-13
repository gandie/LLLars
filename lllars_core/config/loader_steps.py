from __future__ import annotations

from pathlib import Path

from lllars_core.config.runtime_inputs_builder import (
    RuntimeInputs,
    build_runtime_inputs,
)
from lllars_core.config.runtime_section import load_commands
from lllars_core.config.runtime_section import resolve_shell_policy
from lllars_core.config.tools_section import command_profile_registry
from lllars_core.config.tools_section import resolve_command_profile


def resolve_run_inputs(service_mode: str, cfg: dict) -> tuple[str, str, str]:
    model = str(cfg.get("model", "")).strip()
    provider_url = str(cfg.get("provider_url", "")).strip()
    project_root = str(cfg.get("project_root", "")).strip()
    run_configured = bool(model and provider_url and project_root)
    if service_mode != "serve" and not run_configured:
        raise ValueError("Config requires model and provider_url")
    return model, provider_url, project_root


def runtime_inputs(
    cfg: dict,
    *,
    config_root: Path | None = None,
) -> RuntimeInputs:
    return build_runtime_inputs(
        cfg,
        *_command_inputs(
            cfg,
            config_root=config_root,
        ),
    )


def _command_inputs(
    cfg: dict,
    *,
    config_root: Path | None = None,
) -> tuple:
    test_command, eval_command = load_commands(cfg)
    command_profile, profile_commands = resolve_command_profile(
        cfg,
        config_root=config_root,
    )
    registry, _ = command_profile_registry(
        cfg,
        config_root=config_root,
    )
    command_profiles = tuple(
        (profile_name, registry[profile_name])
        for profile_name in sorted(registry)
    )
    shell_settings = resolve_shell_policy(cfg)
    return (
        test_command,
        eval_command,
        command_profile,
        command_profiles,
        profile_commands,
        shell_settings,
    )






































