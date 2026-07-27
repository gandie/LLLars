from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Callable

from lllars_core.config import HarnessConfig
from lllars_core.mcp.capabilities import (
    capability_summary_lines,
    healthy_server_names,
    negotiate_server_capabilities,
)
from lllars_core.mcp.loader import load_toolsets_from_mcp_config
from lllars_core.mcp.runtime import (
    probe_server_connectivity_with_hard_timeout,
    read_servers,
)


def _emit_mcp_lines(
    emit_thought: Callable[[str], None],
    lines: list[str],
) -> None:
    for line in lines:
        emit_thought(f"[mcp] {line}")


def _healthy_server_subset(
    servers: dict[str, dict],
    healthy_servers: list[str],
) -> dict[str, dict]:
    return {name: servers[name] for name in healthy_servers}


def _warn_and_empty(
    emit_thought: Callable[[str], None],
    message: str,
) -> list[object]:
    emit_thought(f"[mcp] warning: {message}")
    return []


def _negotiate_runtime_capabilities(
    cfg: HarnessConfig,
    servers: dict[str, dict],
) -> list[object]:
    hard_timeout_sec = max(15.0, cfg.mcp_init_timeout_sec + 10.0)
    return negotiate_server_capabilities(
        servers,
        lambda name, server_cfg: probe_server_connectivity_with_hard_timeout(
            name,
            server_cfg,
            cfg.mcp_init_timeout_sec,
            hard_timeout_sec,
        ),
    )


def _runtime_servers_or_warning(
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
) -> dict[str, dict] | None:
    servers, parse_error = read_servers(cfg.mcp_config_path)
    if parse_error is None:
        return servers

    _warn_and_empty(
        emit_thought,
        f"{parse_error}; runtime will continue without MCP toolsets",
    )
    return None


def _load_subset_toolsets(
    cfg: HarnessConfig,
    subset_servers: dict[str, dict],
) -> list[object]:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="lllars-mcp-toolsets-",
        delete=False,
    ) as tmp:
        json.dump({"mcpServers": subset_servers}, tmp)
        subset_path = Path(tmp.name)

    try:
        return load_toolsets_from_mcp_config(
            mcp_config_path=subset_path,
            init_timeout_sec=cfg.mcp_init_timeout_sec,
        )
    finally:
        subset_path.unlink(missing_ok=True)


def load_runtime_mcp_toolsets(
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
) -> list[object]:
    if not cfg.mcp_enabled or cfg.mcp_config_path is None:
        return []

    servers = _runtime_servers_or_warning(cfg, emit_thought)
    if servers is None:
        return []

    capabilities = _negotiate_runtime_capabilities(cfg, servers)
    _emit_mcp_lines(emit_thought, capability_summary_lines(capabilities))

    healthy_servers = healthy_server_names(capabilities)
    if not healthy_servers:
        return _warn_and_empty(
            emit_thought,
            (
                "no healthy MCP capability sets; "
                "runtime will continue without MCP toolsets"
            ),
        )

    try:
        subset = _healthy_server_subset(servers, healthy_servers)
        return _load_subset_toolsets(cfg, subset)
    except Exception as exc:
        return _warn_and_empty(
            emit_thought,
            (
                "failed to load healthy MCP toolsets: "
                f"{exc}; runtime will continue without MCP toolsets"
            ),
        )
