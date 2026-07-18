from __future__ import annotations

import argparse
from pathlib import Path

from lllars_core.config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_TIMEOUT_SEC,
    VALID_QUEUE_BACKENDS,
    load_config,
)
from lllars_core.console import Color, print_summary
from lllars_core.cli_output import print_runtime_startup
from lllars_core.mcp import run_startup_preflight
from lllars_core.runtime.api import create_runtime_app
from lllars_core.runtime.job_runner import run_job
from lllars_core.runtime.models import JobSpec


def _run_startup_preflight(cfg: object, skip_mcp_preflight: bool) -> None:
    print(f"{Color.CYAN}[startup] preflight...{Color.RESET}")
    preflight_ok, preflight_lines = run_startup_preflight(
        cfg,
        skip_mcp_preflight=skip_mcp_preflight,
    )
    if preflight_ok:
        print(f"{Color.GREEN}[startup] preflight ok{Color.RESET}")
        return

    print(f"{Color.RED}[startup] preflight failed{Color.RESET}")
    for item in preflight_lines:
        print(f"{Color.YELLOW}[startup] {item}{Color.RESET}")
    raise SystemExit(2)


def _resolve_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    raise SystemExit("Provide --prompt or --prompt-file")


def _emit_runtime_status(message: str) -> None:
    if message == "running tests":
        print(f"{Color.CYAN}[checks] running tests...{Color.RESET}")
        return
    if message == "running eval":
        print(f"{Color.CYAN}[checks] running eval...{Color.RESET}")
        return
    print(f"{Color.YELLOW}[checks] {message}{Color.RESET}")


def _run_oneshot(args: argparse.Namespace) -> None:
    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)
    prompt_text = _resolve_prompt(args)

    print_runtime_startup(cfg)
    _run_startup_preflight(cfg, args.skip_mcp_preflight)

    run_result = run_job(
        JobSpec(
            prompt=prompt_text,
            run=cfg.run,
            timeout_sec=args.timeout_sec,
            config_path=str(config_path),
        ),
        cfg=cfg,
        show_progress=True,
        emit_status=_emit_runtime_status,
    )
    result = run_result.model_dump()

    print_summary(result, verbose=args.verbose)
    raise SystemExit(0 if run_result.success else 1)


def _serve_overrides(args: argparse.Namespace) -> dict[str, object]:
    overrides: dict[str, object] = {}
    if args.host is not None:
        overrides["service_host"] = args.host
    if args.port is not None:
        overrides["service_port"] = args.port
    if args.workers is not None:
        overrides["service_workers"] = args.workers
    if args.queue_backend is not None:
        overrides["queue_backend"] = args.queue_backend
    return overrides


def _validate_serve_settings(cfg: object) -> None:
    if cfg.queue_backend != "inmemory":
        raise SystemExit(
            "Serve mode currently supports only queue_backend=inmemory"
        )
    if cfg.service_workers != 1:
        print(
            f"{Color.YELLOW}[serve] workers={cfg.service_workers} requested; "
            f"using 1 worker for in-process job store.{Color.RESET}"
        )


def _load_uvicorn():
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Missing dependency: uvicorn. Install project dependencies first."
        ) from exc
    return uvicorn


def _run_serve(args: argparse.Namespace) -> None:
    config_path = Path(args.config).resolve()
    cfg = load_config(config_path, overrides=_serve_overrides(args))

    print_runtime_startup(cfg)
    _run_startup_preflight(cfg, args.skip_mcp_preflight)

    print(
        f"{Color.CYAN}[serve]{Color.RESET} "
        f"host={cfg.service_host}; "
        f"port={cfg.service_port}; "
        f"workers={cfg.service_workers}; "
        f"queue_backend={cfg.queue_backend}"
    )

    _validate_serve_settings(cfg)
    uvicorn = _load_uvicorn()

    app = create_runtime_app(cfg)
    uvicorn.run(
        app,
        host=cfg.service_host,
        port=cfg.service_port,
        log_level="info",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LLLARS runner")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--prompt", help="Prompt text to run")
    parser.add_argument("--prompt-file", help="Path to prompt text file")
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument(
        "--skip-mcp-preflight",
        action="store_true",
        help="Skip MCP connectivity preflight check",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    subparsers = parser.add_subparsers(dest="mode")
    serve_ap = subparsers.add_parser(
        "serve",
        help="Run service mode entrypoint",
    )
    serve_ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    serve_ap.add_argument(
        "--skip-mcp-preflight",
        action="store_true",
        help="Skip MCP connectivity preflight check",
    )
    serve_ap.add_argument("--verbose", "-v", action="store_true")
    serve_ap.add_argument("--host", default=None)
    serve_ap.add_argument("--port", type=int, default=None)
    serve_ap.add_argument("--workers", type=int, default=None)
    serve_ap.add_argument(
        "--queue-backend",
        choices=sorted(VALID_QUEUE_BACKENDS),
        default=None,
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.mode == "serve":
        _run_serve(args)
        return

    _run_oneshot(args)
