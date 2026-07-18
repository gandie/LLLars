# T68 Agent Builder PydanticAI Native Model Inference

## Metadata
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Runtime agent construction still hardcodes Ollama model/provider classes and custom parsing helpers. This duplicates framework behavior and risks drift from pydantic_ai native provider/model mechanics.

## Objective
Migrate runtime agent model construction to pydantic_ai native inference while preserving compatibility for legacy unprefixed local model values.

## Scope
- Replace hardcoded Ollama model/provider construction in agent builder with native `infer_model` flow.
- Keep provider_url override support by using provider_factory wiring only where supported by provider classes.
- Preserve legacy compatibility by mapping model strings without explicit provider prefixes to Ollama.
- Add focused tests for model-spec resolution compatibility.

## Non-Goals
- No broad config schema redesign in this task.
- No startup probe behavior changes.
- No runtime API contract changes.

## Target Files
- lllars_core/agent_builder.py
- tests/test_agent_builder.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert agent-builder model construction to OllamaModel/OllamaProvider path.

## Completion Artifact
Agent builder uses pydantic_ai native model inference with passing targeted and full-suite tests.

## Completion Notes
- Replaced direct `OllamaModel`/`OllamaProvider` construction with pydantic_ai native `infer_model` and provider factory wiring.
- Kept backward compatibility by resolving model values without explicit provider prefix to `ollama:<model>`.
- Preserved `provider_url` override behavior for providers that expose a `base_url` constructor parameter.
- Added model spec resolution regression tests in `tests/test_agent_builder.py`.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`