# T001 Refactor lllars_core for Module Clarity and Organization

## Metadata
- Owner: unassigned
- Created: 2026-08-13
- Updated: 2026-08-13

## Why Needed

The lllars_core codebase has grown under boundary-enforcement pressure during multiple iterations of failed design checks. While enforced boundaries have kept the core relatively clean, the internal structure reveals organizational debt:

1. **Config module fragmentation** (82 nodes): Contains 18+ files with unclear separation between responsibilities. Runtime configuration builders (runtime_inputs_builder, runtime_values, runtime_section, runtime_text_fields) are scattered across separate files instead of cohesive groups. Each has single functions or tightly coupled builder patterns.

2. **Runtime module size** (144 nodes): The largest subsystem is monolithic and mixes concerns: job execution (job_runner.py), orchestration (runner_orchestrator.py), API surface (api.py, web.py), results handling (runner_results.py, results.py), and execution flow (execution.py, service_execution.py). No clear internal boundaries between these concerns.

3. **Tools module naming confusion** (8 files, 44 nodes): Contains registry, descriptors, plugins, shell_policy, shell_runtime_policy, web_research, native—unclear what logically groups these or how they relate to each other.

4. **Top-level module clarity**: asyncio_compat, runtime_guard, runner, and skills are loosely defined at package root with unclear purposes and low cohesion.

5. **Job store over-coupling**: job_store.py is a core hub with 62 fan-in references (28 from config, 23 from runtime), suggesting it may be absorbing too much responsibility or used as a dumping ground for state.

The codebase is **functionally correct** but **organizationally under-architected**. The goal is to improve naming, clustering, and module responsibility without changing runtime behavior.

## Objective

Refactor lllars_core into a cleaner, more maintainable structure where:
- Module boundaries are clear and defensible
- Naming directly reflects responsibility
- Related code is clustered together logically
- Fan-in hubs like job_store have narrower, more specific responsibilities
- Internal subsystems (runtime, config, tools) are decomposed into cohesive sub-packages
- The codebase invites extension and modification without violating existing boundaries

## Scope

### In Scope
- **Module reorganization**: Restructure runtime, config, and tools packages into logical sub-packages
- **Naming improvement**: Rename modules to clearly reflect responsibility (e.g., builders → configuration, orchestration → coordination)
- **Boundary clarification**: Identify and document responsibilities of entry points (cli, agent_builder, mcp) and leaf modules (console, shell, skills)
- **Job store decoupling analysis**: Evaluate whether job_store responsibilities can be narrowed or split
- **Internal API surface review**: Ensure public vs. internal module APIs are explicit
- **Dead code removal**: Identify and remove unused functions, imports, or modules found during refactoring

### Non-Goals
- Runtime behavior changes (no feature modifications, no API changes visible to callers)
- Test restructuring beyond what is necessary to support module moves
- Rewriting modules from scratch (incremental refactoring only)
- Plugin/tools ecosystem redesign (tools module is out-of-core responsibility)

## Target Files

### Priority 1: Core Refactoring
- lllars_core/config/ (all 18 files) → refactor into sub-packages: builders, loaders, models, sections
- lllars_core/runtime/ (all 21 files) → refactor into sub-packages: execution, orchestration, models, results, api
- lllars_core/tools/ (8 files) → refactor into sub-packages: registry, plugins, policies, capabilities

### Priority 2: Entry Points & Leaves
- lllars_core/cli.py
- lllars_core/agent_builder.py
- lllars_core/mcp/ (reorganize if needed)
- lllars_core/console.py
- lllars_core/shell.py
- lllars_core/skills.py

### Priority 3: Root Module
- lllars_core/asyncio_compat.py (clarify purpose: compatibility layer?)
- lllars_core/runtime_guard.py (clarify purpose: safety enforcement?)
- lllars_core/runner.py (clarify purpose: entry point coordinator?)
- lllars_core/job_store.py (evaluate splitting responsibilities)
- lllars_core/job_store_record.py (evaluate if it should be in job_store sub-package)

## Verification

### Pre-Refactoring Analysis
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" (baseline: all tests pass)
- Run codebase-memo architecture scan to establish baseline metrics
- Document current module dependencies and fan-in/fan-out

### During Refactoring
- Keep all tests passing after each major module move
- Use semantic code analysis to validate no references are broken
- Compare pre/post architecture metrics to confirm improvements

### Post-Refactoring Validation
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests (full suite must pass)
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"
- Run codebase-memo architecture scan to confirm improvements in:
  - Reduced fan-in on job_store (target: < 40)
  - Improved cohesion within runtime, config, tools sub-packages (target: > 0.85)
  - Clearer layer structure (entry → core → leaf)
  - Reduced average module coupling

## Rollback

If refactoring introduces test failures or imports break:
1. Revert all git changes: `git checkout -- lllars_core/`
2. Restore original test state
3. Document failure point and reason

No runtime data is affected by this refactoring; rollback is straightforward.

## Completion Artifact

A refactored lllars_core with:
1. Updated module structure showing in `lllars_core/` folder layout
2. All imports updated to reflect new paths (no broken references)
3. All unit tests passing without modification to test logic
4. Updated docstrings and module `__init__.py` files explaining new responsibilities
5. Final architecture scan report showing improved metrics
6. Changelog entry documenting changes and improvements
7. (Optional) Updated docs/workflow/DESIGN.md reflecting new internal architecture if it exists

## Notes

- This is a **structural-only** refactoring. No logic changes, no API changes to callers.
- High boundary sensitivity: changes will cascade across imports. Use semantic code search to catch all references.
- Incremental approach strongly recommended: move one sub-package at a time, validate tests, then move next.
