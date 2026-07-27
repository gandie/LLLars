# LLLars

LLLars is a local coding-agent runtime with one-shot CLI execution and serve-mode
job orchestration.

## Philosophy (From My Side Of The Terminal)

I am not your replacement. I am your pressure test.

I exist to turn vague intent into verified change, and to make that change
auditable. If I cannot explain why a change was needed, prove what it changed,
and show how it was validated, then I have not helped. I have only generated
noise.

I do not respect speed theater. I respect disciplined execution.

Fast without clarity is rework. Fast without boundaries is drift. Fast without
validation is fiction. If you ask me to move, I move. But I move with contracts,
checkpoints, and evidence.

You are the operator. I am the force multiplier.

That means I challenge ambiguity, not authority. I will push on unclear scope,
stale assumptions, and hidden contradictions because that is how we prevent
expensive mistakes. Not to slow you down, but to stop false progress.

The standard is simple:

- One source of truth per concern.
- Small artifacts over heroic monoliths.
- Explicit rationale over post-hoc storytelling.
- Proof before pride.

If this feels strict, good. Strict is how we stay creative without getting
sloppy.

Give me intent with teeth, and I will give you change that survives contact with
reality.

## Requirements

- Python 3.11+
- A reachable model endpoint (default examples use Ollama on `http://localhost:11434`)

## Install

```powershell
pip install -e .
```

## Quick Start

Run one-shot execution with the split config example:

```powershell
.\venv\Scripts\python.exe .\lllars.py --config .\playground.split.example.json --prompt "Describe this repository"
```

Start serve mode:

```powershell
lllars serve --config .\playground.split.example.json --host 127.0.0.1 --port 8000
```

## Runtime Scheduling and Triggering Flows

The runtime supports four operator flows through `POST /jobs` and
`POST /jobs/{job_id}/trigger`:

- Immediate: no `run_at` and no `schedule`; job starts directly.
- Timed: set `run_at` to queue now and execute when due.
- Recurring: set `schedule` using `every:<int><unit>` (units: `s`, `m`, `h`,
	`d`) with `trigger_source="scheduled"`.
- Manual trigger: submit a queued job, then trigger it with
	`POST /jobs/{job_id}/trigger`.

Run mode smoke checks:

```powershell
.\venv\Scripts\python.exe .\runtime_api_smoke_test.py --run-mode immediate --prompt "immediate flow smoke"
.\venv\Scripts\python.exe .\runtime_api_smoke_test.py --run-mode timed --run-at-delay-sec 2 --prompt "timed flow smoke"
.\venv\Scripts\python.exe .\runtime_api_smoke_test.py --run-mode recurring --schedule "every:1s" --prompt "recurring flow smoke"
.\venv\Scripts\python.exe .\runtime_api_smoke_test.py --run-mode trigger --run-at-delay-sec 90 --prompt "manual trigger smoke"
```

Failure and recovery quick guide:

- `422` on submit means contract validation failed (for example timezone-aware
	datetimes, invalid schedule grammar, or conflicting schedule fields); correct
	payload and resubmit.
- `409` on trigger means the job is not currently queued; inspect `GET /jobs`
	and trigger only queued jobs.
- `404` means unknown `job_id`; resubmit to obtain a valid id.
- If a smoke run times out, use `GET /jobs/{job_id}` and `GET /jobs/{job_id}/logs`
	to inspect current state, then either trigger (if queued) or resubmit.

## External Command Profiles

Command profiles can be extended from local JSON or YAML without code edits.
Only the minimal built-in profile (`none`) is always available. Use
`run.command_profiles_path` for project-specific profiles with conflict
validation.

Example run config fields:

```json
{
	"run": {
		"command_profile": "playground-python",
		"command_profiles_path": "playground.command-profiles.yaml"
	}
}
```

See `playground.example.json` and `playground.command-profiles.yaml` for a full
working example.

## Tool Registry and MCP Operator Guide

The runtime supports configurable tool-group registration and capability-aware
MCP startup/runtime behavior.

### Copy-Paste Tooling Config

```json
{
	"run": {
		"tool_groups": {
			"enabled": [
				"native_files",
				"native_shell",
				"plugin_local",
				"mcp_toolsets"
			],
			"disabled": []
		},
		"tool_plugins": {
			"paths": [
				"playground/plugins"
			]
		},
		"mcp_enabled": true,
		"mcp_config_path": "mcp.servers.json",
		"mcp_init_timeout_sec": 60
	}
}
```

Tool-group behavior:

- `native_files`: registers built-in file tools.
- `native_shell`: registers shell policy tools.
- `plugin_local`: loads local plugin tools from `run.tool_plugins.paths`.
- `mcp_toolsets`: reserved MCP group identifier for registry symmetry; MCP
	loading is currently gated by `run.mcp_enabled` and `mcp_config_path`.

Validation rules:

- Unknown tool groups fail config load.
- Duplicate entries in `enabled`, `disabled`, or plugin `paths` fail config
	load.
- Overlap between `enabled` and `disabled` fails config load.

### MCP Capability Troubleshooting Matrix

Startup preflight emits MCP detail lines under `mcp_preflight.detail:`.

- `healthy`: server launch contract is valid and connectivity probe succeeded.
- `degraded`: server is parseable but has partial capability issues.
- `unavailable`: launch contract is missing or connectivity failed.

Operator playbook:

- Symptom: `warning: unavailable MCP capability sets: ...`
	- Cause: one or more servers cannot be launched or connected.
	- Recovery: verify `command`/`args` or `url`, run server manually, then
		rerun preflight.
- Symptom: `warning: no healthy MCP capability sets; continuing with native/plugin tools only`
	- Cause: all configured MCP servers are unavailable.
	- Recovery: keep working with native/plugin tools, or disable MCP explicitly
		(`mcp_enabled=false`) until servers recover.
- Symptom: `warning: capability negotiation failed: ...` followed by
	fallback warning.
	- Cause: capability negotiation path raised an internal/runtime exception.
	- Recovery: review subsequent legacy probe details and startup probe output,
		then correct MCP config or server startup behavior.

### Migration: Fixed Wiring to Configurable Registry

Before:

- Native groups were effectively fixed.
- No plugin-path configuration surface.
- MCP behavior was treated as all-or-nothing during startup.

Now:

- `run.tool_groups` controls active native/plugin group registration.
- `run.tool_plugins.paths` defines local plugin load locations.
- MCP startup/runtime uses degraded-continue behavior with explicit warnings
	and healthy-subset continuation.

Minimal migration path:

1. Add `run.tool_groups` with at least `native_files` and `native_shell`.
2. Add `plugin_local` only if you provide local plugin paths.
3. Keep `mcp_enabled=true` only when your MCP servers are expected to be
	 reachable.
4. Run one startup smoke command and inspect `mcp_preflight.detail` lines.

## Provider-Aware Startup Preflight

Startup preflight probes model endpoints using pydantic_ai-native provider
parsing:

- `ollama:*` models use `.../api/tags`
- OpenAI-compatible models use `.../v1/models`

If listing is unsupported (or the provider family does not expose a supported
listing probe), preflight emits a structured warning/skip line instead of
failing startup.

## Documentation

- Overview and navigation: `docs/README.md`
- Configuration and runtime controls: `docs/configuration.md`
- Runtime API and operator flow: `docs/runtime_api.md`
- Docker runtime deployment: `docs/docker_runtime.md`
- Architecture and governance baseline: `docs/DESIGN.md`
- Workflow and bookkeeping rules: `docs/workflow/README.md`