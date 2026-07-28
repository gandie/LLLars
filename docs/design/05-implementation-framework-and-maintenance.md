# Implementation Framework and Maintenance

## Implementation Framework (Now Active)
- Primary implementation agent: Friday.
- Skills:
  - PydanticAI Framework Expertise
  - FastAPI Expert
  - Modern Python Guru
- Task-oriented implementation workflow is managed through
  docs/workflow/README.md and task files under docs/workflow/tasks/.

## Success Criteria
- Reproducible runs from API payloads.
- Strong filesystem safety boundaries in containerized execution.
- No regression between one-shot and runtime service paths.
- Actionable artifacts/logs for debugging and audit.

## Truth-Driven Maintenance Rule
Any roadmap or baseline statement in these design chapters must be updated when
runtime behavior changes and validated.

Validation sources for updates:
- Passing targeted tests and smoke checks.
- Current runtime endpoints/behavior in shipped code.
- Matching entries in planning and changelog docs.
