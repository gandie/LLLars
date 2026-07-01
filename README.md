# LLLars - Large Language Lars

The stupid AI agent.

Ever wanted a small local-running code agent that just works?

This project is the result of countless hours of experimenting,
trying to find balance between 4 characteristics of an agent
driven coding task:

- Task design
- Model choice
- Tool orchestration
- Agentic coding process

While the first two items - "Task design" and "Model choice" may
live in user space, "Tool orchestration" and the "Agentic coding process"
itself are hidden behind walls not reachable for ordinary users.

In practice, poor balancing of those four items leads to chaos and
overengineering, in worst case even dressed as progress.

## Installation

### Requirements

- Python 3.11+
- PowerShell (Windows)
- A running Ollama endpoint (default: `http://localhost:11434`)

### Install from local source

```powershell
pip install .
```

This installs the `lllars` CLI entry point.

### Editable install (development)

```powershell
pip install -e .
```

### Quick start

1. Copy and adapt the example config:

```powershell
Copy-Item .\lllars.example.json .\lllars.json
```

2. Run the agent:

```powershell
lllars --config .\lllars.json --prompt "Describe this repository"
```

### Native runtime controls

The harness now uses native PydanticAI runtime controls instead of custom
budgets/circuit breakers.

Supported config knobs:

- `usage_request_limit`
- `usage_tool_calls_limit`
- `usage_input_tokens_limit`
- `usage_output_tokens_limit`
- `usage_total_tokens_limit`
- `usage_count_tokens_before_request`
- `agent_retries_tools`
- `agent_retries_output`
- `tool_timeout_sec`
- `max_concurrency`
- `instrumentation_enabled`
- `instrumentation_include_content`
- `skills_enabled`
- `skills_glob`
- `skills_defer_loading`
- `skills_require_description`

Example:

```json
{
	"usage_request_limit": null,
	"usage_tool_calls_limit": 24,
	"usage_input_tokens_limit": null,
	"usage_output_tokens_limit": null,
	"usage_total_tokens_limit": null,
	"usage_count_tokens_before_request": false,
	"agent_retries_tools": 1,
	"agent_retries_output": 1,
	"tool_timeout_sec": 90,
	"max_concurrency": null,
	"instrumentation_enabled": false,
	"instrumentation_include_content": false,
	"skills_enabled": false,
	"skills_glob": "skills/*.md",
	"skills_defer_loading": true,
	"skills_require_description": true
}
```

### Markdown skills (prototype)

The harness can load capability skills from markdown files with YAML frontmatter,
based on the PydanticAI capability pattern.

Config fields:

- `skills_enabled`: enable markdown skill loading
- `skills_glob`: glob under `project_root` (for example `skills/*.md`)
- `skills_defer_loading`: when true, skills are loaded on demand via
  `load_capability`
- `skills_require_description`: require `description` in frontmatter

Skill file format:

```markdown
---
id: refunds
description: Use for refund eligibility and refund handling.
---
Always confirm order ID before issuing a refund.
Never issue refunds over $500 without manager approval.
```

Validation behavior:

- `id` is required and must be unique across loaded skill files.
- `description` is required unless `skills_require_description=false`.
- Skill body (instructions) must be non-empty.
- If `skills_enabled=true` and no files match `skills_glob`, startup fails fast.

For resumable history behavior in deferred capabilities, keep each skill `id`
stable over time.

### Live introspection while running

Live terminal progress now uses native PydanticAI stream events from
`event_stream_handler` on `run_sync(...)`.

This means progress lines are emitted from agent lifecycle events (model parts,
tool calls/results, and final-result start) instead of relying only on post-run
message scraping.

The final `thought_trace` is built primarily from these streamed events, with a
fallback merge from run messages for compatibility.

### Environment-aware native agent behavior

The harness now uses native PydanticAI dependency-typed instructions to make
runtime environment constraints explicit during each run.

What this adds:

- Runtime instructions include OS, shell type, and project root.
- Shell execution uses explicit allowlisted command IDs instead of free-form
	command text.
- Agent can discover commands via `list_allowed_shell_commands` and execute one
	with `run_allowlisted_shell(command_id=...)`.
- Shell commands run in configured `project_root`.

This reduces tool misuse (for example trying bash scripts on Windows) while
remaining fully config-driven.

## Architecture

The project is intentionally split so the executable stays small and orchestration
logic is separated by concern.

### Module map

- `lllars.py`: thin console entrypoint wrapper
- `lllars_core/cli.py`: argument parsing and top-level orchestration
- `lllars_core/config.py`: config model, defaults, and config loading
- `lllars_core/agent_builder.py`: agent/tool construction and native runtime config wiring
- `lllars_core/runner.py`: agent execution and timeout subprocess orchestration
- `lllars_core/shell.py`: PowerShell command execution, test/eval helpers
- `lllars_core/console.py`: terminal output formatting and summaries

### Runtime flow

1. `lllars.py` forwards to `lllars_core.cli.main`.
2. CLI loads config and prompt input.
3. Runner executes the agent with timeout safeguards.
4. Shell helpers run test/eval commands.
5. Console helpers print summary and verbose diagnostics.

### Why this split

- Keeps the installed executable simple and stable.
- Isolates agent building from runtime orchestration.
- Makes config, shell, and console concerns independently testable.
- Supports safer refactoring by reducing cross-module coupling.