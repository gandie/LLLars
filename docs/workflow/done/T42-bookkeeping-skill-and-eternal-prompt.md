# T42 Bookkeeping Skill and Eternal Prompt

## Metadata
- Status: Done
- Priority: P1
- Owner: Friday
- Created: 2026-07-18
- Updated: 2026-07-18

## Objective
Lift folder-driven bookkeeping workflow into operational rules and playbook usage.

## Scope
- Add bookkeeping skill for task-handling enforcement.
- Align AGENTS operation rules to folder-driven workflow.
- Add reusable eternal kickoff prompt in workflow playbook.

## Non-Goals
- No runtime behavior changes.
- No endpoint or tool execution policy changes.

## Target Files
- .github/skills/bookkeeping/SKILL.md
- AGENTS.md
- docs/workflow/README.md

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> PASS
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -> PASS

## Rollback
Revert the skill and documentation updates if operator workflow expectations change.

## Completion Notes
- Added bookkeeping skill with hard rules for task file lifecycle and changelog requirements.
- Updated AGENTS post-task protocol to match active and done folder semantics.
- Added eternal kickoff prompt in workflow playbook for repeatable task startup.