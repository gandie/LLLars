from __future__ import annotations

from pathlib import Path

from lllars_core.config.builders import build_run_config
from lllars_core.config.loader_steps import RuntimeInputs
from lllars_core.config.run_core_fields import run_core_from_inputs
from lllars_core.config.runtime_values import (
    load_mcp_settings,
    load_skills_settings,
)


def build_run_cfg(
    run_cfg: dict,
    *,
    runtime: RuntimeInputs,
    model: str,
    provider_url: str,
    project_root: Path,
):
    core_fields = run_core_from_inputs(
        model=model,
        provider_url=provider_url,
        project_root=project_root,
        test_command=runtime.test_command,
        eval_command=runtime.eval_command,
        command_profile=runtime.command_profile,
        enabled_tool_groups=runtime.enabled_tool_groups,
        plugin_tool_paths=runtime.plugin_tool_paths,
        web_research_settings=(
            runtime.web_research_domain_policy,
            runtime.web_research_allowed_domains,
            runtime.web_research_blocked_domains,
            runtime.web_research_local_fallback,
        ),
        eval_expect_json=runtime.eval_expect_json,
        eval_success_pass_rate=runtime.eval_success_pass_rate,
        system_prompt=runtime.system_prompt,
        tool_policy=runtime.tool_policy,
    )
    return build_run_config(
        run_cfg,
        core_fields=core_fields,
        skills_settings=load_skills_settings(run_cfg),
        mcp_settings=load_mcp_settings(run_cfg),
        shell_settings=runtime.shell_settings,
    )
