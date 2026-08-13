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
      1: poor
      3: acceptable
      5: excellent

  outcome:
    correctness: 4
    scope_discipline: 5
    validation_trust: 3

  collaboration:
    ambiguity_handling: 5
    operator_load: 5
    trust_delta: 3

  notes: >
    Simple. Next runs will tell if this really helped.
---

# T87 Tighten Stopcheck and Boundary Enforcement

## Metadata
- Owner: unassigned
- Created: 2026-08-13
- Updated: 2026-08-13

## Why Needed
Recent done-task evaluations (T80-T86) repeatedly reported boundary friction and ambiguity-handling decline despite existing guardrails. The current rules mention stop-check and forcing-line usage, but enforcement remains too soft.

## Objective
Implement minimal rule hardening for three approved changes only: mandatory pre-action stop-check emission, explicit no-relocation-twice boundary guardrail, and expanded forcing-line trigger on first boundary/policy branch conflict.

## Scope
- Update AGENTS baseline rules with concise hard gates for the three approved changes.
- Update Friday mode guardrails/routing to mirror the same enforcement.
- Keep wording compact and avoid policy sprawl.

## Non-Goals
- No changes to boundary checker code.
- No lexical phrase scanner additions.
- No done-task YAML parser changes.

## Target Files
- AGENTS.md
- .github/agents/friday.agent.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert AGENTS and Friday guardrail/routing edits to prior wording.

## Completion Artifact
Rule text in AGENTS and Friday explicitly enforces the three approved gates, with validation evidence and changelog entry recorded.

## Completion Notes
- Added an auditable pre-action stop-check verdict emission requirement in baseline and Friday rules.
- Added explicit boundary anti-ping-pong rule: no relocating the same symbol twice in one task after boundary failure.
- Expanded forcing-line trigger to include first boundary conflict or policy-interpretation branch.

## Validation Evidence
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\` (139 tests)
