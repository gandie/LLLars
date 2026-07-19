# T70 KISS YAGNI Consent Gates

## Metadata
- Owner: unassigned
- Created: 2026-07-19
- Updated: 2026-07-19

## Why Needed
Recent scheduling contract prep showed risk from adding plausible but unspecified policy semantics. KISS/YAGNI needs explicit enforcement that ambiguous behavior must be clarified with the operator before introducing new mechanics.

## Objective
Add lightweight guardrails that block speculative implementation and require operator clarification for unspecified policy dimensions.

## Scope
- Add a short generic anti-speculation guardrail to AGENTS baseline rules.
- Add concrete, enforceable KISS/YAGNI consent gates to Modern Python Guru skill.
- Keep changes minimal and generic.

## Non-Goals
- No runtime behavior changes.
- No toolchain or policy engine changes.

## Target Files
- AGENTS.md
- .github/skills/modern-python-guru/SKILL.md
- docs/workflow/tasks/T70-kiss-yagni-consent-gates.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert AGENTS and Modern Python Guru skill changes.

## Completion Artifact
Guardrails documented in AGENTS and Modern Python Guru with passing validation evidence.

## Completion Notes
- Added a short generic KISS/YAGNI consent gate section to `AGENTS.md` requiring operator clarification before encoding unspecified policy semantics.
- Added concrete enforcement rules to `modern-python-guru` skill: ask-before-structure, opaque-first contracts, no speculative defaults, and validator scope lock.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
