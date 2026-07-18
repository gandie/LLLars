from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

from lllars_core.runtime.api import create_runtime_app


def make_runtime_client(
    *,
    model: str = "test-model",
    provider_url: str = "http://localhost:11434",
) -> TestClient:
    cfg = SimpleNamespace(model=model, provider_url=provider_url)
    return TestClient(create_runtime_app(cfg))


def base_run_payload(
    *,
    project_root: str = ".",
    command_profile: str = "none",
) -> dict[str, Any]:
    return {
        "model": "test-model",
        "provider_url": "http://localhost:11434",
        "project_root": project_root,
        "command_profile": command_profile,
    }


def submit_job(
    client: TestClient,
    *,
    prompt: str = "hello",
    timeout_sec: int = 5,
    run_overrides: dict[str, Any] | None = None,
) -> str:
    run_payload = base_run_payload()
    if run_overrides:
        run_payload.update(run_overrides)
    submit_resp = client.post(
        "/jobs",
        json={
            "prompt": prompt,
            "run": run_payload,
            "timeout_sec": timeout_sec,
        },
    )
    assert submit_resp.status_code == 202
    return submit_resp.json()["job_id"]


def wait_for_terminal_status(
    client: TestClient,
    job_id: str,
    *,
    attempts: int = 60,
) -> dict[str, Any]:
    for _ in range(attempts):
        status_resp = client.get(f"/jobs/{job_id}")
        assert status_resp.status_code == 200
        payload = status_resp.json()
        if payload["status"] in {"succeeded", "failed", "canceled"}:
            return payload
        time.sleep(0.05)
    return payload


def extended_run_payload() -> dict[str, Any]:
    return {
        "model": "test-model",
        "provider_url": "http://localhost:11434",
        "project_root": "playground",
        "commands": {},
        "command_profile": "none",
        "eval_expect_json": False,
        "eval_success_pass_rate": 100.0,
        "usage_request_limit": None,
        "usage_tool_calls_limit": 100,
        "usage_input_tokens_limit": None,
        "usage_output_tokens_limit": None,
        "usage_total_tokens_limit": None,
        "usage_count_tokens_before_request": False,
        "agent_retries_tools": 1,
        "agent_retries_output": 1,
        "tool_timeout_sec": 90,
        "max_concurrency": None,
        "instrumentation_enabled": False,
        "instrumentation_include_content": False,
        "skills_enabled": True,
        "skills_glob": "skills/*.md",
        "skills_defer_loading": False,
        "skills_require_description": True,
        "mcp_enabled": False,
        "mcp_config_path": None,
        "mcp_init_timeout_sec": 60,
        "system_prompt": "You are senior Python developer.",
        "tool_policy": "Tool policy",
    }
