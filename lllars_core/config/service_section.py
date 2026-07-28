from __future__ import annotations

from pathlib import Path

from lllars_core.config.models import ServiceConfig
from lllars_core.config.runtime_values import load_service_settings


def service_config(
    cfg: dict,
    *,
    service_mode: str,
    config_root: Path,
    config_path: Path,
    project_root_raw: str,
) -> tuple[ServiceConfig, Path]:
    service_values = load_service_settings(
        cfg,
        config_root=config_root,
        config_path=config_path,
        project_root_raw=project_root_raw,
    )
    return (
        ServiceConfig(
            mode=service_mode,
            host=service_values[0],
            port=service_values[1],
            workers=service_values[2],
            mount_work_root=service_values[3],
            mount_config_root=service_values[4],
            mount_artifacts_root=service_values[5],
            queue_backend=service_values[6],
            network_policy=service_values[7],
        ),
        service_values[8],
    )