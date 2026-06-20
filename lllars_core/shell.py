from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from lllars_core.config import HarnessConfig, ROOT


def run_powershell(
    command: str,
    cwd: Path,
    timeout_sec: int,
) -> dict[str, Any]:
    p = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout_sec,
    )
    return {
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def run_eval(cfg: HarnessConfig) -> tuple[dict[str, Any] | None, str | None]:
    if cfg.eval_command is None:
        return None, None

    payload = run_powershell(
        command=cfg.eval_command,
        cwd=ROOT,
        timeout_sec=120,
    )
    if payload["returncode"] != 0:
        return None, payload["stderr"]

    if not cfg.eval_expect_json:
        return {
            "raw_stdout": payload["stdout"],
            "raw_stderr": payload["stderr"],
            "returncode": payload["returncode"],
        }, None

    try:
        parsed = json.loads(payload["stdout"])
    except Exception as exc:
        return None, str(exc)

    return parsed if isinstance(parsed, dict) else None, None


def run_tests(cfg: HarnessConfig) -> dict[str, Any]:
    return run_powershell(command=cfg.test_command, cwd=ROOT, timeout_sec=120)


def is_eval_success(
    cfg: HarnessConfig,
    eval_json: dict[str, Any] | None,
) -> bool:
    if cfg.eval_command is None:
        return True
    if not isinstance(eval_json, dict):
        return False
    summary = eval_json.get("summary")
    if not isinstance(summary, dict):
        return False
    pass_rate = summary.get("pass_rate")
    if not isinstance(pass_rate, (int, float)):
        return False
    return float(pass_rate) >= cfg.eval_success_pass_rate
