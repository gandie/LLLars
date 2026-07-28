# LLLars Design

This file is the hub for design governance and architecture references.

## Truth Hierarchy Reminder
When statements in design docs conflict with observed runtime behavior, trust in
this order:
1. Running code and verified runtime behavior.
2. Repository docs and design docs.
3. Human discussion and intent framing.
4. Agent internal reasoning.
5. Any non-repo memory or cached context (lowest trust).

## Design Chapters
- [01 Baseline and Governance](design/01-baseline-and-governance.md)
- [02 Runtime Vision and Roadmap](design/02-runtime-vision-and-roadmap.md)
- [03 Scheduling and Triggering Contract](design/03-scheduling-and-triggering-contract.md)
- [04 Tool Extensibility and MCP Capability Operations](design/04-tool-extensibility-and-mcp-operations.md)
- [05 Implementation Framework and Maintenance](design/05-implementation-framework-and-maintenance.md)

## Maintenance Rule
Any roadmap or baseline statement in the chapter set must be updated when
runtime behavior changes and validated.

Validation sources for updates:
- Passing targeted tests and smoke checks.
- Current runtime endpoints/behavior in shipped code.
- Matching entries in planning and changelog docs.
