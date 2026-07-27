from __future__ import annotations

from collections.abc import Callable
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

from lllars_core.tools.descriptors import AgentDeps
from lllars_core.tools.native import resolve_under

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from lllars_core.config import HarnessConfig


def _append_discovered_path(
    discovered_paths: list[Path],
    seen_paths: set[Path],
    path: Path,
) -> None:
    resolved = path.resolve()
    if resolved in seen_paths:
        raise ValueError(f"Duplicate plugin module path: {resolved}")
    seen_paths.add(resolved)
    discovered_paths.append(resolved)


def _module_files_from_source(source: Path) -> tuple[Path, ...]:
    if source.is_file():
        if source.suffix.lower() != ".py":
            raise ValueError(
                "Plugin file must be a Python module (*.py): "
                f"{source}"
            )
        return (source,)

    if source.is_dir():
        module_files = sorted(
            item
            for item in source.rglob("*.py")
            if item.is_file() and "__pycache__" not in item.parts
        )
        if not module_files:
            raise ValueError(
                "Plugin directory contains no Python modules: "
                f"{source}"
            )
        return tuple(module_files)

    raise ValueError(f"Unsupported plugin path type: {source}")


def _safe_plugin_source(project_root: Path, raw_path: str) -> Path:
    try:
        return resolve_under(project_root, raw_path)
    except ValueError as exc:
        raise ValueError(
            "Unsafe plugin path outside project_root: "
            f"{raw_path}"
        ) from exc


def _plugin_module_paths(
    project_root: Path,
    configured_paths: tuple[str, ...],
) -> tuple[Path, ...]:
    discovered_paths: list[Path] = []
    seen_paths: set[Path] = set()

    for raw_path in configured_paths:
        source = _safe_plugin_source(project_root, raw_path)

        if not source.exists():
            raise ValueError(f"Plugin path not found: {source}")
        for module_file in _module_files_from_source(source):
            _append_discovered_path(discovered_paths, seen_paths, module_file)

    return tuple(discovered_paths)


def _load_plugin_register(module_path: Path) -> Callable[..., None]:
    module_name = "lllars_plugin_" + "_".join(
        "".join(
            character if character.isalnum() else "_"
            for character in segment
        )
        for segment in module_path.parts
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Failed to create plugin spec: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    register_fn = getattr(module, "register_tools", None)
    if not callable(register_fn):
        raise ValueError(
            "Plugin module is missing callable register_tools(agent, cfg, "
            f"tool_error): {module_path}"
        )
    return register_fn


def register_local_plugin_tools(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    for module_path in _plugin_module_paths(
        cfg.project_root,
        cfg.plugin_tool_paths,
    ):
        register_fn = _load_plugin_register(module_path)
        try:
            register_fn(agent=agent, cfg=cfg, tool_error=tool_error)
        except Exception as exc:
            raise ValueError(
                "Plugin register_tools failed "
                f"for {module_path}: {exc}"
            ) from exc
