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
    correctness: 4
    scope_discipline: 5
    validation_trust: 5

  collaboration:
    ambiguity_handling: 3
    operator_load: 4
    trust_delta: 4

  notes: >
    Bugfix run with clear scope. No magic here.
    Yet, ping-pong in python code was spotted, agent struggling with
    file length rule which was handles rather poorly.
---

# T84 Timeout Skill Telemetry Consistency

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
Runtime startup reports configured markdown skills, but timeout summaries can report `skills_loaded=0 [none]`, which is misleading and makes it hard to trust skill usage diagnostics.

## Objective
Ensure timeout and cancellation result telemetry preserves configured skill loading information and any observed skill usage signals so summary output remains consistent.

## Scope
- Seed runtime timeout telemetry with configured skill IDs/counts.
- Capture skill usage IDs from streamed thought events before terminal timeout/cancel.
- Add regression tests for timeout telemetry consistency.

## Non-Goals
- Changing core agent prompt/behavior semantics.
- Redesigning skill capability loading in pydantic-ai.

## Target Files
- lllars_core/runtime/runner_orchestrator.py
- lllars_core/runtime/runner_stream.py
- lllars_core/runtime/runner_single.py
- tests/test_runtime_runner_deadlines.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner_deadlines.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\
- .\venv\Scripts\python.exe .\lllars.py --config .\factorio.example.json --timeout-sec 15 --prompt "Use factorio agent skill! Get base and player overview! Then do refueling and mining sweep! That means refuel everything with coal and bring ore to ovens!"

## Rollback
Revert changes in runner orchestrator/stream/single and deadline tests to previous behavior if skill telemetry changes produce regressions.

## Completion Artifact
Passing targeted and full-suite test outputs plus summary logs showing non-zero `skills_loaded` and non-zero `skills_used` when eager skill loading is enabled.

## Validation Evidence
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner_deadlines.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
- PASS reproduction run: timeout summary reports `skills_loaded=1 [factorio-agent] | skills_used=1 [factorio-agent]`.
