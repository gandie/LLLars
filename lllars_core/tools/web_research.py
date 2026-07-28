from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from pydantic_ai.capabilities import WebFetch, WebSearch
from pydantic_ai.native_tools import WebSearchTool
from pydantic_ai.tools import Tool

if TYPE_CHECKING:
    from lllars_core.config import HarnessConfig


def _normalize_domains(
    domains: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(domain.strip().lower() for domain in domains if domain)


def _host_matches_domain(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def _url_permitted(
    url: str,
    allowed_domains: tuple[str, ...],
    blocked_domains: tuple[str, ...],
) -> bool:
    host = (urlparse(url).hostname or "").strip().lower()
    if not host:
        return False
    if blocked_domains and any(
        _host_matches_domain(host, domain)
        for domain in blocked_domains
    ):
        return False
    if allowed_domains:
        return any(
            _host_matches_domain(host, domain)
            for domain in allowed_domains
        )
    return True


def _filter_web_search_results(
    results: Iterable[Mapping[str, object]],
    *,
    allowed_domains: tuple[str, ...],
    blocked_domains: tuple[str, ...],
) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    for item in results:
        title = str(item.get("title", ""))
        href = str(item.get("href", ""))
        body = str(item.get("body", ""))
        if not href:
            continue
        if not _url_permitted(href, allowed_domains, blocked_domains):
            continue
        filtered.append(
            {
                "title": title,
                "href": href,
                "body": body,
            }
        )
    return filtered


def _local_web_search_tool(
    allowed_domains: tuple[str, ...],
    blocked_domains: tuple[str, ...],
) -> Tool[object]:
    async def local_web_search(query: str) -> list[dict[str, str]]:
        # Import lazily so native-only providers do not require local extras.
        from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

        search_tool = duckduckgo_search_tool()
        results = await search_tool.function(query)
        return _filter_web_search_results(
            results,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )

    return Tool(
        local_web_search,
        name="duckduckgo_search",
        description=(
            "Search DuckDuckGo and return results filtered by configured "
            "allowed/blocked domains."
        ),
    )


def _search_capability(
    allowed_domains: tuple[str, ...],
    blocked_domains: tuple[str, ...],
    local_fallback: bool,
) -> WebSearch:
    search_native = WebSearchTool(
        allowed_domains=(
            list(allowed_domains) if allowed_domains else None
        ),
        blocked_domains=(
            list(blocked_domains) if blocked_domains else None
        ),
    )
    search_local: Tool[object] | bool
    search_local = (
        _local_web_search_tool(allowed_domains, blocked_domains)
        if local_fallback
        else False
    )
    return WebSearch(native=search_native, local=search_local)


def _fetch_capability(
    allowed_domains: tuple[str, ...],
    blocked_domains: tuple[str, ...],
    local_fallback: bool,
) -> WebFetch:
    return WebFetch(
        local=local_fallback,
        allowed_domains=(
            list(allowed_domains) if allowed_domains else None
        ),
        blocked_domains=(
            list(blocked_domains) if blocked_domains else None
        ),
    )


def build_web_research_capabilities(cfg: "HarnessConfig") -> list[object]:
    if "native_web_research" not in set(cfg.enabled_tool_groups):
        return []
    if cfg.network_policy == "offline":
        return []

    allowed_domains = _normalize_domains(cfg.web_research_allowed_domains)
    blocked_domains = _normalize_domains(cfg.web_research_blocked_domains)
    local_fallback = cfg.web_research_local_fallback
    return [
        _search_capability(
            allowed_domains,
            blocked_domains,
            local_fallback,
        ),
        _fetch_capability(
            allowed_domains,
            blocked_domains,
            local_fallback,
        ),
    ]