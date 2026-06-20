from __future__ import annotations

import multiprocessing as mp
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from queue import Empty
from typing import Any

from pydantic_ai import UsageLimits

from lllars_core.agent_builder import build_agent, default_runtime_telemetry
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
    on_telemetry_update: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    runtime_telemetry = default_runtime_telemetry()

    def _persist(telemetry: dict[str, Any]) -> None:
        nonlocal runtime_telemetry
        runtime_telemetry = telemetry
        if on_telemetry_update is not None:
            on_telemetry_update(dict(telemetry))

    def _emit(message: str) -> None:
        emit_live_thought(message, thought_log_path)
        if emit_thought is not None:
            emit_thought(message)

    try:
        agent, runtime_telemetry = build_agent(
            cfg,
            emit_thought=_emit,
            on_telemetry_update=_persist,
        )
        _emit("agent: started")
        result = agent.run_sync(
            prompt_text,
            usage_limits=UsageLimits(
                request_limit=None,
                tool_calls_limit=None,
                input_tokens_limit=None,
                output_tokens_limit=None,
                total_tokens_limit=None,
            ),
        )
        _emit("agent: completed")

        try:
            req = 0
            resp = 0
            response_ids = 0
            for msg in result.all_messages():
                kind = str(getattr(msg, "kind", ""))
                if kind == "request":
                    req += 1
                elif kind == "response":
                    resp += 1
                    if getattr(msg, "provider_response_id", None):
                        response_ids += 1
            runtime_telemetry["ollama_requests_estimated"] = req
            runtime_telemetry["ollama_responses_estimated"] = resp
            runtime_telemetry["provider_response_ids_seen"] = response_ids
        except Exception:
            pass

        return {
            "returncode": 0,
            "stdout": str(result.output),
            "stderr": "",
            "thought_trace": extract_thought_trace(result),
            "runtime_telemetry": runtime_telemetry,
        }
    except Exception:
        raise
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

    def _persist(telemetry: dict[str, Any]) -> None:
        try:
            event_queue.put(
                {
                    "type": "telemetry",
                    "runtime_telemetry": dict(telemetry),
                }
            )
        except Exception:
            return

    payload = run_single_agent(
        cfg=cfg,
        prompt_text=prompt_text,
        thought_log_path=None,
        emit_thought=_emit,
        on_telemetry_update=_persist,
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
    latest_telemetry = default_runtime_telemetry()
    payload: dict[str, Any] | None = None
    last_render_width = 0
    spinner = ["|", "/", "-", "\\"]
    spin_idx = 0

    def _drain_events() -> None:
        nonlocal latest_thought
        nonlocal latest_telemetry
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
            if event_type == "telemetry":
                runtime = event.get("runtime_telemetry")
                if isinstance(runtime, dict):
                    latest_telemetry = dict(runtime)
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
            else default_runtime_telemetry()
        ),
        [str(item) for item in thought_trace],
    )
