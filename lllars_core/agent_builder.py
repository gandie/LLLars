from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import platform

from pydantic_ai import (
    Agent,
    InstrumentationSettings,
    ModelRetry,
    ModelSettings,
    RunContext,
)
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from pydantic_ai_todo import TodoCapability

from lllars_core.config import HarnessConfig, canonicalize_shell_command
from lllars_core.shell import run_powershell
from lllars_core.skills import load_markdown_skill_capabilities


@dataclass(frozen=True)
class AgentDeps:
    project_root: str
    os_name: str
    shell_name: str
    allowed_shell_commands: tuple[str, ...]
    has_test_command: bool
    has_eval_command: bool


def make_agent_deps(cfg: HarnessConfig) -> AgentDeps:
    return AgentDeps(
        project_root=str(cfg.project_root),
        os_name=platform.system() or "unknown",
        shell_name="PowerShell",
        allowed_shell_commands=cfg.allowed_shell_commands,
        has_test_command=cfg.test_command is not None,
        has_eval_command=cfg.eval_command is not None,
    )


def resolve_under(root: Path, user_path: str) -> Path:
    candidate = Path(user_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError("Path is outside configured project-root")
    return candidate


def normalize_ollama_base_url(provider_url: str) -> str:
    base_url = provider_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("Config is missing non-empty provider-url")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def parse_ollama_model(model_value: str) -> str:
    value = model_value.strip()
    if not value:
        raise ValueError("Config field model is empty")
    if value.startswith("ollama:"):
        return value.split(":", 1)[1]
    return value


def _build_agent_instance(cfg: HarnessConfig) -> Agent[AgentDeps, str]:
    model_obj = OllamaModel(
        parse_ollama_model(cfg.model),
        provider=OllamaProvider(
            base_url=normalize_ollama_base_url(cfg.provider_url)
        ),
    )

    capabilities = [TodoCapability(enable_subtasks=True)]
    capabilities.extend(load_markdown_skill_capabilities(cfg))

    agent = Agent[AgentDeps, str](
        model_obj,
        deps_type=AgentDeps,
        instructions=cfg.system_prompt,
        model_settings=ModelSettings(),
        retries={
            "tools": cfg.agent_retries_tools,
            "output": cfg.agent_retries_output,
        },
        tool_timeout=cfg.tool_timeout_sec,
        max_concurrency=cfg.max_concurrency,
        metadata={
            "harness": "lllars",
            "provider": "ollama",
            "project_root": str(cfg.project_root),
        },
        capabilities=capabilities,
    )

    if cfg.instrumentation_enabled:
        agent.instrument = InstrumentationSettings(
            include_content=cfg.instrumentation_include_content,
        )

    return agent


def _runtime_tooling_instructions(
    cfg: HarnessConfig,
    deps: AgentDeps,
) -> str:
    lines = [
        cfg.tool_policy,
        "",
        "Execution environment:",
        f"- OS: {deps.os_name}",
        f"- Shell: {deps.shell_name}",
        f"- Project root: {deps.project_root}",
        "",
        "Operational rules:",
        "- Use only registered tools.",
        "- Do not create or execute bash/sh scripts.",
        "- Use PowerShell-compatible commands only.",
    ]
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


def _make_allowed_shell_runner(
    cfg: HarnessConfig,
) -> Callable[[str, int], str]:
    def _run_allowed_shell(command: str, timeout_sec: int) -> str:
        canonical = canonicalize_shell_command(command)
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
            run_powershell(
                command=command,
                cwd=cfg.project_root,
                timeout_sec=timeout_sec,
            )
        )

    return _run_allowed_shell


