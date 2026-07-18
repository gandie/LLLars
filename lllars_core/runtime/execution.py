from __future__ import annotations

from pathlib import Path

from lllars_core.runtime.models import ShellRuntimeTelemetry
from lllars_core.shell import ShellSelection


def command_cwd(cfg: object) -> Path:
    project_root = getattr(cfg, "project_root", None)
    if isinstance(project_root, Path):
        return project_root
    return Path.cwd()


def resolve_shell_policy(cfg: object) -> tuple[str, str | None]:
    shell_mode_raw = getattr(cfg, "shell_mode", "auto")
    shell_mode = str(shell_mode_raw).strip().lower() or "auto"
    shell_override_raw = getattr(cfg, "shell_override", None)
    shell_override = (
        str(shell_override_raw).strip().lower()
        if isinstance(shell_override_raw, str) and shell_override_raw.strip()
        else None
    )
    return shell_mode, shell_override


def resolve_shell_selection(
    cfg: object,
    *,
    detect_shell_fn,
) -> ShellSelection | None:
    shell_mode, shell_override = resolve_shell_policy(cfg)
    return detect_shell_fn(
        shell_mode=shell_mode,
        shell_override=shell_override,
    )


def shell_invocation_mode(shell_mode: str) -> str:
    return "explicit_override" if shell_mode == "override" else "auto_detect"


def run_tests_with_selection(
    cfg: object,
    selection: ShellSelection,
    *,
    run_shell_fn,
) -> dict[str, object]:
    test_command = getattr(cfg, "test_command", None)
    if test_command is None:
        return {
            "returncode": 0,
            "stdout": "",
            "stderr": "tests not configured",
            "skipped": True,
            "shell": selection.name,
        }

    return run_shell_fn(
        command=test_command,
        cwd=command_cwd(cfg),
        timeout_sec=120,
        shell_mode="override",
        shell_override=selection.name,
    )


def run_eval_with_selection(
    cfg: object,
    selection: ShellSelection,
    *,
    run_shell_fn,
) -> tuple[dict[str, object] | None, str | None]:
    eval_command = getattr(cfg, "eval_command", None)
    if eval_command is None:
        return None, None

    payload = run_shell_fn(
        command=eval_command,
        cwd=command_cwd(cfg),
        timeout_sec=120,
        shell_mode="override",
        shell_override=selection.name,
    )
    if int(payload.get("returncode", 1)) != 0:
        return None, str(payload.get("stderr", ""))

    if not bool(getattr(cfg, "eval_expect_json", True)):
        return _raw_eval_payload(payload, selection), None
    return _json_eval_payload(payload, selection)


def _raw_eval_payload(
    payload: dict[str, object],
    selection: ShellSelection,
) -> dict[str, object]:
    return {
        "raw_stdout": str(payload.get("stdout", "")),
        "raw_stderr": str(payload.get("stderr", "")),
        "returncode": int(payload.get("returncode", 0)),
        "shell": selection.name,
    }


def _json_eval_payload(
    payload: dict[str, object],
    selection: ShellSelection,
) -> tuple[dict[str, object] | None, str | None]:
    import json

    try:
        parsed = json.loads(str(payload.get("stdout", "")))
    except Exception as exc:
        return None, str(exc)
    if not isinstance(parsed, dict):
        return None, None

    parsed.setdefault("shell", selection.name)
    return parsed, None


def build_runtime_telemetry(
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
) -> dict[str, str | None]:
    telemetry = ShellRuntimeTelemetry(
        selected=selection.name,
        shell_mode=shell_mode,
        shell_override=shell_override,
        invocation_mode=shell_invocation_mode(shell_mode),
    )
    return {
        "selected": telemetry.selected,
        "shell_mode": telemetry.shell_mode,
        "shell_override": telemetry.shell_override,
        "invocation_mode": telemetry.invocation_mode,
    }


__all__ = [
    "build_runtime_telemetry",
    "command_cwd",
    "resolve_shell_policy",
    "resolve_shell_selection",
    "run_eval_with_selection",
    "run_tests_with_selection",
    "shell_invocation_mode",
]
