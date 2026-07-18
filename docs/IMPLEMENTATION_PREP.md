# LLLars Implementation Prep for Copilot Agent Loops

## Purpose
Prepare runtime implementation for one-pass Copilot agent execution loops with high completion probability and low ambiguity.

Completed ticket history has been archived to:
- docs/IMPLEMENTATION_CHANGELOG.md

## One-Pass Task Design Standard
Use this contract for every task ticket.

- Single concern only.
- Touch no more than 2-4 files unless task is docs-only.
- Include exact entry points and target files.
- Include a verification command and expected result.
- Include explicit non-goals.
- Include rollback strategy.
- Include completion artifact (diff summary, test output, or generated file).

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

## Active Ticket Backlog (Agent-Ready)

### Priority Sequence (Updated 2026-07-16)
1. T17 Fully Automated Serve Smoke Test
2. T18 Command Profile Externalization
3. T19 Provider-Aware Startup Preflight (deferred)
4. T20 Queue Backend: Redis Minimum (deferred)

Archived in this sweep (moved to docs/IMPLEMENTATION_CHANGELOG.md):
- T16 Runtime Cancellation Hard-Stop (DONE 2026-07-16)
- T21 Shell Runtime Foundation (DONE 2026-07-16)
- T22 Shell Adapter Integration in Runner/API (DONE 2026-07-16)
- T23 Docker Runtime Shell Enablement (DONE 2026-07-16)

### T17 Fully Automated Serve Smoke Test
- Goal: Remove manual two-terminal operator flow from serve smoke verification.
- Files: tests/test_runtime_api_smoke_test.py, runtime_api_smoke_test.py, tests/test_cli_regression.py.
- Adds:
  - In-process serve harness on ephemeral port for smoke execution.
  - Deterministic timeout and teardown behavior for CI stability.
  - Terminal-state coverage for `succeeded`, `failed`, and `canceled`.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
- Non-goals:
  - No docker compose dependency in unit tests.
  - No performance/load benchmark coverage.
- Rollback strategy:
  - Keep current contract-style smoke tests while adding isolated automated harness tests.
- Completion artifact:
  - CI-friendly unittest output proving serve smoke is fully automated.

### T18 Command Profile Externalization
- Goal: Make command profiles extensible without code edits.
- Files: lllars_core/config.py, playground.example.json, README.md, tests/test_config.py.
- Adds:
  - Optional external profile source (JSON/YAML) merged with built-in profiles.
  - Duplicate/override conflict validation rules.
  - Explicit diagnostics for missing requested profile.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
  - .\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --prompt "profile externalization smoke"
- Non-goals:
  - No role-based policy engine.
  - No remote profile fetching.
- Rollback strategy:
  - Fall back to built-in registry when external profile loading fails.
- Completion artifact:
  - Example external profile file and passing config tests.

### T19 Provider-Aware Startup Preflight (Deferred)
- Goal: Expand model endpoint probing beyond Ollama-only assumptions.
- Files: lllars_core/mcp_preflight.py, lllars_core/config.py, tests/test_config.py, README.md.
- Adds:
  - Provider family inference (Ollama vs OpenAI-compatible style endpoints).
  - Probe strategy per provider family (`/api/tags` vs `/models`).
  - Structured warning mode when model listing is unsupported but connectivity is healthy.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
  - .\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --prompt "provider preflight smoke"
- Non-goals:
  - No provider SDK integration.
  - No authentication redesign.
- Rollback strategy:
  - Keep existing Ollama probe as default fallback.
- Completion artifact:
  - Updated preflight docs with multi-provider examples.

### T20 Queue Backend: Redis Minimum (Deferred)
- Goal: Implement redis queue backend baseline for submit/status/cancel lifecycle.
- Files: lllars_core/job_store.py, lllars_core/runtime_api.py, pyproject.toml, tests/test_runtime_api.py.
- Adds:
  - Redis-backed job state persistence with same transition rules as in-memory store.
  - Serve-mode dispatch path for `queue_backend=redis`.
  - Explicit startup diagnostics for unreachable/misconfigured redis.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
  - python .\lllars.py serve --config .\playground.example.json --queue-backend redis (expected: starts or fails with clear redis diagnostics)
- Non-goals:
  - No distributed scheduling layer.
  - No dead-letter/retry policy framework.
- Rollback strategy:
  - Keep in-memory backend as default and gate redis path behind explicit selection.
- Completion artifact:
  - Diff + tests showing both in-memory and redis backend selection behavior.

## Planned Next Wave Backlog (Aggressive Refactor-First Draft 2026-07-16)

