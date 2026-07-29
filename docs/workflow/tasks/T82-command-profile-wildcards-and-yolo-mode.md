# T82 Command Profile Wildcards And Yolo Mode

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
Operators requested more flexible shell command profile behavior for dynamic workflows.

## Objective
Add wildcard command-profile resolution and yolo mode semantics with explicit safety boundaries and full validation coverage.

## Scope
- Implement wildcard resolution semantics for command profiles.
- Implement yolo mode according to operator-approved contract.
- Preserve observability and safety diagnostics for resolved commands.
- Add comprehensive config/runtime tests and docs updates.

## Non-Goals
- No unrestricted shell execution by default.
- No changes to unrelated runtime scheduling or MCP behavior.

## Ambiguity Gates
1. Yolo model: confirm whether yolo is a profile name, boolean flag, or both.
2. Safety semantics: confirm whether yolo bypasses allowlist or only broadens profile selection.
3. Wildcard domain: confirm matching target (profile names only vs command strings too).
4. Pattern syntax: confirm glob-only vs regex support.
5. Conflict behavior: confirm deterministic precedence when multiple wildcard matches occur.

## Ambiguity Resolvers ( Operator answers )
1. Yolo mode is basically a new tool_group like `native_shell`. Lets define it as `native_shell_yolo` right now. Within this new tool group we have an unrestricted, yet environment-aware tool-wrapper for console commands. Simple as that.
2. As definition in answer 1 indicates, `native_shell_yolo` is unrestricted shell access with no allowlist mechanics at all.
3. Wildcards only for command strings, **NOT** for profiles! I want to be able to configure a command like `./venv/bin/python *` to allow specific python interpreter usage, or `./tools/*` to allow workspace tool folder tool calling.
4. Remember use case examples from answer 3. In fact, i only need `*` as wildcard in terms of "command string may continue arbitrarily from here". We dont even need clever resolvers. commands which continue after `*` should just be truncated, e.g. `python *.py` should become just `python *` ! The reasoning is i dont want to complicate things and the meaning of `*`. Otherwise we would have to discuss whether `python *.py` included not only filename, but also arguments. If that was `python * *.py` we would have instantly complicated everything, because meaning of asterisks is different then. I DONT WANT TO ENTER THAT DIRECTION! EVER! NO!
5. Keep it simple and stupid. Answers from 3 and 4 reveal how this issue is treated. Wildcards as defined do not pose any meaningful threat of conflicts. If users defined both `python*` and `python *` commands, first match wins. Period, end of dicussion.

## Target Files
- lllars_core/config/tools_section.py
- lllars_core/runtime/settings.py
- lllars_core/config/models.py
- tests/test_config_command_profiles.py
- tests/test_runtime_runner_overrides.py
- docs/configuration.md
- README.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert wildcard/yolo parsing and restore strict named profile semantics.

## Completion Artifact
Wildcard and yolo behavior is explicitly defined, safety-bounded, tested, and documented.