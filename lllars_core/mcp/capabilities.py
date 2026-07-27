from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

CapabilityState = Literal["healthy", "degraded", "unavailable"]


@dataclass(frozen=True)
class ServerCapability:
    server_name: str
    state: CapabilityState
    details: tuple[str, ...] = ()


ProbeServerFn = Callable[[str, dict], tuple[bool, str]]


def classify_server_launch_contract(
    server_name: str,
    server_cfg: dict,
) -> ServerCapability:
    url_raw = server_cfg.get("url")
    if isinstance(url_raw, str) and url_raw.strip():
        return ServerCapability(server_name=server_name, state="healthy")

    command_raw = server_cfg.get("command")
    if not isinstance(command_raw, str) or not command_raw.strip():
        return ServerCapability(
            server_name=server_name,
            state="unavailable",
            details=("missing_launch_contract",),
        )

    args_raw = server_cfg.get("args", [])
    if not isinstance(args_raw, list):
        return ServerCapability(
            server_name=server_name,
            state="degraded",
            details=("args_not_list",),
        )

    return ServerCapability(server_name=server_name, state="healthy")


def negotiate_server_capabilities(
    servers: dict[str, dict],
    probe_server: ProbeServerFn,
) -> list[ServerCapability]:
    capabilities: list[ServerCapability] = []

    for server_name in sorted(servers.keys()):
        server_cfg = servers[server_name]
        baseline = classify_server_launch_contract(server_name, server_cfg)
        if baseline.state == "unavailable":
            capabilities.append(baseline)
            continue

        probe_ok, probe_message = probe_server(server_name, server_cfg)
        if probe_ok:
            capabilities.append(baseline)
            continue

        capabilities.append(
            ServerCapability(
                server_name=server_name,
                state="unavailable",
                details=(
                    *baseline.details,
                    f"connectivity_probe_failed:{probe_message}",
                ),
            )
        )

    return capabilities


def healthy_server_names(capabilities: list[ServerCapability]) -> list[str]:
    return [
        item.server_name
        for item in capabilities
        if item.state == "healthy"
    ]


def _capability_counts(
    capabilities: list[ServerCapability],
) -> tuple[int, int, int]:
    healthy = sum(1 for item in capabilities if item.state == "healthy")
    degraded = sum(1 for item in capabilities if item.state == "degraded")
    unavailable = sum(
        1
        for item in capabilities
        if item.state == "unavailable"
    )
    return healthy, degraded, unavailable


def _server_detail_lines(capabilities: list[ServerCapability]) -> list[str]:
    lines: list[str] = []
    for item in capabilities:
        detail_text = "none" if not item.details else ",".join(item.details)
        lines.append(
            "mcp_capability.server: "
            f"name={item.server_name} state={item.state} details={detail_text}"
        )
    return lines


def _state_warning_line(
    capabilities: list[ServerCapability],
    *,
    state: CapabilityState,
) -> str | None:
    names = ", ".join(
        item.server_name
        for item in capabilities
        if item.state == state
    )
    if not names:
        return None
    return f"warning: {state} MCP capability sets: {names}"


def capability_summary_lines(
    capabilities: list[ServerCapability],
) -> list[str]:
    total = len(capabilities)
    healthy, degraded, unavailable = _capability_counts(capabilities)

    lines = [
        "mcp_capabilities: "
        f"healthy={healthy} degraded={degraded} unavailable={unavailable} "
        f"total={total}"
    ]
    lines.extend(_server_detail_lines(capabilities))

    degraded_line = _state_warning_line(capabilities, state="degraded")
    if degraded_line is not None:
        lines.append(degraded_line)

    unavailable_line = _state_warning_line(
        capabilities,
        state="unavailable",
    )
    if unavailable_line is not None:
        lines.append(unavailable_line)

    return lines
