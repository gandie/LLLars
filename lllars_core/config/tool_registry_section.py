from __future__ import annotations

from lllars_core.config.models import DEFAULT_ENABLED_TOOL_GROUPS

KNOWN_TOOL_GROUPS: tuple[str, ...] = (
    "native_files",
    "native_file_read",
    "native_file_write",
    "native_shell",
    "plugin_local",
    "mcp_toolsets",
)


def _normalize_string_list(
    value: object,
    *,
    field_name: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")

    normalized: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text:
            raise ValueError(f"{field_name} entries must be non-empty")
        normalized.append(text)
    return tuple(normalized)


def _validate_group_duplicates(
    enabled: tuple[str, ...],
    disabled: tuple[str, ...],
) -> None:
    if len(set(enabled)) != len(enabled):
        raise ValueError("run.tool_groups.enabled contains duplicates")
    if len(set(disabled)) != len(disabled):
        raise ValueError("run.tool_groups.disabled contains duplicates")


def _validate_group_names(groups: tuple[str, ...]) -> None:
    for group in groups:
        if group in KNOWN_TOOL_GROUPS:
            continue
        available = ", ".join(KNOWN_TOOL_GROUPS)
        raise ValueError(
            "Unknown tool group "
            f"{group!r}. Available groups: {available}"
        )


def _validate_group_overlap(
    enabled: tuple[str, ...],
    disabled: tuple[str, ...],
) -> None:
    overlap = set(enabled) & set(disabled)
    if not overlap:
        return
    overlap_text = ", ".join(sorted(overlap))
    raise ValueError(
        "run.tool_groups.enabled and disabled overlap: "
        f"{overlap_text}"
    )


def resolve_enabled_tool_groups(cfg: dict) -> tuple[str, ...]:
    tool_groups = cfg.get("tool_groups")
    if tool_groups is None:
        return DEFAULT_ENABLED_TOOL_GROUPS
    if not isinstance(tool_groups, dict):
        raise ValueError("run.tool_groups must be an object")

    enabled = _normalize_string_list(
        tool_groups.get("enabled"),
        field_name="run.tool_groups.enabled",
    )
    disabled = _normalize_string_list(
        tool_groups.get("disabled"),
        field_name="run.tool_groups.disabled",
    )
    _validate_group_duplicates(enabled, disabled)
    _validate_group_names(enabled + disabled)
    _validate_group_overlap(enabled, disabled)

    enabled_groups = enabled or DEFAULT_ENABLED_TOOL_GROUPS
    disabled_set = set(disabled)
    return tuple(
        group for group in enabled_groups if group not in disabled_set
    )


def resolve_plugin_tool_paths(cfg: dict) -> tuple[str, ...]:
    plugin_cfg = cfg.get("tool_plugins")
    if plugin_cfg is None:
        return ()
    if not isinstance(plugin_cfg, dict):
        raise ValueError("run.tool_plugins must be an object")

    plugin_paths = _normalize_string_list(
        plugin_cfg.get("paths"),
        field_name="run.tool_plugins.paths",
    )
    if len(set(plugin_paths)) != len(plugin_paths):
        raise ValueError("run.tool_plugins.paths contains duplicates")
    return plugin_paths
