"""Tool schemas for the sovth-config plugin.

Each schema describes a single hermes-agent tool. Tools dispatch on an
`action` parameter (one tool = many actions, rather than many tools).
"""

from __future__ import annotations


READING_LIST_SCHEMA = {
    "name": "reading_list",
    "description": (
        "Manage a deeply-researched reading list. Add links or files; each item "
        "auto-triggers a deep-research hook that produces a per-item wiki with "
        "cross-referenced sources. Three depth levels: `low` (single pass, wiki "
        "only), `high` (multi-pass up to 5 iterations, self-evaluates wiki quality "
        "on accuracy/completeness/sourcing/clarity), `max` (everything in `high` "
        "plus a NotebookLM-style manim podcast and a Klerik content-review pass "
        "that loops reviewer feedback back into the wiki). Use `show` to view "
        "the current list and per-item research progress, `add` to register a "
        "new item, `remove` to drop an item, `wiki` to read the global wiki "
        "for the list (only includes wiki-complete items). Storage is per-user "
        "at ~/.hermes/reading-list/."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["show", "add", "remove", "wiki"],
                "description": "What to do with the reading list.",
            },
            "target": {
                "type": "string",
                "description": (
                    "URL or local file path. Required for `add` and `remove`. "
                    "For URLs, must be http(s); for files, must be an absolute "
                    "path readable by the current user (PDF/md/txt/html)."
                ),
            },
            "depth": {
                "type": "string",
                "enum": ["low", "high", "max"],
                "default": "low",
                "description": (
                    "Research depth for `add`. `low` = single pass. `high` = "
                    "1-5 passes, stops when self-eval rates wiki >= 8/10. "
                    "`max` = `high` + manim podcast + Klerik review pass."
                ),
            },
            "list_name": {
                "type": "string",
                "default": "default",
                "description": (
                    "Named list (defaults to 'default'). Use different names to "
                    "keep separate reading lists; the wiki command shows the "
                    "global wiki for the named list."
                ),
            },
            "max_passes": {
                "type": "integer",
                "default": 5,
                "minimum": 1,
                "maximum": 10,
                "description": (
                    "Cap on research passes for `high`/`max` depth. Defaults to 5."
                ),
            },
        },
        "required": ["action"],
    },
}


CHARACTER_CARD_SCHEMA = {
    "name": "character_card",
    "description": (
        "Generate a video-game character card (README + pixel-art portrait) for "
        "a Hermes agent profile. Scans a profile directory for SOUL.md, "
        "AGENTS.md, config.yaml, skills/, and extracts metadata (name, class, "
        "voice, model, eikon, skills). Renders a standardized character-card "
        "README in the game-character-sheet aesthetic, and a pixel-art portrait "
        "in the selected era palette (default: arcade). `generate` builds one "
        "card, `generate_all` walks every profile in ~/.hermes/profiles/, "
        "`show` displays an existing card, `tutorial` returns the import "
        "tutorial for a named profile."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["generate", "generate_all", "show", "tutorial"],
                "description": "What to do.",
            },
            "profile": {
                "type": "string",
                "description": (
                    "Profile name (e.g. 'nous-girl', 'klerik'). Required for "
                    "`generate` (single), `show`, and `tutorial`."
                ),
            },
            "preset": {
                "type": "string",
                "enum": [
                    "arcade", "nes", "snes", "gameboy", "pico8",
                    "c64", "apple2", "mono_green", "mono_amber", "neon", "pastel",
                ],
                "default": "arcade",
                "description": "Pixel-art palette preset. Default: arcade (most game-card energy).",
            },
            "out_dir": {
                "type": "string",
                "default": "~/.hermes/sovth-config/profiles",
                "description": "Where to write generated character cards.",
            },
            "include_portrait": {
                "type": "boolean",
                "default": True,
                "description": "Whether to generate the pixel-art portrait image. Set false to skip if FAL is unavailable.",
            },
        },
        "required": ["action"],
    },
}


INVOKE_PROFILE_SCHEMA = {
    "name": "invoke_profile",
    "description": (
        "Invoke a named Hermes profile as a background agent subprocess. "
        "Spawns the named profile's agent with the given prompt, writing back "
        "to the profile's own sessions/ and MEMORY.md (memory continuity is "
        "preserved per-profile because HERMES_HOME=~/.hermes/profiles/<name>). "
        "Long-running/async work uses the cron primitive (LLM-driven, persists "
        "across sessions); quick ephemeral one-shots use delegate_task with the "
        "profile's SOUL injected as system context. This is the underlying "
        "mechanism for the `^<profile>` quick command."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Profile name (must exist in ~/.hermes/profiles/).",
            },
            "prompt": {
                "type": "string",
                "description": "The prompt/instruction to send to the profile's agent.",
            },
            "mode": {
                "type": "string",
                "enum": ["background", "ephemeral", "auto"],
                "default": "auto",
                "description": (
                    "`background` = long-running cron-style subprocess that "
                    "writes to the profile's session DB. `ephemeral` = fast "
                    "delegate_task with the SOUL injected, in-context. `auto` "
                    "picks based on prompt length/complexity heuristics."
                ),
            },
            "deliver": {
                "type": "string",
                "enum": ["origin", "local", "all"],
                "default": "origin",
                "description": "Where the agent's final response is delivered.",
            },
            "session_label": {
                "type": "string",
                "description": "Optional label for the spawned session (visible in the profile's session history).",
            },
        },
        "required": ["name", "prompt"],
    },
}


SKILL_MARKET_SCHEMA = {
    "name": "skill_market",
    "description": "Search, register, suggest, and refine profiles and skills in the sovth-config repo. Actions: search (find matching artifacts), register (add new artifact), suggest (log a gap), refine (increment similar-gap counter), list (show all artifacts), status (check suggestion state).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "register", "suggest", "refine", "list", "status"],
                "description": "What to do.",
            },
            "query": {
                "type": "string",
                "description": "Search query or suggestion description.",
            },
            "type": {
                "type": "string",
                "enum": ["skill", "profile"],
                "description": "Artifact type (for register).",
            },
            "name": {
                "type": "string",
                "description": "Artifact name (for register/status).",
            },
            "path": {
                "type": "string",
                "description": "File path (for register).",
            },
            "suggestion_id": {
                "type": "string",
                "description": "Suggestion ID (for refine/status).",
            },
        },
        "required": ["action"],
    },
}
