"""sovth-config — Southpaw's hermes-agent toolkit.

Provides three tools:
- reading_list: deep-research wiki generator (low/high/max)
- character_card: profile character-card generator (game-card aesthetic)
- invoke_profile: ^<profile> background agent invocation
"""

from __future__ import annotations

from .schemas import (
    READING_LIST_SCHEMA,
    CHARACTER_CARD_SCHEMA,
    INVOKE_PROFILE_SCHEMA,
)
from .tools import (
    _handle_reading_list,
    _handle_character_card,
    _handle_invoke_profile,
    check_available,
)


def register(ctx) -> None:
    """Register the sovth-config tools with the hermes-agent plugin context."""
    ctx.register_tool(
        name="reading_list",
        toolset="sovth_config",
        schema=READING_LIST_SCHEMA,
        handler=_handle_reading_list,
        check_fn=check_available,
        emoji="📚",
    )
    ctx.register_tool(
        name="character_card",
        toolset="sovth_config",
        schema=CHARACTER_CARD_SCHEMA,
        handler=_handle_character_card,
        check_fn=check_available,
        emoji="🎴",
    )
    ctx.register_tool(
        name="invoke_profile",
        toolset="sovth_config",
        schema=INVOKE_PROFILE_SCHEMA,
        handler=_handle_invoke_profile,
        check_fn=check_available,
        emoji="⚡",
    )


__all__ = ["register"]
