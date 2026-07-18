from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
from pathlib import Path
import subprocess
import time

from lllars_core.asyncio_compat import configure_windows_event_loop_policy
from lllars_core.mcp.loader import load_toolsets_from_mcp_config


def read_servers(mcp_config_path: Path) -> tuple[dict[str, dict], str | None]:
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


def has_utf8_bom(path: Path) -> bool:
    try:
        return path.read_bytes().startswith(b"\xef\xbb\xbf")
    except Exception:
        return False


def _truncate_text(value: str, limit: int = 160) -> str:
    compact = " ".join(value.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _collect_stdio_probe_output(
    proc: subprocess.Popen[str],
) -> tuple[str, str]:
    try:
        return proc.communicate(timeout=2)
    except Exception:
        proc.kill()
        try:
            return proc.communicate(timeout=2)
        except Exception:
            return "", ""


def _build_stdio_probe_command(server_cfg: dict) -> list[str] | None:
    command_raw = server_cfg.get("command")
    if not isinstance(command_raw, str) or not command_raw.strip():
        return None
    args_raw = server_cfg.get("args", [])
    args = (
        [str(item) for item in args_raw]
        if isinstance(args_raw, list)
        else []
    )
    return [command_raw, *args]


def _render_stdio_probe_lines(
    server_name: str,
    out: str,
    err: str,
) -> list[str]:
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


def probe_stdio_startup_noise(
    server_name: str,
    server_cfg: dict,
) -> list[str]:
    cmd = _build_stdio_probe_command(server_cfg)
    if cmd is None:
        return [f"startup_probe[{server_name}]: skipped (no stdio command)"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as exc:
        return [f"startup_probe[{server_name}]: failed to launch: {exc}"]

    time.sleep(0.8)
    if proc.poll() is None:
        proc.terminate()
    out, err = _collect_stdio_probe_output(proc)
    return _render_stdio_probe_lines(server_name, out, err)


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


def probe_connectivity_with_hard_timeout(
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
