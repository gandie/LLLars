---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-08-13
  verdict: accepted
  would_delegate_similar_again: true

  score_scale:
    min: 1
    max: 5
    meaning:
      1: 
      3: 
      5: 

  outcome:
    correctness:  3
    scope_discipline: 3
    validation_trust: 3

  collaboration:
    ambiguity_handling: 3 
    operator_load: 3
    trust_delta: 3

  notes: >
    Too long ago. Nothing to observe. Agent failed copying YAML yet again ... -.-
---

# T85 Todo Capability Configurable and Deactivatable

## Metadata
- Owner: unassigned
- Created: 2026-07-29
- Updated: 2026-07-29

## Why Needed
Runtime errors in factorio/agent runs revealed two related issues:
1. `TodoCapability` from `pydantic_ai_todo` was always enabled, had no configuration option, and could not be disabled
2. When `agent_retries_tools` was set to `null` in config, it was being converted to the default value (1) instead of meaning "no limit"

Both caused `UnexpectedModelBehavior` exceptions when tools (todo tool, MCP find_entities) exceeded max retry count of 1.

## Objective
Make the TodoCapability opt-in via configuration, disabled by default, and allow operators to enable it explicitly in config files when needed.

## Scope
- Add `todo_capability_enabled` boolean config field (default: False)
- Thread configuration through HarnessConfig and RunConfig
- Conditionally instantiate TodoCapability only when enabled
- Fix retry limits parsing to respect explicit null values (use `optional_int` instead of `non_negative_int` for `agent_retries_tools`)
- Update all example config files with explicit `todo_capability_enabled: false`
- Verify full test suite passes

## Non-Goals
- Modify pydantic_ai_todo library
- Change retry behavior or limits
- Add per-tool retry overrides

## Target Files
- lllars_core/config/models.py
- lllars_core/config/run_builder.py (retry limits parsing fix)
- lllars_core/config/harness_builder.py
- lllars_core/agent_builder.py
- tests/test_agent_builder_web_research.py
- factorio.example.json
- playground.example.json
- playground.unrestricted-web.example.json

## Verification
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` — PASS (139 tests)

## Completion Notes
Root cause analysis revealed two distinct issues:

1. **TodoCapability always enabled**: Fixed by adding configurable `todo_capability_enabled` field (default False)
   - Added `DEFAULT_TODO_CAPABILITY_ENABLED = False` to models.py
   - Added `todo_capability_enabled: bool | None` to RunConfig
   - Added `todo_capability_enabled: bool` to HarnessConfig
   - Implemented `_todo_kwargs()` in run_builder.py with boolean parsing
   - Updated harness_builder.py to thread setting to HarnessConfig
   - Modified agent_builder._build_capabilities() to conditionally add TodoCapability
   - Updated all example configs with explicit `todo_capability_enabled: false`

2. **Retry limits ignoring explicit null**: Fixed by config parsing bug in run_builder.py
   - Changed `agent_retries_tools` parsing from `non_negative_int()` to `optional_int()`
   - `non_negative_int()` was converting null to DEFAULT_AGENT_RETRIES_TOOLS (1)
   - `optional_int()` correctly preserves null as None, meaning "no limit"
   - This allows operators to set `"agent_retries_tools": null` to disable tool retry limits entirely

3. **Test coverage**:
   - Fixed test mock in test_agent_builder_web_research.py to include todo_capability_enabled field
   - All 139 tests pass

This enables operators to:
- Disable todo capability: `"todo_capability_enabled": false` (default)
- Disable retry limits for tools: `"agent_retries_tools": null`
- Enable either or both when needed for their use case

## Rollback
1. Remove `todo_capability_enabled` from HarnessConfig and RunConfig
2. Restore `TodoCapability(enable_subtasks=True)` unconditionally in `_build_capabilities()`
3. Remove field from all example config files
4. Restore `DEFAULT_TODO_CAPABILITY_ENABLED` constant removal

## Completion Artifact
✓ Root cause fixed: retry limits now respect explicit null (no limit)
✓ TodoCapability now configurable and disabled by default
✓ Syntax validation passed on all modified Python files
✓ JSON validation passed on all modified config files  
✓ Full test suite passed: `.\venv\Scripts\python.exe -m unittest discover .\tests\` → OK (139 tests, 3.007s)
✓ Changelog entry created in docs/workflow/changelog/2026-07.md
✓ Task moved to docs/workflow/done/
