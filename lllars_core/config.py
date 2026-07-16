from __future__ import annotations

import json
import platform
import warnings
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
DEFAULT_SERVICE_HOST = "127.0.0.1"
DEFAULT_SERVICE_PORT = 8000
DEFAULT_SERVICE_WORKERS = 1
DEFAULT_QUEUE_BACKEND = "inmemory"
DEFAULT_NETWORK_POLICY = "inherit"
DEFAULT_COMMAND_PROFILE = "none"
DEFAULT_SHELL_MODE = "auto"

VALID_SERVICE_MODES = frozenset({"oneshot", "serve"})
VALID_QUEUE_BACKENDS = frozenset({"inmemory", "redis"})
VALID_NETWORK_POLICIES = frozenset({"inherit", "offline"})
VALID_SHELL_MODES = frozenset({"auto", "override"})
WINDOWS_SHELLS = ("pwsh", "powershell", "cmd")
POSIX_SHELLS = ("bash", "sh")
VALID_SHELL_OVERRIDES = frozenset(WINDOWS_SHELLS + POSIX_SHELLS)
COMMAND_PROFILE_REGISTRY = {
    "none": (),
    "python-playground": (
        "python main.py",
        "python test.py",
    ),
}


LEGACY_SERVICE_KEYS = frozenset(
    {
        "service_mode",
        "service_host",
        "service_port",
        "service_workers",
        "mount_work_root",
        "mount_config_root",
        "mount_artifacts_root",
        "queue_backend",
        "network_policy",
    }
)

LEGACY_RUN_KEYS = frozenset(
    {
        "model",
        "provider-url",
        "provider_url",
        "project_root",
        "commands",
        "command_profile",
        "system-prompt",
        "tool-policy",
        "eval_expect_json",
        "eval_success_pass_rate",
        "usage_request_limit",
        "usage_tool_calls_limit",
        "usage_input_tokens_limit",
        "usage_output_tokens_limit",
        "usage_total_tokens_limit",
        "usage_count_tokens_before_request",
        "agent_retries_tools",
        "agent_retries_output",
        "tool_timeout_sec",
        "max_concurrency",
        "instrumentation_enabled",
        "instrumentation_include_content",
        "skills_enabled",
        "skills_glob",
        "skills_defer_loading",
        "skills_require_description",
        "mcp_enabled",
        "mcp_config_path",
        "mcp_init_timeout_sec",
        "shell_mode",
        "shell_override",
    }
)

LEGACY_TOP_LEVEL_KEYS = LEGACY_SERVICE_KEYS | LEGACY_RUN_KEYS

SERVICE_SPLIT_TO_LEGACY_KEY = {
    "mode": "service_mode",
    "host": "service_host",
    "port": "service_port",
    "workers": "service_workers",
    "mount_work_root": "mount_work_root",
    "mount_config_root": "mount_config_root",
    "mount_artifacts_root": "mount_artifacts_root",
    "queue_backend": "queue_backend",
    "network_policy": "network_policy",
}

ENV_TO_CONFIG_KEY = {
    "MODEL": "model",
    "PROVIDER_URL": "provider-url",
    "OLLAMA_BASE_URL": "provider-url",
    "PROJECT_ROOT": "project_root",
    "COMMAND_PROFILE": "command_profile",
    "SYSTEM_PROMPT": "system-prompt",
    "TOOL_POLICY": "tool-policy",
    "EVAL_EXPECT_JSON": "eval_expect_json",
    "EVAL_SUCCESS_PASS_RATE": "eval_success_pass_rate",
    "USAGE_REQUEST_LIMIT": "usage_request_limit",
    "USAGE_TOOL_CALLS_LIMIT": "usage_tool_calls_limit",
    "USAGE_INPUT_TOKENS_LIMIT": "usage_input_tokens_limit",
    "USAGE_OUTPUT_TOKENS_LIMIT": "usage_output_tokens_limit",
    "USAGE_TOTAL_TOKENS_LIMIT": "usage_total_tokens_limit",
    "USAGE_COUNT_TOKENS_BEFORE_REQUEST": "usage_count_tokens_before_request",
    "AGENT_RETRIES_TOOLS": "agent_retries_tools",
    "AGENT_RETRIES_OUTPUT": "agent_retries_output",
    "TOOL_TIMEOUT_SEC": "tool_timeout_sec",
    "MAX_CONCURRENCY": "max_concurrency",
    "INSTRUMENTATION_ENABLED": "instrumentation_enabled",
    "INSTRUMENTATION_INCLUDE_CONTENT": "instrumentation_include_content",
    "SKILLS_ENABLED": "skills_enabled",
    "SKILLS_GLOB": "skills_glob",
    "SKILLS_DEFER_LOADING": "skills_defer_loading",
    "SKILLS_REQUIRE_DESCRIPTION": "skills_require_description",
    "MCP_ENABLED": "mcp_enabled",
    "MCP_CONFIG_PATH": "mcp_config_path",
    "MCP_INIT_TIMEOUT_SEC": "mcp_init_timeout_sec",
    "SERVICE_MODE": "service_mode",
    "LLLARS_HOST": "service_host",
    "SERVICE_HOST": "service_host",
    "LLLARS_PORT": "service_port",
    "SERVICE_PORT": "service_port",
    "LLLARS_WORKERS": "service_workers",
    "SERVICE_WORKERS": "service_workers",
    "QUEUE_BACKEND": "queue_backend",
    "NETWORK_POLICY": "network_policy",
    "MOUNT_WORK_ROOT": "mount_work_root",
    "MOUNT_CONFIG_ROOT": "mount_config_root",
    "MOUNT_ARTIFACTS_ROOT": "mount_artifacts_root",
}


