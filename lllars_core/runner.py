from __future__ import annotations

from typing import Any

from lllars_core.config import HarnessConfig
from lllars_core.runtime.runner_orchestrator import (
    run_agent_with_timeout as run_agent_with_timeout_orchestrated,
)
from lllars_core.runtime.runner_single import run_single_agent
from lllars_core.runtime.runner_worker import worker_run_single_agent


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
    cancel_requested=None,
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    return run_agent_with_timeout_orchestrated(
        cfg,
        prompt_text,
        timeout_sec,
        show_progress,
        worker_target=_worker_run_single_agent,
        cancel_requested=cancel_requested,
    )
