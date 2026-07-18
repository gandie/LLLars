from __future__ import annotations

import json
from pathlib import Path

import yaml

from lllars_core.config.models import DEFAULT_COMMAND_PROFILE

COMMAND_PROFILE_REGISTRY = {
    "none": (),
    "python-playground": (
        "python main.py",
        "python test.py",
    ),
}


def _normalize_profile_name(raw_name: object) -> str:
    normalized_name = str(raw_name).strip().lower()
    if not normalized_name:
        raise ValueError("Command profile name must be non-empty")
    return normalized_name


def _normalize_profile_commands(
    profile_name: str,
    raw_commands: object,
) -> tuple[str, ...]:
    if not isinstance(raw_commands, list):
        raise ValueError(
            "External command profile "
            f"{profile_name!r} must define commands as an array"
        )
    normalized_commands: list[str] = []
    for command in raw_commands:
        text = str(command).strip()
        if text:
            normalized_commands.append(text)
    return tuple(normalized_commands)


def _normalize_external_profiles(
    payload: object,
) -> dict[str, tuple[str, ...]]:
    if isinstance(payload, dict) and "profiles" in payload:
        payload = payload["profiles"]
    if not isinstance(payload, dict):
        raise ValueError(
            "External command profiles must be an object mapping "
            "profile name to command array"
        )

    registry: dict[str, tuple[str, ...]] = {}
    for raw_name, raw_commands in payload.items():
        profile_name = _normalize_profile_name(raw_name)
        if profile_name in registry:
            raise ValueError(
                "Duplicate external command profile "
                f"{profile_name!r} after normalization"
            )
        registry[profile_name] = _normalize_profile_commands(
            profile_name,
            raw_commands,
        )
    return registry


def _load_external_profiles(source_path: Path) -> dict[str, tuple[str, ...]]:
    if not source_path.exists():
        raise ValueError(
            "command_profiles_path does not exist: "
            f"{source_path}"
        )

    suffix = source_path.suffix.lower()
    source_text = source_path.read_text(encoding="utf-8")
    if suffix == ".json":
        payload = json.loads(source_text)
    elif suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(source_text)
    else:
        raise ValueError(
            "command_profiles_path must use .json, .yaml, or .yml"
        )
    return _normalize_external_profiles(payload)


def command_profile_registry(
    cfg: dict,
    *,
    config_root: Path | None = None,
) -> tuple[dict[str, tuple[str, ...]], Path | None]:
    registry = dict(COMMAND_PROFILE_REGISTRY)

    external_source_raw = str(cfg.get("command_profiles_path", "")).strip()
    if not external_source_raw:
        return registry, None

    source_path = Path(external_source_raw)
    if not source_path.is_absolute():
        if config_root is None:
            raise ValueError(
                "Relative command_profiles_path requires config_root"
            )
        source_path = (config_root / source_path).resolve()

    external_registry = _load_external_profiles(source_path)
    for profile_name in sorted(external_registry):
        if profile_name in registry:
            raise ValueError(
                "External command profile "
                f"{profile_name!r} conflicts with built-in profile"
            )
    registry.update(external_registry)
    return registry, source_path


def canonicalize_shell_command(command: str) -> str:
    normalized = " ".join(command.strip().split())
    normalized = normalized.replace('"', "").replace("'", "")
    normalized = normalized.replace("\\", "/")
    return normalized


def collect_allowed_shell_commands(
    test_command: str | None,
    eval_command: str | None,
    profile_commands: tuple[str, ...],
) -> tuple[str, ...]:
    allowed_shell_commands: list[str] = []
    seen_allowed_commands: set[str] = set()

    def append_allowed(raw_command: str) -> None:
        canonical = canonicalize_shell_command(raw_command)
        if canonical and canonical not in seen_allowed_commands:
            seen_allowed_commands.add(canonical)
            allowed_shell_commands.append(canonical)

    if test_command:
        append_allowed(test_command)
    if eval_command:
        append_allowed(eval_command)
    for command in profile_commands:
        append_allowed(command)

    return tuple(allowed_shell_commands)


def resolve_command_profile(
    cfg: dict,
    *,
    config_root: Path | None = None,
) -> tuple[str, tuple[str, ...]]:
    profile_name = _normalize_profile_name(
        cfg.get("command_profile", DEFAULT_COMMAND_PROFILE)
    )
    registry, source_path = command_profile_registry(
        cfg,
        config_root=config_root,
    )
    if profile_name not in registry:
        available = ", ".join(sorted(registry))
        source_detail = (
            f" command_profiles_path={source_path}"
            if source_path is not None
            else ""
        )
        raise ValueError(
            "Unknown command_profile "
            f"{profile_name!r}. Available profiles: {available}."
            f"{source_detail}"
        )
    return profile_name, registry[profile_name]


def build_default_tool_policy(
    test_command: str | None,
    eval_command: str | None,
    allowed_shell_commands: tuple[str, ...],
) -> str:
    lines = [
        "Tool policy:",
        "- Only edit files inside the project root.",
        "- Use list_files/read_file/write_file for file operations.",
    ]
    if test_command is not None:
        lines.append("- Use run_test_command for tests.")
    if eval_command is not None:
        lines.append("- Use run_eval_command for eval.")
    if allowed_shell_commands:
        lines.append(
            "- Use list_allowed_shell_commands and "
            "run_allowlisted_shell for shell execution."
        )
    return "\n".join(lines)
