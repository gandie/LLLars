from __future__ import annotations

import json
from urllib import error as url_error
from urllib import request as url_request

from lllars_core.config import HarnessConfig

OLLAMA_PROVIDER = "ollama"
OPENAI_COMPATIBLE_PROVIDER = "openai-compatible"

KNOWN_PROVIDER_PREFIXES = {
    "anthropic",
    "azure",
    "bedrock",
    "cohere",
    "deepseek",
    "google",
    "groq",
    "mistral",
    "ollama",
    "openai",
    "openrouter",
    "together",
    "vertexai",
}

UNSUPPORTED_LISTING_STATUS_CODES = frozenset({404, 405, 501})


def normalize_model_name(model_value: str) -> str:
    value = model_value.strip()
    if ":" not in value:
        return value
    prefix, remainder = value.split(":", 1)
    if prefix.strip().lower() in KNOWN_PROVIDER_PREFIXES and remainder.strip():
        return remainder.strip()
    return value


def build_ollama_tags_url(provider_url: str) -> str:
    base_url = provider_url.strip().rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    return f"{base_url}/api/tags"


def build_openai_models_url(provider_url: str) -> str:
    base_url = provider_url.strip().rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return f"{base_url}/models"


def read_model_payload(probe_url: str) -> tuple[bool, int, str, str | None]:
    request = url_request.Request(
        probe_url,
        headers={"Accept": "application/json"},
    )
    try:
        with url_request.urlopen(request, timeout=5.0) as response:
            status = int(getattr(response, "status", 200))
            payload_raw = response.read().decode("utf-8", errors="replace")
    except url_error.URLError as exc:
        message = (
            "model_endpoint: failed "
            f"url={probe_url} reason={exc}"
        )
        return False, 0, "", message
    except Exception as exc:
        message = (
            "model_endpoint: failed "
            f"url={probe_url} reason={exc}"
        )
        return False, 0, "", message

    if status >= 400:
        message = (
            "model_endpoint: failed "
            f"url={probe_url} http_status={status}"
        )
        return False, status, payload_raw, message
    return True, status, payload_raw, None


def extract_ollama_model_names(
    payload_raw: str,
) -> tuple[list[str], str | None]:
    payload, warning = parse_json_payload(payload_raw)
    if warning is not None:
        return [], warning

    models = payload.get("models")
    if not isinstance(models, list):
        return [], "model_endpoint: warning response has no models list"

    names = [
        item.get("name").strip()
        for item in models
        if isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and item.get("name", "").strip()
    ]
    if not names:
        return [], "model_endpoint: warning models list is empty"
    return names, None


def extract_openai_model_names(
    payload_raw: str,
) -> tuple[list[str], str | None]:
    payload, warning = parse_json_payload(payload_raw)
    if warning is not None:
        return [], warning

    data = payload.get("data")
    if not isinstance(data, list):
        return [], "model_endpoint: warning response has no data list"

    names = [
        item.get("id").strip()
        for item in data
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item.get("id", "").strip()
    ]
    if not names:
        return [], "model_endpoint: warning data list is empty"
    return names, None


def parse_json_payload(payload_raw: str) -> tuple[dict, str | None]:
    try:
        payload = json.loads(payload_raw)
    except Exception:
        return {}, "model_endpoint: warning response is not valid JSON"
    if not isinstance(payload, dict):
        return {}, "model_endpoint: warning response is not an object"
    return payload, None


def provider_prefix(model_value: str) -> str | None:
    value = model_value.strip()
    if ":" not in value:
        return None
    prefix = value.split(":", 1)[0].strip().lower()
    if prefix in KNOWN_PROVIDER_PREFIXES:
        return prefix
    return None


def infer_provider_family(cfg: HarnessConfig) -> str:
    # Model prefixes follow pydantic_ai provider wrappers.
    prefix = provider_prefix(str(cfg.model))
    if prefix == OLLAMA_PROVIDER:
        return OLLAMA_PROVIDER
    if prefix is not None:
        return OPENAI_COMPATIBLE_PROVIDER

    base_url = str(cfg.provider_url).strip().lower()
    if "/v1" in base_url:
        return OPENAI_COMPATIBLE_PROVIDER
    if "/api" in base_url and "/v1" not in base_url:
        return OLLAMA_PROVIDER
    return OLLAMA_PROVIDER


def is_unsupported_listing_response(
    provider_family: str,
    status_code: int,
    payload_raw: str,
) -> bool:
    if provider_family != OPENAI_COMPATIBLE_PROVIDER:
        return False
    if status_code in UNSUPPORTED_LISTING_STATUS_CODES:
        return True

    payload_text = payload_raw.strip().lower()
    if not payload_text:
        return False
    return (
        "not supported" in payload_text
        or "unsupported" in payload_text
        or "not implemented" in payload_text
    )


def unsupported_listing_warning(
    provider_family: str,
    probe_url: str,
    status_code: int,
) -> str:
    return (
        "model_endpoint: warning model listing unsupported "
        f"provider_family={provider_family} url={probe_url} "
        f"http_status={status_code}"
    )


def probe_url_for_family(provider_family: str, provider_url: str) -> str:
    if provider_family == OLLAMA_PROVIDER:
        return build_ollama_tags_url(provider_url)
    return build_openai_models_url(provider_url)


def extract_model_names_for_family(
    provider_family: str,
    payload_raw: str,
) -> tuple[list[str], str | None]:
    if provider_family == OLLAMA_PROVIDER:
        return extract_ollama_model_names(payload_raw)
    return extract_openai_model_names(payload_raw)
