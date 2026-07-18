# T43 Bookkeeping Wiring and Generic AGENTS

## Metadata
- Status: Done
- Priority: P1
- Owner: Friday
- Created: 2026-07-18
- Updated: 2026-07-18

## Objective
Align bookkeeping operations so the skill is mandatory in Friday, AGENTS stays repo-agnostic, and seed-plan references are removable.

## Scope
- Remove seed-plan reference from bookkeeping skill and workflow playbook.
- Make bookkeeping skill mandatory in Friday agent routing rules.
- Rewrite AGENTS bookkeeping section as generic and repository-agnostic.

## Non-Goals
- No runtime behavior changes.
- No test or service logic changes.

## Target Files
- .github/skills/bookkeeping/SKILL.md
- .github/agents/friday.agent.md
- AGENTS.md
- docs/workflow/README.md

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> PASS
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -> PASS

## Rollback
Revert policy documentation edits if operator decides to restore prior wiring conventions.

## Completion Notes
- Bookkeeping skill now references operational workflow artifacts, not the seed plan.
- Friday agent routing now marks bookkeeping usage as mandatory.
- AGENTS bookkeeping chapter is generic and defers concrete details to repository-local playbooks/skills.