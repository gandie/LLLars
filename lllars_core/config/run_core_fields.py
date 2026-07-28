from __future__ import annotations

from pathlib import Path

WebResearchSettings = tuple[str, tuple[str, ...], tuple[str, ...], bool]


def _command_map(
    test_command: str | None,
    eval_command: str | None,
) -> dict[str, str]:
    commands: dict[str, str] = {}
    if test_command is not None:
        commands["test"] = test_command
    if eval_command is not None:
        commands["eval"] = eval_command
    return commands


def _web_research_kwargs(
    settings: WebResearchSettings,
) -> dict[str, object]:
    return {
        "web_research_domain_policy": settings[0],
        "web_research_allowed_domains": settings[1],
        "web_research_blocked_domains": settings[2],
        "web_research_local_fallback": settings[3],
    }


def run_core_from_inputs(
    *,
    model: str,
    provider_url: str,
    project_root: Path,
    test_command: str | None,
    eval_command: str | None,
    command_profile: str,
    enabled_tool_groups: tuple[str, ...],
    plugin_tool_paths: tuple[str, ...],
    web_research_settings: WebResearchSettings,
    eval_expect_json: bool,
    eval_success_pass_rate: float,
    system_prompt: str,
    tool_policy: str,
) -> dict[str, object]:
    return {
        "model": model,
        "provider_url": provider_url,
        "project_root": project_root,
        "commands": _command_map(test_command, eval_command),
        "test_command": test_command,
        "eval_command": eval_command,
        "command_profile": command_profile,
        "enabled_tool_groups": enabled_tool_groups,
        "plugin_tool_paths": plugin_tool_paths,
        **_web_research_kwargs(web_research_settings),
        "eval_expect_json": eval_expect_json,
        "eval_success_pass_rate": eval_success_pass_rate,
        "system_prompt": system_prompt,
        "tool_policy": tool_policy,
    }
