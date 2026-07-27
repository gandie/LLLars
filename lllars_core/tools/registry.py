from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Literal

from lllars_core.tools.native import register_file_tools
from lllars_core.tools.plugins import register_local_plugin_tools
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
    enabled_groups = tuple(
        getattr(cfg, "enabled_tool_groups", DEFAULT_ENABLED_TOOL_GROUPS)
    )
    for group_name in enabled_groups:
        if group_name == "native_files":
            register_file_tools(agent, cfg, tool_error)
            continue

        if group_name == "native_shell":
            register_shell_tools(
                agent=agent,
                cfg=cfg,
                emit_thought=emit_thought,
                tool_error=tool_error,
                run_allowed_shell=run_allowed_shell,
            )
            continue

        if group_name == "plugin_local":
            register_local_plugin_tools(agent, cfg, tool_error)
            continue

        if group_name == "mcp_toolsets":
            # MCP tools are loaded as toolsets during agent construction.
            continue

        raise ValueError(f"Unknown enabled tool group: {group_name}")
