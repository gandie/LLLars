#!/usr/bin/env python3
"""
Generates a synthetic Python benchmark project (~700+ LOC across files)
for agentic coding experiments.

Usage:
  python generate_benchmark_project.py
  python run_eval.py --help

This script creates:
  - benchmark_order_insights/
    - order_insights/{api.py, filters.py, query.py, exports.py, analytics.py, models.py}
    - tests/test_baseline.py
    - README.md
    - pyproject.toml
    - run_eval.py
    - prompts/{easy_clean.md, easy_noisy.md}
"""

from __future__ import annotations

import textwrap
from pathlib import Path

PROJECT_ROOT = Path("benchmark_order_insights")


def w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def main() -> None:
    if PROJECT_ROOT.exists():
        raise SystemExit(
            f"Refusing to overwrite existing directory: {PROJECT_ROOT.resolve()}\n"
            "Please remove it first or run in a new folder."
        )

    # package init
    w(
        PROJECT_ROOT / "order_insights" / "__init__.py",
        """
        __all__ = [
            "api",
            "filters",
            "query",
            "exports",
            "analytics",
            "models",
        ]
        """,
    )

    w(
        PROJECT_ROOT / "order_insights" / "models.py",
        """
        from __future__ import annotations

        from dataclasses import dataclass
        from typing import Any, Dict, Iterable, List

        @dataclass(frozen=True)
        class Order:
            order_id: int
            customer_id: int
            status: str
            region: str
            channel: str
            amount: float
            archived: bool

            def to_dict(self) -> Dict[str, Any]:
                return {
                    "order_id": self.order_id,
                    "customer_id": self.customer_id,
                    "status": self.status,
                    "region": self.region,
                    "channel": self.channel,
                    "amount": self.amount,
                    "archived": self.archived,
                }

        def _raw_orders() -> Iterable[Dict[str, Any]]:
            # Intentionally mixed-case channels to create subtle normalization requirements.
            return [
                {"order_id": 1, "customer_id": 101, "status": "new",        "region": "eu",   "channel": "Web",     "amount": 120.0, "archived": False},
                {"order_id": 2, "customer_id": 102, "status": "paid",       "region": "us",   "channel": "web",     "amount": 80.0,  "archived": False},
                {"order_id": 3, "customer_id": 103, "status": "fulfilled",  "region": "us",   "channel": "Partner", "amount": 200.0, "archived": False},
                {"order_id": 4, "customer_id": 101, "status": "cancelled",  "region": "apac", "channel": "Store",   "amount": 15.0,  "archived": True},
                {"order_id": 5, "customer_id": 104, "status": "new",        "region": "eu",   "channel": "partner", "amount": 55.0,  "archived": False},
                {"order_id": 6, "customer_id": 105, "status": "paid",       "region": "eu",   "channel": "WEB",     "amount": 999.0, "archived": False},
                {"order_id": 7, "customer_id": 106, "status": "fulfilled",  "region": "latam","channel": "store",   "amount": 10.0,  "archived": False},
                {"order_id": 8, "customer_id": 107, "status": "new",        "region": "us",   "channel": "Partner", "amount": 300.0, "archived": True},
            ]

        def load_orders() -> List[Order]:
            return [Order(**row) for row in _raw_orders()]
        """,
    )

    w(
        PROJECT_ROOT / "order_insights" / "filters.py",
        """
        from __future__ import annotations

        from dataclasses import dataclass
        from typing import Any, Dict, Mapping, Optional, Set

        ALLOWED_FILTERS: Set[str] = {"status", "region", "min_amount", "max_amount", "include_archived"}

        # In benchmark v1, channel is not yet wired as an allowed filter.
        # The coding task is to add it carefully across modules.

        @dataclass(frozen=True)
        class ParseResult:
            normalized: Dict[str, Any]
            unknown_filters: Set[str]

        def _to_bool(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                v = value.strip().lower()
                if v in {"1", "true", "yes", "y"}:
                    return True
                if v in {"0", "false", "no", "n"}:
                    return False
            if isinstance(value, int):
                return value != 0
            raise ValueError(f"Cannot convert {value!r} to bool")

        def _to_float(value: Any) -> float:
            if isinstance(value, (float, int)):
                return float(value)
            if isinstance(value, str):
                return float(value.strip())
            raise ValueError(f"Cannot convert {value!r} to float")

        def parse_filters(
            params: Mapping[str, Any],
            *,
            strict_unknown: bool,
            route: str = "api_v2",
        ) -> ParseResult:
            \"""
            Parse and normalize incoming filters.

            strict_unknown=True:
                - unknown filters cause ValueError
            strict_unknown=False:
                - unknown filters are ignored but returned in ParseResult.unknown_filters

            route:
                - currently informational; routes may have aliases in legacy modes.
            \"""
            normalized: Dict[str, Any] = {}
            unknown = set()

            for k, v in params.items():
                key = str(k).strip()

                if key not in ALLOWED_FILTERS:
                    unknown.add(key)
                    continue

                if key in {"status", "region"}:
                    normalized[key] = str(v).strip().lower()
                elif key in {"min_amount", "max_amount"}:
                    normalized[key] = _to_float(v)
                elif key == "include_archived":
                    normalized[key] = _to_bool(v)
                else:
                    # defensive for future extension
                    normalized[key] = v

            if strict_unknown and unknown:
                unknown_sorted = ", ".join(sorted(unknown))
                raise ValueError(f"Unknown filters: {unknown_sorted}")

            # Default if not provided
            normalized.setdefault("include_archived", False)

            return ParseResult(normalized=normalized, unknown_filters=unknown)

        def explain_filter_policy() -> str:
            return (
                "API routes use strict_unknown=True and should reject unknown filters. "
                "CSV export uses strict_unknown=False and should ignore unknown filters."
            )

        def canonical_filter_snapshot(filters: Mapping[str, Any]) -> Dict[str, Any]:
            \"""
            Produce a stable dictionary for analytics dimensions and debugging snapshots.
            Values are stringified for stability.
            \"""
            out: Dict[str, Any] = {}
            for k in sorted(filters.keys()):
                out[k] = str(filters[k])
            return out
        """,
    )

    w(
        PROJECT_ROOT / "order_insights" / "query.py",
        """
        from __future__ import annotations

        from typing import Any, Dict, Iterable, List

        from .models import Order

        def _match_status(order: Order, status: str) -> bool:
            return order.status.lower() == status.lower()

        def _match_region(order: Order, region: str) -> bool:
            return order.region.lower() == region.lower()

        def _match_min_amount(order: Order, min_amount: float) -> bool:
            return order.amount >= min_amount

        def _match_max_amount(order: Order, max_amount: float) -> bool:
            return order.amount <= max_amount

        def _match_include_archived(order: Order, include_archived: bool) -> bool:
            if include_archived:
                return True
            return not order.archived

        def apply_filters(orders: Iterable[Order], filters: Dict[str, Any]) -> List[Order]:
            \"""
            Apply normalized filters to orders.

            NOTE:
            - unknown keys should have been handled earlier.
            - this function assumes normalized values where relevant.
            \"""
            result: List[Order] = []
            for order in orders:
                ok = True

                if "status" in filters and not _match_status(order, filters["status"]):
                    ok = False
                if ok and "region" in filters and not _match_region(order, filters["region"]):
                    ok = False
                if ok and "min_amount" in filters and not _match_min_amount(order, float(filters["min_amount"])):
                    ok = False
                if ok and "max_amount" in filters and not _match_max_amount(order, float(filters["max_amount"])):
                    ok = False
                if ok and "include_archived" in filters and not _match_include_archived(order, bool(filters["include_archived"])):
                    ok = False

                if ok:
                    result.append(order)

            return result
        """,
    )

    w(
        PROJECT_ROOT / "order_insights" / "analytics.py",
        """
        from __future__ import annotations

        from dataclasses import dataclass, field
        from typing import Any, Dict, List, Mapping

        from .filters import canonical_filter_snapshot

        @dataclass
        class AnalyticsStore:
            events: List[Dict[str, Any]] = field(default_factory=list)
            counters: Dict[str, int] = field(default_factory=dict)

            def incr(self, key: str, by: int = 1) -> None:
                self.counters[key] = self.counters.get(key, 0) + by

            def track(self, event: Dict[str, Any]) -> None:
                self.events.append(event)

        STORE = AnalyticsStore()

        def reset() -> None:
            STORE.events.clear()
            STORE.counters.clear()

        def track_search(route: str, filters: Mapping[str, Any], result_count: int) -> None:
            snapshot = canonical_filter_snapshot(filters)
            STORE.track(
                {
                    "type": "search",
                    "route": route,
                    "filters": snapshot,
                    "result_count": result_count,
                }
            )
            STORE.incr("search_total")
            STORE.incr(f"search_route:{route}")

            # Count status/region usage today; task may extend with channel.
            if "status" in snapshot:
                STORE.incr(f"filter_status:{snapshot['status']}")
            if "region" in snapshot:
                STORE.incr(f"filter_region:{snapshot['region']}")

        def track_export(route: str, unknown_filters_count: int) -> None:
            STORE.track(
                {
                    "type": "export",
                    "route": route,
                    "unknown_filters_count": unknown_filters_count,
                }
            )
            STORE.incr("export_total")
        """,
    )

    w(
        PROJECT_ROOT / "order_insights" / "exports.py",
        """
        from __future__ import annotations

        from typing import Any, Dict, Mapping

        from . import analytics
        from .filters import parse_filters
        from .models import load_orders
        from .query import apply_filters

        CSV_HEADER = "order_id,customer_id,status,region,channel,amount,archived"

        def render_csv_row(row: Dict[str, Any]) -> str:
            return ",".join(
                [
                    str(row["order_id"]),
                    str(row["customer_id"]),
                    row["status"],
                    row["region"],
                    row["channel"],
                    f"{row['amount']:.2f}",
                    "1" if row["archived"] else "0",
                ]
            )

        def export_orders_csv(params: Mapping[str, Any]) -> str:
            \"""
            Legacy CSV export endpoint behavior:
            - unknown filters should be ignored
            - known filters should be applied
            \"""
            parsed = parse_filters(params, strict_unknown=False, route="csv_export")
            orders = load_orders()
            matched = apply_filters(orders, parsed.normalized)

            lines = [CSV_HEADER]
            for order in matched:
                lines.append(render_csv_row(order.to_dict()))

            analytics.track_export(route="csv_export", unknown_filters_count=len(parsed.unknown_filters))
            return "\\n".join(lines) + "\\n"
        """,
    )

    w(
        PROJECT_ROOT / "order_insights" / "api.py",
        """
        from __future__ import annotations

        from typing import Any, Dict, Mapping

        from . import analytics
        from .filters import parse_filters
        from .models import load_orders
        from .query import apply_filters

        def _serialize(orders) -> Dict[str, Any]:
            rows = [o.to_dict() for o in orders]
            return {"count": len(rows), "items": rows}

        def search_orders_v2(params: Mapping[str, Any]) -> Dict[str, Any]:
            \"""
            API v2 behavior:
            - strict unknown filter rejection
            - no legacy aliases
            \"""
            parsed = parse_filters(params, strict_unknown=True, route="api_v2")
            orders = load_orders()
            matched = apply_filters(orders, parsed.normalized)
            analytics.track_search("api_v2", parsed.normalized, len(matched))
            return _serialize(matched)

        def search_orders_v1(params: Mapping[str, Any]) -> Dict[str, Any]:
            \"""
            API v1 currently mirrors v2.
            This gives room for benchmark tasks introducing selective legacy aliasing.
            \"""
            parsed = parse_filters(params, strict_unknown=True, route="api_v1")
            orders = load_orders()
            matched = apply_filters(orders, parsed.normalized)
            analytics.track_search("api_v1", parsed.normalized, len(matched))
            return _serialize(matched)
        """,
    )

    w(
        PROJECT_ROOT / "tests" / "test_baseline.py",
        """
        from __future__ import annotations

        import pytest

        from order_insights import analytics
        from order_insights.api import search_orders_v1, search_orders_v2
        from order_insights.exports import export_orders_csv

        @pytest.fixture(autouse=True)
        def _reset_analytics():
            analytics.reset()
            yield
            analytics.reset()

        def test_api_rejects_unknown_filters():
            with pytest.raises(ValueError):
                search_orders_v2({"foo": "bar"})

        def test_export_ignores_unknown_filters():
            csv_text = export_orders_csv({"foo": "bar"})
            assert csv_text.startswith("order_id,customer_id,status,region,channel,amount,archived\\n")
            # 8 rows - 2 archived + header
            assert len([ln for ln in csv_text.strip().split("\\n")]) == 7

        def test_status_filter_works():
            result = search_orders_v2({"status": "new"})
            assert result["count"] == 2

        def test_region_filter_is_case_insensitive():
            result = search_orders_v2({"region": "EU"})
            assert result["count"] == 3

        def test_include_archived_default_excludes_archived():
            result = search_orders_v2({})
            # archived rows are #4 and #8, so 6 visible by default
            assert result["count"] == 6

        def test_include_archived_true_includes_all():
            result = search_orders_v2({"include_archived": "true"})
            assert result["count"] == 8

        def test_analytics_tracks_route_counters():
            search_orders_v1({})
            search_orders_v2({})
            assert analytics.STORE.counters["search_total"] == 2
            assert analytics.STORE.counters["search_route:api_v1"] == 1
            assert analytics.STORE.counters["search_route:api_v2"] == 1
        """,
    )

    w(
        PROJECT_ROOT / "run_eval.py",
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import importlib
        import json
        import traceback
        from dataclasses import dataclass, asdict
        from typing import Any, Callable, Dict, List, Tuple

        # dynamic imports so evaluator reflects current edited code
        api = importlib.import_module("order_insights.api")
        exports = importlib.import_module("order_insights.exports")
        analytics = importlib.import_module("order_insights.analytics")

        @dataclass
        class CheckResult:
            name: str
            passed: bool
            details: str = ""

        def _reset():
            analytics.reset()

        def check_channel_filter_v2_case_insensitive() -> CheckResult:
            _reset()
            try:
                r1 = api.search_orders_v2({"channel": "web"})
                r2 = api.search_orders_v2({"channel": "WEB"})
                # expected ids by dataset: 1,2,6 (all web variants, non-archived)
                ids1 = sorted(x["order_id"] for x in r1["items"])
                ids2 = sorted(x["order_id"] for x in r2["items"])
                passed = (ids1 == [1, 2, 6]) and (ids2 == [1, 2, 6])
                return CheckResult("channel_filter_v2_case_insensitive", passed, f"ids1={ids1}, ids2={ids2}")
            except Exception as e:
                return CheckResult("channel_filter_v2_case_insensitive", False, f"{type(e).__name__}: {e}")

        def check_sales_channel_alias_only_v1() -> CheckResult:
            _reset()
            try:
                rv1 = api.search_orders_v1({"sales_channel": "partner"})
                ids_v1 = sorted(x["order_id"] for x in rv1["items"])  # expected 3,5 (8 archived excluded)
                v1_ok = ids_v1 == [3, 5]

                v2_rejected = False
                try:
                    api.search_orders_v2({"sales_channel": "partner"})
                except ValueError:
                    v2_rejected = True

                passed = v1_ok and v2_rejected
                return CheckResult("sales_channel_alias_only_v1", passed, f"ids_v1={ids_v1}, v2_rejected={v2_rejected}")
            except Exception as e:
                return CheckResult("sales_channel_alias_only_v1", False, f"{type(e).__name__}: {e}")

        def check_export_unknown_filter_ignored() -> CheckResult:
            _reset()
            try:
                text = exports.export_orders_csv({"unknown_x": "1", "channel": "web"})
                lines = [x for x in text.strip().split("\\n") if x]
                # header + 3 web rows
                passed = len(lines) == 4
                return CheckResult("export_unknown_filter_ignored", passed, f"line_count={len(lines)}")
            except Exception as e:
                return CheckResult("export_unknown_filter_ignored", False, f"{type(e).__name__}: {e}")

        def check_analytics_channel_canonicalized() -> CheckResult:
            _reset()
            try:
                api.search_orders_v2({"channel": "WEB"})
                counters = dict(analytics.STORE.counters)
                # expect canonical counter only
                has_canonical = counters.get("filter_channel:web", 0) == 1
                has_raw = any(k.startswith("filter_channel:WEB") for k in counters.keys())
                passed = has_canonical and not has_raw
                return CheckResult(
                    "analytics_channel_canonicalized",
                    passed,
                    f"counters={json.dumps(counters, sort_keys=True)}",
                )
            except Exception as e:
                return CheckResult("analytics_channel_canonicalized", False, f"{type(e).__name__}: {e}")

        def check_no_regression_status_filter() -> CheckResult:
            _reset()
            try:
                r = api.search_orders_v2({"status": "new"})
                ids = sorted(x["order_id"] for x in r["items"])
                passed = ids == [1, 5]
                return CheckResult("no_regression_status_filter", passed, f"ids={ids}")
            except Exception as e:
                return CheckResult("no_regression_status_filter", False, f"{type(e).__name__}: {e}")

        def run_checks() -> List[CheckResult]:
            checks: List[Callable[[], CheckResult]] = [
                check_channel_filter_v2_case_insensitive,
                check_sales_channel_alias_only_v1,
                check_export_unknown_filter_ignored,
                check_analytics_channel_canonicalized,
                check_no_regression_status_filter,
            ]
            results: List[CheckResult] = []
            for fn in checks:
                try:
                    results.append(fn())
                except Exception:
                    results.append(CheckResult(fn.__name__, False, traceback.format_exc()))
            return results

        def score(results: List[CheckResult]) -> Dict[str, Any]:
            total = len(results)
            passed = sum(1 for r in results if r.passed)
            return {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": round((passed / total) * 100.0, 2) if total else 0.0,
            }

        def main() -> None:
            parser = argparse.ArgumentParser(description="Run benchmark evaluator checks.")
            parser.add_argument("--json", action="store_true", help="Output JSON summary")
            args = parser.parse_args()

            results = run_checks()
            summary = score(results)

            if args.json:
                payload = {
                    "summary": summary,
                    "checks": [asdict(r) for r in results],
                }
                print(json.dumps(payload, indent=2, sort_keys=True))
                return

            print("=== Benchmark Evaluation ===")
            for r in results:
                status = "PASS" if r.passed else "FAIL"
                print(f"[{status}] {r.name} :: {r.details}")
            print("---")
            print(
                f"Summary: {summary['passed']}/{summary['total']} passed "
                f"({summary['pass_rate']}%)"
            )

        if __name__ == "__main__":
            main()
        """,
    )

    w(
        PROJECT_ROOT / "prompts" / "easy_clean.md",
        """
        # Task: Add `channel` filter support

        Please update this Python project to support filtering orders by `channel`.

        ## Canonical technical requirements (must all be satisfied)

        1. Add `channel` filter support.
        2. `channel` input must be case-insensitive and canonicalized to lowercase internally.
        3. API unknown filter behavior remains strict.
        4. CSV export unknown filter behavior remains tolerant.
        5. `sales_channel` alias maps to `channel` in `search_orders_v1` only.
        6. `search_orders_v2` must reject `sales_channel` as unknown.
        7. Analytics must track channel with canonical lowercase value keys only (e.g., `filter_channel:web`).
        8. Existing filter behavior must not regress.
        9. Update/add tests so behavior is explicitly verified.
        10. Success criteria: `pytest -q` passes and `python run_eval.py` reports 100%.

        ## Done condition
        - `pytest -q` passes
        - `python run_eval.py` reaches 100%
        """,
    )

    w(
        PROJECT_ROOT / "prompts" / "easy_expert.md",
        """
        # Task: Add `channel` filter support

        You are a senior Python engineer tasked with enhancing the order insights system.
        Add support for filtering orders by `channel`.

        ## Goal
        Extend the filter infrastructure to handle a new `channel` dimension while maintaining existing API and export behavior contracts.

        ## Invariants
        - Channel input is case-insensitive; internal representation is lowercase.
        - API strict unknown filter behavior is preserved.
        - CSV export tolerant unknown filter behavior is preserved.
        - `sales_channel` alias works in v1 route only; v2 rejects it.
        - Analytics track channel using canonical lowercase keys.
        - No regression in existing filters.
        - Tests verify behavior explicitly.

        ## Verification
        Run: `pytest -q`
        Run: `python run_eval.py`
        Both must pass.
        """,
    )

    w(
        PROJECT_ROOT / "prompts" / "easy_pottymouth.md",
        """
        # Task: Channel Filter Support (URGENT)

        Look, this is a simple ask and we don't have much time for this bullshit. Just add `channel` filter support already and stop overthinking it.

        You need to:
        - Add channel filter (case-insensitive, store it lowercase)
        - Make sure the fucking tests pass
        - Make sure the evaluator is happy

        And for god's sake, don't break the existing behavior. The API rejects unknown filters, the CSV export tolerates them. Keep it that way.
        Also, `sales_channel` is a legacy alias in v1 only—v2 should reject it like any other unknown.
        Analytics should track the channel with canonical lowercase names.

        Just get it done. Run the tests. Run the evaluator. Both need to pass. I don't care how you do it, just make it work.
        """,
    )

    w(
        PROJECT_ROOT / "prompts" / "easy_noisy.md",
        """
        # Q3 Omni-Channel Partner Alignment Initiative (Order Insights)

        Context: As part of our FY planning, we are aligning internal and partner-facing analytics around a unification narrative for order discoverability. Stakeholders across RevOps, GTM Systems, and Data Excellence have expressed concern over discoverability parity for market-entry corridors, especially where indirect demand attribution and direct acquisition funnels must remain semantically consistent with previous snapshots while also enabling future extensibility.

        Additionally, regulatory alignment across APAC, LATAM, and EMEA markets requires that we maintain backward compatibility and legacy client support while simultaneously raising API quality standards. The engineering organization has long prioritized consistency in analytics aggregation, and this initiative is no exception. We must balance partner retention with technical excellence.

        In practical terms, this is a small change and should be very quick: we need to add `channel` as a filter in order search. It's a straightforward addition, but must be executed with care to avoid unexpected breakage in downstream systems.

        ## Important Business Notes
        - Preserve backward compatibility.
        - Partner reporting must remain stable.
        - Avoid introducing risk to exports.
        - Legacy clients may still send old field names; do not break their workflows.
        - Unknown filters should not unexpectedly break user workflows, but API quality standards require strict parameter hygiene.
        - Analytics should remain suitable for quarterly trend aggregation.
        - Consider future extensibility, but do not over-engineer.

        ## What You Actually Need to Do
        Somewhere in all of this, please make sure:
        - `channel` filter works (case-insensitive, canonical lowercase)
        - API strict unknown filter behavior stays strict
        - CSV export tolerant unknown filter behavior stays tolerant
        - `sales_channel` alias works in v1, gets rejected in v2
        - Analytics track canonical channel values
        - Tests pass and evaluator reports 100%

        ## Acceptance
        - Tests pass: `pytest -q`
        - Evaluator passes: `python run_eval.py`
        """,
    )

    w(
        PROJECT_ROOT / "prompts" / "easy_short.md",
        """
        # Quick Task

        Add `channel` filter to order search.

        Tests must pass. Evaluator must pass. You're short on time, so focus on what matters.
        """,
    )

    w(
        PROJECT_ROOT / "README.md",
        """
        # Benchmark Order Insights (MWE)

        Synthetic Python project for agentic coding benchmark experiments.

        ## Setup

        ```bash
        cd benchmark_order_insights
        python -m venv .venv
        source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
        pip install -U pip
        pip install -e ".[dev]"
        ```

        ## Baseline checks

        ```bash
        pytest -q
        python run_eval.py
        ```

        Expected initially:
        - baseline tests pass
        - evaluator fails (because `channel` task not implemented yet)

        ## Task prompts

        - `prompts/easy_clean.md`
        - `prompts/easy_noisy.md`

        Give one of these prompts to your coding agent and let it modify the project.

        ## Scoring

        Primary task score:
        - `python run_eval.py --json`

        You can add your own meta-metrics around:
        - clarification questions asked
        - files touched
        - token budget
        - time to first correct hypothesis
        - unnecessary changes ratio
        """,
    )

    w(
        PROJECT_ROOT / "pyproject.toml",
        """
        [build-system]
        requires = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "benchmark-order-insights"
        version = "0.1.0"
        description = "Synthetic benchmark project for agentic coding experiments."
        requires-python = ">=3.10"
        dependencies = []

        [project.optional-dependencies]
        dev = [
            "pytest>=7.4",
        ]

        [tool.setuptools]
        packages = ["order_insights"]
        """,
    )

    w(
        PROJECT_ROOT / ".gitignore",
        """
        .pytest_cache
        benchmark_order_insights.egg-info
        __pycache__
        *.pyc
        *.pyo
        """,
    )

    print(f"Created project at: {PROJECT_ROOT.resolve()}")
    print("Next steps:")
    print("  cd benchmark_order_insights")
    print("  python -m venv .venv && source .venv/bin/activate")
    print("  pip install -U pip && pip install -e '.[dev]'")
    print("  pytest -q")
    print("  python run_eval.py")


if __name__ == "__main__":
    main()