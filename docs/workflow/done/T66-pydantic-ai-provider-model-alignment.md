# T66 PydanticAI Provider Model Alignment

## Metadata
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Current startup model probing includes custom provider-prefix inference and custom endpoint assumptions. We need to verify where this duplicates or diverges from pydantic_ai native provider/model resolution so we avoid reinforcing non-framework patterns.

## Objective
Produce a docs-first comparison of pydantic_ai provider/model support versus current LLLars implementation, and identify concrete refactor targets to delegate behavior back to pydantic_ai.

## Scope
- Research pydantic_ai docs and runtime APIs for provider/model resolution and support.
- Map current LLLars provider/model probing logic and runtime model construction.
- Identify mismatches, duplication risk, and recommended alignment path.

## Non-Goals
- No broad runtime architecture refactor in this task artifact.
- No provider feature expansion beyond what pydantic_ai already supports.

## Target Files
- lllars_core/mcp/model_probe_support.py
- lllars_core/mcp/model_probe.py
- tests/test_mcp_model_probe.py
- docs/configuration.md
- README.md
- docs/workflow/tasks/T66-pydantic-ai-provider-model-alignment.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\
- PASS: .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_mcp_model_probe.py"
- PASS: .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- PASS: .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- PASS: .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Keep existing provider-aware probe implementation until replacement behavior is validated.

## Completion Artifact
Implemented pydantic_ai-native provider mechanics in startup model probe:

- Removed local static provider-prefix taxonomy and URL-shape inference fallback.
- Adopted pydantic_ai-native `parse_model_id` + `infer_provider_class` validation.
- Derived OpenAI-compatible provider set from pydantic_ai openai compatibility types.
- Changed unsupported provider families to explicit skip lines instead of custom probing.
- Updated tests and docs to reflect framework-native behavior.