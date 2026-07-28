from __future__ import annotations

import json
import time
from collections.abc import AsyncIterable, Callable
from queue import Empty
from typing import Any

from pydantic_ai import AgentStreamEvent, RunContext

from lllars_core.console import (
    Color,
    append_trace,
    summarize_agent_stream_event,
    truncate,
)


def extract_loaded_skill_id(event: AgentStreamEvent) -> str | None:
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

    if not isinstance(args, str):
        return None

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


def build_event_stream_handler(
    *,
    event_start: float,
    emit: Callable[[str], None],
    live_trace: list[str],
    telemetry_timeline: list[dict[str, Any]],
    used_skill_ids: list[str],
    used_skill_id_set: set[str],
) -> Callable[[RunContext[None], AsyncIterable[AgentStreamEvent]], Any]:
    async def _event_stream_handler(
        ctx: RunContext[None],
        event_stream: AsyncIterable[AgentStreamEvent],
    ) -> None:
        _ = ctx
        async for event in event_stream:
            loaded_skill_id = extract_loaded_skill_id(event)
            if loaded_skill_id and loaded_skill_id not in used_skill_id_set:
                used_skill_id_set.add(loaded_skill_id)
                used_skill_ids.append(loaded_skill_id)
                emit(f"skills-used: {loaded_skill_id}")

            summary = summarize_agent_stream_event(event)
            if not summary:
                continue
            emit(summary)
            append_trace(live_trace, summary)
            telemetry_timeline.append(
                {
                    "event": summary,
                    "offset_sec": round(time.time() - event_start, 3),
                }
            )

    return _event_stream_handler


def extract_used_skill_id_from_thought(message: str) -> str | None:
    text = message.strip()
    prefix = "skills-used:"
    if not text.startswith(prefix):
        return None
    skill_id = text[len(prefix) :].strip()
    if not skill_id:
        return None
    return skill_id


def drain_agent_events(
    event_queue: Any,
    latest_thought: str,
    payload: dict[str, Any] | None,
) -> tuple[str, dict[str, Any] | None, list[str]]:
    thought_events: list[str] = []
    while True:
        try:
            event = event_queue.get_nowait()
        except Empty:
            return latest_thought, payload, thought_events
        except Exception:
            return latest_thought, payload, thought_events

        if not isinstance(event, dict):
            continue

        event_type = str(event.get("type", ""))
        if event_type == "thought":
            message = str(event.get("message", "")).strip()
            if message:
                thought_events.append(message)
                latest_thought = truncate(message, 90)
            continue

        if event_type == "result":
            maybe_payload = event.get("payload")
            if isinstance(maybe_payload, dict):
                payload = maybe_payload


def render_running_progress(
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