@dataclass(frozen=True)
class ServiceConfig:
    mode: str
    host: str
    port: int
    workers: int
    mount_work_root: Path
    mount_config_root: Path
    mount_artifacts_root: Path
    queue_backend: str
    network_policy: str


@dataclass(frozen=True)
class RunConfig:
    model: str
    provider_url: str
    project_root: Path
    commands: dict[str, str] | None = None
    test_command: str | None = None
    eval_command: str | None = None
    command_profile: str = DEFAULT_COMMAND_PROFILE
    eval_expect_json: bool | None = None
    eval_success_pass_rate: float | None = None
    system_prompt: str | None = None
    tool_policy: str | None = None
    usage_request_limit: int | None = None
    usage_tool_calls_limit: int | None = None
    usage_input_tokens_limit: int | None = None
    usage_output_tokens_limit: int | None = None
    usage_total_tokens_limit: int | None = None
    usage_count_tokens_before_request: bool | None = None
    agent_retries_tools: int | None = None
    agent_retries_output: int | None = None
    tool_timeout_sec: float | None = None
    max_concurrency: int | None = None
    instrumentation_enabled: bool | None = None
    instrumentation_include_content: bool | None = None
    skills_enabled: bool | None = None
    skills_glob: str | None = None
    skills_defer_loading: bool | None = None
    skills_require_description: bool | None = None
    mcp_enabled: bool | None = None
    mcp_config_path: Path | None = None
    mcp_init_timeout_sec: float | None = None
    shell_mode: str = DEFAULT_SHELL_MODE
    shell_override: str | None = None


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
    shell_mode: str
    shell_override: str | None
    service_mode: str
    service_host: str
    service_port: int
    service_workers: int
    mount_work_root: Path
    mount_config_root: Path
    mount_artifacts_root: Path
    queue_backend: str
    network_policy: str
    command_profile: str
    service: ServiceConfig
    run: RunConfig


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


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file():
        raise ValueError(f"Invalid env_file path: {path}")

    env: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _build_env_layer(raw_env: dict[str, str]) -> dict[str, object]:
    layer: dict[str, object] = {}
    commands: dict[str, str] = {}

    test_command = raw_env.get("TEST_COMMAND", "").strip()
    eval_command = raw_env.get("EVAL_COMMAND", "").strip()
    if test_command:
        commands["test"] = test_command
    if eval_command:
        commands["eval"] = eval_command
    if commands:
        layer["commands"] = commands

    for env_key, cfg_key in ENV_TO_CONFIG_KEY.items():
        if env_key in raw_env:
            layer[cfg_key] = raw_env[env_key]
    return layer


def _flatten_split_config(cfg: dict) -> dict:
    has_service = "service" in cfg
    has_run = "run" in cfg

    if not has_service and not has_run:
        legacy_present = [
            key for key in cfg.keys() if key in LEGACY_TOP_LEVEL_KEYS
        ]
        if legacy_present:
            warnings.warn(
                "Legacy top-level config fields are deprecated. "
                "Use split service/run objects.",
                DeprecationWarning,
                stacklevel=2,
            )
        return dict(cfg)

    service = cfg.get("service", {})
    run = cfg.get("run", {})
    if has_service and not isinstance(service, dict):
        raise ValueError("Config service must be an object")
    if has_run and not isinstance(run, dict):
        raise ValueError("Config run must be an object")

    mixed_legacy = [
        key for key in cfg.keys() if key in LEGACY_TOP_LEVEL_KEYS
    ]
    if mixed_legacy:
        mixed_text = ", ".join(sorted(mixed_legacy))
        raise ValueError(
            "Config cannot mix split and legacy fields: "
            f"{mixed_text}"
        )

    flattened: dict[str, object] = {}
    for split_key, legacy_key in SERVICE_SPLIT_TO_LEGACY_KEY.items():
        if split_key in service:
            flattened[legacy_key] = service[split_key]

    flattened_run = dict(run)
    if "provider_url" in flattened_run and "provider-url" not in flattened_run:
        flattened_run["provider-url"] = flattened_run.pop("provider_url")
    flattened.update(flattened_run)
    return flattened


