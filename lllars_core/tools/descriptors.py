from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentDeps:
    project_root: str
    os_name: str
    shell_name: str
    command_profile: str
    allowed_shell_commands: tuple[str, ...]
    has_test_command: bool
    has_eval_command: bool
