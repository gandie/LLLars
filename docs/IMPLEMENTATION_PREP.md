# LLLars Implementation Prep for Copilot Agent Loops

## Purpose
Prepare runtime implementation for one-pass Copilot agent execution loops with high completion probability and low ambiguity.

## One-Pass Task Design Standard
Use this contract for every task ticket.

- Single concern only.
- Touch no more than 2-4 files unless task is docs-only.
- Include exact entry points and target files.
- Include a verification command and expected result.
- Include explicit non-goals.
- Include rollback strategy.
- Include completion artifact (diff summary, test output, or generated file).

## Task Backlog (Agent-Ready)

### T1 Runtime Config Surface (DONE 2026-07-14)
- Goal: Add runtime-mode config keys and validation defaults.
- Files: lllars_core/config.py, playground.example.json, README.md.
- Adds: service_mode, mount_work_root, mount_config_root, mount_artifacts_root, queue_backend, network_policy.
- Validation: config load succeeds with omitted optional fields and fails on invalid roots/policies.
- Done when: CLI can parse config and print normalized runtime config at startup.

### T2 CLI Serve Entrypoint (DONE 2026-07-14)
- Goal: Add serve path while preserving existing one-shot path.
- Files: lllars_core/cli.py, README.md.
- Adds: serve subcommand args (host, port, workers, queue backend).
- Validation: lllars serve --help works; default one-shot execution still works unchanged.
- Done when: command dispatch clearly separates run-once and serve mode.

### T3 Job Models (DONE 2026-07-14)
- Goal: Create stable API payload contracts.
- Files: lllars_core/runtime_models.py (new), README.md.
- Adds: JobSpec, RunResult, JobStatus, ErrorEnvelope.
- Validation: schema serialization/deserialization roundtrip passes.
- Done when: all runtime endpoints use shared models only.

### T4 In-Memory Job Store (DONE 2026-07-14)
- Goal: Track lifecycle and artifacts for submitted jobs.
- Files: lllars_core/job_store.py (new).
- Adds: create/get/list/update/cancel primitives with thread-safe state transitions.
- Validation: unit tests for transition rules and cancellation race edge cases.
- Done when: states cannot skip invalid transitions.

### T5 Job Runner Adapter (DONE 2026-07-14)
- Goal: Wrap current agent run logic as reusable service primitive.
- Files: lllars_core/runner.py, lllars_core/runtime_runner.py (new).
- Adds: run_job(JobSpec) -> RunResult with existing telemetry passthrough.
- Validation: existing runner behavior unchanged in one-shot mode.
- Done when: API path and CLI path call same underlying run unit.

### T6 Minimal Runtime API (DONE 2026-07-14)
- Goal: Expose operational endpoints.
- Files: lllars_core/runtime_api.py (new), lllars_core/cli.py.
- Adds: health, submit, status, logs, cancel.
- Validation: submit job then poll status until terminal state.
- Done when: one full run can be managed via HTTP only.

### T7 Filesystem Boundary Enforcement (DONE 2026-07-14)
- Goal: Prevent jobs from escaping mounted work root.
- Files: lllars_core/runtime_guard.py (new), lllars_core/config.py.
- Adds: path canonicalization + allow/deny checks.
- Validation: escape attempts using .., symlinks, absolute paths are denied.
- Done when: all project roots resolve under configured /work equivalent.

### T8 Command Profile Policy (DONE 2026-07-14)
- Goal: Replace ad-hoc allowlist text with named command profiles.
- Files: lllars_core/config.py, lllars_core/agent_builder.py, playground.example.json.
- Adds: profile registry and profile resolution.
- Validation: unknown profile rejected; known profile exposes expected commands.
- Done when: operator chooses profile name, not raw command list, in normal mode.

### T9 Observability Artifacts (DONE 2026-07-14)
- Goal: Persist per-job logs and telemetry timeline.
- Files: lllars_core/runtime_artifacts.py (new), lllars_core/runner.py.
- Adds: /artifacts/<job-id>/summary.json, stdout.txt, stderr.txt, telemetry.json.
- Validation: artifacts produced for success and failure paths.
- Done when: post-mortem possible from artifacts only.

### T10 Startup Preflight Summary (DONE 2026-07-14)
- Goal: Runtime startup should surface environment health.
- Files: lllars_core/cli.py, lllars_core/mcp_preflight.py.
- Adds: model endpoint check, MCP check, mount writeability check.
- Validation: failing preflight returns clear structured startup errors.
- Done when: operator sees immediate actionable startup diagnostics.

