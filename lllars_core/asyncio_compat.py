from __future__ import annotations

import asyncio
import sys


def configure_windows_event_loop_policy() -> None:
    """Use Selector policy on Windows for stable stdio subprocess transport."""
    if sys.platform != "win32":
        return

    policy_cls = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if policy_cls is None:
        return

    current_policy = asyncio.get_event_loop_policy()
    if isinstance(current_policy, policy_cls):
        return

    asyncio.set_event_loop_policy(policy_cls())
