from __future__ import annotations

import platform
from pathlib import Path

from lllars_core.config.models import (
    DEFAULT_SHELL_MODE,
    POSIX_SHELLS,
    VALID_SHELL_MODES,
    VALID_SHELL_OVERRIDES,
    WINDOWS_SHELLS,
)
from lllars_core.runtime_guard import resolve_mount_directory


def as_bool(raw: object, default: bool) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return default
    value = str(raw).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def merge_layers(
    defaults: dict[str, object],
    env_layer: dict[str, object],
    json_layer: dict[str, object],
    overrides: dict[str, object] | None,
) -> dict[str, object]:
    merged = dict(defaults)
    merged.update(env_layer)
    merged.update(json_layer)
    if overrides:
        merged.update(overrides)
    return merged


def validate_choice(
    cfg: dict,
    key: str,
    *,
    default: str,
    valid_values: frozenset[str],
) -> str:
    value = str(cfg.get(key, default)).strip().lower()
    if value not in valid_values:
        allowed = ", ".join(sorted(valid_values))
        raise ValueError(
            f"Invalid {key}: {value!r}. Allowed values: {allowed}"
        )
    return value


def load_commands(cfg: dict) -> tuple[str | None, str | None]:
    commands = cfg.get("commands", {})
    if commands is None:
        commands = {}
    if not isinstance(commands, dict):
        raise ValueError("Config requires commands object")

    test_raw = str(commands.get("test", "")).strip()
    eval_raw = str(commands.get("eval", "")).strip()
    return (test_raw or None), (eval_raw or None)


def resolve_shell_policy(cfg: dict) -> tuple[str, str | None]:
    shell_mode = validate_choice(
        cfg,
        "shell_mode",
        default=DEFAULT_SHELL_MODE,
        valid_values=VALID_SHELL_MODES,
    )

    shell_override_raw = str(cfg.get("shell_override", "")).strip().lower()
    shell_override = shell_override_raw or None
    if (
        shell_override is not None
        and shell_override not in VALID_SHELL_OVERRIDES
    ):
        allowed = ", ".join(sorted(VALID_SHELL_OVERRIDES))
        raise ValueError(
            "Unknown shell_override "
            f"{shell_override!r}. Allowed values: {allowed}"
        )

    if shell_mode == "override" and shell_override is None:
        raise ValueError(
            "shell_mode=override requires non-empty shell_override"
        )

    supported = _supported_shells()
    if shell_override is not None and shell_override not in supported:
        supported_text = ", ".join(supported)
        raise ValueError(
            f"Unsupported shell_override {shell_override!r} on this platform. "
            f"Supported values: {supported_text}"
        )

    return shell_mode, shell_override


def _supported_shells() -> tuple[str, ...]:
    if platform.system() == "Windows":
        return WINDOWS_SHELLS
    return POSIX_SHELLS


def optional_int(cfg: dict, key: str, default: int | None) -> int | None:
    raw = cfg.get(key, default)
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value < 0:
        return None
    return value


def optional_float(cfg: dict, key: str, default: float | None) -> float | None:
    raw = cfg.get(key, default)
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return None
    return value


def non_negative_int(cfg: dict, key: str, default: int) -> int:
    raw = cfg.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(0, value)


def positive_int(cfg: dict, key: str, default: int) -> int:
    raw = cfg.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


def resolve_mount_root(
    cfg: dict,
    key: str,
    *,
    config_root: Path,
    default_path: Path,
) -> Path:
    raw_value = str(cfg.get(key, "")).strip()
    return resolve_mount_directory(
        raw_value,
        config_root=config_root,
        default_path=default_path,
        field_name=key,
    )
