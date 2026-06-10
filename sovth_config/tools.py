"""sovth-config tool handlers.

All handlers return JSON strings with shape `{"ok": bool, ...}`. The plugin
contract mirrors the eikon plugin: small, JSON-only, no side effects outside
the configured data directory.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .research import (
    trigger_research_hook,
    build_global_wiki,
    list_items_with_status,
    cancel_research,
    ReadingListError,
)
from .research.character_card import (
    generate_character_card,
    generate_all_character_cards,
    show_character_card,
    build_tutorial,
)
from .research.profile_invoker import invoke_profile


# ---------------------------------------------------------------------------
# Data directory helpers
# ---------------------------------------------------------------------------

# Allow override via SOVTH_READING_LIST_ROOT env var (for testing,
# for users who want a non-default location, or for the local-nosync
# pattern when working across machines). Default: ~/.hermes/reading-list
DATA_ROOT = Path(
    os.environ.get("SOVTH_READING_LIST_ROOT")
    or os.path.expanduser("~/.hermes/reading-list")
)


def _list_dir(list_name: str) -> Path:
    p = DATA_ROOT / list_name
    p.mkdir(parents=True, exist_ok=True)
    (p / "wiki").mkdir(exist_ok=True)
    return p


def _ok(**kwargs: Any) -> str:
    return json.dumps({"ok": True, **kwargs})


def _err(msg: str, **kwargs: Any) -> str:
    return json.dumps({"ok": False, "error": msg, **kwargs})


def check_available() -> bool:
    """Plugin-level availability check. Returns True if data root is writable."""
    try:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        return os.access(DATA_ROOT, os.W_OK)
    except OSError:
        return False


# ---------------------------------------------------------------------------
# reading_list
# ---------------------------------------------------------------------------

def _handle_reading_list(args: dict[str, Any], **_: Any) -> str:
    action = str(args.get("action") or "").strip()
    if not action:
        return _err("action is required (show|add|remove|wiki)")

    list_name = str(args.get("list_name") or "default").strip() or "default"
    list_dir = _list_dir(list_name)

    if action == "show":
        try:
            items = list_items_with_status(list_dir)
            return _ok(list=list_name, items=items, count=len(items))
        except ReadingListError as e:
            return _err(str(e))

    if action == "add":
        target = str(args.get("target") or "").strip()
        if not target:
            return _err("target is required for `add` (URL or file path)")
        depth = str(args.get("depth") or "low").strip()
        max_passes = int(args.get("max_passes") or 5)
        try:
            item = trigger_research_hook(
                list_dir=list_dir,
                target=target,
                depth=depth,
                max_passes=max_passes,
            )
            return _ok(
                list=list_name,
                added=item["id"],
                status=item["status"],
                depth=depth,
                message=(
                    f"Item registered. Research hook is {'running async' if depth != 'low' else 'in progress'}; "
                    f"use `show` to poll status, `wiki` to read the global wiki once complete."
                ),
            )
        except ReadingListError as e:
            return _err(str(e))

    if action == "remove":
        target = str(args.get("target") or "").strip()
        if not target:
            return _err("target is required for `remove`")
        try:
            removed = cancel_research(list_dir, target)
            if removed:
                return _ok(list=list_name, removed=target, message="Removed (and any in-flight research cancelled).")
            return _err(f"No item matching '{target}' found in list '{list_name}'.")
        except ReadingListError as e:
            return _err(str(e))

    if action == "wiki":
        try:
            wiki_md = build_global_wiki(list_dir, list_name=list_name)
            return _ok(
                list=list_name,
                wiki=wiki_md,
                path=str(list_dir / "wiki" / "_index.md"),
            )
        except ReadingListError as e:
            return _err(str(e))

    return _err(f"unknown action: {action!r}")


# ---------------------------------------------------------------------------
# character_card
# ---------------------------------------------------------------------------

def _handle_character_card(args: dict[str, Any], **_: Any) -> str:
    action = str(args.get("action") or "").strip()
    if not action:
        return _err("action is required (generate|generate_all|show|tutorial)")

    preset = str(args.get("preset") or "arcade").strip()
    out_dir = Path(os.path.expanduser(str(args.get("out_dir") or "~/.hermes/sovth-config/profiles")))
    include_portrait = bool(args.get("include_portrait", True))

    try:
        if action == "generate":
            profile = str(args.get("profile") or "").strip()
            if not profile:
                return _err("profile is required for `generate`")
            card_path = generate_character_card(
                profile_name=profile,
                preset=preset,
                out_dir=out_dir,
                include_portrait=include_portrait,
            )
            return _ok(profile=profile, card=str(card_path), preset=preset)

        if action == "generate_all":
            cards = generate_all_character_cards(
                preset=preset,
                out_dir=out_dir,
                include_portrait=include_portrait,
            )
            return _ok(generated=cards, count=len(cards), preset=preset, out_dir=str(out_dir))

        if action == "show":
            profile = str(args.get("profile") or "").strip()
            if not profile:
                return _err("profile is required for `show`")
            content = show_character_card(profile, out_dir=out_dir)
            return _ok(profile=profile, content=content)

        if action == "tutorial":
            profile = str(args.get("profile") or "").strip()
            if not profile:
                return _err("profile is required for `tutorial`")
            tutorial = build_tutorial(profile)
            return _ok(profile=profile, tutorial=tutorial)

    except (ReadingListError, FileNotFoundError) as e:
        return _err(str(e))

    return _err(f"unknown action: {action!r}")


# ---------------------------------------------------------------------------
# invoke_profile (^<profile>)
# ---------------------------------------------------------------------------

def _handle_invoke_profile(args: dict[str, Any], **_: Any) -> str:
    name = str(args.get("name") or "").strip()
    prompt = str(args.get("prompt") or "").strip()
    if not name:
        return _err("name is required (profile name)")
    if not prompt:
        return _err("prompt is required")
    mode = str(args.get("mode") or "auto").strip()
    deliver = str(args.get("deliver") or "origin").strip()
    session_label = args.get("session_label")

    try:
        result = invoke_profile(
            profile_name=name,
            prompt=prompt,
            mode=mode,
            deliver=deliver,
            session_label=session_label,
        )
        return _ok(**result)
    except ReadingListError as e:
        return _err(str(e))


# ---------------------------------------------------------------------------
# internal: subprocess sanity (for plugin self-check)
# ---------------------------------------------------------------------------

def _git_available() -> bool:
    return shutil.which("git") is not None
