from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "lllars.example.json"
DEFAULT_TIMEOUT_SEC = 600
DEFAULT_TOOL_CALL_BUDGET = 24
DEFAULT_FILE_READ_CHAR_LIMIT = 20000


@dataclass(frozen=True)
class HarnessConfig:
    model: str
    provider_url: str
    project_root: Path
    test_command: str
    eval_command: str | None
    eval_expect_json: bool
    eval_success_pass_rate: float
    allowed_shell_commands: set[str]
    system_prompt: str
    tool_policy: str
    tool_call_budget: int
    file_read_char_limit: int


def canonicalize_shell_command(command: str) -> str:
    normalized = " ".join(command.strip().split())
    normalized = normalized.replace('"', "").replace("'", "")
    normalized = normalized.replace("\\", "/")
    return normalized


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

    test_command = str(commands.get("test", "")).strip()
    if not test_command:
        raise ValueError("Config requires commands.test")

    eval_command_raw = str(commands.get("eval", "")).strip()
    eval_command = eval_command_raw if eval_command_raw else None

    allowed_shell_commands = {canonicalize_shell_command(test_command)}
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
        tool_policy = (
            "Tool policy:\n"
            "- Only edit files inside the project root.\n"
            "- Use list_files/read_file/write_file for file operations.\n"
            "- Use run_test_command for tests and run_eval_command for eval.\n"
            "- run_shell is restricted to the config allowlist.\n"
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
        tool_call_budget=int(
            cfg.get("tool_call_budget", DEFAULT_TOOL_CALL_BUDGET)
        ),
        file_read_char_limit=int(
            cfg.get("file_read_char_limit", DEFAULT_FILE_READ_CHAR_LIMIT)
        ),
    )
