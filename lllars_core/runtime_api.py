from __future__ import annotations

from lllars_core.runtime.api import create_runtime_app
from lllars_core.runtime.service import RuntimeService


IMPORT_MIGRATION_NOTE = (
    "Preferred import path: lllars_core.runtime.create_runtime_app and "
    "lllars_core.runtime.RuntimeService"
)


__all__ = [
    "IMPORT_MIGRATION_NOTE",
    "RuntimeService",
    "create_runtime_app",
]
