from __future__ import annotations

from lllars_core.console import Color
from lllars_core.skills import configured_markdown_skill_ids


def _fmt(value: object) -> str:
    return "none" if value is None else str(value)


def _native_core_line(cfg: object) -> str:
    return (
        f"{Color.CYAN}[native-core]{Color.RESET} "
        f"request_limit={_fmt(cfg.usage_request_limit)}; "
        f"tool_calls_limit={_fmt(cfg.usage_tool_calls_limit)}; "
        f"input_tokens_limit={_fmt(cfg.usage_input_tokens_limit)}; "
        f"output_tokens_limit={_fmt(cfg.usage_output_tokens_limit)}; "
        f"total_tokens_limit={_fmt(cfg.usage_total_tokens_limit)}; "
        "count_tokens_before_request="
        f"{cfg.usage_count_tokens_before_request}; "
        "retries={"
        f"tools:{cfg.agent_retries_tools},"
        f"output:{cfg.agent_retries_output}"
        "}; "
        f"tool_timeout_sec={_fmt(cfg.tool_timeout_sec)}; "
        f"max_concurrency={_fmt(cfg.max_concurrency)}; "
        "instrumentation="
        f"{cfg.instrumentation_enabled}"
    )


def _skills_line(cfg: object) -> str:
    skill_ids = configured_markdown_skill_ids(cfg)
    skill_ids_text = ", ".join(skill_ids) if skill_ids else "none"
    return (
        f"{Color.CYAN}[skills]{Color.RESET} "
        f"enabled={cfg.skills_enabled}; "
        f"defer_loading={cfg.skills_defer_loading}; "
        f"loaded={len(skill_ids)}; "
        f"ids={skill_ids_text}"
    )


def _mcp_line(cfg: object) -> str:
    mcp_config_text = (
        str(cfg.mcp_config_path)
        if cfg.mcp_config_path is not None
        else "none"
    )
    return (
        f"{Color.CYAN}[mcp]{Color.RESET} "
        f"enabled={cfg.mcp_enabled}; "
        f"config={mcp_config_text}; "
        f"init_timeout_sec={cfg.mcp_init_timeout_sec}"
    )


def _runtime_line(cfg: object) -> str:
    return (
        f"{Color.CYAN}[runtime]{Color.RESET} "
        f"service_mode={cfg.service_mode}; "
        f"service_host={cfg.service_host}; "
        f"service_port={cfg.service_port}; "
        f"service_workers={cfg.service_workers}; "
        f"mount_work_root={cfg.mount_work_root}; "
        f"mount_config_root={cfg.mount_config_root}; "
        f"mount_artifacts_root={cfg.mount_artifacts_root}; "
        f"queue_backend={cfg.queue_backend}; "
        f"network_policy={cfg.network_policy}"
    )


def print_runtime_startup(cfg: object) -> None:
    print(_native_core_line(cfg))
    print(_skills_line(cfg))
    print(_mcp_line(cfg))
    print(_runtime_line(cfg))


__all__ = ["print_runtime_startup"]
