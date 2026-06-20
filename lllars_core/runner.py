from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

from lllars_core.agent_builder import build_agent, default_runtime_telemetry
from lllars_core.config import HarnessConfig, ROOT
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
) -> dict[str, Any]:
    runtime_telemetry = default_runtime_telemetry()

    def _persist(telemetry: dict[str, Any]) -> None:
        nonlocal runtime_telemetry
        runtime_telemetry = telemetry

    def _emit(message: str) -> None:
        emit_live_thought(message, thought_log_path)

    try:
        agent, runtime_telemetry = build_agent(
            cfg,
            emit_thought=_emit,
            on_telemetry_update=_persist,
        )
        _emit("agent: started")
        result = agent.run_sync(prompt_text)
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
        return {
            "returncode": 125,
            "stdout": "",
            "stderr": traceback.format_exc(),
            "thought_trace": [],
            "runtime_telemetry": runtime_telemetry,
        }


def run_agent_with_timeout(
    cfg: HarnessConfig,
    prompt_text: str,
    timeout_sec: int,
    show_progress: bool,
    config_path: Path,
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    payload_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix="lllars_payload_",
        delete=False,
        encoding="utf-8",
    )
    payload_path = Path(payload_file.name)
    payload_file.close()

    prompt_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        prefix="lllars_prompt_",
        delete=False,
        encoding="utf-8",
    )
    prompt_path = Path(prompt_file.name)
    prompt_file.write(prompt_text)
    prompt_file.close()

    thought_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".log",
        prefix="lllars_thoughts_",
        delete=False,
        encoding="utf-8",
    )
    thought_path = Path(thought_file.name)
    thought_file.close()

    cmd = [
        sys.executable,
        "-m",
        "lllars",
        "--config",
        str(config_path),
        "--internal-run",
        "--internal-prompt-file",
        str(prompt_path),
        "--internal-output-json",
        str(payload_path),
        "--internal-thought-log",
        str(thought_path),
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    start_time = time.time()
    thought_pos = 0
    latest_thought = ""
    last_render_width = 0
    spinner = ["|", "/", "-", "\\"]
    spin_idx = 0
    while proc.poll() is None:
        elapsed = int(time.time() - start_time)
        if thought_path.exists():
            try:
                with thought_path.open(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                ) as handle:
                    handle.seek(thought_pos)
                    chunk = handle.read()
                    thought_pos = handle.tell()
                if chunk:
                    for line in chunk.splitlines():
                        stripped = line.strip()
                        if stripped:
                            latest_thought = truncate(stripped, 90)
            except Exception:
                pass
        if elapsed > timeout_sec:
            proc.kill()
            proc.wait(timeout=5)
            payload_path.unlink(missing_ok=True)
            prompt_path.unlink(missing_ok=True)
            thought_path.unlink(missing_ok=True)
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
                default_runtime_telemetry(),
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

    _, stderr_text = proc.communicate(timeout=5)
    if show_progress:
        elapsed_done = time.time() - start_time
        print(
            f"\r{Color.GREEN}[agent] done in {elapsed_done:.1f}s{Color.RESET}"
            + " " * 20
        )

    payload: dict[str, Any] = {
        "returncode": 125,
        "stdout": "",
        "stderr": stderr_text[-2000:],
        "runtime_telemetry": default_runtime_telemetry(),
    }
    if payload_path.exists():
        try:
            loaded = json.loads(payload_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                payload = loaded
        except Exception:
            pass

    payload_path.unlink(missing_ok=True)
    prompt_path.unlink(missing_ok=True)
    thought_path.unlink(missing_ok=True)

    thought_trace = payload.get("thought_trace")
    if not isinstance(thought_trace, list):
        thought_trace = []

    return (
        str(payload.get("stdout", "")) or "",
        str(payload.get("stderr", "")) or "",
        int(payload.get("returncode", 125)),
        payload.get("runtime_telemetry")
        if isinstance(payload.get("runtime_telemetry"), dict)
        else default_runtime_telemetry(),
        [str(item) for item in thought_trace],
    )
