from __future__ import annotations

import multiprocessing as mp
from typing import Any

from lllars_core.config import HarnessConfig


def worker_run_single_agent(
    cfg: HarnessConfig,
    prompt_text: str,
    event_queue: Any,
    *,
    run_single_agent_fn: Any,
) -> None:
    def _emit(message: str) -> None:
        try:
            event_queue.put({"type": "thought", "message": message})
        except Exception:
            return

    payload = run_single_agent_fn(
        cfg=cfg,
        prompt_text=prompt_text,
        thought_log_path=None,
        emit_thought=_emit,
    )
    try:
        event_queue.put({"type": "result", "payload": payload})
    except Exception:
        return


def terminate_worker_process(proc: mp.Process) -> None:
    proc.terminate()
    proc.join(timeout=5)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=5)
