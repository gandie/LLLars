from __future__ import annotations

import json
from pathlib import Path

from lllars_core.config.builders import build_harness_config
from lllars_core.config.env_layer import build_service_env_layer
from lllars_core.config.env_layer import parse_env_file
from lllars_core.config.loader_steps import resolve_run_inputs
from lllars_core.config.loader_steps import RuntimeInputs
from lllars_core.config.loader_steps import runtime_inputs
from lllars_core.config.service_section import service_config
from lllars_core.config.run_cfg_loader import build_run_cfg
from lllars_core.config.models import (
    DEFAULT_COMMAND_PROFILE,
    DEFAULT_QUEUE_BACKEND,
    DEFAULT_SERVICE_MODE,
    VALID_SERVICE_MODES,
    HarnessConfig,
    RunConfig,
    ServiceConfig,
)
from lllars_core.config.runtime_section import (
    validate_choice,
)


def _load_config_object(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("Top-level config must be a JSON object")
    return cfg


def _load_service_env_layer(
    config_root: Path,
    raw_cfg: dict,
) -> dict[str, object]:
    env_file_raw = str(raw_cfg.get("env_file", "")).strip()
    if not env_file_raw:
        return {}
    env_file_path = Path(env_file_raw)
    if not env_file_path.is_absolute():
        env_file_path = (config_root / env_file_path).resolve()
    return build_service_env_layer(parse_env_file(env_file_path))


def _reject_unknown_root_keys(raw_cfg: dict) -> None:
    allowed = {"service", "run", "env_file"}
    unknown = [key for key in raw_cfg if key not in allowed]
    if unknown:
        unknown_text = ", ".join(sorted(unknown))
        raise ValueError(f"Config has unsupported root keys: {unknown_text}")


def _section(raw_cfg: dict, name: str) -> dict:
    section = raw_cfg.get(name, {})
    if name in raw_cfg and not isinstance(section, dict):
        raise ValueError(f"Config {name} must be an object")
    return dict(section)


def _defaults() -> dict[str, object]:
    return {
        "service_mode": DEFAULT_SERVICE_MODE,
        "queue_backend": DEFAULT_QUEUE_BACKEND,
        "command_profile": DEFAULT_COMMAND_PROFILE,
        "shell_mode": "auto",
        "shell_override": "",
    }


SERVICE_KEY_MAP = {
    "mode": "service_mode",
    "host": "service_host",
    "port": "service_port",
    "workers": "service_workers",
    "mount_work_root": "mount_work_root",
    "mount_config_root": "mount_config_root",
    "mount_artifacts_root": "mount_artifacts_root",
    "queue_backend": "queue_backend",
    "network_policy": "network_policy",
}


def _service_flat(service_section: dict) -> dict[str, object]:
    return {
        flat_key: service_section[split_key]
        for split_key, flat_key in SERVICE_KEY_MAP.items()
        if split_key in service_section
    }


def _split_cfg(
    config_path: Path,
    overrides: dict[str, object] | None,
) -> tuple[dict, dict, Path]:
    raw_cfg = _load_config_object(config_path)
    _reject_unknown_root_keys(raw_cfg)
    config_root = config_path.parent.resolve()
    run_cfg = _section(raw_cfg, "run")
    service_cfg = _service_flat(_section(raw_cfg, "service"))
    if overrides:
        service_cfg.update(
            {
                key: value
                for key, value in overrides.items()
                if key in SERVICE_KEY_MAP.values()
            }
        )
        run_cfg.update(
            {
                key: value
                for key, value in overrides.items()
                if key not in SERVICE_KEY_MAP.values()
            }
        )
    # env_file has highest precedence for service settings.
    service_cfg.update(_load_service_env_layer(config_root, raw_cfg))
    service_cfg = {**_defaults(), **service_cfg}
    run_cfg = {**_defaults(), **run_cfg}
    return service_cfg, run_cfg, config_root


def _build_configs(
    service_cfg: dict,
    run_cfg: dict,
    *,
    service_mode: str,
    config_root: Path,
    config_path: Path,
) -> tuple[RuntimeInputs, ServiceConfig, RunConfig]:
    model, provider_url, project_root_raw = resolve_run_inputs(
        service_mode,
        run_cfg,
    )
    runtime = runtime_inputs(run_cfg, config_root=config_root)
    service_cfg, project_root = service_config(
        service_cfg,
        service_mode=service_mode,
        config_root=config_root,
        config_path=config_path,
        project_root_raw=project_root_raw,
    )
    run_cfg = build_run_cfg(
        run_cfg,
        runtime=runtime,
        model=model,
        provider_url=provider_url,
        project_root=project_root,
    )
    return runtime, service_cfg, run_cfg


def load_config(
    config_path: Path,
    *,
    overrides: dict[str, object] | None = None,
) -> HarnessConfig:
    service_cfg, run_cfg, config_root = _split_cfg(config_path, overrides)
    service_mode = validate_choice(
        service_cfg,
        "service_mode",
        default=DEFAULT_SERVICE_MODE,
        valid_values=VALID_SERVICE_MODES,
    )
    runtime, service_cfg, run_cfg = _build_configs(
        service_cfg,
        run_cfg,
        service_mode=service_mode,
        config_root=config_root,
        config_path=config_path,
    )
    return build_harness_config(
        run_cfg,
        service_cfg,
        allowed_shell_commands=runtime.allowed_shell_commands,
        system_prompt=runtime.system_prompt,
        tool_policy=runtime.tool_policy,
        enabled_tool_groups=runtime.enabled_tool_groups,
        plugin_tool_paths=runtime.plugin_tool_paths,
        command_profile=runtime.command_profile,
        command_profiles=runtime.command_profiles,
    )
