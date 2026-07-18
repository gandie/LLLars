from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from lllars_core.config import RunConfig


def base_run_cfg() -> SimpleNamespace:
    project_root = Path("playground").resolve()
    return SimpleNamespace(
        model="test-model",
        provider_url="http://localhost:11434",
        project_root=project_root,
        mount_work_root=project_root,
        command_profile="none",
        test_command=None,
        eval_command=None,
        run=RunConfig(
            model="test-model",
            provider_url="http://localhost:11434",
            project_root=project_root,
        ),
    )
