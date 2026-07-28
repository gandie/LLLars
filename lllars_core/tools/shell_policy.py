from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING

from pydantic_ai import ModelRetry, RunContext
from lllars_core.tools.descriptors import AgentDeps

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from lllars_core.config import HarnessConfig


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
    if deps.allowed_shell_commands:
        lines.append(
            "- For shell execution, call "
            "list_allowed_shell_commands, then "
            "run_allowlisted_shell(command_id=...)."
        )
    else:
        lines.append(
            "- No shell command tool is available in "
            "this configuration."
        )
    return "\n".join(lines)


def make_allowed_shell_runner(
    cfg: "HarnessConfig",
    canonicalize_shell_command_fn: Callable[[str], str],
    run_shell_fn: Callable[..., dict[str, object]],
) -> Callable[[str, int], str]:
    def _run_allowed_shell(command: str, timeout_sec: int) -> str:
        canonical = canonicalize_shell_command_fn(command)
        if canonical not in cfg.allowed_shell_commands:
            payload = {
                "returncode": 126,
                "stdout": "",
                "stderr": (
                    "[lllars] rejected shell command: not in allowlist. "
                    "Use list_allowed_shell_commands first."
                ),
            }
            return json.dumps(payload)
        return json.dumps(
            run_shell_fn(
                command=command,
                cwd=cfg.project_root,
                timeout_sec=timeout_sec,
                shell_mode=cfg.shell_mode,
                shell_override=cfg.shell_override,
            )
        )

    return _run_allowed_shell


def _register_allowlisted_shell_tools(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
) -> None:
    @agent.tool
    def list_allowed_shell_commands(ctx: RunContext[AgentDeps]) -> str:
        """Return numeric IDs for each allowed shell command."""
        _ = ctx
        return "\n".join(
            f"{idx}: {cmd}"
            for idx, cmd in enumerate(cfg.allowed_shell_commands, start=1)
        )


def _resolve_allowlisted_command(
    cfg: "HarnessConfig",
    command_id: int,
) -> str:
    if command_id < 1 or command_id > len(cfg.allowed_shell_commands):
        raise ModelRetry(
            "Invalid command_id. Call "
            "list_allowed_shell_commands and use "
            "a listed ID."
        )
    return cfg.allowed_shell_commands[command_id - 1]


def _register_run_allowlisted_shell_tool(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    @agent.tool
    def run_allowlisted_shell(
        ctx: RunContext[AgentDeps],
        command_id: int,
        timeout_sec: int = 90,
    ) -> str:
        """Run one allowed shell command by numeric ID.

        Always call list_allowed_shell_commands first and
        pass one of those IDs.
        """
        _ = ctx
        emit_thought("tool: run_allowlisted_shell")
        try:
            command = _resolve_allowlisted_command(cfg, command_id)
            return run_allowed_shell(command, timeout_sec)
        except ModelRetry:
            # Preserve pydantic_ai-native retry signaling.
            raise
        except Exception as exc:
            return tool_error(
                "run_allowlisted_shell",
                str(exc),
                "Use a valid command_id from list_allowed_shell_commands.",
            )


def _register_test_tool(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    @agent.tool
    def run_test_command(ctx: RunContext[AgentDeps]) -> str:
        """Run the configured test command."""
        _ = ctx
        emit_thought("tool: run_test_command")
        try:
            return run_allowed_shell(cfg.test_command, 90)
        except ModelRetry:
            raise
        except Exception as exc:
            return tool_error("run_test_command", str(exc), None)


def _register_eval_tool(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    @agent.tool
    def run_eval_command(ctx: RunContext[AgentDeps]) -> str:
        """Run the configured evaluation command."""
        _ = ctx
        emit_thought("tool: run_eval_command")
        try:
            return run_allowed_shell(cfg.eval_command, 90)
        except ModelRetry:
            raise
        except Exception as exc:
            return tool_error("run_eval_command", str(exc), None)


def register_shell_tools(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    if cfg.allowed_shell_commands:
        _register_allowlisted_shell_tools(agent, cfg)
        _register_run_allowlisted_shell_tool(
            agent, cfg, emit_thought, tool_error, run_allowed_shell
        )
    if cfg.test_command is not None:
        _register_test_tool(
            agent, cfg, emit_thought, tool_error, run_allowed_shell
        )
    if cfg.eval_command is not None:
        _register_eval_tool(
            agent, cfg, emit_thought, tool_error, run_allowed_shell
        )
