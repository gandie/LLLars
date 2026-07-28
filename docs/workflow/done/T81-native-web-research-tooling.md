---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-07-28
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
    correctness: 4
    scope_discipline: 4
    validation_trust: 3

  collaboration:
    ambiguity_handling: 4
    operator_load: 3
    trust_delta: 4

  notes: >
    Many files needed to be touched. Worried about boundary ping-pong might harm code quality
---

# T81 Native Web Research Tooling

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-28

## Why Needed
The runtime lacked first-class web research tooling, limiting research-heavy operator workflows.

## Objective
Add native local websearch/webfetch tooling using pydantic-oriented capabilities with explicit policy controls and test coverage.

## Scope
- Implement native web search/fetch tool registration path.
- Add config controls for web tooling enablement and policy behavior.
- Integrate with existing network policy and runtime guardrails.
- Add tests for enabled, disabled, and offline behavior.
- Document operator usage and safety boundaries.
- Add example to playground config.

## Non-Goals
- No broad crawling framework.
- No background indexing system.

## Ambiguity Gates
- Domain policy: confirm allowlist/denylist/none default behavior.
- Offline policy: confirm expected tool behavior when network_policy=offline.
- Content limits: confirm response-size and truncation policy.
- Error policy: confirm whether external fetch errors surface raw or normalized.

## Ambiguity Resolutions
- Domain policy default: `none`.
- Offline behavior: skip registering web tools when `network_policy=offline`.
- Content limits: use provider defaults (no extra LLLars truncation layer).
- Error policy: normalized runtime tool-error envelopes.

## Target Files
- lllars_core/tools/
- lllars_core/config/
- lllars_core/runtime/
- docs/configuration.md
- docs/runtime_api.md
- tests/

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Disable/remove web tooling group and revert config/docs/test additions.

## Completion Artifact
Web research tools are configurable, policy-bound, test-covered, and documented.

## Validation Evidence
- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`.
