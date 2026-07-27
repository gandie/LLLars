from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Literal

from lllars_core.tools.native import register_file_tools
from lllars_core.tools.shell_policy import register_shell_tools

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from lllars_core.config import HarnessConfig
    from lllars_core.tools.descriptors import AgentDeps


ToolGroupName = Literal[
    "native_files",
    "native_shell",
    "plugin_local",
    "mcp_toolsets",
]

DEFAULT_ENABLED_TOOL_GROUPS: tuple[ToolGroupName, ...] = (
    "native_files",
    "native_shell",
)

KNOWN_TOOL_GROUPS: tuple[ToolGroupName, ...] = (
    "native_files",
    "native_shell",
    "plugin_local",
    "mcp_toolsets",
)


def draft_tool_group_catalog() -> tuple[ToolGroupName, ...]:
    """Return the stable group names planned for configurable registry work."""
    return KNOWN_TOOL_GROUPS


def register_runtime_tools(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    register_file_tools(agent, cfg, tool_error)
    register_shell_tools(
        agent=agent,
        cfg=cfg,
        emit_thought=emit_thought,
        tool_error=tool_error,
        run_allowed_shell=run_allowed_shell,
    )
