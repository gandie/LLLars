from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic_ai import RunContext
from lllars_core.tools.descriptors import AgentDeps

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from lllars_core.config import HarnessConfig


def resolve_under(root: Path, user_path: str) -> Path:
    candidate = Path(user_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError("Path is outside configured project-root")
    return candidate


def _to_relpath(root: Path, item: Path) -> str:
    return str(item.relative_to(root)).replace("\\", "/")


def _list_files_result(
    project_root: Path,
    path: str,
    recursive: bool,
) -> tuple[str | None, str | None, str | None]:
    target = resolve_under(project_root, path)
    if not target.exists():
        return None, f"Path not found: {path}", (
            "Choose an existing path under project_root."
        )
    if target.is_file():
        return _to_relpath(project_root, target), None, None
    iterator = target.rglob("*") if recursive else target.iterdir()
    listing = "\n".join(
        sorted(_to_relpath(project_root, item) for item in iterator)
    )
    return listing, None, None


def _register_list_files_tool(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    @agent.tool
    def list_files(
        ctx: RunContext[AgentDeps],
        path: str = ".",
        recursive: bool = True,
    ) -> str:
        """List files and folders under project root."""
        _ = ctx
        try:
            result, message, hint = _list_files_result(
                cfg.project_root,
                path,
                recursive,
            )
            if message is not None:
                return tool_error("list_files", message, hint)
            return result or ""
        except Exception as exc:
            return tool_error(
                "list_files",
                str(exc),
                "Only access files inside project_root.",
            )


def _register_read_file_tool(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    @agent.tool
    def read_file(ctx: RunContext[AgentDeps], path: str) -> str:
        """Read a UTF-8 text file under project root."""
        _ = ctx
        try:
            target = resolve_under(cfg.project_root, path)
            if not target.exists() or not target.is_file():
                return tool_error(
                    "read_file",
                    f"File not found: {path}",
                    "Pass a valid file path under project_root.",
                )
            return target.read_text(encoding="utf-8")
        except Exception as exc:
            return tool_error(
                "read_file",
                str(exc),
                "Only access files inside project_root.",
            )


def _register_write_file_tool(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    @agent.tool
    def write_file(
        ctx: RunContext[AgentDeps],
        path: str,
        content: str,
    ) -> str:
        """Write UTF-8 text content to a file under project root."""
        _ = ctx
        try:
            target = resolve_under(cfg.project_root, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            rel = str(target.relative_to(cfg.project_root)).replace("\\", "/")
            return f"Wrote {rel}"
        except Exception as exc:
            return tool_error(
                "write_file",
                str(exc),
                "Use a writable path inside project_root.",
            )


def register_file_tools(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    """Backward-compatible registration for full native file access."""
    register_file_read_tools(agent, cfg, tool_error)
    register_file_write_tools(agent, cfg, tool_error)


def register_file_read_tools(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    _register_list_files_tool(agent, cfg, tool_error)
    _register_read_file_tool(agent, cfg, tool_error)


def register_file_write_tools(
    agent: "Agent[AgentDeps, str]",
    cfg: "HarnessConfig",
    tool_error: Callable[[str, str, str | None], str],
) -> None:
    _register_write_file_tool(agent, cfg, tool_error)