def _register_file_tools(
    agent: Agent[AgentDeps, str],
    cfg: HarnessConfig,
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    @agent.tool
    def list_files(
        ctx: RunContext[AgentDeps],
        path: str = ".",
        recursive: bool = True,
    ) -> str:
        """List files and folders under project root."""
        _ = ctx
        try:
            target = resolve_under(cfg.project_root, path)
            if not target.exists():
                return tool_error(
                    "list_files",
                    f"Path not found: {path}",
                    "Choose an existing path under project_root.",
                )
            if target.is_file():
                return str(target.relative_to(cfg.project_root)).replace(
                    "\\", "/"
                )
            iterator = target.rglob("*") if recursive else target.iterdir()
            return "\n".join(
                sorted(
                    str(item.relative_to(cfg.project_root)).replace("\\", "/")
                    for item in iterator
                )
            )
        except Exception as exc:
            return tool_error(
                "list_files",
                str(exc),
                "Only access files inside project_root.",
            )

    @agent.tool
    def read_file(ctx: RunContext[AgentDeps], path: str) -> str:
        """Read a UTF-8 text file under project root."""
        _ = ctx
        try:
            target = resolve_under(cfg.project_root, path)
            if not target.exists() or not target.is_file():
                return tool_error(
                    "read_file",
                    f"File not found: {path}",
                    "Pass a valid file path under project_root.",
                )
            return target.read_text(encoding="utf-8")
        except Exception as exc:
            return tool_error(
                "read_file",
                str(exc),
                "Only access files inside project_root.",
            )

    @agent.tool
    def write_file(
        ctx: RunContext[AgentDeps],
        path: str,
        content: str,
    ) -> str:
        """Write UTF-8 text content to a file under project root."""
        _ = ctx
        try:
            target = resolve_under(cfg.project_root, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            rel = str(target.relative_to(cfg.project_root)).replace("\\", "/")
            return f"Wrote {rel}"
        except Exception as exc:
            return tool_error(
                "write_file",
                str(exc),
                "Use a writable path inside project_root.",
            )


def _register_shell_tools(
    agent: Agent[AgentDeps, str],
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    if cfg.allowed_shell_commands:

        @agent.tool
        def list_allowed_shell_commands(ctx: RunContext[AgentDeps]) -> str:
            """Return numeric IDs for each allowed PowerShell command."""
            _ = ctx
            return "\n".join(
                f"{idx}: {cmd}"
                for idx, cmd in enumerate(cfg.allowed_shell_commands, start=1)
            )

        @agent.tool
        def run_allowlisted_shell(
            ctx: RunContext[AgentDeps],
            command_id: int,
            timeout_sec: int = 90,
        ) -> str:
            """Run one allowed PowerShell command by numeric ID.

            Always call list_allowed_shell_commands first and
            pass one of those IDs.
            """
            _ = ctx
            emit_thought("tool: run_allowlisted_shell")
            try:
                if (
                    command_id < 1
                    or command_id > len(cfg.allowed_shell_commands)
                ):
                    raise ModelRetry(
                        "Invalid command_id. Call "
                        "list_allowed_shell_commands and use "
                        "a listed ID."
                    )
                command = cfg.allowed_shell_commands[command_id - 1]
                return run_allowed_shell(command, timeout_sec)
            except Exception as exc:
                return tool_error(
                    "run_allowlisted_shell",
                    str(exc),
                    "Use a valid command_id from list_allowed_shell_commands.",
                )

    if cfg.test_command is not None:

        @agent.tool
        def run_test_command(ctx: RunContext[AgentDeps]) -> str:
            """Run the configured test command."""
            _ = ctx
            emit_thought("tool: run_test_command")
            try:
                return run_allowed_shell(cfg.test_command, 90)
            except Exception as exc:
                return tool_error("run_test_command", str(exc), None)

    if cfg.eval_command is not None:

        @agent.tool
        def run_eval_command(ctx: RunContext[AgentDeps]) -> str:
            """Run the configured evaluation command."""
            _ = ctx
            emit_thought("tool: run_eval_command")
            try:
                return run_allowed_shell(cfg.eval_command, 90)
            except Exception as exc:
                return tool_error("run_eval_command", str(exc), None)


def build_agent(
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
) -> Agent[AgentDeps, str]:
    def _tool_error(
        tool_name: str,
        message: str,
        hint: str | None = None,
    ) -> str:
        clean = " ".join(message.strip().split())
        payload = f"[tool-error:{tool_name}] {clean}"
        if hint:
            payload = f"{payload} Hint: {hint}"
        emit_thought(payload)
        return payload

    agent = _build_agent_instance(cfg)

    @agent.instructions
    def runtime_tooling_instructions(ctx: RunContext[AgentDeps]) -> str:
        return _runtime_tooling_instructions(cfg, ctx.deps)

    run_allowed_shell = _make_allowed_shell_runner(cfg)
    _register_file_tools(agent, cfg, _tool_error)
    _register_shell_tools(
        agent,
        cfg,
        emit_thought,
        _tool_error,
        run_allowed_shell,
    )

    return agent
