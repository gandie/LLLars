# T81 Native Web Research Tooling

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
The runtime lacks first-class web research tools, limiting research-heavy operator workflows.

## Objective
Add native local websearch/webfetch tooling using pydantic-oriented capabilities with explicit policy controls and test coverage.

## Scope
- Implement native web search/fetch tool registration path.
- Add config controls for web tooling enablement and policy behavior.
- Integrate with existing network policy and runtime guardrails.
- Add tests for enabled, disabled, and offline behavior.
- Document operator usage and safety boundaries.

## Non-Goals
- No broad crawling framework.
- No background indexing system.

## Ambiguity Gates
- Domain policy: confirm allowlist/denylist/none default behavior.
- Offline policy: confirm expected tool behavior when network_policy=offline.
- Content limits: confirm response-size and truncation policy.
- Error policy: confirm whether external fetch errors surface raw or normalized.

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