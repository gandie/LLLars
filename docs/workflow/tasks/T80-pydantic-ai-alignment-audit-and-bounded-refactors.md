# T80 Pydantic AI Alignment Audit And Bounded Refactors

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
Custom wrappers remain around framework-native capabilities; a bounded audit is needed to reduce maintenance drift and avoid unnecessary bespoke behavior.

## Objective
Run a docs-first pydantic_ai alignment audit, then implement only the highest-value 1-2 bounded refactors that remove or simplify custom framework-native replacements.

## Scope
- Produce an audit matrix of current custom implementations versus pydantic_ai native features.
- Identify and prioritize bounded refactor slices with risk notes.
- Implement only approved bounded slices with tests.
- Update docs to reflect post-refactor native usage.

## Non-Goals
- No broad rewrite of agent/runtime architecture.
- No unbounded refactor campaign in a single task.

## Target Files
- lllars_core/agent_builder.py
- lllars_core/runtime/
- lllars_core/tools/
- docs/DESIGN.md
- docs/configuration.md
- tests/

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert bounded refactor commits and retain prior wrapper behavior.

## Completion Artifact
Audit report exists, selected bounded slices are implemented, and full-suite regressions are clear.