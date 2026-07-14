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

### Serve mode entrypoint

The CLI now exposes a dedicated serve path while keeping the existing one-shot
path unchanged.

Inspect serve options:

```powershell
lllars serve --help
```

Serve arguments:

- `--host` (default `127.0.0.1`)
- `--port` (default `8000`)
- `--workers` (default `1`)
- `--queue-backend` (`inmemory` or `redis`, default `inmemory`)

Current status: runtime API is available in serve mode (T6).

### Runtime API endpoints (T6)

Serve mode now exposes the minimal runtime API:

- `GET /health`
- `POST /jobs` (submit)
- `GET /jobs/{job_id}` (status)
- `GET /jobs/{job_id}/logs` (logs)
- `POST /jobs/{job_id}/cancel` (cancel)

Example validation flow (PowerShell):

```powershell
# Start service in a separate terminal:
lllars serve --config .\playground.example.json --host 127.0.0.1 --port 8000

# Submit a job:
$submit = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/jobs" -ContentType "application/json" -Body '{"prompt":"Describe this repository"}'
$jobId = $submit.job_id

# Poll status until terminal:
do {
	Start-Sleep -Milliseconds 300
	$status = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/jobs/$jobId"
} while ($status.status -in @("queued", "running"))

# Fetch logs:
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/jobs/$jobId/logs"
```

Notes:

- Current implementation supports `queue_backend=inmemory` for serve mode.
- `--workers` values other than `1` are accepted but currently run as single-worker.

### Docker Compose runtime deployment (T11)

Environment file support:

```powershell
# Defaults are committed in .env.runtime.
# Optional: reset from template if needed.
Copy-Item .\.env.runtime.example .\.env.runtime -Force
```

Run the runtime API with build + env-file support:

```powershell
docker compose -f .\docker-compose.runtime.yml up --build
```

This compose target wires the runtime mount boundaries explicitly:

- `/work` -> named volume `lllars-work`
- `/config` -> named volume `lllars-config`
- `/artifacts` -> named volume `lllars-artifacts`

Behavior details:

- Image is built from `Dockerfile.runtime` and installs `lllars` during image build.
- Runtime bootstraps `/config/runtime.json` from `/config/playground.example.json` using values from `.env.runtime`.
- Service binds to `0.0.0.0:8000` in-container and publishes `localhost:${LLLARS_PORT}`.
- On first start, defaults are seeded into volumes (`playground` into `/work`, example config into `/config`).

Common environment knobs in `.env.runtime`:

- `OLLAMA_BASE_URL`
- `LLLARS_PORT`
- `QUEUE_BACKEND`
- `NETWORK_POLICY`
- `MCP_ENABLED`
- `SKIP_MCP_PREFLIGHT`

Minimal submit check (service accepts job requests on documented port):

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/jobs" -ContentType "application/json" -Body '{"prompt":"runtime smoke"}'
```

### Runtime API payload contracts

Shared runtime payload contracts now live in `lllars_core/runtime_models.py`:

- `JobSpec`: submit payload for a runtime job.
- `RunResult`: normalized run outcome payload.
- `JobStatus`: lifecycle payload for queued/running/terminal jobs.
- `ErrorEnvelope`: stable error payload shape for API responses.

These models are intended to be the single contract source for runtime endpoints.
Validation roundtrip example:

```powershell
python -c "from lllars_core.runtime_models import ErrorEnvelope, JobSpec, JobStatus, RunResult; spec = JobSpec(prompt='ping'); spec = JobSpec.model_validate(spec.model_dump()); result = RunResult(success=True, agent_returncode=0, elapsed_sec=0.1, agent_stdout='ok', agent_stderr=''); result = RunResult.model_validate(result.model_dump()); status = JobStatus(job_id='job-1', status='succeeded', result=result); status = JobStatus.model_validate(status.model_dump()); err = ErrorEnvelope(code='bad_request', message='invalid input'); err = ErrorEnvelope.model_validate(err.model_dump()); print('roundtrip-ok')"
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
- `service_mode`
- `mount_work_root`
- `mount_config_root`
- `mount_artifacts_root`
- `queue_backend`
- `network_policy`

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
	"skills_require_description": true,
	"service_mode": "oneshot",
	"mount_work_root": "playground",
	"mount_config_root": ".",
	"mount_artifacts_root": ".",
	"queue_backend": "inmemory",
	"network_policy": "inherit"
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