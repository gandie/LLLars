from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Literal

from lllars_core.tools.native import register_file_read_tools
from lllars_core.tools.native import register_file_write_tools
from lllars_core.tools.plugins import register_local_plugin_tools
from lllars_core.tools.shell_policy import register_shell_tools

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from lllars_core.config import HarnessConfig
    from lllars_core.tools.descriptors import AgentDeps


ToolGroupName = Literal[
    "native_files",
    "native_file_read",
    "native_file_write",
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
    "native_file_read",
    "native_file_write",
    "native_shell",
    "plugin_local",
    "mcp_toolsets",
)


def draft_tool_group_catalog() -> tuple[ToolGroupName, ...]:
    """Return the stable group names planned for configurable registry work."""
    return KNOWN_TOOL_GROUPS


def _update_file_group_flags(
    group_name: str,
    *,
    enable_file_read: bool,
    enable_file_write: bool,
) -> tuple[bool, bool, bool]:
    if group_name == "native_files":
        return True, True, True
    if group_name == "native_file_read":
        return True, True, enable_file_write
    if group_name == "native_file_write":
        return True, enable_file_read, True
    return False, enable_file_read, enable_file_write


def _register_non_file_group(
    group_name: str,
    *,
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
) -> None:
    if group_name == "native_shell":
        register_shell_tools(
            agent=agent,
            cfg=cfg,
            emit_thought=emit_thought,
            tool_error=tool_error,
            run_allowed_shell=run_allowed_shell,
        )
        return

    if group_name == "plugin_local":
        register_local_plugin_tools(agent, cfg, tool_error)
        return

    if group_name == "mcp_toolsets":
        # MCP tools are loaded as toolsets during agent construction.
        return

    raise ValueError(f"Unknown enabled tool group: {group_name}")


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
    enable_file_read = False
    enable_file_write = False
    for group_name in enabled_groups:
        handled, enable_file_read, enable_file_write = _update_file_group_flags(
            group_name,
            enable_file_read=enable_file_read,
            enable_file_write=enable_file_write,
        )
        if handled:
            continue
        _register_non_file_group(
            group_name,
            agent=agent,
            cfg=cfg,
            emit_thought=emit_thought,
            tool_error=tool_error,
            run_allowed_shell=run_allowed_shell,
        )

    if enable_file_read:
        register_file_read_tools(agent, cfg, tool_error)
    if enable_file_write:
        register_file_write_tools(agent, cfg, tool_error)
