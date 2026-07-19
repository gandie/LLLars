# T72 Wire Forcing Line Skill Into Friday

## Metadata
- Owner: unassigned
- Created: 2026-07-19
- Updated: 2026-07-19

## Why Needed
A new forcing-line-development skill exists but is not explicitly routed in Friday's skill selection rules. Without routing, ambiguity-heavy tasks may not consistently trigger the intended decision discipline.

## Objective
Wire forcing-line-development into Friday skill routing rules with minimal changes.

## Scope
- Update Friday agent skill routing section to include forcing-line-development trigger conditions.
- Keep wording concise and consistent with existing rule style.

## Non-Goals
- No runtime code changes.
- No additional policy framework changes.

## Target Files
- .github/agents/friday.agent.md
- docs/workflow/tasks/T72-wire-forcing-line-skill-into-friday.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert Friday agent skill routing rule addition.

## Completion Artifact
Friday skill routing explicitly includes forcing-line-development usage criteria.

## Completion Notes
- Added forcing-line-development routing rule in Friday `Skill Routing Rules` section.
- Rule explicitly targets ambiguity-heavy design/implementation decisions and treats unresolved branches as stop-and-ask blockers.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
