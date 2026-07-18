from __future__ import annotations

from lllars_core.tools.descriptors import AgentDeps
from lllars_core.tools.native import register_file_tools, resolve_under
from lllars_core.tools.registry import register_runtime_tools
from lllars_core.tools.shell_policy import (
    make_allowed_shell_runner,
    register_shell_tools,
    runtime_tooling_instructions,
)

SYMBOL_MIGRATION_MAP = {
    "AgentDeps": "lllars_core.tools.descriptors.AgentDeps",
    "resolve_under": "lllars_core.tools.native.resolve_under",
    "register_file_tools": "lllars_core.tools.native.register_file_tools",
    "make_allowed_shell_runner": (
        "lllars_core.tools.shell_policy.make_allowed_shell_runner"
    ),
    "register_shell_tools": (
        "lllars_core.tools.shell_policy.register_shell_tools"
    ),
    "runtime_tooling_instructions": (
        "lllars_core.tools.shell_policy.runtime_tooling_instructions"
    ),
    "register_runtime_tools": (
        "lllars_core.tools.registry.register_runtime_tools"
    ),
}

__all__ = [
    "AgentDeps",
    "SYMBOL_MIGRATION_MAP",
    "make_allowed_shell_runner",
    "register_file_tools",
    "register_runtime_tools",
    "register_shell_tools",
    "resolve_under",
    "runtime_tooling_instructions",
]
