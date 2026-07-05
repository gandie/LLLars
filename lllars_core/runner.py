from __future__ import annotations

import multiprocessing as mp
import time
import traceback
from collections.abc import AsyncIterable, Callable
from pathlib import Path
from queue import Empty
from typing import Any
import json

from pydantic_ai import AgentStreamEvent, RunContext, UsageLimits

from lllars_core.agent_builder import build_agent, make_agent_deps
from lllars_core.asyncio_compat import configure_windows_event_loop_policy
from lllars_core.config import HarnessConfig
from lllars_core.console import (
    Color,
    append_trace,
    emit_live_thought,
    extract_thought_trace,
    summarize_agent_stream_event,
    truncate,
)
from lllars_core.skills import configured_markdown_skill_ids


def _extract_loaded_skill_id(event: AgentStreamEvent) -> str | None:
    if event.__class__.__name__ != "FunctionToolCallEvent":
        return None

    part = getattr(event, "part", None)
    tool_name = getattr(part, "tool_name", None)
    if tool_name != "load_capability":
        return None

    args = getattr(part, "args", None)
    if isinstance(args, dict):
        value = args.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    if isinstance(args, str):
        try:
            parsed = json.loads(args)
        except Exception:
            return None
        if not isinstance(parsed, dict):
            return None
        value = parsed.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _drain_agent_events(
    event_queue: Any,
    latest_thought: str,
    payload: dict[str, Any] | None,
) -> tuple[str, dict[str, Any] | None]:
    while True:
        try:
            event = event_queue.get_nowait()
        except Empty:
            return latest_thought, payload
        except Exception:
            return latest_thought, payload

        if not isinstance(event, dict):
            continue

        event_type = str(event.get("type", ""))
        if event_type == "thought":
            message = str(event.get("message", "")).strip()
            if message:
                latest_thought = truncate(message, 90)
            continue

        if event_type == "result":
            maybe_payload = event.get("payload")
            if isinstance(maybe_payload, dict):
                payload = maybe_payload


def _terminate_worker_process(proc: mp.Process) -> None:
    proc.terminate()
    proc.join(timeout=5)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=5)


def _render_running_progress(
    elapsed: int,
    timeout_sec: int,
    spinner: list[str],
    spin_idx: int,
    latest_thought: str,
    last_render_width: int,
) -> tuple[int, int]:
    line = (
        f"{Color.CYAN}[agent] {spinner[spin_idx % 4]} "
        f"running {elapsed}s/{timeout_sec}s{Color.RESET}"
    )
    if latest_thought:
        line += f" {Color.YELLOW}| {latest_thought}{Color.RESET}"
    pad = " " * max(0, last_render_width - len(line))
    print(f"\r{line}{pad}", end="", flush=True)
    return len(line), spin_idx + 1


def run_single_agent(
    cfg: HarnessConfig,
    prompt_text: str,
    thought_log_path: Path | None = None,
    emit_thought: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    configure_windows_event_loop_policy()

    runtime_telemetry: dict[str, Any] = {}
    live_trace: list[str] = []
    configured_skill_ids = configured_markdown_skill_ids(cfg)
    used_skill_ids: list[str] = []
    used_skill_id_set: set[str] = set()

    def _emit(message: str) -> None:
        emit_live_thought(message, thought_log_path)
        if emit_thought is not None:
            emit_thought(message)

    async def _event_stream_handler(
        ctx: RunContext[None],
        event_stream: AsyncIterable[AgentStreamEvent],
    ) -> None:
        _ = ctx
        async for event in event_stream:
            loaded_skill_id = _extract_loaded_skill_id(event)
            if (
                loaded_skill_id
                and loaded_skill_id not in used_skill_id_set
            ):
                used_skill_id_set.add(loaded_skill_id)
                used_skill_ids.append(loaded_skill_id)
                _emit(f"skills-used: {loaded_skill_id}")
            summary = summarize_agent_stream_event(event)
            if summary:
                _emit(summary)
                append_trace(live_trace, summary)

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
            event_stream_handler=_event_stream_handler,
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
    def _emit(message: str) -> None:
        try:
            event_queue.put({"type": "thought", "message": message})
        except Exception:
            return

    payload = run_single_agent(
        cfg=cfg,
        prompt_text=prompt_text,
        thought_log_path=None,
        emit_thought=_emit,
    )
    try:
        event_queue.put({"type": "result", "payload": payload})
    except Exception:
        return


def run_agent_with_timeout(
    cfg: HarnessConfig,
    prompt_text: str,
    timeout_sec: int,
    show_progress: bool,
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    ctx = mp.get_context("spawn")
    event_queue = ctx.Queue()
    proc = ctx.Process(
        target=_worker_run_single_agent,
        args=(cfg, prompt_text, event_queue),
    )
    proc.start()

    start_time = time.time()
    latest_thought = ""
    latest_telemetry: dict[str, Any] = {}
    payload: dict[str, Any] | None = None
    last_render_width = 0
    spinner = ["|", "/", "-", "\\"]
    spin_idx = 0

    while proc.is_alive():
        latest_thought, payload = _drain_agent_events(
            event_queue,
            latest_thought,
            payload,
        )
        elapsed = int(time.time() - start_time)
        if elapsed > timeout_sec:
            _terminate_worker_process(proc)
            if show_progress:
                print(
                    (
                        f"\r{Color.RED}[agent] timeout after "
                        f"{timeout_sec}s{Color.RESET}"
                    )
                    + " " * 20
                )
            return (
                "",
                "[lllars] agent timed out",
                124,
                latest_telemetry,
                [],
            )
        if show_progress:
            last_render_width, spin_idx = _render_running_progress(
                elapsed,
                timeout_sec,
                spinner,
                spin_idx,
                latest_thought,
                last_render_width,
            )
        time.sleep(0.2)

    proc.join(timeout=5)
    latest_thought, payload = _drain_agent_events(
        event_queue,
        latest_thought,
        payload,
    )

    if show_progress:
        elapsed_done = time.time() - start_time
        print(
            f"\r{Color.GREEN}[agent] done in {elapsed_done:.1f}s{Color.RESET}"
            + " " * 20
        )

    if payload is None:
        payload = {
            "returncode": 125,
            "stdout": "",
            "stderr": (
                "[lllars] agent process exited without payload "
                f"(exitcode={proc.exitcode})"
            ),
            "runtime_telemetry": latest_telemetry,
            "thought_trace": [],
        }

    thought_trace = payload.get("thought_trace")
    if not isinstance(thought_trace, list):
        thought_trace = []

    return (
        str(payload.get("stdout", "")) or "",
        str(payload.get("stderr", "")) or "",
        int(payload.get("returncode", 125)),
        (
            payload.get("runtime_telemetry")
            if isinstance(payload.get("runtime_telemetry"), dict)
            else {}
        ),
        [str(item) for item in thought_trace],
    )
