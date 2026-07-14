from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from lllars_core.runtime_guard import (
    resolve_mount_directory,
    resolve_project_root,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "lllars.example.json"
DEFAULT_TIMEOUT_SEC = 600
DEFAULT_USAGE_TOOL_CALLS_LIMIT = 24
DEFAULT_AGENT_RETRIES_TOOLS = 1
DEFAULT_AGENT_RETRIES_OUTPUT = 1
DEFAULT_TOOL_TIMEOUT_SEC = 90.0
DEFAULT_MCP_INIT_TIMEOUT_SEC = 60.0
DEFAULT_SERVICE_MODE = "oneshot"
DEFAULT_QUEUE_BACKEND = "inmemory"
DEFAULT_NETWORK_POLICY = "inherit"

VALID_SERVICE_MODES = frozenset({"oneshot", "serve"})
VALID_QUEUE_BACKENDS = frozenset({"inmemory", "redis"})
VALID_NETWORK_POLICIES = frozenset({"inherit", "offline"})


@dataclass(frozen=True)
class HarnessConfig:
    model: str
    provider_url: str
    project_root: Path
    test_command: str | None
    eval_command: str | None
    eval_expect_json: bool
    eval_success_pass_rate: float
    allowed_shell_commands: tuple[str, ...]
    system_prompt: str
    tool_policy: str
    usage_request_limit: int | None
    usage_tool_calls_limit: int | None
    usage_input_tokens_limit: int | None
    usage_output_tokens_limit: int | None
    usage_total_tokens_limit: int | None
    usage_count_tokens_before_request: bool
    agent_retries_tools: int
    agent_retries_output: int
    tool_timeout_sec: float | None
    max_concurrency: int | None
    instrumentation_enabled: bool
    instrumentation_include_content: bool
    skills_enabled: bool
    skills_glob: str
    skills_defer_loading: bool
    skills_require_description: bool
    mcp_enabled: bool
    mcp_config_path: Path | None
    mcp_init_timeout_sec: float
    service_mode: str
    mount_work_root: Path
    mount_config_root: Path
    mount_artifacts_root: Path
    queue_backend: str
    network_policy: str


def canonicalize_shell_command(command: str) -> str:
    normalized = " ".join(command.strip().split())
    normalized = normalized.replace('"', "").replace("'", "")
    normalized = normalized.replace("\\", "/")
    return normalized


def _load_config_object(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("Top-level config must be a JSON object")
    return cfg


def _require_non_empty_str(
    cfg: dict,
    key: str,
    error_message: str,
) -> str:
    value = str(cfg.get(key, "")).strip()
    if not value:
        raise ValueError(error_message)
    return value


def _resolve_mount_root(
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


def _validate_choice(
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


def _load_commands(cfg: dict) -> tuple[str | None, str | None]:
    commands = cfg.get("commands")
    if not isinstance(commands, dict):
        raise ValueError("Config requires commands object")

    test_command_raw = str(commands.get("test", "")).strip()
    eval_command_raw = str(commands.get("eval", "")).strip()

    test_command = test_command_raw if test_command_raw else None
    eval_command = eval_command_raw if eval_command_raw else None
    return test_command, eval_command


def _collect_allowed_shell_commands(
    cfg: dict,
    test_command: str | None,
    eval_command: str | None,
) -> tuple[str, ...]:
    allowed_shell_commands_list: list[str] = []
    seen_allowed_commands: set[str] = set()

    def _append_allowed(raw_command: str) -> None:
        canonical = canonicalize_shell_command(raw_command)
        if canonical and canonical not in seen_allowed_commands:
            seen_allowed_commands.add(canonical)
            allowed_shell_commands_list.append(canonical)

    if test_command:
        _append_allowed(test_command)
    if eval_command:
        _append_allowed(eval_command)

    extra = cfg.get("allowed_shell_commands", [])
    if isinstance(extra, list):
        for item in extra:
            text = str(item).strip()
            if text:
                _append_allowed(text)

    return tuple(allowed_shell_commands_list)


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


def load_config(config_path: Path) -> HarnessConfig:
    cfg = _load_config_object(config_path)
    config_root = config_path.parent.resolve()

    model = _require_non_empty_str(
        cfg,
        "model",
        "Config requires model and provider-url",
    )
    provider_url = _require_non_empty_str(
        cfg,
        "provider-url",
        "Config requires model and provider-url",
    )
    project_root_raw = _require_non_empty_str(
        cfg,
        "project_root",
        "Config requires project_root",
    )
    test_command, eval_command = _load_commands(cfg)
    allowed_shell_commands = _collect_allowed_shell_commands(
        cfg,
        test_command,
        eval_command,
    )

    system_prompt = str(cfg.get("system-prompt", "")).strip()
    if not system_prompt:
        system_prompt = "You are a coding agent."

    tool_policy = str(cfg.get("tool-policy", "")).strip()
    if not tool_policy:
        tool_policy = build_default_tool_policy(
            test_command=test_command,
            eval_command=eval_command,
            allowed_shell_commands=allowed_shell_commands,
        )

    def _optional_int(key: str, default: int | None) -> int | None:
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

    def _optional_float(key: str, default: float | None) -> float | None:
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

    def _non_negative_int(key: str, default: int) -> int:
        raw = cfg.get(key, default)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        return max(0, value)

    skills_enabled = bool(cfg.get("skills_enabled", False))
    skills_glob = str(cfg.get("skills_glob", "")).strip()
    skills_defer_loading = bool(cfg.get("skills_defer_loading", True))
    skills_require_description = bool(
        cfg.get("skills_require_description", True)
    )

    if skills_enabled and not skills_glob:
        raise ValueError(
            "skills_enabled is true but skills_glob is empty"
        )

    mcp_enabled = bool(cfg.get("mcp_enabled", False))
    mcp_config_raw = str(cfg.get("mcp_config_path", "")).strip()
    mcp_config_path: Path | None = None
    if mcp_config_raw:
        mcp_config_path = (ROOT / mcp_config_raw).resolve()

    mcp_init_timeout_raw = cfg.get(
        "mcp_init_timeout_sec", DEFAULT_MCP_INIT_TIMEOUT_SEC
    )
    try:
        mcp_init_timeout_sec = float(mcp_init_timeout_raw)
    except (TypeError, ValueError):
        mcp_init_timeout_sec = DEFAULT_MCP_INIT_TIMEOUT_SEC
    if mcp_init_timeout_sec <= 0:
        mcp_init_timeout_sec = DEFAULT_MCP_INIT_TIMEOUT_SEC

    if mcp_enabled:
        if mcp_config_path is None:
            raise ValueError(
                "mcp_enabled is true but mcp_config_path is empty"
            )
        if not mcp_config_path.exists() or not mcp_config_path.is_file():
            raise ValueError(
                f"Invalid mcp_config_path: {mcp_config_path}"
            )

    service_mode = _validate_choice(
        cfg,
        "service_mode",
        default=DEFAULT_SERVICE_MODE,
        valid_values=VALID_SERVICE_MODES,
    )
    queue_backend = _validate_choice(
        cfg,
        "queue_backend",
        default=DEFAULT_QUEUE_BACKEND,
        valid_values=VALID_QUEUE_BACKENDS,
    )
    network_policy = _validate_choice(
        cfg,
        "network_policy",
        default=DEFAULT_NETWORK_POLICY,
        valid_values=VALID_NETWORK_POLICIES,
    )

    mount_work_root = _resolve_mount_root(
        cfg,
        "mount_work_root",
        config_root=config_root,
        default_path=(config_root / project_root_raw).resolve(),
    )
    project_root = resolve_project_root(
        project_root_raw,
        config_root=config_root,
        mount_work_root=mount_work_root,
    )
    mount_config_root = _resolve_mount_root(
        cfg,
        "mount_config_root",
        config_root=config_root,
        default_path=config_path.parent.resolve(),
    )
    mount_artifacts_root = _resolve_mount_root(
        cfg,
        "mount_artifacts_root",
        config_root=config_root,
        default_path=ROOT,
    )

    return HarnessConfig(
        model=model,
        provider_url=provider_url,
        project_root=project_root,
        test_command=test_command,
        eval_command=eval_command,
        eval_expect_json=bool(cfg.get("eval_expect_json", True)),
        eval_success_pass_rate=float(cfg.get("eval_success_pass_rate", 100.0)),
        allowed_shell_commands=allowed_shell_commands,
        system_prompt=system_prompt,
        tool_policy=tool_policy,
        usage_request_limit=_optional_int("usage_request_limit", None),
        usage_tool_calls_limit=_optional_int(
            "usage_tool_calls_limit",
            DEFAULT_USAGE_TOOL_CALLS_LIMIT,
        ),
        usage_input_tokens_limit=_optional_int(
            "usage_input_tokens_limit", None
        ),
        usage_output_tokens_limit=_optional_int(
            "usage_output_tokens_limit", None
        ),
        usage_total_tokens_limit=_optional_int(
            "usage_total_tokens_limit", None
        ),
        usage_count_tokens_before_request=bool(
            cfg.get("usage_count_tokens_before_request", False)
        ),
        agent_retries_tools=_non_negative_int(
            "agent_retries_tools", DEFAULT_AGENT_RETRIES_TOOLS
        ),
        agent_retries_output=_non_negative_int(
            "agent_retries_output", DEFAULT_AGENT_RETRIES_OUTPUT
        ),
        tool_timeout_sec=_optional_float(
            "tool_timeout_sec", DEFAULT_TOOL_TIMEOUT_SEC
        ),
        max_concurrency=_optional_int("max_concurrency", None),
        instrumentation_enabled=bool(
            cfg.get("instrumentation_enabled", False)
        ),
        instrumentation_include_content=bool(
            cfg.get("instrumentation_include_content", False)
        ),
        skills_enabled=skills_enabled,
        skills_glob=skills_glob,
        skills_defer_loading=skills_defer_loading,
        skills_require_description=skills_require_description,
        mcp_enabled=mcp_enabled,
        mcp_config_path=mcp_config_path,
        mcp_init_timeout_sec=mcp_init_timeout_sec,
        service_mode=service_mode,
        mount_work_root=mount_work_root,
        mount_config_root=mount_config_root,
        mount_artifacts_root=mount_artifacts_root,
        queue_backend=queue_backend,
        network_policy=network_policy,
    )
