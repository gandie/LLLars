from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lllars_core.runtime.models import ErrorEnvelope, RunResult


def _artifact_payload(
    status: str,
    result: RunResult | None,
    error: ErrorEnvelope | None,
) -> tuple[str, str, dict[str, Any], float, int | None, bool]:
    if result is None:
        return (
            "",
            "" if error is None else error.message,
            {},
            0.0,
            None,
            status == "succeeded",
        )
    return (
        result.agent_stdout,
        result.agent_stderr,
        result.runtime_telemetry,
        result.elapsed_sec,
        result.agent_returncode,
        result.success,
    )


def _write_runtime_stream_artifacts(
    job_dir: Path,
    stdout_text: str,
    stderr_text: str,
    telemetry: dict[str, Any],
) -> None:
    (job_dir / "stdout.txt").write_text(stdout_text, encoding="utf-8")
    (job_dir / "stderr.txt").write_text(stderr_text, encoding="utf-8")
    (job_dir / "telemetry.json").write_text(
        json.dumps(telemetry, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _summary_payload(
    *,
    job_id: str,
    status: str,
    success: bool,
    elapsed_sec: float,
    returncode: int | None,
    error: ErrorEnvelope | None,
    trigger_source: str,
    trigger_payload_ref: str | None,
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "status": status,
        "trigger": {
            "source": trigger_source,
            "payload_ref": trigger_payload_ref,
        },
        "success": success,
        "elapsed_sec": elapsed_sec,
        "agent_returncode": returncode,
        "error": None if error is None else error.model_dump(),
        "artifacts": {
            "summary": "summary.json",
            "stdout": "stdout.txt",
            "stderr": "stderr.txt",
            "telemetry": "telemetry.json",
        },
    }


def _artifact_refs(job_id: str) -> dict[str, str]:
    base = Path("artifacts") / job_id
    return {
        "summary": (base / "summary.json").as_posix(),
        "stdout": (base / "stdout.txt").as_posix(),
        "stderr": (base / "stderr.txt").as_posix(),
        "telemetry": (base / "telemetry.json").as_posix(),
    }


def _write_summary_artifact(
    *,
    job_dir: Path,
    job_id: str,
    status: str,
    success: bool,
    elapsed_sec: float,
    returncode: int | None,
    error: ErrorEnvelope | None,
    trigger_source: str,
    trigger_payload_ref: str | None,
) -> None:
    payload = _summary_payload(
        job_id=job_id,
        status=status,
        success=success,
        elapsed_sec=elapsed_sec,
        returncode=returncode,
        error=error,
        trigger_source=trigger_source,
        trigger_payload_ref=trigger_payload_ref,
    )
    (job_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_job_artifacts(
    *,
    job_dir: Path,
    job_id: str,
    status: str,
    result: RunResult | None,
    error: ErrorEnvelope | None,
    trigger_source: str,
    trigger_payload_ref: str | None,
) -> None:
    (
        stdout_text,
        stderr_text,
        telemetry,
        elapsed_sec,
        returncode,
        success,
    ) = _artifact_payload(status, result, error)
    _write_runtime_stream_artifacts(
        job_dir,
        stdout_text,
        stderr_text,
        telemetry,
    )
    _write_summary_artifact(
        job_dir=job_dir,
        job_id=job_id,
        status=status,
        success=success,
        elapsed_sec=elapsed_sec,
        returncode=returncode,
        error=error,
        trigger_source=trigger_source,
        trigger_payload_ref=trigger_payload_ref,
    )


def persist_job_artifacts(
    *,
    artifacts_root: Path,
    job_id: str,
    status: str,
    result: RunResult | None,
    error: ErrorEnvelope | None,
    trigger_source: str,
    trigger_payload_ref: str | None,
) -> dict[str, str]:
    job_dir = artifacts_root / "artifacts" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    _write_job_artifacts(
        job_dir=job_dir,
        job_id=job_id,
        status=status,
        result=result,
        error=error,
        trigger_source=trigger_source,
        trigger_payload_ref=trigger_payload_ref,
    )
    return _artifact_refs(job_id)


def persist_runtime_artifacts(
    *,
    artifacts_root: Path | None,
    job_id: str,
    status: str,
    result: RunResult | None,
    error: ErrorEnvelope | None,
    trigger_source: str,
    trigger_payload_ref: str | None,
) -> dict[str, str]:
    if artifacts_root is None:
        return {}

    try:
        return persist_job_artifacts(
            artifacts_root=artifacts_root,
            job_id=job_id,
            status=status,
            result=result,
            error=error,
            trigger_source=trigger_source,
            trigger_payload_ref=trigger_payload_ref,
        )
    except Exception:
        return {}


__all__ = ["persist_job_artifacts", "persist_runtime_artifacts"]
