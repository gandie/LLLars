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
from lllars_core.runtime.runner_orchestrator import (
    run_agent_with_timeout as run_agent_with_timeout_orchestrated,
)
from lllars_core.runtime.runner_stream import build_event_stream_handler
from lllars_core.runtime.runner_worker import worker_run_single_agent
from lllars_core.skills import configured_markdown_skill_ids


def run_single_agent(
    cfg: HarnessConfig,
    prompt_text: str,
    thought_log_path: Path | None = None,
    emit_thought: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    configure_windows_event_loop_policy()

    runtime_telemetry: dict[str, Any] = {"timeline": []}
    live_trace: list[str] = []
    telemetry_timeline: list[dict[str, Any]] = []
    event_start = time.time()
    configured_skill_ids = configured_markdown_skill_ids(cfg)
    used_skill_ids: list[str] = []
    used_skill_id_set: set[str] = set()

    def _emit(message: str) -> None:
        emit_live_thought(message, thought_log_path)
        if emit_thought is not None:
            emit_thought(message)

    event_stream_handler = build_event_stream_handler(
        event_start=event_start,
        emit=_emit,
        live_trace=live_trace,
        telemetry_timeline=telemetry_timeline,
        used_skill_ids=used_skill_ids,
        used_skill_id_set=used_skill_id_set,
    )

    try:
        agent = build_agent(
            cfg,
            emit_thought=_emit,
        )
        deps = make_agent_deps(cfg)
        if configured_skill_ids:
            _emit(
                "skills-loaded: " + ", ".join(configured_skill_ids)
            )
        else:
            _emit("skills-loaded: none")
        _emit("agent: started")
        result = agent.run_sync(
            prompt_text,
            deps=deps,
            usage_limits=UsageLimits(
                request_limit=cfg.usage_request_limit,
                tool_calls_limit=cfg.usage_tool_calls_limit,
                input_tokens_limit=cfg.usage_input_tokens_limit,
                output_tokens_limit=cfg.usage_output_tokens_limit,
                total_tokens_limit=cfg.usage_total_tokens_limit,
                count_tokens_before_request=(
                    cfg.usage_count_tokens_before_request
                ),
            ),
            metadata={
                "entrypoint": "run_sync",
                "prompt_chars": len(prompt_text),
            },
            event_stream_handler=event_stream_handler,
        )
        _emit("agent: completed")

        thought_trace = list(live_trace)
        if not thought_trace:
            thought_trace = extract_thought_trace(result)
        else:
            for item in extract_thought_trace(result):
                append_trace(thought_trace, item)

        usage = result.usage
        runtime_telemetry = {
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

        return {
            "returncode": 0,
            "stdout": str(result.output),
            "stderr": "",
            "thought_trace": thought_trace,
            "runtime_telemetry": runtime_telemetry,
        }
    except Exception:
        return {
            "returncode": 125,
            "stdout": "",
            "stderr": traceback.format_exc(),
            "thought_trace": list(live_trace),
            "runtime_telemetry": runtime_telemetry,
        }


def _worker_run_single_agent(
    cfg: HarnessConfig,
    prompt_text: str,
    event_queue: Any,
) -> None:
    worker_run_single_agent(
        cfg,
        prompt_text,
        event_queue,
        run_single_agent_fn=run_single_agent,
    )


def run_agent_with_timeout(
    cfg: HarnessConfig,
    prompt_text: str,
    timeout_sec: int,
    show_progress: bool,
    cancel_requested: Callable[[], bool] | None = None,
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    return run_agent_with_timeout_orchestrated(
        cfg,
        prompt_text,
        timeout_sec,
        show_progress,
        worker_target=_worker_run_single_agent,
        cancel_requested=cancel_requested,
    )
