from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from collections.abc import Callable
from typing import Any


def _request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: bytes | None = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url=url,
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HTTP {exc.code} for {method} {url}: {text}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Request failed for {method} {url}: {exc}"
        ) from exc

    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Expected JSON response from {url}, got: {text}"
        ) from exc


def run_smoke_test(
    base_url: str,
    prompt: str,
    model: str,
    provider_url: str,
    project_root: str,
    command_profile: str,
    test_command: str,
    expected_shells: tuple[str, ...],
    poll_interval_sec: float,
    timeout_sec: float,
    run_mode: str = "immediate",
    run_at_delay_sec: float = 2.0,
    schedule: str = "every:1s",
    trigger_source: str = "manual",
    trigger_payload_ref: str | None = None,
    *,
    request_json: Callable[
        [str, str, dict[str, Any] | None],
        dict[str, Any],
    ] = _request_json,
    now_fn: Callable[[], datetime] = datetime.now,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    base = base_url.rstrip("/")
    supported_modes = {"immediate", "timed", "recurring", "trigger"}
    if run_mode not in supported_modes:
        raise ValueError(
            f"Unsupported run mode {run_mode!r}; expected one of {supported_modes}"
        )

    health = request_json("GET", f"{base}/health")
    print("health:")
    print(json.dumps(health, indent=2))

    submit_payload: dict[str, Any] = {
        "prompt": prompt,
        "run": {
            "model": model,
            "provider_url": provider_url,
            "project_root": project_root,
            "command_profile": command_profile,
            "test_command": test_command,
        },
    }

    if run_mode in {"timed", "trigger"}:
        run_at = now_fn() + timedelta(seconds=run_at_delay_sec)
        submit_payload["run_at"] = run_at.isoformat(timespec="seconds")
    elif run_mode == "recurring":
        submit_payload["schedule"] = schedule
        submit_payload["trigger_source"] = "scheduled"

    submit = request_json("POST", f"{base}/jobs", submit_payload)
    job_id = str(submit.get("job_id", "")).strip()
    if not job_id:
        raise RuntimeError(f"Submit response missing job_id: {submit}")

    print(f"submitted job_id={job_id}")

    if run_mode == "trigger":
        trigger_payload: dict[str, Any] = {"trigger_source": trigger_source}
        if trigger_payload_ref is not None:
            trigger_payload["trigger_payload_ref"] = trigger_payload_ref
        trigger_result = request_json(
            "POST",
            f"{base}/jobs/{job_id}/trigger",
            trigger_payload,
        )
        print("trigger response:")
        print(json.dumps(trigger_result, indent=2))

    terminal_states = {"succeeded", "failed", "canceled"}
    start = monotonic()
    last_status: dict[str, Any] = {}
    recurring_cycle_observed = False

    while True:
        status = request_json("GET", f"{base}/jobs/{job_id}")
        state = str(status.get("status", "")).strip().lower()
        print(f"status={state}")

        if run_mode == "recurring":
            run_count = int(status.get("run_count", 0))
            if (
                state == "queued"
                and run_count >= 1
                and status.get("next_run_at") is not None
            ):
                last_status = status
                recurring_cycle_observed = True
                break

            if state in {"failed", "canceled"}:
                last_status = status
                break
        elif state in terminal_states:
            last_status = status
            break

        elapsed = monotonic() - start
        if elapsed > timeout_sec:
            raise TimeoutError(
                (
                    "Timed out waiting for terminal status after "
                    f"{timeout_sec:.1f}s"
                )
            )
        sleep(poll_interval_sec)

    logs = request_json("GET", f"{base}/jobs/{job_id}/logs")

    print("final status:")
    print(json.dumps(last_status, indent=2))
    print("logs:")
    print(json.dumps(logs, indent=2))

    if run_mode == "recurring":
        if not recurring_cycle_observed:
            print("recurring mode did not observe a completed requeue cycle")
            return 1
        return 0

    if str(last_status.get("status", "")).lower() != "succeeded":
        return 1

    if run_mode == "trigger":
        observed_source = str(last_status.get("trigger_source", "")).strip().lower()
        if observed_source != trigger_source.strip().lower():
            print(
                "unexpected trigger_source "
                f"{observed_source!r}; expected {trigger_source!r}"
            )
            return 1
        observed_payload_ref = last_status.get("trigger_payload_ref")
        if observed_payload_ref != trigger_payload_ref:
            print(
                "unexpected trigger_payload_ref "
                f"{observed_payload_ref!r}; expected {trigger_payload_ref!r}"
            )
            return 1

    result = last_status.get("result")
    if not isinstance(result, dict):
        print("missing result payload in terminal status")
        return 1

    test_payload = result.get("test")
    if not isinstance(test_payload, dict):
        print("missing test payload in terminal status result")
        return 1

    test_returncode = int(test_payload.get("returncode", 1))
    if test_returncode != 0:
        print(f"test command failed with returncode={test_returncode}")
        return 1

    runtime_telemetry = result.get("runtime_telemetry")
    if not isinstance(runtime_telemetry, dict):
        print("missing runtime telemetry in terminal status result")
        return 1

    shell_details = runtime_telemetry.get("shell")
    if not isinstance(shell_details, dict):
        print("missing shell telemetry in terminal status result")
        return 1

    selected_shell = str(shell_details.get("selected", "")).strip().lower()
    if selected_shell not in {item.lower() for item in expected_shells}:
        print(
            "unexpected selected shell "
            f"{selected_shell!r}; expected one of {expected_shells}"
        )
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke test for the LLLars runtime API"
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--prompt", default="runtime api smoke test")
    parser.add_argument(
        "--model",
        default="ollama:rafw007/qwen35-claude-coder:9b",
    )
    parser.add_argument(
        "--provider-url",
        default="http://host.docker.internal:11434",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--command-profile",
        default="playground-python",
    )
    parser.add_argument(
        "--test-command",
        default="python test.py",
    )
    parser.add_argument(
        "--expected-shells",
        default="bash,sh",
        help="Comma-separated list of acceptable detected shell names",
    )
    parser.add_argument("--poll-interval-sec", type=float, default=0.3)
    parser.add_argument("--timeout-sec", type=float, default=120.0)
    parser.add_argument(
        "--run-mode",
        choices=("immediate", "timed", "recurring", "trigger"),
        default="immediate",
        help="Smoke scenario to execute",
    )
    parser.add_argument(
        "--run-at-delay-sec",
        type=float,
        default=2.0,
        help="Delay applied when run mode requires run_at",
    )
    parser.add_argument(
        "--schedule",
        default="every:1s",
        help="Schedule expression used in recurring mode",
    )
    parser.add_argument(
        "--trigger-source",
        default="manual",
        help="Trigger source sent in trigger mode",
    )
    parser.add_argument(
        "--trigger-payload-ref",
        default=None,
        help="Optional trigger payload reference sent in trigger mode",
    )
    args = parser.parse_args()

    expected_shells = tuple(
        item.strip().lower()
        for item in args.expected_shells.split(",")
        if item.strip()
    )
    if not expected_shells:
        raise SystemExit("--expected-shells must include at least one shell")

    if args.run_mode == "recurring" and not args.schedule.strip():
        raise SystemExit("--schedule must be non-empty in recurring mode")

    raise SystemExit(
        run_smoke_test(
            base_url=args.base_url,
            prompt=args.prompt,
            model=args.model,
            provider_url=args.provider_url,
            project_root=args.project_root,
            command_profile=args.command_profile,
            test_command=args.test_command,
            expected_shells=expected_shells,
            poll_interval_sec=args.poll_interval_sec,
            timeout_sec=args.timeout_sec,
            run_mode=args.run_mode,
            run_at_delay_sec=args.run_at_delay_sec,
            schedule=args.schedule,
            trigger_source=args.trigger_source,
            trigger_payload_ref=args.trigger_payload_ref,
        )
    )


if __name__ == "__main__":
    main()
