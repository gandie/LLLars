from __future__ import annotations

from lllars_core.tools.descriptors import AgentDeps
from lllars_core.tools.native import register_file_tools, resolve_under
from lllars_core.tools.registry import register_runtime_tools
from lllars_core.tools.shell_policy import (
    make_allowed_shell_runner,
    register_shell_tools,
    runtime_tooling_instructions,
)

__all__ = [
    "AgentDeps",
    "make_allowed_shell_runner",
    "register_file_tools",
    "register_runtime_tools",
    "register_shell_tools",
    "resolve_under",
    "runtime_tooling_instructions",
]
