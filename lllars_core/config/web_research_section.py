from __future__ import annotations

from lllars_core.config.models import (
    DEFAULT_WEB_RESEARCH_DOMAIN_POLICY,
    DEFAULT_WEB_RESEARCH_LOCAL_FALLBACK,
    VALID_WEB_RESEARCH_DOMAIN_POLICIES,
)
from lllars_core.config.runtime_section import as_bool


def _normalize_domains(
    value: object,
    *,
    field_name: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    domains = tuple(str(item).strip().lower() for item in value)
    if any(not domain for domain in domains):
        raise ValueError(f"{field_name} entries must be non-empty")
    if len(set(domains)) != len(domains):
        raise ValueError(f"{field_name} contains duplicates")
    return domains


def _resolve_domain_policy(web_research: dict) -> str:
    policy = str(
        web_research.get(
            "domain_policy",
            DEFAULT_WEB_RESEARCH_DOMAIN_POLICY,
        )
    ).strip().lower()
    if policy in VALID_WEB_RESEARCH_DOMAIN_POLICIES:
        return policy
    available = ", ".join(sorted(VALID_WEB_RESEARCH_DOMAIN_POLICIES))
    raise ValueError(
        "run.web_research.domain_policy must be one of: "
        f"{available}"
    )


def _validate_web_research_fields(web_research: dict) -> None:
    allowed = {
        "domain_policy",
        "allowed_domains",
        "blocked_domains",
        "local_fallback",
    }
    unknown = sorted(key for key in web_research if key not in allowed)
    if unknown:
        unknown_text = ", ".join(unknown)
        raise ValueError(
            "run.web_research has unsupported keys: "
            f"{unknown_text}"
        )


def _validate_domain_policy(
    domain_policy: str,
    allowed_domains: tuple[str, ...],
    blocked_domains: tuple[str, ...],
) -> None:
    if domain_policy == "none" and (allowed_domains or blocked_domains):
        raise ValueError(
            "run.web_research.domain_policy='none' requires "
            "empty allowed_domains and blocked_domains"
        )
    if domain_policy == "allowlist":
        if not allowed_domains:
            raise ValueError(
                "run.web_research.allowed_domains is required "
                "when domain_policy='allowlist'"
            )
        if blocked_domains:
            raise ValueError(
                "run.web_research.blocked_domains must be empty "
                "when domain_policy='allowlist'"
            )
    if domain_policy == "denylist":
        if not blocked_domains:
            raise ValueError(
                "run.web_research.blocked_domains is required "
                "when domain_policy='denylist'"
            )
        if allowed_domains:
            raise ValueError(
                "run.web_research.allowed_domains must be empty "
                "when domain_policy='denylist'"
            )


def _normalized_web_research_values(
    web_research: dict,
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    domain_policy = _resolve_domain_policy(web_research)
    allowed_domains = _normalize_domains(
        web_research.get("allowed_domains"),
        field_name="run.web_research.allowed_domains",
    )
    blocked_domains = _normalize_domains(
        web_research.get("blocked_domains"),
        field_name="run.web_research.blocked_domains",
    )
    _validate_domain_policy(
        domain_policy,
        allowed_domains,
        blocked_domains,
    )
    return domain_policy, allowed_domains, blocked_domains


def resolve_web_research_settings(
    cfg: dict,
) -> tuple[str, tuple[str, ...], tuple[str, ...], bool]:
    web_research_raw = cfg.get("web_research")
    if web_research_raw is None:
        return (
            DEFAULT_WEB_RESEARCH_DOMAIN_POLICY,
            (),
            (),
            DEFAULT_WEB_RESEARCH_LOCAL_FALLBACK,
        )
    if not isinstance(web_research_raw, dict):
        raise ValueError("run.web_research must be an object")

    web_research = dict(web_research_raw)
    _validate_web_research_fields(web_research)
    domain_policy, allowed_domains, blocked_domains = (
        _normalized_web_research_values(web_research)
    )
    local_fallback = as_bool(
        web_research.get(
            "local_fallback",
            DEFAULT_WEB_RESEARCH_LOCAL_FALLBACK,
        ),
        DEFAULT_WEB_RESEARCH_LOCAL_FALLBACK,
    )
    return (
        domain_policy,
        allowed_domains,
        blocked_domains,
        local_fallback,
    )
