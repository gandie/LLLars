from __future__ import annotations

from pathlib import Path

SERVICE_ENV_TO_CONFIG_KEY = {
    "SERVICE_MODE": "service_mode",
    "LLLARS_HOST": "service_host",
    "SERVICE_HOST": "service_host",
    "LLLARS_PORT": "service_port",
    "SERVICE_PORT": "service_port",
    "LLLARS_WORKERS": "service_workers",
    "SERVICE_WORKERS": "service_workers",
    "QUEUE_BACKEND": "queue_backend",
    "NETWORK_POLICY": "network_policy",
    "MOUNT_WORK_ROOT": "mount_work_root",
    "MOUNT_CONFIG_ROOT": "mount_config_root",
    "MOUNT_ARTIFACTS_ROOT": "mount_artifacts_root",
}


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file():
        raise ValueError(f"Invalid env_file path: {path}")

    env: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def build_service_env_layer(raw_env: dict[str, str]) -> dict[str, object]:
    layer: dict[str, object] = {}
    for env_key, cfg_key in SERVICE_ENV_TO_CONFIG_KEY.items():
        if env_key in raw_env:
            layer[cfg_key] = raw_env[env_key]
    return layer
