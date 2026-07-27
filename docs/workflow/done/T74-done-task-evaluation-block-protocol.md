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
    correctness: 2
    scope_discipline: 5
    validation_trust: 2

  collaboration:
    ambiguity_handling: 1
    operator_load: 2
    trust_delta: 2

  notes: >
    Agent tried to sneak in different formats for YAML frontmatter.
    Forced to create parsing tool NOW to force correct style.
---

# T74 Done Task Evaluation Block Protocol

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
Human operator acceptance is a high-signal quality source, but current bookkeeping rules do not provide a structured, machine-readable way to capture that signal per completed task.

## Objective
Add a reusable evaluation frontmatter snippet to workflow docs and require done-task evaluation blocks in bookkeeping completion protocol.

## Scope
- Add reusable split-score YAML snippet to workflow README.
- Update bookkeeping skill rules to require evaluation block for done tasks.
- Keep active task template unchanged.

## Non-Goals
- No scoring automation or parser implementation.
- No historical backfill requirement for existing done tasks.

## Target Files
- docs/workflow/README.md
- .github/skills/bookkeeping/SKILL.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Remove evaluation-block guidance and revert bookkeeping completion requirement to prior state.

## Completion Artifact
Workflow docs and bookkeeping skill consistently require evaluation block after moving tasks to done.

## Completion Notes
- Added a reusable operator-filled YAML frontmatter snippet in `docs/workflow/README.md` with split scores for outcome and collaboration.
- Extended `.github/skills/bookkeeping/SKILL.md` to require `agent_evaluation` frontmatter in done task files after move to `docs/workflow/done/`.
- Kept active task template unchanged and clarified that done-task evaluation frontmatter is not a lifecycle metadata extension.
- Validation results:
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
