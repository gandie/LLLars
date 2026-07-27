from __future__ import annotations

import tempfile
from pathlib import Path

from lllars_core.config import HarnessConfig
from lllars_core.mcp.capabilities import (
    ServerCapability,
    capability_summary_lines,
    healthy_server_names,
    negotiate_server_capabilities,
)
from lllars_core.mcp.diagnostics import (
    preflight_initial_lines,
    preflight_probe_hints,
    startup_mcp_lines,
)
from lllars_core.mcp.model_probe import check_model_endpoint
from lllars_core.mcp.runtime import (
    has_utf8_bom,
    probe_connectivity_with_hard_timeout,
    probe_server_connectivity_with_hard_timeout,
    probe_stdio_startup_noise,
    read_servers,
)


def _check_mount_writable(
    mount_name: str,
    mount_path: Path,
) -> tuple[bool, str]:
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=mount_path,
            prefix=".lllars-preflight-",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write("preflight")
            tmp_path = Path(tmp.name)
        tmp_path.unlink(missing_ok=True)
    except Exception as exc:
        return (
            False,
            "mount_writable: failed "
            f"mount={mount_name} path={mount_path} reason={exc}",
        )
    return True, f"mount_writable: ok mount={mount_name} path={mount_path}"


def run_startup_preflight(
    cfg: HarnessConfig,
    *,
    skip_mcp_preflight: bool = False,
) -> tuple[bool, list[str]]:
    ok = True
    lines: list[str] = []

    model_ok, model_lines = check_model_endpoint(cfg)
    ok = ok and model_ok
    lines.extend(model_lines)

    for mount_name, mount_path in (
        ("mount_work_root", cfg.mount_work_root),
        ("mount_artifacts_root", cfg.mount_artifacts_root),
    ):
        mount_ok, mount_line = _check_mount_writable(mount_name, mount_path)
        ok = ok and mount_ok
        lines.append(mount_line)

    if skip_mcp_preflight:
        lines.append("mcp_preflight: skipped via CLI flag")
        return ok, lines

    mcp_ok, mcp_lines = run_mcp_preflight(cfg)
    ok = ok and mcp_ok
    lines.extend(startup_mcp_lines(mcp_ok, mcp_lines))
    return ok, lines


def _append_connectivity_failure_details(
    lines: list[str],
    message: str,
    servers: dict[str, dict],
) -> None:
    lines.append(f"connectivity_probe_failed: {message}")
    for server_name, server_cfg in servers.items():
        lines.extend(probe_stdio_startup_noise(server_name, server_cfg))
    lines.extend(preflight_probe_hints(message))


def _build_preflight_context(
    cfg: HarnessConfig,
    timeout_sec: float | None,
) -> tuple[Path, float, list[str]]:
    mcp_config_path = cfg.mcp_config_path
    assert mcp_config_path is not None
    hard_timeout_sec = (
        float(timeout_sec)
        if timeout_sec is not None
        else max(15.0, cfg.mcp_init_timeout_sec + 10.0)
    )
    lines = preflight_initial_lines(
        mcp_config_path,
        has_bom=has_utf8_bom(mcp_config_path),
    )
    return mcp_config_path, hard_timeout_sec, lines


def _load_servers(
    mcp_config_path: Path,
    lines: list[str],
) -> tuple[dict[str, dict] | None, list[str]]:
    servers, parse_error = read_servers(mcp_config_path)
    if parse_error:
        lines.append(parse_error)
        return None, lines
    lines.append("servers=" + ", ".join(servers.keys()))
    return servers, lines


def _run_legacy_preflight_fallback(
    cfg: HarnessConfig,
    mcp_config_path: Path,
    hard_timeout_sec: float,
    servers: dict[str, dict],
    lines: list[str],
) -> tuple[bool, list[str]]:
    ok, message = probe_connectivity_with_hard_timeout(
        mcp_config_path,
        cfg.mcp_init_timeout_sec,
        hard_timeout_sec,
    )
    if ok:
        lines.append("connectivity_probe=ok")
        return True, lines

    _append_connectivity_failure_details(lines, message, servers)
    return False, lines


def _negotiate_capabilities(
    cfg: HarnessConfig,
    servers: dict[str, dict],
    hard_timeout_sec: float,
) -> tuple[list[ServerCapability] | None, str | None]:
    try:
        capabilities = negotiate_server_capabilities(
            servers,
            lambda name, server_cfg: (
                probe_server_connectivity_with_hard_timeout(
                    name,
                    server_cfg,
                    cfg.mcp_init_timeout_sec,
                    hard_timeout_sec,
                )
            ),
        )
    except Exception as exc:
        return None, str(exc)

    return capabilities, None


def _finalize_capability_mode(
    lines: list[str],
    capabilities: list[ServerCapability],
) -> tuple[bool, list[str]]:
    lines.extend(capability_summary_lines(capabilities))
    if healthy_server_names(capabilities):
        lines.append(
            "mcp_degraded_mode: continuing with healthy MCP capability sets"
        )
        return True, lines

    lines.append(
        "warning: no healthy MCP capability sets; "
        "continuing with native/plugin tools only"
    )
    return True, lines


def run_mcp_preflight(
    cfg: HarnessConfig,
    timeout_sec: float | None = None,
) -> tuple[bool, list[str]]:
    if not cfg.mcp_enabled:
        return True, ["MCP disabled in config"]
    if cfg.mcp_config_path is None:
        return False, ["mcp_enabled=true but mcp_config_path is empty"]
    mcp_config_path, hard_timeout_sec, lines = _build_preflight_context(
        cfg,
        timeout_sec,
    )
    servers, lines = _load_servers(mcp_config_path, lines)
    if servers is None:
        return False, lines
    capabilities, negotiation_error = _negotiate_capabilities(
        cfg,
        servers,
        hard_timeout_sec,
    )
    if negotiation_error is not None or capabilities is None:
        lines.append(
            f"warning: capability negotiation failed: {negotiation_error}"
        )
        lines.append(
            "warning: falling back to legacy MCP connectivity preflight"
        )
        return _run_legacy_preflight_fallback(
            cfg,
            mcp_config_path,
            hard_timeout_sec,
            servers,
            lines,
        )
    return _finalize_capability_mode(lines, capabilities)
