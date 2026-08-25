---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: YYYY-MM-DD
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
    correctness:
    scope_discipline:
    validation_trust:

  collaboration:
    ambiguity_handling:
    operator_load:
    trust_delta:

  notes: >
    HUMAN NOTES
---

# T89 Strict OpenAI System Message Compatibility

## Metadata
- Owner: unassigned
- Created: 2026-08-25
- Updated: 2026-08-25

## Why Needed
FreeToken (OpenAI-compatible) rejects current request payloads with HTTP 400: "System message must be at the beginning." In this repository, agent requests currently combine multiple instruction/system sources, which can produce multiple system-role messages in chat-completions formatting. This breaks strict providers and blocks runtime execution even when model prefix and provider URL are correct.

## Objective
Implement the most direct fix so requests sent through the OpenAI-compatible path always satisfy strict system-message ordering/shape expectations for this project.

## Scope
- Add a strict OpenAI-compatible request-shaping path for this repository's runtime agent flow.
- Ensure only one leading system message is emitted in request payloads for the affected path.
- Remove/avoid additional system-role message emission after the first position for that path.
- Validate the failing FreeToken scenario now succeeds.

## Non-Goals
- Preserving backward compatibility for other OpenAI-compatible providers.
- Adding provider-specific feature toggles for broad multi-provider behavior.
- Refactoring unrelated runtime, tools, or MCP architecture.

## Target Files
- lllars_core/agent_builder.py
- lllars_core/openai_compat.py
- tests/test_agent_builder.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
- .\venv\Scripts\python.exe .\lllars.py --verbose --config .\playground.example.json --timeout-sec 600 --prompt "List files in workspace"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert all changes introduced for strict system-message compatibility in the target files and restore prior behavior by resetting those files to their pre-task contents.

## Completion Artifact
A merged change where:
- FreeToken no longer returns HTTP 400 for "System message must be at the beginning" on the reproduced command.
- Unit tests covering agent builder/config behavior pass.
- Full test suite passes.
- Changelog entry documents the strict-message compatibility decision and residual risk.

## Completion Notes
- Implemented strict OpenAI-compatible profile enforcement by forcing:
  - supports_inline_system_prompts = false
  - openai_chat_supports_multiple_system_messages = false
  for openai-prefixed models used by the runtime harness.
- Extracted strict-profile mutation logic into lllars_core/openai_compat.py and kept
  lllars_core/agent_builder.py as a thin orchestration layer to satisfy refactor boundaries.
- Added regression tests for strict-profile enforcement behavior in tests/test_agent_builder.py.

## Validation Evidence
- PASS .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
- PASS .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_config.py"
- PASS .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- PASS .\venv\Scripts\python.exe -m unittest discover .\tests\ (141 tests)
- Runtime reproduction confirmed by operator: FreeToken request now succeeds for the previous failing path.
