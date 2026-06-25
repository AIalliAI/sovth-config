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
# skill_market
# ---------------------------------------------------------------------------

# Allow override via SOVTH_CONFIG_ROOT env var (for testing or non-default
# repo locations). Default: ~/projects/sovth-config
SOVTH_CONFIG_ROOT = Path(
    os.environ.get("SOVTH_CONFIG_ROOT")
    or os.path.expanduser("~/projects/sovth-config")
)

# Suggestion log lives outside the repo (per-user state).
SUGGESTIONS_PATH = Path(
    os.environ.get("SOVTH_CONFIG_SUGGESTIONS")
    or os.path.expanduser("~/.hermes/sovth-config/suggestions.json")
)

# Files scanned for keyword matches during `search`.
_MARKET_DOC_FILES = ("SOUL.md", "AGENTS.md", "SKILL.md", "README.md")


def _suggestions_load() -> list[dict[str, Any]]:
    if not SUGGESTIONS_PATH.exists():
        return []
    try:
        data = json.loads(SUGGESTIONS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _suggestions_save(items: list[dict[str, Any]]) -> None:
    SUGGESTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUGGESTIONS_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


def _market_description(artifact_dir: Path) -> str:
    """Best-effort one-line description for an artifact directory."""
    for docname in _MARKET_DOC_FILES:
        doc = artifact_dir / docname
        if doc.exists():
            try:
                text = doc.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # First non-empty, non-heading line.
            for line in text.splitlines():
                stripped = line.strip().lstrip("#").strip()
                if stripped:
                    return stripped[:200]
    return ""


def _scan_artifacts() -> list[dict[str, Any]]:
    """Walk profiles/*/ and skills/*/ and return a flat list of artifacts."""
    root = SOVTH_CONFIG_ROOT
    artifacts: list[dict[str, Any]] = []
    for kind, subdir in (("profile", "profiles"), ("skill", "skills")):
        base = root / subdir
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            artifacts.append(
                {
                    "type": kind,
                    "name": entry.name,
                    "path": str(entry),
                    "description": _market_description(entry),
                }
            )
    return artifacts


def _handle_skill_market(args: dict[str, Any], **_: Any) -> str:
    action = str(args.get("action") or "").strip()
    if not action:
        return _err("action is required (search|register|suggest|refine|list|status)")

    # ----- list -----
    if action == "list":
        artifacts = _scan_artifacts()
        return _ok(
            artifacts=artifacts,
            count=len(artifacts),
            root=str(SOVTH_CONFIG_ROOT),
        )

    # ----- search -----
    if action == "search":
        query = str(args.get("query") or "").strip().lower()
        if not query:
            return _err("query is required for `search`")
        terms = [t for t in query.split() if t]
        if not terms:
            return _err("query is required for `search`")
        matches: list[dict[str, Any]] = []
        for art in _scan_artifacts():
            haystack = " ".join(
                [art["name"], art["description"], art["type"]]
            ).lower()
            hits = sum(1 for t in terms if t in haystack)
            if hits == 0:
                continue
            confidence = round(hits / len(terms), 3)
            matches.append({**art, "confidence": confidence, "matched_terms": hits})
        matches.sort(key=lambda m: m["confidence"], reverse=True)
        return _ok(
            query=query,
            matches=matches,
            count=len(matches),
        )

    # ----- register -----
    if action == "register":
        atype = str(args.get("type") or "").strip()
        name = str(args.get("name") or "").strip()
        src = str(args.get("path") or "").strip()
        if atype not in ("skill", "profile"):
            return _err("type is required for `register` (skill|profile)")
        if not name:
            return _err("name is required for `register`")
        if not src:
            return _err("path is required for `register` (source file)")
        src_path = Path(os.path.expanduser(src))
        if not src_path.is_file():
            return _err(f"source file not found: {src_path}")
        subdir = "skills" if atype == "skill" else "profiles"
        dest_dir = SOVTH_CONFIG_ROOT / subdir / name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / src_path.name
        try:
            shutil.copy2(src_path, dest_path)
        except OSError as e:
            return _err(f"failed to copy file: {e}")
        return _ok(
            type=atype,
            name=name,
            path=str(dest_path),
            message=f"Registered {atype} '{name}' at {dest_path}",
        )

    # ----- suggest -----
    if action == "suggest":
        description = str(args.get("query") or "").strip()
        if not description:
            return _err("query is required for `suggest` (gap description)")
        items = _suggestions_load()
        import time, uuid
        sid = uuid.uuid4().hex[:12]
        items.append(
            {
                "id": sid,
                "description": description,
                "counter": 1,
                "state": "pending",
                "created_at": int(time.time()),
            }
        )
        _suggestions_save(items)
        return _ok(
            suggestion_id=sid,
            counter=1,
            state="pending",
            message="Suggestion logged. Use `refine` to bump the counter if the gap recurs.",
        )

    # ----- refine -----
    if action == "refine":
        sid = str(args.get("suggestion_id") or "").strip()
        if not sid:
            return _err("suggestion_id is required for `refine`")
        items = _suggestions_load()
        target = next((s for s in items if s.get("id") == sid), None)
        if target is None:
            return _err(f"no suggestion found with id '{sid}'")
        target["counter"] = int(target.get("counter", 0)) + 1
        ready = target["counter"] >= 3
        if ready:
            target["state"] = "ready"
        _suggestions_save(items)
        return _ok(
            suggestion_id=sid,
            counter=target["counter"],
            state=target["state"],
            ready_for_creation_chain=ready,
            message=(
                "Counter reached threshold — ready for creation chain."
                if ready
                else f"Counter bumped to {target['counter']}. Creation chain triggers at 3+."
            ),
        )

    # ----- status -----
    if action == "status":
        sid = str(args.get("suggestion_id") or "").strip()
        name = str(args.get("name") or "").strip()
        items = _suggestions_load()
        if sid:
            target = next((s for s in items if s.get("id") == sid), None)
            if target is None:
                return _err(f"no suggestion found with id '{sid}'")
            return _ok(suggestion=target)
        # No id — return all suggestions (optionally filtered by name/desc).
        if name:
            filtered = [s for s in items if name.lower() in s.get("description", "").lower()]
        else:
            filtered = items
        return _ok(suggestions=filtered, count=len(filtered))

    return _err(f"unknown action: {action!r}")


# ---------------------------------------------------------------------------
# internal: subprocess sanity (for plugin self-check)
# ---------------------------------------------------------------------------

def _git_available() -> bool:
    return shutil.which("git") is not None
