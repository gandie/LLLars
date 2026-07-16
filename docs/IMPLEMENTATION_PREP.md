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
1. T21 Shell Runtime Foundation (NEW)
2. T22 Shell Adapter Integration in Runner/API (NEW)
3. T23 Docker Runtime Shell Enablement (NEW)
4. T16 Runtime Cancellation Hard-Stop
5. T17 Fully Automated Serve Smoke Test
6. T18 Command Profile Externalization
7. T19 Provider-Aware Startup Preflight (deferred)
8. T20 Queue Backend: Redis Minimum (deferred)

### T21 Shell Runtime Foundation
- Goal: Replace PowerShell-only command assumption with automatic shell environment detection and normalized shell execution contract.
- Files: lllars_core/shell.py, lllars_core/config.py, tests/test_config.py, tests/test_cli_regression.py.
- Adds:
  - Shell detection order for common environments:
    - Windows: PowerShell 7 (`pwsh`), Windows PowerShell (`powershell`), `cmd` fallback.
    - Linux/macOS and containers: `bash`, `sh` fallback.
  - Config-level shell policy fields with safe defaults (`auto` detect plus explicit override).
  - Validation for unknown shell overrides and unsupported combinations.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
- Non-goals:
  - No runtime cancellation hard-stop changes.
  - No redis queue backend work.
- Rollback strategy:
  - Keep existing PowerShell path as compatibility fallback behind feature flag/config default.
- Completion artifact:
  - Diff + tests proving `auto` detection picks an available shell and preserves explicit override behavior.

### T22 Shell Adapter Integration in Runner/API
- Goal: Thread shell selection through runner and runtime API so allowlisted console commands run with detected shell instead of PowerShell-only assumptions.
- Files: lllars_core/runner.py, lllars_core/runtime_runner.py, lllars_core/runtime_api.py, tests/test_runtime_runner.py, tests/test_runtime_api.py.
- Adds:
  - Unified shell-execution adapter used by one-shot and runtime job execution paths.
  - Job-level runtime metadata capturing selected shell and invocation mode.
  - Clear failure envelopes when no supported shell is available.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
- Non-goals:
  - No static frontend redesign.
  - No command profile externalization yet.
- Rollback strategy:
  - Preserve old shell invocation code path behind compatibility branch toggle while landing adapter tests.
- Completion artifact:
  - Test evidence that one-shot and runtime API paths execute allowlisted commands through the same shell adapter.

### T23 Docker Runtime Shell Enablement
- Goal: Ensure dockerized runtime can execute allowlisted console commands by providing and detecting supported shells in container runtime.
- Files: Dockerfile.runtime, docker/runtime-entrypoint.sh, docker-compose.runtime.yml, tests/test_runtime_api_smoke_test.py, README.md.
- Adds:
  - Container image/runtime setup that guarantees at least one supported POSIX shell path.
  - Startup diagnostics that show detected shell inside container context.
  - Automated smoke assertion that submitted jobs can execute allowlisted console command in dockerized runtime.
- Validation:
  - docker compose -f .\docker-compose.runtime.yml --env-file .\.env.runtime up --build
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
- Non-goals:
  - No distributed queue integration.
  - No provider preflight expansion.
- Rollback strategy:
  - Keep previous image/runtime docs path as fallback while introducing shell-enabled image variant.
- Completion artifact:
  - Docker smoke output showing console command success in runtime container.

### T16 Runtime Cancellation Hard-Stop
- Goal: Ensure cancel transitions terminate active agent execution, not only mark job state.
- Files: lllars_core/runtime_api.py, lllars_core/runtime_runner.py, tests/test_runtime_api.py, tests/test_runtime_runner.py.
- Adds:
  - Cancel handle propagation from runtime service into active run process.
  - Runner-level termination path returning a canceled terminal outcome.
  - Race-safe finalization for cancel vs success/failure completion.
- Validation:
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
  - .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner.py"
- Non-goals:
  - No distributed cross-host cancellation control.
  - No external queue dependency required.
- Rollback strategy:
  - Preserve state-only cancel behavior as compatibility fallback path.
- Completion artifact:
  - Test evidence that in-flight jobs can be force-terminated to `canceled`.

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
