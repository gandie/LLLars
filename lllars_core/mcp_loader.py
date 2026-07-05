from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("MCP config must be a JSON object")
    return payload


def load_toolsets_from_mcp_config(
    mcp_config_path: Path,
    init_timeout_sec: float,
) -> list[object]:
    try:
        from fastmcp.client.transports import StdioTransport
        from pydantic_ai.mcp import MCPToolset
    except ImportError as exc:
        raise RuntimeError(
            "MCP support requires pydantic-ai/fastmcp MCP dependencies"
        ) from exc

    payload = _load_config(mcp_config_path)
    servers = payload.get("mcpServers")
    if not isinstance(servers, dict):
        raise ValueError("MCP config is missing object field mcpServers")

    toolsets: list[object] = []
    for server_name, server_cfg in servers.items():
        if not isinstance(server_cfg, dict):
            continue

        toolset: object | None = None
        url_raw = server_cfg.get("url")
        if isinstance(url_raw, str) and url_raw.strip():
            toolset = MCPToolset(
                url_raw.strip(),
                init_timeout=float(init_timeout_sec),
            )
        else:
            command_raw = server_cfg.get("command")
            if isinstance(command_raw, str) and command_raw.strip():
                args_raw = server_cfg.get("args", [])
                args: list[str] = []
                if isinstance(args_raw, list):
                    args = [str(item) for item in args_raw]
                transport = StdioTransport(
                    command=command_raw.strip(),
                    args=args,
                    keep_alive=False,
                )
                toolset = MCPToolset(
                    transport,
                    init_timeout=float(init_timeout_sec),
                )

        if toolset is None:
            continue

        toolsets.append(toolset.prefixed(str(server_name)))

    return toolsets