### T11 Deployment Assets
- Goal: Add runnable deployment examples.
- Files: docker-compose.runtime.yml (new), README.md.
- Adds: service wiring for /work, /config, /artifacts mounts.
- Validation: runtime starts and accepts submit requests on documented port.
- Done when: target user can run with one documented command.

### T12 Hardening and Regression Sweep
- Goal: Prove no regression to current single-shot behavior.
- Files: tests/ runtime tests as needed (new/updated), README.md.
- Adds: baseline CLI regression checks + runtime path smoke tests.
- Validation: one-shot + serve smoke tests both green.
- Done when: release checklist passes.

## Run Kickoff (Minimal)
Use this sequence at the start of each implementation run.

1. Read task.
2. Understand task, preferring architectural/codebase analysis tools over manual file-by-file reading.
3. Ask clarifying questions if needed.
4. Proceed to implementation only when clarity is sufficient.

## Active Agent and Skills

### Primary Implementation Agent
- Agent: Friday
- File: .github/agents/friday.agent.md
- Role: reusable implementation operator across the roadmap horizon (not tied to specific task IDs).
- Built-in behavior: minimal-noise execution loop, architecture-first understanding, clarify-before-edit, strict validation before completion.

### Baseline Global Rules
- File: AGENTS.md
- Applies to all runs.
- Contains:
  - Human authority and veto rights.
  - Slow-and-methodical execution discipline.
  - Strict hierarchy of truth.

### Active Skill Packs

1. PydanticAI Framework Expertise
- File: .github/skills/pydantic-ai-framework-expertise/SKILL.md
- Use when: agent behavior, pydantic_ai usage limits/retries/toolsets/MCP integration.
- Rule: docs first, no framework guessing.

2. FastAPI Expert
- File: .github/skills/fastapi-expert/SKILL.md
- Use when: HTTP endpoints, API lifecycle, request/response contracts.
- Rule: FastAPI reference first, no ad-hoc API patterns.

3. Modern Python Guru
- File: .github/skills/modern-python-guru/SKILL.md
- Use when: any Python implementation task.
- Rule: KISS, YAGNI, short and Pythonic code.

### Practical Invocation Mapping
- T1, T5, T8: PydanticAI Framework Expertise + Modern Python Guru.
- T2, T4, T7, T9, T10, T12: Modern Python Guru.
- T3, T6: FastAPI Expert + Modern Python Guru.
- T11: Modern Python Guru (plus deployment docs discipline in README updates).

## Delivery Cadence Recommendation
- Batch 1: T1-T3 (contracts and entrypoints).
- Batch 2: T4-T6 (job lifecycle and API minimum vertical slice).
- Batch 3: T7-T9 (security boundaries and artifacts).
- Batch 4: T10-T12 (preflight, deployment assets, regression sweep).

## Decision Log Template (Per Task)
Append per task to keep context between agent passes.

```text
Task: <ID>
Date:
Implemented by:
Files changed:
Validation command(s):
Result:
Risks:
Next handoff note:
```

## Decision Log Entries

