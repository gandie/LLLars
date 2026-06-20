from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from lllars_core.config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_TIMEOUT_SEC,
    load_config,
)
from lllars_core.console import Color, print_summary
from lllars_core.runner import run_agent_with_timeout, run_single_agent
from lllars_core.shell import is_eval_success, run_eval, run_tests


def main() -> None:
    ap = argparse.ArgumentParser(description="LLLARS single-shot runner")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    ap.add_argument("--prompt", help="Prompt text to run")
    ap.add_argument("--prompt-file", help="Path to prompt text file")
    ap.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument(
        "--internal-run",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    ap.add_argument(
        "--internal-prompt-file",
        default="",
        help=argparse.SUPPRESS,
    )
    ap.add_argument(
        "--internal-output-json",
        default="",
        help=argparse.SUPPRESS,
    )
    ap.add_argument(
        "--internal-thought-log",
        default="",
        help=argparse.SUPPRESS,
    )
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)

    if args.internal_run:
        if not args.internal_prompt_file or not args.internal_output_json:
            raise SystemExit(125)

        thought_log_path = None
        if args.internal_thought_log:
            thought_log_path = Path(args.internal_thought_log)

        prompt_text = Path(args.internal_prompt_file).read_text(
            encoding="utf-8"
        )
        payload = run_single_agent(
            cfg,
            prompt_text,
            thought_log_path=thought_log_path,
        )
        Path(args.internal_output_json).write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        raise SystemExit(int(payload.get("returncode", 125)))

    if args.prompt:
        prompt_text = args.prompt
    elif args.prompt_file:
        prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")
    else:
        raise SystemExit("Provide --prompt or --prompt-file")

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
        show_progress=not args.internal_run,
        config_path=config_path,
    )
    elapsed = round(time.time() - start, 2)

    print(f"{Color.CYAN}[checks] running tests...{Color.RESET}")
    test_info = run_tests(cfg)
    if cfg.eval_command:
        print(f"{Color.CYAN}[checks] running eval...{Color.RESET}")
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
