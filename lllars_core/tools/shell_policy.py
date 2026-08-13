from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from pydantic_ai import ModelRetry, RunContext
from lllars_core.tools.descriptors import AgentDeps
from lllars_core.tools.shell_runtime_policy import (
    make_allowed_shell_runner as _make_allowed_shell_runner,
    make_unrestricted_shell_runner as _make_unrestricted_shell_runner,
    runtime_tooling_instructions as _runtime_tooling_instructions,
)

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from lllars_core.config import HarnessConfig


runtime_tooling_instructions = _runtime_tooling_instructions
make_allowed_shell_runner = _make_allowed_shell_runner
make_unrestricted_shell_runner = _make_unrestricted_shell_runner


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


def _resolve_allowlisted_input_command(
    cfg: "HarnessConfig",
    command: str | None,
    command_id: int | None,
) -> str:
    if command is not None:
        text = str(command).strip()
        if not text:
            raise ModelRetry("command must be non-empty when provided.")
        return text
    if command_id is None:
        raise ModelRetry(
            "Provide either command or command_id. "
            "Call list_allowed_shell_commands first."
        )
    return _resolve_allowlisted_command(cfg, command_id)


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
        command: str | None = None,
        command_id: int | None = None,
        timeout_sec: int = 90,
    ) -> str:
        """Run one allowlisted shell command by text or command_id."""
        _ = ctx
        emit_thought("tool: run_allowlisted_shell")
        try:
            resolved_command = _resolve_allowlisted_input_command(
                cfg,
                command,
                command_id,
            )
            return run_allowed_shell(resolved_command, timeout_sec)
        except ModelRetry:
            raise
        except Exception as exc:
            return tool_error(
                "run_allowlisted_shell",
                str(exc),
                "Use a valid command_id from list_allowed_shell_commands.",
            )


def _register_run_unrestricted_shell_tool(
    agent: "Agent[AgentDeps, str]",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_unrestricted_shell_fn: Callable[[str, int], str],
) -> None:
    @agent.tool
    def run_unrestricted_shell(
        ctx: RunContext[AgentDeps],
        command: str,
        timeout_sec: int = 90,
    ) -> str:
        """Run a shell command without allowlist checks.

        Use only when native_shell_yolo is explicitly enabled.
        """
        _ = ctx
        emit_thought("tool: run_unrestricted_shell")
        try:
            text = str(command).strip()
            if not text:
                raise ModelRetry("command must be non-empty")
            return run_unrestricted_shell_fn(text, timeout_sec)
        except ModelRetry:
            raise
        except Exception as exc:
            return tool_error(
                "run_unrestricted_shell",
                str(exc),
                "Provide a valid shell command string.",
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
    run_unrestricted_shell: Callable[[str, int], str] | None = None,
) -> None:
    if cfg.allowed_shell_commands:
        _register_allowlisted_shell_tools(agent, cfg)
        _register_run_allowlisted_shell_tool(
            agent, cfg, emit_thought, tool_error, run_allowed_shell
        )
    if run_unrestricted_shell is not None:
        _register_run_unrestricted_shell_tool(
            agent,
            emit_thought,
            tool_error,
            run_unrestricted_shell,
        )
    if cfg.test_command is not None:
        _register_test_tool(
            agent, cfg, emit_thought, tool_error, run_allowed_shell
        )
    if cfg.eval_command is not None:
        _register_eval_tool(
            agent, cfg, emit_thought, tool_error, run_allowed_shell
        )