```text
Task: T2 CLI Serve Entrypoint
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/cli.py
- README.md
Validation command(s):
- .\venv\Scripts\python.exe .\lllars.py serve --help
- .\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json
- python .\lllars.py serve --config .\playground.example.json
Result:
- PASS
- Serve subcommand is available with host/port/workers/queue-backend args.
- Default one-shot dispatch remains unchanged (prompt is still required).
Risks:
- Serve mode is currently an entrypoint scaffold and does not host runtime API endpoints yet (planned in T6).
Next handoff note:
- Proceed with T3 Job Models and keep API payload contracts centralized in lllars_core/runtime_models.py.

Task: T3 Job Models
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/runtime_models.py
- README.md
Validation command(s):
- Python schema roundtrip check using workspace interpreter:
  JobSpec/RunResult/JobStatus/ErrorEnvelope model_dump -> model_validate
Result:
- PASS
- Added shared runtime payload contracts in lllars_core/runtime_models.py.
- Added README documentation section for runtime API payload contracts and roundtrip example.
Risks:
- Runtime endpoints are not implemented yet (planned in T6), so endpoint-level adoption of shared models is pending.
Next handoff note:
- Proceed with T4 In-Memory Job Store and keep lifecycle status values aligned with JobStatus.status in runtime_models.

Task: T4 In-Memory Job Store
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/job_store.py
- tests/test_job_store.py
Validation command(s):
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
Result:
- PASS
- Added thread-safe in-memory job store primitives: create/get/list/update/cancel.
- Enforced lifecycle transitions: queued -> running -> terminal (or canceled), no skip transitions.
- Added cancellation race coverage proving atomic terminal-state resolution.
Risks:
- Store is in-memory only and process-local; durability/redis behavior is pending future queue backend work.
Next handoff note:
- Proceed with T5 Job Runner Adapter and route job execution updates through InMemoryJobStore.update/cancel.

Task: T5 Job Runner Adapter
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/runtime_runner.py
- lllars_core/cli.py
- tests/test_runtime_runner.py
Validation command(s):
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
Result:
- PASS
- Added reusable runtime primitive `run_job(JobSpec) -> RunResult` in lllars_core/runtime_runner.py.
- Preserved telemetry passthrough from existing runner (`run_agent_with_timeout`) into `RunResult.runtime_telemetry`.
- Updated one-shot CLI path to call the shared runtime run unit.
Risks:
- Runtime API path is not implemented yet (planned in T6), so shared adapter is currently exercised by CLI and tests.
Next handoff note:
- Proceed with T6 Minimal Runtime API and invoke `run_job` from submit worker execution path.

Task: T6 Minimal Runtime API
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/runtime_api.py
- lllars_core/cli.py
- tests/test_runtime_api.py
- pyproject.toml
- README.md
Validation command(s):
- .\venv\Scripts\python.exe -m pip install -e .
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
Result:
- PASS
- Added FastAPI runtime endpoints: health, submit, status, logs, cancel.
- Wired `lllars serve` to launch uvicorn with runtime app.
- Added HTTP lifecycle test: submit then poll status to terminal state, then fetch logs.
Risks:
- Queue backend support in serve mode is currently limited to `inmemory`; `redis` remains unimplemented for T6.
- Cancellation marks job state immediately, but in-flight agent subprocess work is not hard-stopped yet.
Next handoff note:
- Proceed with T7 Filesystem Boundary Enforcement to constrain runtime job roots before broader deployment.

Task: T7 Filesystem Boundary Enforcement
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/runtime_guard.py
- lllars_core/config.py
- tests/test_config.py
Validation command(s):
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
Result:
- PASS
- Added filesystem boundary guard module with canonical path checks.
- Enforced project_root confinement under mount_work_root during config load.
- Added regression tests for parent traversal, absolute path, and symlink escape attempts.
Risks:
- Symlink denial test may be skipped in environments where directory symlink creation is unavailable.
Next handoff note:
- Proceed with T8 Command Profile Policy and keep profile resolution centralized in config loading.

Task: T8 Command Profile Policy
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/config.py
- lllars_core/agent_builder.py
- playground.example.json
- tests/test_config.py
Validation command(s):
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
Result:
- PASS
- Added named command profile registry + resolution in config load flow.
- Unknown profile names now fail fast during config validation.
- Known profile (`python-playground`) resolves expected shell commands.
- Example config now selects `command_profile` instead of raw `allowed_shell_commands`.
Risks:
- Profiles are currently code-defined in registry; adding new profiles requires code changes.
Next handoff note:
- Proceed with T9 Observability Artifacts and keep artifact persistence isolated from runtime API contracts.

Task: T9 Observability Artifacts
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/runtime_artifacts.py
- lllars_core/runtime_api.py
- lllars_core/runner.py
- tests/test_runtime_api.py
Validation command(s):
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_*.py"
Result:
- PASS
- Added per-job artifact persistence for summary, stdout, stderr, and telemetry.
- Persisted artifacts for success, failed run, and exception execution paths.
- Added runtime telemetry timeline and saved it to telemetry artifacts.
- Added runtime API tests that verify artifact files are created for success and failure paths.
Risks:
- Exception-path artifacts intentionally contain minimal runtime details because no RunResult exists.
Next handoff note:
- Proceed with T10 Startup Preflight Summary and keep startup diagnostics explicit and structured.

Task: T10 Startup Preflight Summary
Date: 2026-07-14
Implemented by: GitHub Copilot (Friday mode)
Files changed:
- lllars_core/cli.py
- lllars_core/mcp_preflight.py
Validation command(s):
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_*.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
- .\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --prompt "startup preflight smoke"
Result:
- PASS
- Added unified startup preflight flow for model endpoint health, mount writeability, and MCP readiness.
- Startup now exits early with structured diagnostics when preflight fails.
- Preserved successful startup flow for healthy environment.
Risks:
- Model endpoint probe is currently Ollama-oriented (`/api/tags`) and would need extension for additional provider families.
Next handoff note:
- Proceed with T11 Deployment Assets and keep deployment examples aligned with runtime mount expectations.
```
