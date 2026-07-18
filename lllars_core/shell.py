from __future__ import annotations

import json
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lllars_core.config import HarnessConfig, ROOT


@dataclass(frozen=True)
class ShellSelection:
    name: str
    executable: str
    command_prefix: tuple[str, ...]


def _windows_shells() -> tuple[ShellSelection, ...]:
    return (
        ShellSelection(
            name="pwsh",
            executable="pwsh",
            command_prefix=(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
            ),
        ),
        ShellSelection(
            name="powershell",
            executable="powershell",
            command_prefix=(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
            ),
        ),
        ShellSelection(
            name="cmd",
            executable="cmd",
            command_prefix=("/d", "/s", "/c"),
        ),
    )


def _posix_shells() -> tuple[ShellSelection, ...]:
    return (
        ShellSelection(
            name="bash",
            executable="bash",
            command_prefix=("-lc",),
        ),
        ShellSelection(
            name="sh",
            executable="sh",
            command_prefix=("-lc",),
        ),
    )


def _candidate_shells() -> tuple[ShellSelection, ...]:
    if platform.system() == "Windows":
        return _windows_shells()
    return _posix_shells()


def detect_shell(
    *,
    shell_mode: str = "auto",
    shell_override: str | None = None,
) -> ShellSelection | None:
    candidates = _candidate_shells()
    if shell_override:
        override = shell_override.strip().lower()
        shell_map = {item.name: item for item in candidates}
        selected = shell_map.get(override)
        if selected is None:
            return None
        if shell_mode == "override":
            return (
                selected
                if shutil.which(selected.executable) is not None
                else None
            )
        if shutil.which(selected.executable) is not None:
            return selected

    for candidate in candidates:
        if shutil.which(candidate.executable) is not None:
            return candidate
    return None


def run_shell(
    command: str,
    cwd: Path,
    timeout_sec: int,
    *,
    shell_mode: str = "auto",
    shell_override: str | None = None,
) -> dict[str, Any]:
    selection = detect_shell(
        shell_mode=shell_mode,
        shell_override=shell_override,
    )
    if selection is None:
        raise RuntimeError("No supported shell executable found")

    p = subprocess.run(
        [
            selection.executable,
            *selection.command_prefix,
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
        "shell": selection.name,
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def run_powershell(
    command: str,
    cwd: Path,
    timeout_sec: int,
) -> dict[str, Any]:
    # Preserve the legacy entrypoint while routing through the shell adapter.
    return run_shell(
        command=command,
        cwd=cwd,
        timeout_sec=timeout_sec,
        shell_mode="override",
        shell_override="powershell",
    )


def run_eval(cfg: HarnessConfig) -> tuple[dict[str, Any] | None, str | None]:
    if cfg.eval_command is None:
        return None, None

    payload = run_shell(
        command=cfg.eval_command,
        cwd=ROOT,
        timeout_sec=120,
        shell_mode=cfg.shell_mode,
        shell_override=cfg.shell_override,
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
    if cfg.test_command is None:
        return {
            "returncode": 0,
            "stdout": "",
            "stderr": "tests not configured",
            "skipped": True,
        }
    return run_shell(
        command=cfg.test_command,
        cwd=ROOT,
        timeout_sec=120,
        shell_mode=cfg.shell_mode,
        shell_override=cfg.shell_override,
    )


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
