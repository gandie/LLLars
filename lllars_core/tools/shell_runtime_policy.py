from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING

from lllars_core.tools.descriptors import AgentDeps

if TYPE_CHECKING:
    from lllars_core.config import HarnessConfig


def _web_research_instruction(cfg: "HarnessConfig") -> str | None:
    if "native_web_research" not in set(cfg.enabled_tool_groups):
        return None
    if cfg.network_policy == "offline":
        return (
            "- Web research is configured but disabled because "
            "network_policy=offline."
        )
    return (
        "- Web research is available with domain_policy="
        f"{cfg.web_research_domain_policy}."
    )


def _shell_execution_rules(
    cfg: "HarnessConfig",
    deps: "AgentDeps",
) -> list[str]:
    enabled_groups = set(cfg.enabled_tool_groups)
    has_allowlisted_shell = "native_shell" in enabled_groups
    has_yolo_shell = "native_shell_yolo" in enabled_groups
    if has_yolo_shell:
        lines = [
            "- For shell execution, call "
            "run_unrestricted_shell(command=...)."
        ]
        if has_allowlisted_shell and deps.allowed_shell_commands:
            lines.append(
                "- Allowlisted shell commands are also available via "
                "list_allowed_shell_commands and "
                "run_allowlisted_shell(...)."
            )
        return lines
    if has_allowlisted_shell and deps.allowed_shell_commands:
        return [
            "- For shell execution, call "
            "list_allowed_shell_commands, then "
            "run_allowlisted_shell(...)."
        ]
    return ["- No shell command tool is available in this configuration."]


def runtime_tooling_instructions(
    cfg: "HarnessConfig",
    deps: "AgentDeps",
) -> str:
    lines = [
        cfg.tool_policy,
        "",
        "Execution environment:",
        f"- OS: {deps.os_name}",
        f"- Shell: {deps.shell_name}",
        f"- Project root: {deps.project_root}",
        f"- Command profile: {deps.command_profile}",
        "",
        "Operational rules:",
        "- Use only registered tools.",
    ]
    if deps.os_name.lower() == "windows":
        lines.append("- Use PowerShell-compatible commands only.")
    else:
        lines.append("- Use POSIX shell-compatible commands only.")
    lines.extend(_shell_execution_rules(cfg, deps))
    web_research_line = _web_research_instruction(cfg)
    if web_research_line is not None:
        lines.append(web_research_line)
    return "\n".join(lines)


def _match_allowlist_pattern(
    patterns: tuple[str, ...],
    canonical_command: str,
) -> str | None:
    for pattern in patterns:
        wildcard_idx = pattern.find("*")
        if wildcard_idx < 0 and canonical_command == pattern:
            return pattern
        if wildcard_idx >= 0 and canonical_command.startswith(
            pattern[:wildcard_idx]
        ):
            return pattern
    return None


def _rejected_allowlist_payload() -> dict[str, object]:
    return {
        "returncode": 126,
        "stdout": "",
        "stderr": (
            "[lllars] rejected shell command: not in allowlist. "
            "Use list_allowed_shell_commands first."
        ),
    }


def make_allowed_shell_runner(
    cfg: "HarnessConfig",
    canonicalize_shell_command_fn: Callable[[str], str],
    run_shell_fn: Callable[..., dict[str, object]],
) -> Callable[[str, int], str]:
    def _run_allowed_shell(command: str, timeout_sec: int) -> str:
        canonical = canonicalize_shell_command_fn(command)
        matched = _match_allowlist_pattern(
            cfg.allowed_shell_commands,
            canonical,
        )
        if matched is None:
            return json.dumps(_rejected_allowlist_payload())
        payload = run_shell_fn(
            command=command,
            cwd=cfg.project_root,
            timeout_sec=timeout_sec,
            shell_mode=cfg.shell_mode,
            shell_override=cfg.shell_override,
        )
        payload["allowlist_match"] = matched
        payload["canonical_command"] = canonical
        return json.dumps(payload)

    return _run_allowed_shell


def make_unrestricted_shell_runner(
    cfg: "HarnessConfig",
    run_shell_fn: Callable[..., dict[str, object]],
) -> Callable[[str, int], str]:
    def _run_unrestricted_shell(command: str, timeout_sec: int) -> str:
        payload = run_shell_fn(
            command=command,
            cwd=cfg.project_root,
            timeout_sec=timeout_sec,
            shell_mode=cfg.shell_mode,
            shell_override=cfg.shell_override,
        )
        return json.dumps(payload)

    return _run_unrestricted_shell
