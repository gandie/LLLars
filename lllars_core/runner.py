from __future__ import annotations

import multiprocessing as mp
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from queue import Empty
from typing import Any

from pydantic_ai import UsageLimits

from lllars_core.agent_builder import build_agent
from lllars_core.config import HarnessConfig
from lllars_core.console import (
    Color,
    emit_live_thought,
    extract_thought_trace,
    truncate,
)


def run_single_agent(
    cfg: HarnessConfig,
    prompt_text: str,
    thought_log_path: Path | None = None,
    emit_thought: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    runtime_telemetry: dict[str, Any] = {}

    def _emit(message: str) -> None:
        emit_live_thought(message, thought_log_path)
        if emit_thought is not None:
            emit_thought(message)

    try:
        agent = build_agent(
            cfg,
            emit_thought=_emit,
        )
        _emit("agent: started")
        result = agent.run_sync(
            prompt_text,
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
        )
        _emit("agent: completed")

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
        }

        return {
            "returncode": 0,
            "stdout": str(result.output),
            "stderr": "",
            "thought_trace": extract_thought_trace(result),
            "runtime_telemetry": runtime_telemetry,
        }
    except Exception:
        return {
            "returncode": 125,
            "stdout": "",
            "stderr": traceback.format_exc(),
            "thought_trace": [],
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

    def _drain_events() -> None:
        nonlocal latest_thought
        nonlocal payload
        while True:
            try:
                event = event_queue.get_nowait()
            except Empty:
                return
            except Exception:
                return
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

    while proc.is_alive():
        _drain_events()
        elapsed = int(time.time() - start_time)
        if elapsed > timeout_sec:
            proc.terminate()
            proc.join(timeout=5)
            if proc.is_alive():
                proc.kill()
                proc.join(timeout=5)
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
            line = (
                f"{Color.CYAN}[agent] {spinner[spin_idx % 4]} "
                f"running {elapsed}s/{timeout_sec}s{Color.RESET}"
            )
            if latest_thought:
                line += f" {Color.YELLOW}| {latest_thought}{Color.RESET}"
            pad = " " * max(0, last_render_width - len(line))
            print(f"\r{line}{pad}", end="", flush=True)
            last_render_width = len(line)
            spin_idx += 1
        time.sleep(0.2)

    proc.join(timeout=5)
    _drain_events()

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