def _merge_layers(
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


def _as_bool(raw: object, default: bool) -> bool:
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
    commands = cfg.get("commands", {})
    if commands is None:
        commands = {}
    if not isinstance(commands, dict):
        raise ValueError("Config requires commands object")

    test_command_raw = str(commands.get("test", "")).strip()
    eval_command_raw = str(commands.get("eval", "")).strip()

    test_command = test_command_raw if test_command_raw else None
    eval_command = eval_command_raw if eval_command_raw else None
    return test_command, eval_command


def _collect_allowed_shell_commands(
    test_command: str | None,
    eval_command: str | None,
    profile_commands: tuple[str, ...],
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

    for command in profile_commands:
        _append_allowed(command)

    return tuple(allowed_shell_commands_list)


def _resolve_command_profile(cfg: dict) -> tuple[str, tuple[str, ...]]:
    profile_name = str(
        cfg.get("command_profile", DEFAULT_COMMAND_PROFILE)
    ).strip().lower()
    if profile_name not in COMMAND_PROFILE_REGISTRY:
        available = ", ".join(sorted(COMMAND_PROFILE_REGISTRY))
        raise ValueError(
            "Unknown command_profile "
            f"{profile_name!r}. Available profiles: {available}"
        )
    return profile_name, COMMAND_PROFILE_REGISTRY[profile_name]


def _resolve_shell_policy(cfg: dict) -> tuple[str, str | None]:
    shell_mode = _validate_choice(
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

    supported = (
        WINDOWS_SHELLS
        if platform.system() == "Windows"
        else POSIX_SHELLS
    )
    if shell_override is not None and shell_override not in supported:
        supported_text = ", ".join(supported)
        raise ValueError(
            f"Unsupported shell_override {shell_override!r} on this platform. "
            f"Supported values: {supported_text}"
        )

    return shell_mode, shell_override


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


def load_config(
    config_path: Path,
    *,
    overrides: dict[str, object] | None = None,
) -> HarnessConfig:
    json_cfg = _load_config_object(config_path)
    config_root = config_path.parent.resolve()

    env_layer: dict[str, object] = {}
    env_file_raw = str(json_cfg.get("env_file", "")).strip()
    if env_file_raw:
        env_file_path = Path(env_file_raw)
        if not env_file_path.is_absolute():
            env_file_path = (config_root / env_file_path).resolve()
        env_layer = _build_env_layer(_parse_env_file(env_file_path))

    json_layer = _flatten_split_config(json_cfg)
    defaults: dict[str, object] = {
        "service_mode": DEFAULT_SERVICE_MODE,
        "service_host": DEFAULT_SERVICE_HOST,
        "service_port": DEFAULT_SERVICE_PORT,
        "service_workers": DEFAULT_SERVICE_WORKERS,
        "queue_backend": DEFAULT_QUEUE_BACKEND,
        "network_policy": DEFAULT_NETWORK_POLICY,
        "command_profile": DEFAULT_COMMAND_PROFILE,
        "shell_mode": DEFAULT_SHELL_MODE,
        "shell_override": "",
    }
    cfg = _merge_layers(defaults, env_layer, json_layer, overrides)

    service_mode = _validate_choice(
        cfg,
        "service_mode",
        default=DEFAULT_SERVICE_MODE,
        valid_values=VALID_SERVICE_MODES,
    )

    model_raw = str(cfg.get("model", "")).strip()
    provider_url_raw = str(cfg.get("provider-url", "")).strip()
    project_root_raw = str(cfg.get("project_root", "")).strip()
    run_configured = bool(
        model_raw and provider_url_raw and project_root_raw
    )

    if service_mode != "serve" and not run_configured:
        raise ValueError("Config requires model and provider-url")

    model = model_raw
    provider_url = provider_url_raw
    test_command, eval_command = _load_commands(cfg)
    command_profile, profile_commands = _resolve_command_profile(cfg)
    shell_mode, shell_override = _resolve_shell_policy(cfg)
    allowed_shell_commands = _collect_allowed_shell_commands(
        test_command,
        eval_command,
        profile_commands,
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

    skills_enabled = _as_bool(cfg.get("skills_enabled", False), False)
    skills_glob = str(cfg.get("skills_glob", "")).strip()
    skills_defer_loading = _as_bool(
        cfg.get("skills_defer_loading", True),
        True,
    )
    skills_require_description = _as_bool(
        cfg.get("skills_require_description", True),
        True,
    )

    if skills_enabled and not skills_glob:
        raise ValueError(
            "skills_enabled is true but skills_glob is empty"
        )

    mcp_enabled = _as_bool(cfg.get("mcp_enabled", False), False)
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

    service_host = str(
        cfg.get("service_host", DEFAULT_SERVICE_HOST)
    ).strip() or DEFAULT_SERVICE_HOST

    def _positive_int(key: str, default: int) -> int:
        raw = cfg.get(key, default)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        if value <= 0:
            return default
        return value

    service_port = _positive_int("service_port", DEFAULT_SERVICE_PORT)
    service_workers = _positive_int(
        "service_workers", DEFAULT_SERVICE_WORKERS
    )

    mount_work_root = _resolve_mount_root(
        cfg,
        "mount_work_root",
        config_root=config_root,
        default_path=(config_root / project_root_raw).resolve()
        if project_root_raw
        else config_root,
    )
    if project_root_raw:
        project_root = resolve_project_root(
            project_root_raw,
            config_root=config_root,
            mount_work_root=mount_work_root,
        )
    else:
        project_root = mount_work_root
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
        eval_expect_json=_as_bool(cfg.get("eval_expect_json", True), True),
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
        usage_count_tokens_before_request=_as_bool(
            cfg.get("usage_count_tokens_before_request", False),
            False,
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
        instrumentation_enabled=_as_bool(
            cfg.get("instrumentation_enabled", False),
            False,
        ),
        instrumentation_include_content=_as_bool(
            cfg.get("instrumentation_include_content", False),
            False,
        ),
        skills_enabled=skills_enabled,
        skills_glob=skills_glob,
        skills_defer_loading=skills_defer_loading,
        skills_require_description=skills_require_description,
        mcp_enabled=mcp_enabled,
        mcp_config_path=mcp_config_path,
        mcp_init_timeout_sec=mcp_init_timeout_sec,
        shell_mode=shell_mode,
        shell_override=shell_override,
        service_mode=service_mode,
        service_host=service_host,
        service_port=service_port,
        service_workers=service_workers,
        mount_work_root=mount_work_root,
        mount_config_root=mount_config_root,
        mount_artifacts_root=mount_artifacts_root,
        queue_backend=queue_backend,
        network_policy=network_policy,
        command_profile=command_profile,
        service=ServiceConfig(
            mode=service_mode,
            host=service_host,
            port=service_port,
            workers=service_workers,
            mount_work_root=mount_work_root,
            mount_config_root=mount_config_root,
            mount_artifacts_root=mount_artifacts_root,
            queue_backend=queue_backend,
            network_policy=network_policy,
        ),
        run=RunConfig(
            model=model,
            provider_url=provider_url,
            project_root=project_root,
            commands={
                key: value
                for key, value in {
                    "test": test_command,
                    "eval": eval_command,
                }.items()
                if value is not None
            },
            test_command=test_command,
            eval_command=eval_command,
            command_profile=command_profile,
            eval_expect_json=_as_bool(
                cfg.get("eval_expect_json", True),
                True,
            ),
            eval_success_pass_rate=float(
                cfg.get("eval_success_pass_rate", 100.0)
            ),
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
            usage_count_tokens_before_request=_as_bool(
                cfg.get("usage_count_tokens_before_request", False),
                False,
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
            instrumentation_enabled=_as_bool(
                cfg.get("instrumentation_enabled", False),
                False,
            ),
            instrumentation_include_content=_as_bool(
                cfg.get("instrumentation_include_content", False),
                False,
            ),
            skills_enabled=skills_enabled,
            skills_glob=skills_glob,
            skills_defer_loading=skills_defer_loading,
            skills_require_description=skills_require_description,
            mcp_enabled=mcp_enabled,
            mcp_config_path=mcp_config_path,
            mcp_init_timeout_sec=mcp_init_timeout_sec,
            shell_mode=shell_mode,
            shell_override=shell_override,
        ),
    )
