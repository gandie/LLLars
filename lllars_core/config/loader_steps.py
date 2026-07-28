from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lllars_core.config.runtime_text_fields import runtime_text_fields
from lllars_core.config.runtime_section import load_commands
from lllars_core.config.runtime_section import resolve_shell_policy
from lllars_core.config.tools_section import collect_allowed_shell_commands
from lllars_core.config.tools_section import resolve_enabled_tool_groups
from lllars_core.config.tools_section import resolve_plugin_tool_paths
from lllars_core.config.tools_section import resolve_command_profile
from lllars_core.config.tools_section import resolve_web_research_settings


@dataclass(frozen=True)
class RuntimeInputs:
    test_command: str | None
    eval_command: str | None
    command_profile: str
    shell_settings: tuple[str, str | None]
    allowed_shell_commands: tuple[str, ...]
    enabled_tool_groups: tuple[str, ...]
    plugin_tool_paths: tuple[str, ...]
    web_research_domain_policy: str
    web_research_allowed_domains: tuple[str, ...]
    web_research_blocked_domains: tuple[str, ...]
    web_research_local_fallback: bool
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
    return _runtime_inputs_from_cfg(cfg, config_root=config_root)


def _runtime_inputs_from_cfg(
    cfg: dict,
    *,
    config_root: Path | None,
) -> RuntimeInputs:
    (
        test_command,
        eval_command,
        command_profile,
        profile_commands,
        shell_settings,
    ) = _command_inputs(
        cfg,
        config_root=config_root,
    )
    return _runtime_inputs_from_command_values(
        cfg,
        test_command,
        eval_command,
        command_profile,
        profile_commands,
        shell_settings,
    )


def _runtime_inputs_from_command_values(
    cfg: dict,
    test_command: str | None,
    eval_command: str | None,
    command_profile: str,
    profile_commands: tuple[str, ...],
    shell_settings: tuple[str, str | None],
) -> RuntimeInputs:
    tooling_fields = _tooling_inputs(
        cfg,
        test_command,
        eval_command,
        profile_commands,
    )
    allowed_shell_commands = tooling_fields[0]
    text_fields = runtime_text_fields(
        cfg,
        test_command,
        eval_command,
        allowed_shell_commands,
    )
    return _build_runtime_inputs(
        test_command=test_command,
        eval_command=eval_command,
        command_profile=command_profile,
        shell_settings=shell_settings,
        tooling_fields=tooling_fields,
        text_fields=text_fields,
    )


def _build_runtime_inputs(
    *,
    test_command: str | None,
    eval_command: str | None,
    command_profile: str,
    shell_settings: tuple[str, str | None],
    tooling_fields: tuple[
        tuple[str, ...],
        tuple[str, ...],
        tuple[str, ...],
        tuple[str, tuple[str, ...], tuple[str, ...], bool],
    ],
    text_fields: tuple[str, str, bool, float],
) -> RuntimeInputs:
    allowed_shell_commands, enabled_tool_groups, plugin_tool_paths, web = (
        tooling_fields
    )
    return RuntimeInputs(
        test_command=test_command,
        eval_command=eval_command,
        command_profile=command_profile,
        shell_settings=shell_settings,
        allowed_shell_commands=allowed_shell_commands,
        enabled_tool_groups=enabled_tool_groups,
        plugin_tool_paths=plugin_tool_paths,
        web_research_domain_policy=web[0],
        web_research_allowed_domains=web[1],
        web_research_blocked_domains=web[2],
        web_research_local_fallback=web[3],
        system_prompt=text_fields[0],
        tool_policy=text_fields[1],
        eval_expect_json=text_fields[2],
        eval_success_pass_rate=text_fields[3],
    )


def _tooling_inputs(
    cfg: dict,
    test_command: str | None,
    eval_command: str | None,
    profile_commands: tuple[str, ...],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, tuple[str, ...], tuple[str, ...], bool],
]:
    allowed_shell_commands = collect_allowed_shell_commands(
        test_command,
        eval_command,
        profile_commands,
    )
    enabled_tool_groups = resolve_enabled_tool_groups(cfg)
    plugin_tool_paths = resolve_plugin_tool_paths(cfg)
    web_research_settings = resolve_web_research_settings(cfg)
    return (
        allowed_shell_commands,
        enabled_tool_groups,
        plugin_tool_paths,
        web_research_settings,
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







