from __future__ import annotations

from typing import Any

from lllars_core.runtime import compat


__all__ = [
    "RuntimeService",
    "create_runtime_app",
    "ShellAdapterUnavailableError",
    "run_job",
]


def __getattr__(name: str) -> Any:
    return getattr(compat, name)
