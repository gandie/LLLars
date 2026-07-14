from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lllars_core.runtime_models import ErrorEnvelope, RunResult


def persist_job_artifacts(
    *,
    artifacts_root: Path,
    job_id: str,
    status: str,
    result: RunResult | None,
    error: ErrorEnvelope | None,
) -> dict[str, str]:
    job_dir = artifacts_root / "artifacts" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    summary_path = job_dir / "summary.json"
    stdout_path = job_dir / "stdout.txt"
    stderr_path = job_dir / "stderr.txt"
    telemetry_path = job_dir / "telemetry.json"

    if result is None:
        stdout_text = ""
        stderr_text = "" if error is None else error.message
        telemetry: dict[str, Any] = {}
        elapsed_sec = 0.0
        agent_returncode = None
        success = status == "succeeded"
    else:
        stdout_text = result.agent_stdout
        stderr_text = result.agent_stderr
        telemetry = result.runtime_telemetry
        elapsed_sec = result.elapsed_sec
        agent_returncode = result.agent_returncode
        success = result.success

    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    telemetry_path.write_text(
        json.dumps(telemetry, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    summary = {
        "job_id": job_id,
        "status": status,
        "success": success,
        "elapsed_sec": elapsed_sec,
        "agent_returncode": agent_returncode,
        "error": None if error is None else error.model_dump(),
        "artifacts": {
            "summary": "summary.json",
            "stdout": "stdout.txt",
            "stderr": "stderr.txt",
            "telemetry": "telemetry.json",
        },
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    root_rel = Path("artifacts") / job_id
    return {
        "summary": str((root_rel / "summary.json").as_posix()),
        "stdout": str((root_rel / "stdout.txt").as_posix()),
        "stderr": str((root_rel / "stderr.txt").as_posix()),
        "telemetry": str((root_rel / "telemetry.json").as_posix()),
    }


__all__ = ["persist_job_artifacts"]
