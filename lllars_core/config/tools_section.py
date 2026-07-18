from __future__ import annotations

from lllars_core.config.models import DEFAULT_COMMAND_PROFILE

COMMAND_PROFILE_REGISTRY = {
    "none": (),
    "python-playground": (
        "python main.py",
        "python test.py",
    ),
}


def canonicalize_shell_command(command: str) -> str:
    normalized = " ".join(command.strip().split())
    normalized = normalized.replace('"', "").replace("'", "")
    normalized = normalized.replace("\\", "/")
    return normalized


def collect_allowed_shell_commands(
    test_command: str | None,
    eval_command: str | None,
    profile_commands: tuple[str, ...],
) -> tuple[str, ...]:
    allowed_shell_commands: list[str] = []
    seen_allowed_commands: set[str] = set()

    def append_allowed(raw_command: str) -> None:
        canonical = canonicalize_shell_command(raw_command)
        if canonical and canonical not in seen_allowed_commands:
            seen_allowed_commands.add(canonical)
            allowed_shell_commands.append(canonical)

    if test_command:
        append_allowed(test_command)
    if eval_command:
        append_allowed(eval_command)
    for command in profile_commands:
        append_allowed(command)

    return tuple(allowed_shell_commands)


def resolve_command_profile(cfg: dict) -> tuple[str, tuple[str, ...]]:
    profile_name = str(
        cfg.get("command_profile", DEFAULT_COMMAND_PROFILE)
    ).strip().lower()
    if profile_name not in COMMAND_PROFILE_REGISTRY:
        available = ", ".join(sorted(COMMAND_PROFILE_REGISTRY))
        raise ValueError(
            "Unknown command_profile "
            f"{profile_name!r}. Available profiles: {available}"
        )
    return profile_name, COMMAND_PROFILE_REGISTRY[profile_name]


def build_default_tool_policy(
    test_command: str | None,
    eval_command: str | None,
    allowed_shell_commands: tuple[str, ...],
) -> str:
    lines = [
        "Tool policy:",
        "- Only edit files inside the project root.",
        "- Use list_files/read_file/write_file for file operations.",
    ]
    if test_command is not None:
        lines.append("- Use run_test_command for tests.")
    if eval_command is not None:
        lines.append("- Use run_eval_command for eval.")
    if allowed_shell_commands:
        lines.append(
            "- Use list_allowed_shell_commands and "
            "run_allowlisted_shell for shell execution."
        )
    return "\n".join(lines)
