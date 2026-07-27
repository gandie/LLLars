from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
DEFAULT_ENABLED_TOOL_GROUPS = ("native_files", "native_shell")

VALID_SERVICE_MODES = frozenset({"oneshot", "serve"})
VALID_QUEUE_BACKENDS = frozenset({"inmemory", "redis"})
VALID_NETWORK_POLICIES = frozenset({"inherit", "offline"})
VALID_SHELL_MODES = frozenset({"auto", "override"})
WINDOWS_SHELLS = ("pwsh", "powershell", "cmd")
POSIX_SHELLS = ("bash", "sh")
VALID_SHELL_OVERRIDES = frozenset(WINDOWS_SHELLS + POSIX_SHELLS)


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
    enabled_tool_groups: tuple[str, ...] = DEFAULT_ENABLED_TOOL_GROUPS
    plugin_tool_paths: tuple[str, ...] = ()


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
    enabled_tool_groups: tuple[str, ...]
    plugin_tool_paths: tuple[str, ...]
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
