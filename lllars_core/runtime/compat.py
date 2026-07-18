from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lllars_core.runtime_api import RuntimeService, create_runtime_app
    from lllars_core.runtime_runner import (
        ShellAdapterUnavailableError,
        run_job,
    )


__all__ = [
    "RuntimeService",
    "create_runtime_app",
    "ShellAdapterUnavailableError",
    "run_job",
]


# Import migration notes for T25:
# - Preferred import path for runtime entry points is lllars_core.runtime.
# - Legacy imports from lllars_core.runtime_api and lllars_core.runtime_runner
#   remain supported during the refactor window.
def __getattr__(name: str) -> Any:
    if name in {"RuntimeService", "create_runtime_app"}:
        from lllars_core import runtime_api as legacy_runtime_api

        return getattr(legacy_runtime_api, name)

    if name in {"ShellAdapterUnavailableError", "run_job"}:
        from lllars_core import runtime_runner as legacy_runtime_runner

        return getattr(legacy_runtime_runner, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
