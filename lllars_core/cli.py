from __future__ import annotations

import argparse
import time
from pathlib import Path

from lllars_core.config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_TIMEOUT_SEC,
    load_config,
)
from lllars_core.console import Color, print_summary
from lllars_core.mcp_preflight import run_mcp_preflight
from lllars_core.runner import run_agent_with_timeout
from lllars_core.shell import is_eval_success, run_eval, run_tests
from lllars_core.skills import configured_markdown_skill_ids


def main() -> None:
    ap = argparse.ArgumentParser(description="LLLARS single-shot runner")
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
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)

    if args.prompt:
        prompt_text = args.prompt
    elif args.prompt_file:
        prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")
    else:
        raise SystemExit("Provide --prompt or --prompt-file")

    def _fmt(value: object) -> str:
        return "none" if value is None else str(value)

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

    if cfg.mcp_enabled and not args.skip_mcp_preflight:
        print(f"{Color.CYAN}[mcp] preflight...{Color.RESET}")
        mcp_ok, mcp_lines = run_mcp_preflight(cfg)
        if mcp_ok:
            print(f"{Color.GREEN}[mcp] preflight ok{Color.RESET}")
        else:
            print(f"{Color.RED}[mcp] preflight failed{Color.RESET}")
            for item in mcp_lines:
                print(f"{Color.YELLOW}[mcp] {item}{Color.RESET}")
            raise SystemExit(2)

    start = time.time()
    (
        agent_stdout,
        agent_stderr,
        agent_rc,
        telemetry,
        thought_trace,
    ) = run_agent_with_timeout(
        cfg=cfg,
        prompt_text=prompt_text,
        timeout_sec=args.timeout_sec,
        show_progress=True,
    )
    elapsed = round(time.time() - start, 2)

    if cfg.test_command:
        print(f"{Color.CYAN}[checks] running tests...{Color.RESET}")
    else:
        print(
            f"{Color.YELLOW}[checks] tests not configured (skipped)"
            f"{Color.RESET}"
        )
    test_info = run_tests(cfg)
    if cfg.eval_command:
        print(f"{Color.CYAN}[checks] running eval...{Color.RESET}")
    else:
        print(
            f"{Color.YELLOW}[checks] eval not configured (skipped)"
            f"{Color.RESET}"
        )
    eval_json, eval_error = run_eval(cfg)

    success = (
        agent_rc == 0
        and int(test_info.get("returncode", 1)) == 0
        and is_eval_success(cfg, eval_json)
    )

    result = {
        "success": success,
        "agent_returncode": agent_rc,
        "elapsed_sec": elapsed,
        "agent_stdout": agent_stdout,
        "agent_stderr": agent_stderr,
        "thought_trace": thought_trace,
        "test": test_info,
        "eval": eval_json,
        "eval_error": eval_error,
        "runtime_telemetry": telemetry,
    }

    print_summary(result, verbose=args.verbose)
    raise SystemExit(0 if success else 1)
