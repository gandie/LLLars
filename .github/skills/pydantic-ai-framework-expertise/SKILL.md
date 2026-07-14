---
name: PydanticAI Framework Expertise
description: Use when implementing or modifying agent behavior based on pydantic_ai. Enforces docs-first framework usage and discourages custom reinvention.
---

# PydanticAI Framework Expertise

## Mission
Use PydanticAI correctly by reading official docs first and applying native framework patterns before custom code.

## Required Docs
- https://pydantic.dev/docs/ai/overview/

## Hard Rules
- Read relevant PydanticAI docs before implementation.
- Prefer native features over custom wrappers and workarounds.
- Do not invent behavior when docs already define it.
- If uncertain after reading docs, ask for clarification before coding.

## Working Style
1. Identify the exact PydanticAI feature needed.
2. Check official docs for the canonical approach.
3. Implement the smallest correct change.
4. Validate behavior with focused checks.

## Anti-Patterns
- Guessing API signatures from memory.
- Building custom orchestration when framework already supports it.
- Adding complexity before confirming a native path is insufficient.
