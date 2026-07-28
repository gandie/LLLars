---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-07-28
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
    correctness: 4
    scope_discipline: 3
    validation_trust: 3

  collaboration:
    ambiguity_handling: 3
    operator_load: 2
    trust_delta: 3

  notes: >
    Agent included file_write ONLY as option for whatever godforsaken reason.
    Leaving it intact because its also kind of hilariously useless.
    Agent also forgot to update docs and example config.
---

# T78 Native File Tools Read Write Split

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-28

## Why Needed
Current native_files group couples read and write operations; least-privilege operation requires the ability to run read-only agents.

## Objective
Introduce finer native file tool group controls so agents can be configured for read-only file access without write capability.

## Scope
- Add granular tool-group options for file-read and file-write capability separation.
- Preserve backward compatibility for existing native_files configurations.
- Update registry/config validation and documentation.
- Add tests for read-only, write-enabled, and compatibility paths.

## Non-Goals
- No shell-policy semantic changes.
- No plugin or MCP behavior redesign.

## Target Files
- lllars_core/tools/registry.py
- lllars_core/tools/native.py
- lllars_core/config/tool_registry_section.py
- tests/test_tool_registry.py
- tests/test_tool_registry_file_groups.py
- tests/test_config.py
- docs/configuration.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert to coarse native_files grouping and remove new granular group references.

## Completion Artifact
Config can express read-only native file tool mode, behavior is test-covered, and legacy configs still function.

## Completion Notes
- Added granular tool groups `native_file_read` and `native_file_write` while keeping `native_files` as a backward-compatible alias.
- Updated runtime tool registration flow to avoid duplicate file-tool registration when legacy and granular groups are configured together.
- Split native file registration into dedicated read and write registration paths while preserving the existing full-access registration helper.
- Extended config tool-group validation to accept the new granular group names.
- Added focused tests for read-only, write-enabled, and compatibility behavior and kept boundary limits compliant by splitting file-group tests into a dedicated module.
- Documented `run.tool_groups` usage for read-only mode and listed supported group names.
- Validation results:
  - PASS `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_config.py"`
  - PASS `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_tool_registry.py"`
  - PASS `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_tool_registry_file_groups.py"`
  - PASS `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
  - PASS `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
  - PASS `./venv/Scripts/python.exe -m unittest discover ./tests/`