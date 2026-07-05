from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
from pathlib import Path
import subprocess
import time

from lllars_core.asyncio_compat import configure_windows_event_loop_policy
from lllars_core.config import HarnessConfig
from lllars_core.mcp_loader import load_toolsets_from_mcp_config


def _read_servers(
    mcp_config_path: Path,
) -> tuple[dict[str, dict], str | None]:
    try:
        raw = mcp_config_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except Exception as exc:
        return {}, f"Failed to parse MCP config JSON: {exc}"

    servers = payload.get("mcpServers")
    if not isinstance(servers, dict):
        return {}, "MCP config is missing object field mcpServers"

    normalized: dict[str, dict] = {}
    for key, value in servers.items():
        if isinstance(value, dict):
            normalized[str(key)] = value
    if not normalized:
        return {}, "MCP config has no valid server objects under mcpServers"
    return normalized, None


def _has_utf8_bom(path: Path) -> bool:
    try:
        return path.read_bytes().startswith(b"\xef\xbb\xbf")
    except Exception:
        return False


def _truncate_text(value: str, limit: int = 160) -> str:
    compact = " ".join(value.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _probe_stdio_startup_noise(
    server_name: str,
    server_cfg: dict,
) -> list[str]:
    command_raw = server_cfg.get("command")
    if not isinstance(command_raw, str) or not command_raw.strip():
        return [
            f"startup_probe[{server_name}]: skipped (no stdio command)"
        ]

    args_raw = server_cfg.get("args", [])
    args: list[str] = []
    if isinstance(args_raw, list):
        args = [str(item) for item in args_raw]

    cmd = [command_raw, *args]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as exc:
        return [
            f"startup_probe[{server_name}]: failed to launch: {exc}"
        ]

    time.sleep(0.8)
    if proc.poll() is None:
        proc.terminate()

    try:
        out, err = proc.communicate(timeout=2)
    except Exception:
        proc.kill()
        try:
            out, err = proc.communicate(timeout=2)
        except Exception:
            out, err = "", ""

    lines: list[str] = []
    out_text = _truncate_text(out)
    err_text = _truncate_text(err)
    if out_text:
        lines.append(f"startup_probe[{server_name}] stdout: {out_text}")
    if err_text:
        lines.append(f"startup_probe[{server_name}] stderr: {err_text}")
    if not lines:
        lines.append(f"startup_probe[{server_name}]: no early output")
    return lines


async def _probe_toolsets(toolsets: list[object]) -> None:
    for toolset in toolsets:
        async with toolset:
            continue


def _probe_connectivity_worker(
    mcp_config_path: str,
    init_timeout_sec: float,
    result_queue: mp.Queue,
) -> None:
    try:
        configure_windows_event_loop_policy()
        toolsets = load_toolsets_from_mcp_config(
            mcp_config_path=Path(mcp_config_path),
            init_timeout_sec=init_timeout_sec,
        )
        asyncio.run(_probe_toolsets(toolsets))
        result_queue.put((True, "ok"))
    except Exception as exc:
        result_queue.put((False, str(exc)))


def _probe_connectivity_with_hard_timeout(
    mcp_config_path: Path,
    init_timeout_sec: float,
    timeout_sec: float,
) -> tuple[bool, str]:
    ctx = mp.get_context("spawn")
    result_queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(
        target=_probe_connectivity_worker,
        args=(str(mcp_config_path), init_timeout_sec, result_queue),
    )
    proc.start()
    proc.join(timeout=max(1.0, float(timeout_sec)))

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=3)
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=3)
        return False, f"preflight probe exceeded {timeout_sec:.1f}s"

    try:
        ok, message = result_queue.get_nowait()
    except Exception:
        return False, (
            "preflight probe exited without result "
            f"(exitcode={proc.exitcode})"
        )

    return bool(ok), str(message)


def run_mcp_preflight(
    cfg: HarnessConfig,
    timeout_sec: float | None = None,
) -> tuple[bool, list[str]]:
    if not cfg.mcp_enabled:
        return True, ["MCP disabled in config"]

    if cfg.mcp_config_path is None:
        return False, ["mcp_enabled=true but mcp_config_path is empty"]

    mcp_config_path = cfg.mcp_config_path
    hard_timeout_sec = (
        float(timeout_sec)
        if timeout_sec is not None
        else max(15.0, cfg.mcp_init_timeout_sec + 10.0)
    )
    lines: list[str] = [f"config={mcp_config_path}"]

    if _has_utf8_bom(mcp_config_path):
        lines.append(
            "warning: config file starts with UTF-8 BOM; "
            "some MCP JSON loaders reject BOM"
        )

    servers, parse_error = _read_servers(mcp_config_path)
    if parse_error:
        lines.append(parse_error)
        return False, lines
    server_names = list(servers.keys())
    lines.append("servers=" + ", ".join(server_names))

    try:
        toolsets = load_toolsets_from_mcp_config(
            mcp_config_path=mcp_config_path,
            init_timeout_sec=cfg.mcp_init_timeout_sec,
        )
    except Exception as exc:
        lines.append(f"Failed to load MCP toolsets: {exc}")
        return False, lines

    if not toolsets:
        lines.append("No MCP toolsets were loaded")
        return False, lines

    lines.append(f"toolsets_loaded={len(toolsets)}")

    ok, message = _probe_connectivity_with_hard_timeout(
        mcp_config_path,
        cfg.mcp_init_timeout_sec,
        hard_timeout_sec,
    )
    if not ok:
        lines.append(f"connectivity_probe_failed: {message}")
        for server_name, server_cfg in servers.items():
            lines.extend(_probe_stdio_startup_noise(server_name, server_cfg))
        if "Failed to initialize server session" in message:
            lines.append(
                "hint: MCP server started but did not complete initialize "
                "handshake over stdio"
            )
            lines.append(
                "hint: if startup_probe stdout contains logs, "
                "that can break MCP framing"
            )
            lines.append(
                "hint: check if server writes non-protocol logs to stdout"
            )
            lines.append(
                "hint: verify client/server transport compatibility "
                "and startup args"
            )
        elif "exceeded" in message:
            lines.append(
                "hint: MCP client operation stalled; hard timeout "
                "terminated probe process"
            )
        return False, lines

    lines.append("connectivity_probe=ok")
    return True, lines