### Deep Analysis Snapshot (Why Aggressive Split)
- File size concentration from AST scan:
  - `lllars_core/config.py`: 888 lines, `load_config` 353 lines.
  - `lllars_core/runtime_runner.py`: 540 lines, `_apply_job_run_settings` 278 lines.
  - `lllars_core/mcp_preflight.py`: 399 lines, `run_mcp_preflight` 80 lines, `_check_model_endpoint` 77 lines.
  - `lllars_core/agent_builder.py`: 379 lines, `_register_file_tools` 79 lines, `_register_shell_tools` 73 lines.
  - `lllars_core/runner.py`: 379 lines, `run_single_agent` 126 lines, `run_agent_with_timeout` 116 lines.
  - `lllars_core/runtime_api.py`: 341 lines, `RuntimeService._run_job` 141 lines.
- Dependency pressure from graph trace:
  - `load_config` is called from both one-shot and serve paths and indirectly influences runtime job execution.
  - `run_job` bridges config, shell, runner, and store concerns in one path.
  - `create_runtime_app` combines service setup and web mounting concerns.

### Refactor Outcome Targets (For Snappy Agent Context)
- Core-module file budget: target <= 220 lines, hard ceiling <= 280 lines.
- Core routine budget: target <= 35 lines, hard ceiling <= 55 lines.
- Package-first layout: each concern gets a folder with focused files and a thin compatibility facade.
- Zero behavior change during refactor phase: all splits are extract-and-route only.

### Target Folder Architecture After Refactor Phase
- `lllars_core/runtime/`
  - `api.py`, `web.py`, `service.py`, `execution.py`, `settings.py`, `scheduler.py`, `artifacts.py`, `models.py`, `store_adapter.py`, `compat.py`
- `lllars_core/tools/`
  - `registry.py`, `native.py`, `shell_policy.py`, `plugins.py`, `descriptors.py`, `compat.py`
- `lllars_core/mcp/`
  - `loader.py`, `preflight.py`, `capabilities.py`, `runtime.py`, `diagnostics.py`, `compat.py`
- `lllars_core/config/`
  - `loader.py`, `models.py`, `env_layer.py`, `runtime_section.py`, `tools_section.py`, `legacy_bridge.py`, `compat.py`

### Proposed Execution Order After T17-T20
1. T24 Refactor Governance and Size Gates (DONE 2026-07-17)
2. T25 Runtime Package Bootstrap + Compatibility Facade
3. T26 Runtime Execution/Settings Deep Extraction
4. T27 Runtime API/Web/Service Split
5. T28 Runner Core Split (orchestration/worker/stream) (DONE 2026-07-18)
6. T29 Config Package Split + Legacy Bridge
7. T30 MCP Package Split + Diagnostics Boundary
8. T31 Tools Package Split + Agent Builder Slimming
9. T32 Integration Stabilization Sweep (imports, facades, naming)
10. T33 Scheduling and Triggering Design Prep (on new runtime package)
11. T34 Timed Job Runs (Runtime Deadlines)
12. T35 Job Scheduling Core (Delayed and Recurring)
13. T36 Job Triggering Integration
14. T37 Scheduling and Triggering Operator Docs
15. T38 Tool Extensibility and MCP Design Prep (on new tools/mcp packages)
16. T39 Configurable Native and Plugin Tool Registry
17. T40 MCP Support Hardening and Capability Layer
18. T41 Tooling and MCP Operator Docs

### T24 Refactor Governance and Size Gates (DONE 2026-07-17)
- Goal: Establish enforceable size and structure constraints before moving code.
- Files: docs/DESIGN.md, docs/refactor_boundaries.json, lllars_core/refactor_boundaries.py, tests/test_refactor_boundaries.py.
- Adds:
  - Refactor guardrails section with file/routine size budgets and exception policy.
  - Lightweight CI check (or test utility) that fails when core files exceed agreed budget.
  - Refactor migration ledger template for extracted symbols.
  - Machine-readable boundary tool and baseline waiver contract for incremental debt burn-down.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- Non-goals:
  - No runtime behavior changes.
  - No folder moves yet.
- Rollback strategy:
  - Keep strict defaults and tune waivers in docs/refactor_boundaries.json per refactor ticket.
- Completion artifact:
  - Boundary checker active with passing baseline and full test suite.

Boundary tool contract for code-touching tasks (T25+):
- Tool command: .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- Target values: defaults in docs/refactor_boundaries.json (`max_file_lines=220`, `max_function_lines=35`)
- If a touched file cannot meet defaults in the same ticket: add explicit waiver with reason + linked ticket for removal.

