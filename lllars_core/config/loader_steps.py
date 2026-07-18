from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lllars_core.config.models import ServiceConfig
from lllars_core.config.runtime_section import as_bool
from lllars_core.config.runtime_section import load_commands
from lllars_core.config.runtime_section import resolve_shell_policy
from lllars_core.config.runtime_values import load_service_settings
from lllars_core.config.tools_section import build_default_tool_policy
from lllars_core.config.tools_section import collect_allowed_shell_commands
from lllars_core.config.tools_section import resolve_command_profile


@dataclass(frozen=True)
class RuntimeInputs:
    test_command: str | None
    eval_command: str | None
    command_profile: str
    shell_settings: tuple[str, str | None]
    allowed_shell_commands: tuple[str, ...]
    system_prompt: str
    tool_policy: str
    eval_expect_json: bool
    eval_success_pass_rate: float


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
    test_command, eval_command, command_profile, profile_commands, shell_settings = _command_inputs(
        cfg,
        config_root=config_root,
    )
    allowed_shell_commands = collect_allowed_shell_commands(
        test_command,
        eval_command,
        profile_commands,
    )
    system_prompt, tool_policy, eval_expect_json, eval_success_pass_rate = runtime_text_fields(
        cfg,
        test_command,
        eval_command,
        allowed_shell_commands,
    )
    return RuntimeInputs(
        test_command=test_command,
        eval_command=eval_command,
        command_profile=command_profile,
        shell_settings=shell_settings,
        allowed_shell_commands=allowed_shell_commands,
        system_prompt=system_prompt,
        tool_policy=tool_policy,
        eval_expect_json=eval_expect_json,
        eval_success_pass_rate=eval_success_pass_rate,
    )


def _command_inputs(
    cfg: dict,
    *,
    config_root: Path | None = None,
) -> tuple[
    str | None,
    str | None,
    str,
    tuple[str, ...],
    tuple[str, str | None],
]:
    test_command, eval_command = load_commands(cfg)
    command_profile, profile_commands = resolve_command_profile(
        cfg,
        config_root=config_root,
    )
    shell_settings = resolve_shell_policy(cfg)
    return (
        test_command,
        eval_command,
        command_profile,
        profile_commands,
        shell_settings,
    )


def runtime_text_fields(
    cfg: dict,
    test_command: str | None,
    eval_command: str | None,
    allowed_shell_commands: tuple[str, ...],
) -> tuple[str, str, bool, float]:
    system_prompt = str(cfg.get("system_prompt", "")).strip()
    if not system_prompt:
        system_prompt = "You are a coding agent."

    tool_policy = str(cfg.get("tool_policy", "")).strip()
    if not tool_policy:
        tool_policy = build_default_tool_policy(
            test_command=test_command,
            eval_command=eval_command,
            allowed_shell_commands=allowed_shell_commands,
        )

    eval_expect_json = as_bool(cfg.get("eval_expect_json", True), True)
    eval_success_pass_rate = float(cfg.get("eval_success_pass_rate", 100.0))
    return (
        system_prompt,
        tool_policy,
        eval_expect_json,
        eval_success_pass_rate,
    )


def service_config(
    cfg: dict,
    *,
    service_mode: str,
    config_root: Path,
    config_path: Path,
    project_root_raw: str,
) -> tuple[ServiceConfig, Path]:
    service_values = load_service_settings(
        cfg,
        config_root=config_root,
        config_path=config_path,
        project_root_raw=project_root_raw,
    )
    return (
        ServiceConfig(
            mode=service_mode,
            host=service_values[0],
            port=service_values[1],
            workers=service_values[2],
            mount_work_root=service_values[3],
            mount_config_root=service_values[4],
            mount_artifacts_root=service_values[5],
            queue_backend=service_values[6],
            network_policy=service_values[7],
        ),
        service_values[8],
    )
