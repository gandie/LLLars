# T69 Restore Ollama v1 Base URL Normalization

## Metadata
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
After migrating agent model construction to pydantic_ai native inference, oneshot runtime requests to Ollama started failing with OpenAI-path 404 errors. The regression was caused by removing legacy `/v1` base-url normalization for Ollama.

## Objective
Restore Ollama-compatible base-url normalization in provider factory wiring while keeping native pydantic_ai inference.

## Scope
- Reintroduce Ollama-only `/v1` base-url normalization during provider construction.
- Add regression tests for provider base-url normalization behavior.
- Validate e2e oneshot command path and full suite.

## Non-Goals
- No additional provider-specific URL rewrites beyond Ollama compatibility fix.
- No config schema changes.

## Target Files
- lllars_core/agent_builder.py
- tests/test_agent_builder.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
- .\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --timeout-sec 60 --prompt "Quick! Run tests in workspace!"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert provider factory base-url normalization changes in agent_builder.

## Completion Artifact
Oneshot run no longer crashes with Ollama 404 path regression and targeted/full tests pass.

## Completion Notes
- Added `_normalize_provider_base_url` in agent builder and restored Ollama-only `/v1` normalization.
- Kept non-Ollama provider URLs unchanged.
- Added focused regression tests for provider URL normalization.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"`
	- PASS `.\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --timeout-sec 60 --prompt "Quick! Run tests in workspace!"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`