### T25 Runtime Package Bootstrap + Compatibility Facade (DONE 2026-07-18)
- Goal: Create `runtime/` package and preserve existing imports through compatibility shims.
- Files: lllars_core/runtime/__init__.py, lllars_core/runtime/compat.py, lllars_core/runtime_runner.py, lllars_core/runtime_api.py, tests/test_runtime_runner.py, tests/test_runtime_api.py.
- Adds:
  - Runtime package skeleton and compatibility exports.
  - Existing top-level modules forward to package entry points without behavior change.
  - Import migration notes for subsequent tickets.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No scheduling logic.
  - No endpoint contract changes.
- Rollback strategy:
  - Rebind top-level modules directly to legacy functions if package import wiring regresses.
- Completion artifact:
  - Passing tests with both old and new import paths.

### T26 Runtime Execution/Settings Deep Extraction (DONE 2026-07-18)
- Goal: Aggressively split runtime execution and settings mapping into small files.
- Files: lllars_core/runtime/execution.py, lllars_core/runtime/settings.py, lllars_core/runtime/models.py, lllars_core/runtime_runner.py, tests/test_runtime_runner.py.
- Adds:
  - `_apply_job_run_settings` decomposition into focused mappers/validators.
  - `run_job` orchestration reduced to composition steps and terminal mapping.
  - Execution helpers grouped by concern (agent run, eval run, tests run).
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No new runtime features.
  - No scheduler implementation.
- Rollback strategy:
  - Keep wrapper functions with old names and restore previous call chain if parity breaks.
- Completion artifact:
  - `runtime_runner.py` trimmed below budget (178 lines) with passing tests.

### T27 Runtime API/Web/Service Split (DONE 2026-07-18)
- Goal: Move HTTP, service, and frontend mounting concerns into dedicated runtime package modules.
- Files: lllars_core/runtime/api.py, lllars_core/runtime/web.py, lllars_core/runtime/service.py, lllars_core/runtime/artifacts.py, lllars_core/runtime_api.py, tests/test_runtime_api.py.
- Adds:
  - Dedicated route-registration module.
  - Dedicated runtime service orchestration module.
  - Artifact persistence integration extracted from request path logic.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No new API routes yet.
  - No auth redesign.
- Rollback strategy:
  - Keep `create_runtime_app` compatibility wrapper in top-level module.
- Completion artifact:
  - Route/service split landed with unchanged API behavior.

### T28 Runner Core Split (orchestration/worker/stream) (DONE 2026-07-18)
- Goal: Split `runner.py` so orchestration, worker lifecycle, and stream handling are isolated.
- Files: lllars_core/runner.py, lllars_core/runtime/runner_orchestrator.py, lllars_core/runtime/runner_worker.py, lllars_core/runtime/runner_stream.py, tests/test_cli_regression.py.
- Adds:
  - Worker process lifecycle module.
  - Event stream extraction module.
  - Orchestrator module for timeout/cancel policy.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No model/provider behavior changes.
  - No CLI UX changes.
- Rollback strategy:
  - Preserve existing `run_single_agent` and `run_agent_with_timeout` function signatures.
- Completion artifact:
  - Runner modules each under size budget with unchanged behavior.

### T29 Config Package Split (DONE 2026-07-18)
- Goal: Break `config.py` monolith into package modules while preserving `load_config` API stability.
- Files: lllars_core/config/__init__.py, lllars_core/config/loader.py, lllars_core/config/models.py, lllars_core/config/env_layer.py, lllars_core/config/runtime_section.py, lllars_core/config/tools_section.py, lllars_core/config.py, tests/test_config.py.
- Adds:
  - Split parsers by concern (service, run, tools).
  - Strict split-root config handling (`service`/`run` plus optional `env_file`).
  - Top-level `config.py` shim forwarding to package loader.
  - Symbol migration map for downstream imports.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No new config keys.
  - No role/policy feature expansion.
- Rollback strategy:
  - Rebind shim to previous config loader flow if behavior drift appears.
- Completion artifact:
  - `config.py` reduced to facade with parity tests passing and boundary checks green.

### T30 MCP Package Split + Diagnostics Boundary (DONE 2026-07-18)
- Goal: Isolate MCP loading, probing, and diagnostics into focused package modules.
- Files: lllars_core/mcp/__init__.py, lllars_core/mcp/loader.py, lllars_core/mcp/preflight.py, lllars_core/mcp/diagnostics.py, lllars_core/mcp/runtime.py, lllars_core/mcp_loader.py, lllars_core/mcp_preflight.py, tests/test_cli_regression.py.
- Adds:
  - MCP package boundary with normalized result objects.
  - Diagnostic formatting module separated from probing logic.
  - Top-level shim modules preserving existing imports.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
  - .\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --prompt "mcp package split smoke"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No capability-policy logic yet.
  - No protocol changes.
