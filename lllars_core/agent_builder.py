from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import platform

from pydantic_ai import (
    Agent,
    InstrumentationSettings,
    ModelSettings,
    RunContext,
)
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from pydantic_ai_todo import TodoCapability

from lllars_core.config import HarnessConfig, canonicalize_shell_command
from lllars_core.mcp import load_toolsets_from_mcp_config
from lllars_core.shell import detect_shell, run_shell
from lllars_core.skills import load_markdown_skill_capabilities
from lllars_core.tools import (
    AgentDeps,
    make_allowed_shell_runner as make_allowed_shell_runner_policy,
    register_file_tools as register_file_tools_policy,
    register_runtime_tools,
    register_shell_tools as register_shell_tools_policy,
    resolve_under as resolve_under_policy,
    runtime_tooling_instructions as runtime_tooling_instructions_policy,
)


def make_agent_deps(cfg: HarnessConfig) -> AgentDeps:
    selection = detect_shell(
        shell_mode=cfg.shell_mode,
        shell_override=cfg.shell_override,
    )
    return AgentDeps(
        project_root=str(cfg.project_root),
        os_name=platform.system() or "unknown",
        shell_name=(selection.name if selection is not None else "unknown"),
        command_profile=cfg.command_profile,
        allowed_shell_commands=cfg.allowed_shell_commands,
        has_test_command=cfg.test_command is not None,
        has_eval_command=cfg.eval_command is not None,
    )


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


def resolve_under(root: Path, user_path: str) -> Path:
    return resolve_under_policy(root, user_path)


def _build_capabilities(cfg: HarnessConfig) -> list[object]:
    capabilities = [TodoCapability(enable_subtasks=True)]
    capabilities.extend(load_markdown_skill_capabilities(cfg))
    return capabilities


def _load_mcp_toolsets(cfg: HarnessConfig) -> list[object]:
    if not cfg.mcp_enabled or cfg.mcp_config_path is None:
        return []
    return load_toolsets_from_mcp_config(
        mcp_config_path=cfg.mcp_config_path,
        init_timeout_sec=cfg.mcp_init_timeout_sec,
    )


def _build_agent_instance(cfg: HarnessConfig) -> Agent[AgentDeps, str]:
    model_obj = OllamaModel(
        parse_ollama_model(cfg.model),
        provider=OllamaProvider(
            base_url=normalize_ollama_base_url(cfg.provider_url)
        ),
    )

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
        capabilities=_build_capabilities(cfg),
        toolsets=_load_mcp_toolsets(cfg),
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
    return runtime_tooling_instructions_policy(cfg, deps)


def _make_allowed_shell_runner(
    cfg: HarnessConfig,
) -> Callable[[str, int], str]:
    return make_allowed_shell_runner_policy(
        cfg,
        canonicalize_shell_command,
        lambda **kwargs: run_shell(**kwargs),
    )


def _register_file_tools(
    agent: Agent[AgentDeps, str],
    cfg: HarnessConfig,
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    register_file_tools_policy(agent, cfg, tool_error)


def _register_shell_tools(
    agent: Agent[AgentDeps, str],
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    register_shell_tools_policy(
        agent=agent,
        cfg=cfg,
        emit_thought=emit_thought,
        tool_error=tool_error,
        run_allowed_shell=run_allowed_shell,
    )


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
    register_runtime_tools(
        agent=agent,
        cfg=cfg,
        emit_thought=emit_thought,
        tool_error=_tool_error,
        run_allowed_shell=run_allowed_shell,
    )

    return agent
