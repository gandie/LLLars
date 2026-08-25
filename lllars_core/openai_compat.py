from __future__ import annotations

from pydantic_ai.profiles.openai import OpenAIModelProfile


def enforce_strict_openai_profile(model_obj: object) -> None:
    try:
        profile = getattr(model_obj, "profile")
    except Exception:
        return

    strict_profile = OpenAIModelProfile(
        supports_inline_system_prompts=False,
        openai_chat_supports_multiple_system_messages=False,
    ).update(profile)
    setattr(model_obj, "_profile", strict_profile)
    model_state = getattr(model_obj, "__dict__", None)
    if isinstance(model_state, dict):
        model_state.pop("profile", None)