- Rollback strategy:
  - Keep shim calls to legacy preflight/loader flow available.
- Completion artifact:
  - MCP modules split and startup diagnostics unchanged.

### T31 Tools Package Split + Agent Builder Slimming (DONE 2026-07-18)
- Goal: Move tool registration policy out of `agent_builder.py` into a dedicated tools package.
- Files: lllars_core/tools/__init__.py, lllars_core/tools/registry.py, lllars_core/tools/native.py, lllars_core/tools/shell_policy.py, lllars_core/tools/descriptors.py, lllars_core/agent_builder.py, tests/test_agent_builder.py.
- Adds:
  - Native tool descriptor and registration modules.
  - Shell policy/instruction module.
  - Slimmed `build_agent` orchestration path.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No plugin loading yet.
  - No MCP capability upgrades yet.
- Rollback strategy:
  - Preserve existing tool registration signatures with adapter wrappers.
- Completion artifact:
  - `agent_builder.py` reduced to assembly orchestration with parity tests.

### T32 Integration Stabilization Sweep (imports, facades, naming) (DONE 2026-07-18)
- Goal: Normalize imports and enforce package/facade boundaries after aggressive splits.
- Files: lllars_core/*.py, lllars_core/runtime/*.py, lllars_core/tools/*.py, lllars_core/mcp/*.py, lllars_core/config/*.py, tests/test_*.py.
- Adds:
  - Standardized import style and no-cross-layer shortcut imports.
  - Removed compatibility facades and alias maps in favor of canonical package paths.
  - Final pass on file-size budget compliance with zero waivers.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No new product features.
  - No endpoint/CLI feature expansion.
- Rollback strategy:
  - Recreate thin wrappers only if external integration breakage is explicitly reported.
- Completion artifact:
  - Green baseline test suite with stable package boundaries and no boundary waivers.

### T33 Scheduling and Triggering Design Prep
- Goal: Define stable contracts for deadlines, schedules, and trigger sources on top of `runtime/` package boundaries.
- Files: docs/DESIGN.md, docs/IMPLEMENTATION_PREP.md, docs/IMPLEMENTATION_CHANGELOG.md, lllars_core/runtime/models.py.
- Adds:
  - Terminology and lifecycle states for timed/scheduled/triggered jobs.
  - Data contract draft for `deadline_at`, `run_at`, `schedule`, and `trigger_source`.
  - Compatibility notes for existing immediate-submit flow.
- Validation:
  - Design review pass against `runtime/service.py` and `runtime/execution.py` boundaries.
- Non-goals:
  - No endpoint additions.
  - No scheduler loop implementation.
- Rollback strategy:
  - Keep submit-only lifecycle and remove draft contract references.
- Completion artifact:
  - Approved design contract for T34-T36.

### T34 Timed Job Runs (Runtime Deadlines)
- Goal: Add per-job execution deadlines so long-running jobs stop deterministically.
- Files: lllars_core/runtime/models.py, lllars_core/runtime/execution.py, lllars_core/runtime/service.py, tests/test_runtime_runner.py, tests/test_runtime_api.py.
- Adds:
  - Optional per-job deadline fields with validation.
  - Deadline enforcement path to terminal timeout outcome.
  - Runtime telemetry markers for deadline-reached termination.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No recurring scheduling yet.
  - No queue backend redesign.
- Rollback strategy:
  - Gate deadline enforcement behind config fallback.
- Completion artifact:
  - Deterministic timeout-state tests passing.

### T35 Job Scheduling Core (Delayed and Recurring)
- Goal: Add delayed (`run_at`) and recurring schedule support inside runtime package.
- Files: lllars_core/runtime/scheduler.py, lllars_core/runtime/service.py, lllars_core/runtime/models.py, lllars_core/job_store.py, tests/test_job_store.py, tests/test_runtime_api.py.
- Adds:
  - Schedule metadata and next-run persistence.
  - Scheduler loop promoting due jobs.
  - Minimal recurrence parser and validator.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_job_store.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No distributed scheduler clustering.
  - No UI calendar workflow.
- Rollback strategy:
  - Keep scheduler opt-in and preserve immediate submit as default.
- Completion artifact:
  - Scheduled and recurring execution tests passing.

### T36 Job Triggering Integration
- Goal: Introduce explicit trigger pathways for API and internal scheduler events.
- Files: lllars_core/runtime/web.py, lllars_core/runtime/service.py, lllars_core/runtime/models.py, lllars_core/runtime/execution.py, tests/test_runtime_api.py.
- Adds:
  - Trigger metadata (`trigger_source`, `trigger_payload_ref`) across run lifecycle.
  - Trigger route/action contract for preconfigured jobs.
  - Artifact linkage from trigger event to spawned run.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No external event bus integration.
  - No auth redesign.
- Rollback strategy:
  - Keep direct submit contract as fallback pathway.
- Completion artifact:
  - Trigger-flow API tests with auditable metadata.

### T37 Scheduling and Triggering Operator Docs
- Goal: Document timed, scheduled, recurring, and trigger flows for operators.
- Files: README.md, docs/DESIGN.md, runtime_api_smoke_test.py, tests/test_runtime_api_smoke_test.py.
- Adds:
  - End-to-end usage examples for new run modes.
  - Failure-mode and recovery guidance.
  - Smoke test scenarios aligned to docs.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
  - .\venv\Scripts\python.exe .\runtime_api_smoke_test.py --prompt "scheduling docs smoke"
- Non-goals:
  - No frontend scheduler UX.
  - No benchmark claims.
- Rollback strategy:
  - Keep existing submit/status docs as baseline sections.
- Completion artifact:
  - Operator docs plus passing smoke checks.

### T38 Tool Extensibility and MCP Design Prep
- Goal: Define architecture for configurable native tools, plugin tools, and MCP capability handling on top of split packages.
- Files: docs/DESIGN.md, docs/IMPLEMENTATION_PREP.md, lllars_core/tools/registry.py, lllars_core/mcp/runtime.py.
- Adds:
  - Tool taxonomy and execution boundaries.
  - Config schema draft for tool-group enable/disable.
  - MCP capability matrix and fallback policy.
- Validation:
  - Design review against `tools/` and `mcp/` package seams.
- Non-goals:
  - No plugin runtime implementation yet.
  - No capability negotiation code yet.
- Rollback strategy:
  - Keep current fixed wiring and treat design as draft until T39/T40 land.
- Completion artifact:
  - Approved design checklist for T39 and T40.

### T39 Configurable Native and Plugin Tool Registry
- Goal: Implement configurable native tools and local plugin tool loading with safety controls.
- Files: lllars_core/tools/registry.py, lllars_core/tools/native.py, lllars_core/tools/plugins.py, lllars_core/config/tools_section.py, lllars_core/agent_builder.py, tests/test_config.py, tests/test_agent_builder.py.
- Adds:
  - Native tool toggles with allow/deny rules.
  - Plugin discovery and registration from local paths.
  - Duplicate/missing/unsafe plugin diagnostics.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No remote plugin marketplace.
  - No dynamic code download.
- Rollback strategy:
  - Fallback to built-in fixed native toolset.
- Completion artifact:
  - Deterministic tool-registration tests for native and plugin modes.

### T40 MCP Support Hardening and Capability Layer
- Goal: Add capability-aware startup checks and runtime degradation behavior.
- Files: lllars_core/mcp/capabilities.py, lllars_core/mcp/runtime.py, lllars_core/mcp/preflight.py, lllars_core/agent_builder.py, tests/test_cli_regression.py.
- Adds:
  - Capability negotiation summary in startup diagnostics.
  - Structured degraded-mode behavior for partial MCP capability.
  - Clear operator warnings for unavailable capability sets.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
  - .\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --prompt "mcp capability smoke"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" (targets: file<=220, function<=35 unless explicit waiver)
- Non-goals:
  - No MCP protocol extensions.
  - No provider-specific capability hardcoding.
- Rollback strategy:
  - Keep current preflight-only behavior as fallback.
- Completion artifact:
  - Startup/runtime traces proving capability-aware degradation.

### T41 Tooling and MCP Operator Docs
- Goal: Document configuration, troubleshooting, and migration for tool extensibility and MCP changes.
- Files: README.md, docs/AGENTOPS_BOOTSTRAP.md, docs/DESIGN.md, playground.example.json.
- Adds:
  - Native/plugin tool configuration how-to.
  - MCP health/degraded/unavailable troubleshooting matrix.
  - Migration guide from fixed wiring to configurable registry.
- Validation:
  - Manual docs walkthrough using example configs.
- Non-goals:
  - No UI documentation portal.
  - No full plugin SDK tutorial.
- Rollback strategy:
  - Keep old docs sections available until next release cycle.
- Completion artifact:
  - Operator docs with copy-paste examples and recovery playbooks.

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
