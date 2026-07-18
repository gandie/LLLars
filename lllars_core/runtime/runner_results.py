from __future__ import annotations

import multiprocessing as mp
from typing import Any

from lllars_core.console import Color


def terminal_result(
    *,
    reason: str,
    show_progress: bool,
    timeout_sec: int,
    latest_telemetry: dict[str, Any],
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    if show_progress and reason == "canceled":
        print(
            f"\r{Color.YELLOW}[agent] canceled by operator"
            f"{Color.RESET}" + " " * 20
        )
    if show_progress and reason == "timeout":
        print(
            f"\r{Color.RED}[agent] timeout after {timeout_sec}s"
            f"{Color.RESET}" + " " * 20
        )

    stderr = (
        "[lllars] agent canceled"
        if reason == "canceled"
        else "[lllars] agent timed out"
    )
    code = 130 if reason == "canceled" else 124
    return "", stderr, code, latest_telemetry, []


def normalize_payload(
    payload: dict[str, Any] | None,
    proc: mp.Process,
    latest_telemetry: dict[str, Any],
) -> dict[str, Any]:
    if payload is not None:
        return payload
    return {
        "returncode": 125,
        "stdout": "",
        "stderr": (
            "[lllars] agent process exited without payload "
            f"(exitcode={proc.exitcode})"
        ),
        "runtime_telemetry": latest_telemetry,
        "thought_trace": [],
    }


def finalize_result(
    payload: dict[str, Any],
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    thought_trace = payload.get("thought_trace")
    if not isinstance(thought_trace, list):
        thought_trace = []

    telemetry = payload.get("runtime_telemetry")
    if not isinstance(telemetry, dict):
        telemetry = {}

    return (
        str(payload.get("stdout", "")) or "",
        str(payload.get("stderr", "")) or "",
        int(payload.get("returncode", 125)),
        telemetry,
        [str(item) for item in thought_trace],
    )
