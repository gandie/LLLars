from __future__ import annotations

from lllars_core.config import HarnessConfig
from lllars_core.mcp.model_probe_support import (
    extract_model_names_for_family,
    infer_provider_family,
    is_unsupported_listing_response,
    normalize_model_name,
    probe_url_for_family,
    read_model_payload,
    unsupported_listing_warning,
)


def check_model_endpoint(cfg: HarnessConfig) -> tuple[bool, list[str]]:
    skip_line = _skip_probe_line(cfg)
    if skip_line is not None:
        return True, [skip_line]

    provider_family = infer_provider_family(cfg)
    probe_url = probe_url_for_family(provider_family, cfg.provider_url)
    lines = [f"model_endpoint: provider_family={provider_family}"]

    ok, status_code, payload_raw, error_line = read_model_payload(probe_url)
    if not ok:
        return _failed_probe_result(
            provider_family,
            probe_url,
            status_code,
            payload_raw,
            error_line,
            lines,
        )

    lines.append(
        f"model_endpoint: ok url={probe_url} http_status={status_code}"
    )
    return _verify_configured_model(
        cfg.model,
        provider_family,
        payload_raw,
        lines,
    )


def _skip_probe_line(cfg: HarnessConfig) -> str | None:
    if cfg.service_mode == "serve" and (
        not str(cfg.model).strip() or not str(cfg.provider_url).strip()
    ):
        return "model_endpoint: skipped (serve mode without run config)"
    if cfg.network_policy == "offline":
        return "model_endpoint: skipped (network_policy=offline)"
    return None


def _failed_probe_result(
    provider_family: str,
    probe_url: str,
    status_code: int,
    payload_raw: str,
    error_line: str | None,
    lines: list[str],
) -> tuple[bool, list[str]]:
    if is_unsupported_listing_response(
        provider_family,
        status_code,
        payload_raw,
    ):
        lines.append(
            unsupported_listing_warning(
                provider_family,
                probe_url,
                status_code,
            )
        )
        return True, lines

    if error_line is not None:
        lines.append(error_line)
    return False, lines


def _verify_configured_model(
    model_value: str,
    provider_family: str,
    payload_raw: str,
    lines: list[str],
) -> tuple[bool, list[str]]:
    model_names, warning_line = extract_model_names_for_family(
        provider_family,
        payload_raw,
    )
    if warning_line is not None:
        lines.append(warning_line)
        return True, lines

    configured_model = normalize_model_name(model_value)
    if configured_model in model_names:
        lines.append(
            "model_endpoint: model_found "
            f"configured_model={configured_model!r}"
        )
        return True, lines

    sample = ", ".join(model_names[:5])
    return False, [
        "model_endpoint: failed "
        f"configured_model={configured_model!r} not present; "
        f"available_models={sample}"
    ]
