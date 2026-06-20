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
	"instrumentation_include_content": false
}
```

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