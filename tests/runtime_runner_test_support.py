from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lllars_core.runtime.models import JobSpec
from lllars_core.shell import ShellSelection


def basic_spec(
    *,
    timeout_sec: int = 5,
    config_path: str | None = None,
    deadline_at: datetime | None = None,
    run_overrides: dict[str, object] | None = None,
) -> JobSpec:
    run = {
        "model": "test-model",
        "provider_url": "http://localhost:11434",
        "project_root": ".",
        "command_profile": "none",
    }
    if run_overrides:
        run.update(run_overrides)
    return JobSpec(
        prompt="hello",
        run=run,
        config_path=config_path,
        timeout_sec=timeout_sec,
        deadline_at=deadline_at,
    )


def powershell_selection() -> ShellSelection:
    return ShellSelection(
        name="powershell",
        executable="powershell",
        command_prefix=(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
        ),
    )


def resolved_config_path() -> Path:
    return Path("playground.example.json").resolve()
