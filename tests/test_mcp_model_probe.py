from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from urllib import error as url_error
from unittest.mock import patch

from lllars_core.mcp.model_probe import check_model_endpoint


class _FakeResponse:
    def __init__(self, status: int, payload: dict[str, object]) -> None:
        self.status = status
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _cfg(
    *,
    model: str,
    provider_url: str,
    service_mode: str = "oneshot",
    network_policy: str = "inherit",
) -> SimpleNamespace:
    return SimpleNamespace(
        model=model,
        provider_url=provider_url,
        service_mode=service_mode,
        network_policy=network_policy,
    )


class ModelProbeTests(unittest.TestCase):
    def test_ollama_probe_uses_tags_and_finds_model(self) -> None:
        cfg = _cfg(
            model="ollama:qwen2.5-coder:7b",
            provider_url="http://localhost:11434",
        )
        payload = {"models": [{"name": "qwen2.5-coder:7b"}]}

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
            return_value=_FakeResponse(200, payload),
        ) as urlopen:
            ok, lines = check_model_endpoint(cfg)

        self.assertTrue(ok)
        request_obj = urlopen.call_args.args[0]
        self.assertIn("/api/tags", request_obj.full_url)
        self.assertIn("provider_family=ollama", "\n".join(lines))

    def test_openai_compatible_probe_uses_models_and_finds_model(self) -> None:
        cfg = _cfg(
            model="openai:gpt-4o-mini",
            provider_url="https://api.example.com",
        )
        payload = {"data": [{"id": "gpt-4o-mini"}]}

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
            return_value=_FakeResponse(200, payload),
        ) as urlopen, patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "probe-token"},
        ):
            ok, lines = check_model_endpoint(cfg)

        self.assertTrue(ok)
        request_obj = urlopen.call_args.args[0]
        self.assertIn("/v1/models", request_obj.full_url)
        self.assertEqual(
            request_obj.get_header("Authorization"),
            "Bearer probe-token",
        )
        self.assertIn("provider_family=openai-compatible", "\n".join(lines))

    def test_ollama_probe_ignores_openai_api_key(self) -> None:
        cfg = _cfg(
            model="ollama:qwen2.5-coder:7b",
            provider_url="http://localhost:11434",
        )
        payload = {"models": [{"name": "qwen2.5-coder:7b"}]}

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
            return_value=_FakeResponse(200, payload),
        ) as urlopen, patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "probe-token"},
        ):
            ok, _lines = check_model_endpoint(cfg)

        self.assertTrue(ok)
        request_obj = urlopen.call_args.args[0]
        self.assertIsNone(request_obj.get_header("Authorization"))

    def test_openai_listing_unsupported_is_warning(self) -> None:
        cfg = _cfg(
            model="openai:gpt-4o-mini",
            provider_url="https://api.example.com",
        )
        payload = {"error": {"message": "listing not supported"}}

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
            return_value=_FakeResponse(404, payload),
        ):
            ok, lines = check_model_endpoint(cfg)

        self.assertTrue(ok)
        self.assertIn(
            "model listing unsupported",
            "\n".join(lines),
        )

    def test_missing_model_fails_when_listing_available(self) -> None:
        cfg = _cfg(
            model="openai:gpt-4o-mini",
            provider_url="https://api.example.com",
        )
        payload = {"data": [{"id": "gpt-4o"}]}

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
            return_value=_FakeResponse(200, payload),
        ):
            ok, lines = check_model_endpoint(cfg)

        self.assertFalse(ok)
        self.assertIn("configured_model", "\n".join(lines))

    def test_connectivity_error_fails_probe(self) -> None:
        cfg = _cfg(
            model="ollama:qwen2.5-coder:7b",
            provider_url="http://localhost:11434",
        )

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
            side_effect=url_error.URLError("boom"),
        ):
            ok, lines = check_model_endpoint(cfg)

        self.assertFalse(ok)
        self.assertIn("reason=", "\n".join(lines))

    def test_non_openai_non_ollama_provider_is_skipped(self) -> None:
        cfg = _cfg(
            model="anthropic:claude-sonnet-4-6",
            provider_url="https://api.anthropic.com",
        )

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
        ) as urlopen:
            ok, lines = check_model_endpoint(cfg)

        self.assertTrue(ok)
        self.assertIn(
            "skipped unsupported provider family provider=anthropic",
            "\n".join(lines),
        )
        urlopen.assert_not_called()

    def test_unknown_provider_prefix_is_skipped(self) -> None:
        cfg = _cfg(
            model="totally-custom:my-model",
            provider_url="https://example.invalid",
        )

        with patch(
            "lllars_core.mcp.model_probe_support.url_request.urlopen",
        ) as urlopen:
            ok, lines = check_model_endpoint(cfg)

        self.assertTrue(ok)
        self.assertIn(
            "skipped unsupported provider family provider=unknown",
            "\n".join(lines),
        )
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
