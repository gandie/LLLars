---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-07-27
  verdict: accepted
  would_delegate_similar_again: true

  score_scale:
    min: 1
    max: 5
    meaning:
      1: poor
      3: acceptable
      5: excellent

  outcome:
    correctness: 3
    scope_discipline: 3
    validation_trust: 3

  collaboration:
    ambiguity_handling: 4
    operator_load: 4
    trust_delta: 4

  notes: >
    Done as specified afaik
---

# T39 Configurable Native and Plugin Tool Registry

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-27

## Why Needed
Runtime tool registration was fixed to built-in native wiring, which blocked
operator-controlled native tool toggles and safe onboarding of local plugin
tools. T39 establishes explicit config semantics and diagnostics for safe,
deterministic extensibility.

## Objective
Implement configurable native tools and local plugin tool loading with safety
controls.

## Scope
- Native tool toggles with allow/deny rules.
- Plugin discovery and registration from local paths.
- Duplicate/missing/unsafe plugin diagnostics.

## Non-Goals
- No remote plugin marketplace.
- No dynamic code download.

## Target Files
- lllars_core/tools/registry.py
- lllars_core/tools/plugins.py
- lllars_core/config/tool_registry_section.py
- lllars_core/config/tools_section.py
- lllars_core/config/models.py
- lllars_core/config/loader_steps.py
- lllars_core/config/loader.py
- lllars_core/config/run_builder.py
- lllars_core/config/harness_builder.py
- lllars_core/runtime/models.py
- tests/test_config.py
- tests/test_agent_builder.py
- tests/test_tool_registry.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_tool_registry.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Fallback to built-in fixed native toolset.

## Completion Artifact
Deterministic tool-registration tests for native and plugin modes.

## Completion Notes
- Added run-config parsing for `tool_groups` (`enabled`/`disabled`) and
  `tool_plugins.paths` with duplicate/unknown/overlap diagnostics.
- Added configurable runtime registry routing by enabled tool groups in
  `register_runtime_tools`.
- Added local plugin loader with safety controls: project-root confinement,
  missing-path diagnostics, Python-module filtering, duplicate module
  detection, and required `register_tools(agent, cfg, tool_error)` entrypoint.
- Added config and registry regression tests in `test_config.py` and
  `test_tool_registry.py`, and kept `test_agent_builder.py` focused on
  builder-specific regressions.
- Validation results:
  - PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"`
  - PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"`
  - PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_tool_registry.py"`
  - PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
  - PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`