from __future__ import annotations

import json
from pathlib import Path


def base_config(project_root: str, *, mount_work_root: str | None) -> dict[str, object]:
    service: dict[str, object] = {}
    if mount_work_root is not None:
        service["mount_work_root"] = mount_work_root
    return {
        "service": service,
        "run": {
            "model": "test-model",
            "provider_url": "http://localhost:11434",
            "project_root": project_root,
            "commands": {},
            "command_profile": "none",
        },
    }


def write_config(root: Path, payload: dict[str, object], *, name: str = "config.json") -> Path:
    path = root / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def default_service_block(*, workers: int = 1, queue_backend: str = "inmemory") -> dict[str, object]:
    return {
        "mode": "serve",
        "host": "0.0.0.0",
        "port": 9000,
        "workers": workers,
        "mount_work_root": "workspace",
        "mount_config_root": ".",
        "mount_artifacts_root": ".",
        "queue_backend": queue_backend,
        "network_policy": "inherit",
    }
