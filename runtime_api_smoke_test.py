from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
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
        raise RuntimeError(f"HTTP {exc.code} for {method} {url}: {text}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {method} {url}: {exc}") from exc

    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Expected JSON response from {url}, got: {text}") from exc


def run_smoke_test(
    base_url: str,
    prompt: str,
    model: str,
    provider_url: str,
    project_root: str,
    poll_interval_sec: float,
    timeout_sec: float,
) -> int:
    base = base_url.rstrip("/")

    health = _request_json("GET", f"{base}/health")
    print("health:")
    print(json.dumps(health, indent=2))

    submit = _request_json(
        "POST",
        f"{base}/jobs",
        {
            "prompt": prompt,
            "run": {
                "model": model,
                "provider_url": provider_url,
                "project_root": project_root,
                "command_profile": "none",
            },
        },
    )
    job_id = str(submit.get("job_id", "")).strip()
    if not job_id:
        raise RuntimeError(f"Submit response missing job_id: {submit}")

    print(f"submitted job_id={job_id}")

    terminal_states = {"succeeded", "failed", "canceled"}
    start = time.monotonic()
    last_status: dict[str, Any] = {}

    while True:
        status = _request_json("GET", f"{base}/jobs/{job_id}")
        state = str(status.get("status", "")).strip().lower()
        print(f"status={state}")

        if state in terminal_states:
            last_status = status
            break

        elapsed = time.monotonic() - start
        if elapsed > timeout_sec:
            raise TimeoutError(
                f"Timed out waiting for terminal status after {timeout_sec:.1f}s"
            )
        time.sleep(poll_interval_sec)

    logs = _request_json("GET", f"{base}/jobs/{job_id}/logs")

    print("final status:")
    print(json.dumps(last_status, indent=2))
    print("logs:")
    print(json.dumps(logs, indent=2))

    return 0 if str(last_status.get("status", "")).lower() == "succeeded" else 1


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
    parser.add_argument("--poll-interval-sec", type=float, default=0.3)
    parser.add_argument("--timeout-sec", type=float, default=120.0)
    args = parser.parse_args()

    raise SystemExit(
        run_smoke_test(
            base_url=args.base_url,
            prompt=args.prompt,
            model=args.model,
            provider_url=args.provider_url,
            project_root=args.project_root,
            poll_interval_sec=args.poll_interval_sec,
            timeout_sec=args.timeout_sec,
        )
    )


if __name__ == "__main__":
    main()
