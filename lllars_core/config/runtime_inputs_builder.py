from __future__ import annotations

from dataclasses import dataclass

from lllars_core.config.runtime_text_fields import runtime_text_fields
from lllars_core.config.tools_section import collect_allowed_shell_commands
from lllars_core.config.tools_section import resolve_enabled_tool_groups
from lllars_core.config.tools_section import resolve_plugin_tool_paths
from lllars_core.config.tools_section import resolve_web_research_settings


@dataclass(frozen=True)
class RuntimeInputs:
    test_command: str | None
    eval_command: str | None
    command_profile: str
    command_profiles: tuple[tuple[str, tuple[str, ...]], ...]
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


def build_runtime_inputs(
    cfg: dict,
    test_command: str | None,
    eval_command: str | None,
    command_profile: str,
    command_profiles: tuple[tuple[str, tuple[str, ...]], ...],
    profile_commands: tuple[str, ...],
    shell_settings: tuple[str, str | None],
) -> RuntimeInputs:
    tooling = _tooling_values(
        cfg,
        test_command,
        eval_command,
        profile_commands,
    )
    text = _text_values(
        cfg,
        test_command,
        eval_command,
        tooling[0],
    )
    return RuntimeInputs(
        **_runtime_inputs_kwargs(
            test_command,
            eval_command,
            command_profile,
            command_profiles,
            shell_settings,
            tooling,
            text,
        )
    )


def _tooling_values(
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
    web_research = resolve_web_research_settings(cfg)
    return (
        allowed_shell_commands,
        enabled_tool_groups,
        plugin_tool_paths,
        web_research,
    )


def _text_values(
    cfg: dict,
    test_command: str | None,
    eval_command: str | None,
    allowed_shell_commands: tuple[str, ...],
) -> tuple[str, str, bool, float]:
    return runtime_text_fields(
        cfg,
        test_command,
        eval_command,
        allowed_shell_commands,
    )


def _runtime_inputs_kwargs(
    test_command: str | None,
    eval_command: str | None,
    command_profile: str,
    command_profiles: tuple[tuple[str, tuple[str, ...]], ...],
    shell_settings: tuple[str, str | None],
    tooling: tuple[
        tuple[str, ...],
        tuple[str, ...],
        tuple[str, ...],
        tuple[str, tuple[str, ...], tuple[str, ...], bool],
    ],
    text: tuple[str, str, bool, float],
) -> dict[str, object]:
    return {
        "test_command": test_command,
        "eval_command": eval_command,
        "command_profile": command_profile,
        "command_profiles": command_profiles,
        "shell_settings": shell_settings,
        "allowed_shell_commands": tooling[0],
        "enabled_tool_groups": tooling[1],
        "plugin_tool_paths": tooling[2],
        "web_research_domain_policy": tooling[3][0],
        "web_research_allowed_domains": tooling[3][1],
        "web_research_blocked_domains": tooling[3][2],
        "web_research_local_fallback": tooling[3][3],
        "system_prompt": text[0],
        "tool_policy": text[1],
        "eval_expect_json": text[2],
        "eval_success_pass_rate": text[3],
    }
