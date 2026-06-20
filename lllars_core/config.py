from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "lllars.example.json"
DEFAULT_TIMEOUT_SEC = 600
DEFAULT_USAGE_TOOL_CALLS_LIMIT = 24
DEFAULT_AGENT_RETRIES_TOOLS = 1
DEFAULT_AGENT_RETRIES_OUTPUT = 1
DEFAULT_TOOL_TIMEOUT_SEC = 90.0


@dataclass(frozen=True)
class HarnessConfig:
    model: str
    provider_url: str
    project_root: Path
    test_command: str | None
    eval_command: str | None
    eval_expect_json: bool
    eval_success_pass_rate: float
    allowed_shell_commands: set[str]
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


def canonicalize_shell_command(command: str) -> str:
    normalized = " ".join(command.strip().split())
    normalized = normalized.replace('"', "").replace("'", "")
    normalized = normalized.replace("\\", "/")
    return normalized


def build_default_tool_policy(
    test_command: str | None,
    eval_command: str | None,
    allowed_shell_commands: set[str],
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
        lines.append("- run_shell is restricted to the config allowlist.")
    return "\n".join(lines)


def load_config(config_path: Path) -> HarnessConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("Top-level config must be a JSON object")

    model = str(cfg.get("model", "")).strip()
    provider_url = str(cfg.get("provider-url", "")).strip()
    if not model or not provider_url:
        raise ValueError("Config requires model and provider-url")

    project_root_raw = str(cfg.get("project_root", "")).strip()
    if not project_root_raw:
        raise ValueError("Config requires project_root")
    project_root = (ROOT / project_root_raw).resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise ValueError(f"Invalid project_root: {project_root}")

    commands = cfg.get("commands")
    if not isinstance(commands, dict):
        raise ValueError("Config requires commands object")

    test_command_raw = str(commands.get("test", "")).strip()
    test_command = test_command_raw if test_command_raw else None

    eval_command_raw = str(commands.get("eval", "")).strip()
    eval_command = eval_command_raw if eval_command_raw else None

    allowed_shell_commands: set[str] = set()
    if test_command:
        allowed_shell_commands.add(canonicalize_shell_command(test_command))
    if eval_command:
        allowed_shell_commands.add(canonicalize_shell_command(eval_command))

    extra = cfg.get("allowed_shell_commands", [])
    if isinstance(extra, list):
        for item in extra:
            text = str(item).strip()
            if text:
                allowed_shell_commands.add(canonicalize_shell_command(text))

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
    )
