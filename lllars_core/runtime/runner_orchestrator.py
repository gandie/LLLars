from __future__ import annotations

import multiprocessing as mp
import time
from collections.abc import Callable
from typing import Any

from lllars_core.config import HarnessConfig
from lllars_core.console import Color
from lllars_core.runtime.runner_results import (
    finalize_result,
    normalize_payload,
    terminal_result,
)
from lllars_core.runtime.runner_stream import (
    drain_agent_events,
    extract_used_skill_id_from_thought,
    render_running_progress,
)
from lllars_core.runtime.runner_worker import terminate_worker_process
from lllars_core.skills import configured_markdown_skill_ids


def _run_until_worker_exit(
    cfg: HarnessConfig,
    proc: mp.Process,
    event_queue: Any,
    timeout_sec: int,
    show_progress: bool,
    cancel_requested: Callable[[], bool] | None,
) -> tuple[
    tuple[str, str, int, dict[str, Any], list[str]] | None,
    dict[str, Any] | None,
    dict[str, Any],
]:
    state = _initial_loop_state(cfg)
    loop_context = {
        "timeout_sec": timeout_sec,
        "show_progress": show_progress,
        "cancel_requested": cancel_requested,
        "state": state,
    }
    while proc.is_alive():
        early_result = _process_worker_iteration(
            proc,
            event_queue,
            loop_context,
        )
        if early_result is not None:
            return early_result, state["payload"], state["latest_telemetry"]
    return None, state["payload"], state["latest_telemetry"]


def _initial_loop_state(cfg: HarnessConfig) -> dict[str, Any]:
    configured_skill_ids = list(configured_markdown_skill_ids(cfg))
    used_skill_ids = (
        list(configured_skill_ids)
        if configured_skill_ids and not cfg.skills_defer_loading
        else []
    )
    return {
        "start_time": time.time(),
        "latest_thought": "",
        "latest_telemetry": {
            "skills_enabled": cfg.skills_enabled,
            "skills_defer_loading": cfg.skills_defer_loading,
            "skills_loaded_ids": configured_skill_ids,
            "skills_loaded_count": len(configured_skill_ids),
            "skills_used_ids": used_skill_ids,
            "skills_used_count": len(used_skill_ids),
            "timeline": [],
        },
        "payload": None,
        "last_render_width": 0,
        "spinner": ["|", "/", "-", "\\"],
        "spin_idx": 0,
    }


def _process_worker_iteration(
    proc: mp.Process,
    event_queue: Any,
    loop_context: dict[str, Any],
) -> tuple[str, str, int, dict[str, Any], list[str]] | None:
    state = loop_context["state"]
    _drain_state(event_queue, state)
    maybe_terminal = _maybe_terminate(proc, loop_context)
    if maybe_terminal is not None:
        return maybe_terminal
    if bool(loop_context["show_progress"]):
        timeout_sec = int(loop_context["timeout_sec"])
        elapsed = int(time.time() - state["start_time"])
        state["last_render_width"], state["spin_idx"] = (
            render_running_progress(
                elapsed,
                timeout_sec,
                state["spinner"],
                state["spin_idx"],
                state["latest_thought"],
                state["last_render_width"],
            )
        )
    time.sleep(0.2)
    return None


def _drain_state(event_queue: Any, state: dict[str, Any]) -> None:
    (
        state["latest_thought"],
        state["payload"],
        thought_events,
    ) = drain_agent_events(
        event_queue,
        state["latest_thought"],
        state["payload"],
    )
    payload = state.get("payload")
    if isinstance(payload, dict):
        runtime_telemetry = payload.get("runtime_telemetry")
        if isinstance(runtime_telemetry, dict):
            state["latest_telemetry"] = dict(runtime_telemetry)

    latest_telemetry = state.get("latest_telemetry")
    if not isinstance(latest_telemetry, dict):
        return
    used_ids = latest_telemetry.get("skills_used_ids")
    if not isinstance(used_ids, list):
        used_ids = []
        latest_telemetry["skills_used_ids"] = used_ids
    for message in thought_events:
        skill_id = extract_used_skill_id_from_thought(message)
        if skill_id and skill_id not in used_ids:
            used_ids.append(skill_id)
    latest_telemetry["skills_used_count"] = len(used_ids)


def _maybe_terminate(
    proc: mp.Process,
    loop_context: dict[str, Any],
) -> tuple[str, str, int, dict[str, Any], list[str]] | None:
    timeout_sec = int(loop_context["timeout_sec"])
    show_progress = bool(loop_context["show_progress"])
    cancel_requested = loop_context["cancel_requested"]
    state = loop_context["state"]
    reason: str | None = None
    if cancel_requested is not None and cancel_requested():
        reason = "canceled"
    elif int(time.time() - state["start_time"]) > timeout_sec:
        reason = "timeout"
    if reason is None:
        return None
    terminate_worker_process(proc)
    return terminal_result(
        reason=reason,
        show_progress=show_progress,
        timeout_sec=timeout_sec,
        latest_telemetry=state["latest_telemetry"],
    )


def _finish_worker_collection(
    proc: mp.Process,
    event_queue: Any,
    payload: dict[str, Any] | None,
    show_progress: bool,
    latest_telemetry: dict[str, Any],
) -> dict[str, Any]:
    proc.join(timeout=5)
    _, payload, _ = drain_agent_events(event_queue, "", payload)

    if show_progress:
        print(f"\r{Color.GREEN}[agent] done{Color.RESET}" + " " * 20)

    return normalize_payload(payload, proc, latest_telemetry)


def run_agent_with_timeout(
    cfg: HarnessConfig,
    prompt_text: str,
    timeout_sec: int,
    show_progress: bool,
    *,
    worker_target: Any,
    cancel_requested: Callable[[], bool] | None = None,
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    ctx = mp.get_context("spawn")
    event_queue = ctx.Queue()
    proc = ctx.Process(
        target=worker_target,
        args=(cfg, prompt_text, event_queue),
    )
    proc.start()
    early_result, payload, latest_telemetry = _run_until_worker_exit(
        cfg,
        proc,
        event_queue,
        timeout_sec,
        show_progress,
        cancel_requested,
    )
    if early_result is not None:
        return early_result

    normalized_payload = _finish_worker_collection(
        proc,
        event_queue,
        payload,
        show_progress,
        latest_telemetry,
    )
    return finalize_result(normalized_payload)
