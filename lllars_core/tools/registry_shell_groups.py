from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from lllars_core.tools.plugins import register_local_plugin_tools
from lllars_core.tools.shell_policy import register_shell_tools

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from lllars_core.config import HarnessConfig
    from lllars_core.tools.descriptors import AgentDeps


def register_non_file_group(
    group_name: str,
    *,
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    emit_thought: Callable[[str], None],
    tool_error: Callable[[str, str, str | None], str],
    run_allowed_shell: Callable[[str, int], str],
    run_unrestricted_shell: Callable[[str, int], str] | None,
) -> None:
    if group_name in {"native_shell", "native_shell_yolo"}:
        register_shell_tools(
            agent=agent,
            cfg=cfg,
            emit_thought=emit_thought,
            tool_error=tool_error,
            run_allowed_shell=run_allowed_shell,
            run_unrestricted_shell=(
                run_unrestricted_shell
                if group_name == "native_shell_yolo"
                else None
            ),
        )
        return

    if group_name == "plugin_local":
        register_local_plugin_tools(agent, cfg, tool_error)
        return

    if group_name in {"mcp_toolsets", "native_web_research"}:
        return

    raise ValueError(f"Unknown enabled tool group: {group_name}")
