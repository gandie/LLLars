from __future__ import annotations

import argparse
from pathlib import Path

from lllars_core.config import (
    DEFAULT_CONFIG_PATH,
    RunConfig,
    DEFAULT_TIMEOUT_SEC,
    VALID_QUEUE_BACKENDS,
    load_config,
)
from lllars_core.console import Color, print_summary
from lllars_core.mcp_preflight import run_startup_preflight
from lllars_core.runtime_models import JobSpec
from lllars_core.runtime_api import create_runtime_app
from lllars_core.runtime_runner import run_job
from lllars_core.skills import configured_markdown_skill_ids


def _fmt(value: object) -> str:
    return "none" if value is None else str(value)


def _print_runtime_startup(cfg: object) -> None:
    print(
        f"{Color.CYAN}[native-core]{Color.RESET} "
        f"request_limit={_fmt(cfg.usage_request_limit)}; "
        f"tool_calls_limit={_fmt(cfg.usage_tool_calls_limit)}; "
        f"input_tokens_limit={_fmt(cfg.usage_input_tokens_limit)}; "
        f"output_tokens_limit={_fmt(cfg.usage_output_tokens_limit)}; "
        f"total_tokens_limit={_fmt(cfg.usage_total_tokens_limit)}; "
        "count_tokens_before_request="
        f"{cfg.usage_count_tokens_before_request}; "
        "retries={"
        f"tools:{cfg.agent_retries_tools},"
        f"output:{cfg.agent_retries_output}"
        "}; "
        f"tool_timeout_sec={_fmt(cfg.tool_timeout_sec)}; "
        f"max_concurrency={_fmt(cfg.max_concurrency)}; "
        "instrumentation="
        f"{cfg.instrumentation_enabled}"
    )

    skill_ids = configured_markdown_skill_ids(cfg)
    skill_ids_text = ", ".join(skill_ids) if skill_ids else "none"
    print(
        f"{Color.CYAN}[skills]{Color.RESET} "
        f"enabled={cfg.skills_enabled}; "
        f"defer_loading={cfg.skills_defer_loading}; "
        f"loaded={len(skill_ids)}; "
        f"ids={skill_ids_text}"
    )

    mcp_config_text = (
        str(cfg.mcp_config_path)
        if cfg.mcp_config_path is not None
        else "none"
    )
    print(
        f"{Color.CYAN}[mcp]{Color.RESET} "
        f"enabled={cfg.mcp_enabled}; "
        f"config={mcp_config_text}; "
        f"init_timeout_sec={cfg.mcp_init_timeout_sec}"
    )

    print(
        f"{Color.CYAN}[runtime]{Color.RESET} "
        f"service_mode={cfg.service_mode}; "
        f"service_host={cfg.service_host}; "
        f"service_port={cfg.service_port}; "
        f"service_workers={cfg.service_workers}; "
        f"mount_work_root={cfg.mount_work_root}; "
        f"mount_config_root={cfg.mount_config_root}; "
        f"mount_artifacts_root={cfg.mount_artifacts_root}; "
        f"queue_backend={cfg.queue_backend}; "
        f"network_policy={cfg.network_policy}"
    )


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


def _run_oneshot(args: argparse.Namespace) -> None:
    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)

    if args.prompt:
        prompt_text = args.prompt
    elif args.prompt_file:
        prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")
    else:
        raise SystemExit("Provide --prompt or --prompt-file")

    _print_runtime_startup(cfg)
    _run_startup_preflight(cfg, args.skip_mcp_preflight)

    def _emit_runtime_status(message: str) -> None:
        if message == "running tests":
            print(f"{Color.CYAN}[checks] running tests...{Color.RESET}")
            return
        if message == "running eval":
            print(f"{Color.CYAN}[checks] running eval...{Color.RESET}")
            return
        print(
            f"{Color.YELLOW}[checks] {message}{Color.RESET}"
        )

    project_root_rel = "."
    try:
        relative_root = cfg.project_root.resolve().relative_to(
            cfg.mount_work_root.resolve()
        )
        project_root_rel = (
            "."
            if str(relative_root) in {"", "."}
            else str(relative_root).replace("\\", "/")
        )
    except ValueError:
        project_root_rel = "."

    run_result = run_job(
        JobSpec(
            prompt=prompt_text,
            run=RunConfig(
                model=cfg.model,
                provider_url=cfg.provider_url,
                project_root=cfg.mount_work_root / project_root_rel,
                test_command=cfg.test_command,
                eval_command=cfg.eval_command,
                command_profile=cfg.command_profile,
            ),
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


def _run_serve(args: argparse.Namespace) -> None:
    config_path = Path(args.config).resolve()
    overrides: dict[str, object] = {}
    if args.host is not None:
        overrides["service_host"] = args.host
    if args.port is not None:
        overrides["service_port"] = args.port
    if args.workers is not None:
        overrides["service_workers"] = args.workers
    if args.queue_backend is not None:
        overrides["queue_backend"] = args.queue_backend

    cfg = load_config(config_path, overrides=overrides)

    _print_runtime_startup(cfg)
    _run_startup_preflight(cfg, args.skip_mcp_preflight)

    print(
        f"{Color.CYAN}[serve]{Color.RESET} "
        f"host={cfg.service_host}; "
        f"port={cfg.service_port}; "
        f"workers={cfg.service_workers}; "
        f"queue_backend={cfg.queue_backend}"
    )

    if cfg.queue_backend != "inmemory":
        raise SystemExit(
            "Serve mode currently supports only queue_backend=inmemory"
        )

    if cfg.service_workers != 1:
        print(
            f"{Color.YELLOW}[serve] workers={cfg.service_workers} requested; "
            f"using 1 worker for in-process job store.{Color.RESET}"
        )

    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Missing dependency: uvicorn. Install project dependencies first."
        ) from exc

    app = create_runtime_app(cfg)
    uvicorn.run(
        app,
        host=cfg.service_host,
        port=cfg.service_port,
        log_level="info",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="LLLARS runner")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    ap.add_argument("--prompt", help="Prompt text to run")
    ap.add_argument("--prompt-file", help="Path to prompt text file")
    ap.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    ap.add_argument(
        "--skip-mcp-preflight",
        action="store_true",
        help="Skip MCP connectivity preflight check",
    )
    ap.add_argument("--verbose", "-v", action="store_true")

    subparsers = ap.add_subparsers(dest="mode")
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

    args = ap.parse_args()
    if args.mode == "serve":
        _run_serve(args)
        return

    _run_oneshot(args)
