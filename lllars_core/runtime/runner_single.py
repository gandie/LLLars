from __future__ import annotations

import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic_ai import UsageLimits

from lllars_core.agent_builder import build_agent, make_agent_deps
from lllars_core.asyncio_compat import configure_windows_event_loop_policy
from lllars_core.config import HarnessConfig
from lllars_core.console import (
    append_trace,
    emit_live_thought,
    extract_thought_trace,
)
from lllars_core.runtime.runner_stream import build_event_stream_handler
from lllars_core.skills import configured_markdown_skill_ids


def _usage_limits(cfg: HarnessConfig) -> UsageLimits:
    return UsageLimits(
        request_limit=cfg.usage_request_limit,
        tool_calls_limit=cfg.usage_tool_calls_limit,
        input_tokens_limit=cfg.usage_input_tokens_limit,
        output_tokens_limit=cfg.usage_output_tokens_limit,
        total_tokens_limit=cfg.usage_total_tokens_limit,
        count_tokens_before_request=cfg.usage_count_tokens_before_request,
    )


def _build_runtime_telemetry(
    cfg: HarnessConfig,
    result,
    live_trace: list[str],
    telemetry_timeline: list[dict[str, Any]],
    configured_skill_ids: list[str],
    used_skill_ids: list[str],
) -> dict[str, Any]:
    usage = result.usage
    return {
        "run_id": result.run_id,
        "conversation_id": result.conversation_id,
        "metadata": result.metadata or {},
        "requests": usage.requests,
        "tool_calls": usage.tool_calls,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "details": dict(usage.details),
        "live_trace_events": len(live_trace),
        "skills_enabled": cfg.skills_enabled,
        "skills_defer_loading": cfg.skills_defer_loading,
        "skills_loaded_ids": list(configured_skill_ids),
        "skills_loaded_count": len(configured_skill_ids),
        "skills_used_ids": list(used_skill_ids),
        "skills_used_count": len(used_skill_ids),
        "timeline": telemetry_timeline,
    }


def _collect_thought_trace(result, live_trace: list[str]) -> list[str]:
    if not live_trace:
        return extract_thought_trace(result)
    thought_trace = list(live_trace)
    for item in extract_thought_trace(result):
        append_trace(thought_trace, item)
    return thought_trace


def _skills_loaded_message(configured_skill_ids: list[str]) -> str:
    if configured_skill_ids:
        return "skills-loaded: " + ", ".join(configured_skill_ids)
    return "skills-loaded: none"


def _run_agent_sync(
    agent,
    cfg: HarnessConfig,
    prompt_text: str,
    deps,
    handler,
):
    return agent.run_sync(
        prompt_text,
        deps=deps,
        usage_limits=_usage_limits(cfg),
        metadata={"entrypoint": "run_sync", "prompt_chars": len(prompt_text)},
        event_stream_handler=handler,
    )


def _build_emit(
    thought_log_path: Path | None,
    emit_thought: Callable[[str], None] | None,
):
    def _emit(message: str) -> None:
        emit_live_thought(message, thought_log_path)
        if emit_thought is not None:
            emit_thought(message)

    return _emit


def _agent_state(
    cfg: HarnessConfig,
    thought_log_path: Path | None,
    emit_thought: Callable[[str], None] | None,
) -> dict[str, Any]:
    live_trace: list[str] = []
    telemetry_timeline: list[dict[str, Any]] = []
    configured_skill_ids = configured_markdown_skill_ids(cfg)
    used_skill_ids: list[str] = (
        list(configured_skill_ids)
        if configured_skill_ids and not cfg.skills_defer_loading
        else []
    )
    emit = _build_emit(thought_log_path, emit_thought)
    handler = build_event_stream_handler(
        event_start=time.time(),
        emit=emit,
        live_trace=live_trace,
        telemetry_timeline=telemetry_timeline,
        used_skill_ids=used_skill_ids,
        used_skill_id_set=set(used_skill_ids),
    )
    return {
        "emit": emit,
        "handler": handler,
        "live_trace": live_trace,
        "telemetry_timeline": telemetry_timeline,
        "configured_skill_ids": configured_skill_ids,
        "used_skill_ids": used_skill_ids,
        "runtime_telemetry": {"timeline": []},
    }


def _run_single_agent_success(
    cfg: HarnessConfig,
    prompt_text: str,
    state: dict[str, Any],
) -> dict[str, Any]:
    emit = state["emit"]
    agent = build_agent(cfg, emit_thought=emit)
    deps = make_agent_deps(cfg)
    emit(_skills_loaded_message(state["configured_skill_ids"]))
    emit("agent: started")
    result = _run_agent_sync(agent, cfg, prompt_text, deps, state["handler"])
    emit("agent: completed")
    thought_trace = _collect_thought_trace(result, state["live_trace"])
    state["runtime_telemetry"] = _build_runtime_telemetry(
        cfg,
        result,
        state["live_trace"],
        state["telemetry_timeline"],
        state["configured_skill_ids"],
        state["used_skill_ids"],
    )
    return {
        "returncode": 0,
        "stdout": str(result.output),
        "stderr": "",
        "thought_trace": thought_trace,
        "runtime_telemetry": state["runtime_telemetry"],
    }


def _run_single_agent_failure(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "returncode": 125,
        "stdout": "",
        "stderr": traceback.format_exc(),
        "thought_trace": list(state["live_trace"]),
        "runtime_telemetry": state["runtime_telemetry"],
    }


def run_single_agent(
    cfg: HarnessConfig,
    prompt_text: str,
    thought_log_path: Path | None = None,
    emit_thought: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    configure_windows_event_loop_policy()
    state = _agent_state(cfg, thought_log_path, emit_thought)
    try:
        return _run_single_agent_success(cfg, prompt_text, state)
    except Exception:
        return _run_single_agent_failure(state)


__all__ = ["run_single_agent"]
