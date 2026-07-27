from __future__ import annotations

from pydantic_ai import RunContext


def register_tools(agent, cfg, tool_error) -> None:
    _ = (cfg, tool_error)

    @agent.tool
    def plugin_echo(ctx: RunContext[object], message: str = "hello") -> str:
        _ = ctx
        return f"plugin-echo: {message.strip() or 'hello'}"
