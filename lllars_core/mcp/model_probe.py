from __future__ import annotations

import json
from urllib import error as url_error
from urllib import request as url_request

from lllars_core.config import HarnessConfig


def _normalize_model_name(model_value: str) -> str:
    value = model_value.strip()
    if value.startswith("ollama:"):
        return value.split(":", 1)[1]
    return value


def _build_ollama_tags_url(provider_url: str) -> str:
    base_url = provider_url.strip().rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    return f"{base_url}/api/tags"


def _read_model_payload(probe_url: str) -> tuple[bool, int, str, list[str]]:
    request = url_request.Request(
        probe_url,
        headers={"Accept": "application/json"},
    )
    try:
        with url_request.urlopen(request, timeout=5.0) as response:
            status = int(getattr(response, "status", 200))
            payload_raw = response.read().decode("utf-8", errors="replace")
    except url_error.URLError as exc:
        return False, 0, "", [
            f"model_endpoint: failed url={probe_url} reason={exc}"
        ]
    except Exception as exc:
        return False, 0, "", [
            f"model_endpoint: failed url={probe_url} reason={exc}"
        ]

    if status >= 400:
        return False, status, payload_raw, [
            f"model_endpoint: failed url={probe_url} http_status={status}"
        ]
    return True, status, payload_raw, [
        f"model_endpoint: ok url={probe_url} http_status={status}"
    ]


def _extract_model_names(payload_raw: str) -> tuple[list[str], str | None]:
    try:
        payload = json.loads(payload_raw)
    except Exception:
        return [], "model_endpoint: warning response is not valid JSON"

    models = payload.get("models")
    if not isinstance(models, list):
        return [], "model_endpoint: warning response has no models list"

    model_names: list[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                model_names.append(name.strip())
    if not model_names:
        return [], "model_endpoint: warning models list is empty"
    return model_names, None


def check_model_endpoint(cfg: HarnessConfig) -> tuple[bool, list[str]]:
    if cfg.service_mode == "serve" and (
        not str(cfg.model).strip() or not str(cfg.provider_url).strip()
    ):
        return True, [
            "model_endpoint: skipped (serve mode without run config)"
        ]
    if cfg.network_policy == "offline":
        return True, ["model_endpoint: skipped (network_policy=offline)"]

    probe_url = _build_ollama_tags_url(cfg.provider_url)
    ok, _, payload_raw, lines = _read_model_payload(probe_url)
    if not ok:
        return False, lines

    model_names, warning_line = _extract_model_names(payload_raw)
    if warning_line is not None:
        lines.append(warning_line)
        return True, lines

    configured_model = _normalize_model_name(cfg.model)
    if configured_model not in model_names:
        sample = ", ".join(model_names[:5])
        return False, [
            "model_endpoint: failed "
            f"configured_model={configured_model!r} not present; "
            f"available_models={sample}"
        ]

    lines.append(
        "model_endpoint: model_found "
        f"configured_model={configured_model!r}"
    )
    return True, lines
