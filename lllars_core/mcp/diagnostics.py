from __future__ import annotations

from pathlib import Path


def startup_mcp_lines(
    mcp_ok: bool,
    mcp_lines: list[str],
) -> list[str]:
    lines = ["mcp_preflight: ok" if mcp_ok else "mcp_preflight: failed"]
    for item in mcp_lines:
        lines.append(f"mcp_preflight.detail: {item}")
    return lines


def preflight_probe_hints(message: str) -> list[str]:
    if "Failed to initialize server session" in message:
        return [
            "hint: MCP server started but did not complete "
            "initialize handshake over stdio",
            "hint: if startup_probe stdout contains logs, "
            "that can break MCP framing",
            "hint: check if server writes non-protocol logs to stdout",
            "hint: verify client/server transport compatibility "
            "and startup args",
        ]

    if "exceeded" in message:
        return [
            "hint: MCP client operation stalled; hard timeout "
            "terminated probe process"
        ]

    return []


def preflight_initial_lines(
    mcp_config_path: Path,
    *,
    has_bom: bool,
) -> list[str]:
    lines = [f"config={mcp_config_path}"]
    if has_bom:
        lines.append(
            "warning: config file starts with UTF-8 BOM; "
            "some MCP JSON loaders reject BOM"
        )
    return lines
