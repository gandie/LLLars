from __future__ import annotations

from lllars_core.config.runtime_section import as_bool
from lllars_core.config.tools_section import build_default_tool_policy


def runtime_text_fields(
    cfg: dict,
    test_command: str | None,
    eval_command: str | None,
    allowed_shell_commands: tuple[str, ...],
) -> tuple[str, str, bool, float]:
    system_prompt = str(cfg.get("system_prompt", "")).strip()
    if not system_prompt:
        system_prompt = "You are a coding agent."

    tool_policy = str(cfg.get("tool_policy", "")).strip()
    if not tool_policy:
        tool_policy = build_default_tool_policy(
            test_command=test_command,
            eval_command=eval_command,
            allowed_shell_commands=allowed_shell_commands,
        )

    eval_expect_json = as_bool(cfg.get("eval_expect_json", True), True)
    eval_success_pass_rate = float(cfg.get("eval_success_pass_rate", 100.0))
    return (
        system_prompt,
        tool_policy,
        eval_expect_json,
        eval_success_pass_rate,
    )