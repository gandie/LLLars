from __future__ import annotations

from collections.abc import Callable
import inspect
from pathlib import Path
import platform

from pydantic_ai import (
    Agent,
    InstrumentationSettings,
    ModelSettings,
    RunContext,
)
from pydantic_ai.models import infer_model, infer_provider_class

from pydantic_ai_todo import TodoCapability

from lllars_core.config import HarnessConfig, canonicalize_shell_command
from lllars_core.mcp.runtime_capability import load_runtime_mcp_toolsets
from lllars_core.shell import detect_shell, run_shell
from lllars_core.skills import load_markdown_skill_capabilities
from lllars_core.tools import (
    AgentDeps,
    make_allowed_shell_runner as make_allowed_shell_runner_policy,
    register_runtime_tools,
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


def _resolve_model_spec(model_value: str) -> str:
    value = model_value.strip()
    if not value:
        raise ValueError("Config field model is empty")

    provider_name, sep, provider_model = value.partition(":")
    if sep and provider_model.strip():
        try:
            infer_provider_class(provider_name.strip().lower())
            return value
        except Exception:
            pass

    # Backward compatibility for unprefixed/local model names.
    return f"ollama:{value}"


def _provider_supports_base_url(provider_cls: type[object]) -> bool:
    return "base_url" in inspect.signature(provider_cls).parameters


def _normalize_provider_base_url(
    provider_name: str,
    provider_url: str,
) -> str:
    base_url = provider_url.strip().rstrip("/")
    if provider_name == "ollama" and base_url and not base_url.endswith("/v1"):
        return f"{base_url}/v1"
    return base_url


def _infer_runtime_model(cfg: HarnessConfig) -> tuple[object, str]:
    model_spec = _resolve_model_spec(cfg.model)
    provider_url = cfg.provider_url.strip().rstrip("/")

    def _provider_factory(provider_name: str):
        provider_cls = infer_provider_class(provider_name)
        base_url = _normalize_provider_base_url(provider_name, provider_url)
        if base_url and _provider_supports_base_url(provider_cls):
            return provider_cls(base_url=base_url)
        return provider_cls()

    model_obj = infer_model(model_spec, provider_factory=_provider_factory)
    provider_name = model_spec.split(":", 1)[0]
    return model_obj, provider_name


def resolve_under(root: Path, user_path: str) -> Path:
    return resolve_under_policy(root, user_path)


def _build_capabilities(cfg: HarnessConfig) -> list[object]:
    capabilities = [TodoCapability(enable_subtasks=True)]
    capabilities.extend(load_markdown_skill_capabilities(cfg))
    return capabilities


def _load_mcp_toolsets(
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
) -> list[object]:
    return load_runtime_mcp_toolsets(cfg, emit_thought)


def _build_agent_instance(
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
) -> Agent[AgentDeps, str]:
    model_obj, provider_name = _infer_runtime_model(cfg)

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
            "provider": provider_name,
            "project_root": str(cfg.project_root),
        },
        capabilities=_build_capabilities(cfg),
        toolsets=_load_mcp_toolsets(cfg, emit_thought),
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

    agent = _build_agent_instance(cfg, emit_thought)

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
