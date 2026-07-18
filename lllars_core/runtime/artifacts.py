from __future__ import annotations

from pathlib import Path

from lllars_core.runtime_artifacts import persist_job_artifacts
from lllars_core.runtime_models import ErrorEnvelope, RunResult


def persist_runtime_artifacts(
    *,
    artifacts_root: Path | None,
    job_id: str,
    status: str,
    result: RunResult | None,
    error: ErrorEnvelope | None,
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
        )
    except Exception:
        return {}


__all__ = ["persist_runtime_artifacts"]
