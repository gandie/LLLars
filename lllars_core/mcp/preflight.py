from __future__ import annotations

import tempfile
from pathlib import Path

from lllars_core.config import HarnessConfig
from lllars_core.mcp.diagnostics import (
    preflight_initial_lines,
    preflight_probe_hints,
    startup_mcp_lines,
)
from lllars_core.mcp.loader import load_toolsets_from_mcp_config
from lllars_core.mcp.model_probe import check_model_endpoint
from lllars_core.mcp.runtime import (
    has_utf8_bom,
    probe_connectivity_with_hard_timeout,
    probe_stdio_startup_noise,
    read_servers,
)


def _check_model_endpoint(cfg: HarnessConfig) -> tuple[bool, list[str]]:
    return check_model_endpoint(cfg)


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

    model_ok, model_lines = _check_model_endpoint(cfg)
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


def _load_toolsets_or_error(
    cfg: HarnessConfig,
    mcp_config_path: Path,
) -> tuple[list[object] | None, str | None]:
    try:
        toolsets = load_toolsets_from_mcp_config(
            mcp_config_path=mcp_config_path,
            init_timeout_sec=cfg.mcp_init_timeout_sec,
        )
    except Exception as exc:
        return None, f"Failed to load MCP toolsets: {exc}"

    if not toolsets:
        return None, "No MCP toolsets were loaded"
    return toolsets, None


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


def _load_servers_and_toolsets(
    cfg: HarnessConfig,
    mcp_config_path: Path,
    lines: list[str],
) -> tuple[dict[str, dict] | None, list[str]]:
    servers, parse_error = read_servers(mcp_config_path)
    if parse_error:
        lines.append(parse_error)
        return None, lines
    lines.append("servers=" + ", ".join(servers.keys()))

    toolsets, toolset_error = _load_toolsets_or_error(cfg, mcp_config_path)
    if toolset_error is not None:
        lines.append(toolset_error)
        return None, lines
    lines.append(f"toolsets_loaded={len(toolsets or [])}")
    return servers, lines


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
    servers, lines = _load_servers_and_toolsets(
        cfg,
        mcp_config_path,
        lines,
    )
    if servers is None:
        return False, lines

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
