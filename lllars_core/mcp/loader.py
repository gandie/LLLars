from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("MCP config must be a JSON object")
    return payload


def _normalize_args(args_raw: object) -> list[str]:
    if not isinstance(args_raw, list):
        return []
    return [str(item) for item in args_raw]


def _build_toolset_from_server(
    server_cfg: dict[str, object],
    init_timeout_sec: float,
    stdio_transport_cls: object,
    mcp_toolset_cls: object,
) -> object | None:
    url_raw = server_cfg.get("url")
    if isinstance(url_raw, str) and url_raw.strip():
        return mcp_toolset_cls(
            url_raw.strip(),
            init_timeout=float(init_timeout_sec),
        )

    command_raw = server_cfg.get("command")
    if not isinstance(command_raw, str) or not command_raw.strip():
        return None

    transport = stdio_transport_cls(
        command=command_raw.strip(),
        args=_normalize_args(server_cfg.get("args", [])),
        keep_alive=False,
    )
    return mcp_toolset_cls(
        transport,
        init_timeout=float(init_timeout_sec),
    )


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
        toolset = _build_toolset_from_server(
            server_cfg,
            init_timeout_sec,
            StdioTransport,
            MCPToolset,
        )
        if toolset is not None:
            toolsets.append(toolset.prefixed(str(server_name)))
    return toolsets
