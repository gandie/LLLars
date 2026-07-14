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

### T2 CLI Serve Entrypoint
- Goal: Add serve path while preserving existing one-shot path.
- Files: lllars_core/cli.py, README.md.
- Adds: serve subcommand args (host, port, workers, queue backend).
- Validation: lllars serve --help works; default one-shot execution still works unchanged.
- Done when: command dispatch clearly separates run-once and serve mode.

### T3 Job Models
- Goal: Create stable API payload contracts.
- Files: lllars_core/runtime_models.py (new), README.md.
- Adds: JobSpec, RunResult, JobStatus, ErrorEnvelope.
- Validation: schema serialization/deserialization roundtrip passes.
- Done when: all runtime endpoints use shared models only.

### T4 In-Memory Job Store
- Goal: Track lifecycle and artifacts for submitted jobs.
- Files: lllars_core/job_store.py (new).
- Adds: create/get/list/update/cancel primitives with thread-safe state transitions.
- Validation: unit tests for transition rules and cancellation race edge cases.
- Done when: states cannot skip invalid transitions.

### T5 Job Runner Adapter
- Goal: Wrap current agent run logic as reusable service primitive.
- Files: lllars_core/runner.py, lllars_core/runtime_runner.py (new).
- Adds: run_job(JobSpec) -> RunResult with existing telemetry passthrough.
- Validation: existing runner behavior unchanged in one-shot mode.
- Done when: API path and CLI path call same underlying run unit.

### T6 Minimal Runtime API
- Goal: Expose operational endpoints.
- Files: lllars_core/runtime_api.py (new), lllars_core/cli.py.
- Adds: health, submit, status, logs, cancel.
- Validation: submit job then poll status until terminal state.
- Done when: one full run can be managed via HTTP only.

### T7 Filesystem Boundary Enforcement
- Goal: Prevent jobs from escaping mounted work root.
- Files: lllars_core/runtime_guard.py (new), lllars_core/config.py.
- Adds: path canonicalization + allow/deny checks.
- Validation: escape attempts using .., symlinks, absolute paths are denied.
- Done when: all project roots resolve under configured /work equivalent.

### T8 Command Profile Policy
- Goal: Replace ad-hoc allowlist text with named command profiles.
- Files: lllars_core/config.py, lllars_core/agent_builder.py, playground.example.json.
- Adds: profile registry and profile resolution.
- Validation: unknown profile rejected; known profile exposes expected commands.
- Done when: operator chooses profile name, not raw command list, in normal mode.

### T9 Observability Artifacts
- Goal: Persist per-job logs and telemetry timeline.
- Files: lllars_core/runtime_artifacts.py (new), lllars_core/runner.py.
- Adds: /artifacts/<job-id>/summary.json, stdout.txt, stderr.txt, telemetry.json.
- Validation: artifacts produced for success and failure paths.
- Done when: post-mortem possible from artifacts only.

### T10 Startup Preflight Summary
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
