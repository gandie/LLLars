# T71 Forcing Line Development Skill

## Metadata
- Owner: unassigned
- Created: 2026-07-19
- Updated: 2026-07-19

## Why Needed
Current guardrails exist, but the core thinking model is not captured as a reusable development skill. A dedicated skill can encode candidate-move generation, forcing-line evaluation, and ambiguity stop behavior across design and implementation work.

## Objective
Create a reusable repository skill that operationalizes forcing-line thinking for software development, especially during early design and also during implementation decisions.

## Scope
- Add a new skill under `.github/skills/` with clear mission, triggers, loop, and hard rules.
- Keep instructions generic enough for broad software development use.
- Emphasize ambiguity stop-and-ask behavior and minimal winning-line execution.

## Non-Goals
- No runtime code changes.
- No framework-specific process engine or CI policy changes.

## Target Files
- .github/skills/forcing-line-development/SKILL.md
- docs/workflow/tasks/T71-forcing-line-development-skill.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Remove the new skill file and task artifact updates.

## Completion Artifact
Skill file exists with forcing-line workflow and validation evidence is recorded.

## Completion Notes
- Added new skill `.github/skills/forcing-line-development/SKILL.md` to encode candidate-move generation, forcing-line selection, ambiguity stop behavior, and minimal winning-line execution.
- Scoped skill for early design and broader software development decisions.
- Included explicit anti-patterns to block speculative drift and hidden assumptions.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
