"""The research hook — data/state layer.

This module is the plugin's source of truth for reading-list state. It
adds items, updates status, cancels in-flight research, and assembles the
global wiki. The actual LLM-driven research happens in `runner.py`, which
is called by the LLM agent (inline for low, via delegate_task for high/max).

The flow:
1. User: /reading-list add <url> --depth high
2. Main agent -> reading_list tool: trigger_research_hook()
3. Hook: adds item to list.yaml in 'pending-research' state, returns item
4. LLM agent: calls runner.run_research(item, depth, max_passes) to do the work
5. Runner: extracts source, generates wiki, self-evals, loops, (max) Klerik, (max) podcast
6. Runner: updates list.yaml to 'wiki-complete' (or 'podcast-complete' for max)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import ReadingListError
from .storage import (
    SCHEMA_VERSION,
    load_list,
    save_list,
    load_research_state,
    save_research_state,
    now_iso,
    slugify,
    wiki_dir,
)
from .extract import detect


# Status constants
STATUS_PENDING = "pending-research"
STATUS_RESEARCHING = "researching"
STATUS_WIKI = "wiki-complete"
STATUS_PODCAST = "podcast-complete"
STATUS_REMOVED = "removed"


def _make_item_id(target: str) -> str:
    date = datetime.utcnow().strftime("%Y-%m-%d")
    return f"{date}-{slugify(target)}"


def _find_item(data: dict[str, Any], target: str) -> dict[str, Any] | None:
    target_norm = target.strip().rstrip("/")
    for item in data.get("items", []):
        if item.get("status") == STATUS_REMOVED:
            continue
        src = (item.get("source") or "").strip().rstrip("/")
        if src == target_norm:
            return item
    return None


def trigger_research_hook(
    list_dir: Path,
    target: str,
    depth: str = "low",
    max_passes: int = 5,
) -> dict[str, Any]:
    """Register a new reading-list item. Returns the item dict.

    The caller (LLM agent) is responsible for invoking `runner.run_research`
    on the returned item. This separation keeps the plugin a pure data layer.
    """
    if depth not in ("low", "high", "max"):
        raise ReadingListError(f"unknown depth: {depth!r}")
    if max_passes < 1 or max_passes > 10:
        raise ReadingListError("max_passes must be between 1 and 10")

    # Validate the target early — fail fast before mutating state.
    try:
        kind = detect(target)
    except ReadingListError as e:
        raise ReadingListError(str(e))

    data = load_list(list_dir)
    existing = _find_item(data, target)
    if existing:
        # Idempotent: same target already in the list, return it as-is.
        return existing

    item = {
        "id": _make_item_id(target),
        "added": now_iso(),
        "source": target,
        "type": kind,
        "status": STATUS_PENDING,
        "depth": depth,
        "max_passes": max_passes,
        "research": {
            "started": None,
            "finished": None,
            "passes_completed": 0,
            "self_eval_score": None,
            "sources_extracted": 0,
            "sources_crossrefed": 0,
            "facts_confirmed": 0,
        },
    }
    data["items"].append(item)
    save_list(list_dir, data)
    return item


def update_item(
    list_dir: Path,
    item_id: str,
    **fields: Any,
) -> dict[str, Any] | None:
    """Mutate fields on an item. Returns the updated item, or None if not found."""
    data = load_list(list_dir)
    for item in data.get("items", []):
        if item.get("id") == item_id:
            item.update(fields)
            save_list(list_dir, data)
            return item
    return None


def mark_research_started(list_dir: Path, item_id: str) -> None:
    data = load_list(list_dir)
    for item in data.get("items", []):
        if item.get("id") == item_id:
            item["status"] = STATUS_RESEARCHING
            item.setdefault("research", {})
            item["research"]["started"] = now_iso()
            save_list(list_dir, data)
            return
    raise ReadingListError(f"item not found: {item_id}")


def mark_wiki_complete(
    list_dir: Path,
    item_id: str,
    wiki_path: str,
    passes: int,
    self_eval: float,
    sources_extracted: int,
    sources_crossrefed: int,
    facts_confirmed: int,
    title: str | None = None,
) -> None:
    data = load_list(list_dir)
    for item in data.get("items", []):
        if item.get("id") == item_id:
            item["status"] = STATUS_WIKI
            item["wiki"] = wiki_path
            if title:
                item["title"] = title
            r = item.setdefault("research", {})
            r["finished"] = now_iso()
            r["passes_completed"] = passes
            r["self_eval_score"] = self_eval
            r["sources_extracted"] = sources_extracted
            r["sources_crossrefed"] = sources_crossrefed
            r["facts_confirmed"] = facts_confirmed
            save_list(list_dir, data)
            return
    raise ReadingListError(f"item not found: {item_id}")


def mark_podcast_complete(list_dir: Path, item_id: str, podcast_path: str) -> None:
    data = load_list(list_dir)
    for item in data.get("items", []):
        if item.get("id") == item_id:
            item["status"] = STATUS_PODCAST
            item["podcast"] = podcast_path
            data_local = item.setdefault("review", {})
            data_local.setdefault("podcast_at", now_iso())
            save_list(list_dir, data)
            return
    raise ReadingListError(f"item not found: {item_id}")


def list_items_with_status(list_dir: Path) -> list[dict[str, Any]]:
    """Return all non-removed items with display-friendly fields."""
    data = load_list(list_dir)
    out = []
    for item in data.get("items", []):
        if item.get("status") == STATUS_REMOVED:
            continue
        out.append({
            "id": item.get("id"),
            "title": item.get("title") or item.get("source"),
            "source": item.get("source"),
            "type": item.get("type"),
            "status": item.get("status"),
            "depth": item.get("depth"),
            "added": item.get("added"),
            "wiki": item.get("wiki"),
            "podcast": item.get("podcast"),
            "research": item.get("research", {}),
        })
    return out


def cancel_research(list_dir: Path, target: str) -> bool:
    """Mark the item matching `target` as removed. Returns True if found."""
    data = load_list(list_dir)
    target_norm = target.strip().rstrip("/")
    for item in data.get("items", []):
        src = (item.get("source") or "").strip().rstrip("/")
        if src == target_norm:
            item["status"] = STATUS_REMOVED
            item["removed_at"] = now_iso()
            save_list(list_dir, data)
            # Also drop any in-flight research state for this item.
            state = load_research_state(list_dir)
            in_flight = state.get("in_flight", {})
            in_flight.pop(item["id"], None)
            state["in_flight"] = in_flight
            save_research_state(list_dir, state)
            return True
    return False


def build_global_wiki(list_dir: Path, list_name: str) -> str:
    """Assemble the global wiki from all wiki-complete items.

    The global wiki has:
    - Header (list name, generated date, item count)
    - Per-item index (with links to per-item wiki files)
    - Cross-references between items (related reading)
    """
    data = load_list(list_dir)
    items = [
        i for i in data.get("items", [])
        if i.get("status") in (STATUS_WIKI, STATUS_PODCAST)
    ]
    if not items:
        return (
            f"# {list_name} — Reading List Wiki\n\n"
            f"_No wiki-complete items yet. Use `/reading-list add <url> --depth high` to start._\n"
        )

    lines: list[str] = []
    lines.append(f"# {list_name} — Reading List Wiki")
    lines.append("")
    lines.append(f"_Generated {now_iso()} • {len(items)} item(s) • schema v{SCHEMA_VERSION}_")
    lines.append("")
    lines.append("## Index")
    lines.append("")
    for item in items:
        title = item.get("title") or item.get("source")
        wiki_rel = item.get("wiki") or ""
        status_icon = "🎙️" if item.get("status") == STATUS_PODCAST else "📄"
        lines.append(f"- {status_icon} **{title}** — `{item.get('source')}` → [wiki]({wiki_rel})")
    lines.append("")

    # Cross-references section: related reading
    lines.append("## Related Reading")
    lines.append("")
    for item in items:
        title = item.get("title") or item.get("source")
        # If the item's wiki file exists, try to find a "## Related" or "## See also" section.
        wiki_path = list_dir / item.get("wiki", "")
        related: list[str] = []
        if wiki_path.is_file():
            content = wiki_path.read_text(errors="replace")
            in_section = False
            for ln in content.splitlines():
                stripped = ln.strip()
                if stripped.lower().startswith(("## related", "## see also", "## references")):
                    in_section = True
                    continue
                if in_section:
                    if stripped.startswith("## "):
                        in_section = False
                        continue
                    if stripped.startswith(("- ", "* ")):
                        related.append(stripped[2:].strip())
        if related:
            lines.append(f"### {title}")
            for r in related:
                lines.append(f"- {r}")
            lines.append("")

    # Per-item summaries (first 2 paragraphs of each wiki)
    lines.append("---")
    lines.append("")
    lines.append("## Summaries")
    lines.append("")
    for item in items:
        title = item.get("title") or item.get("source")
        wiki_path = list_dir / item.get("wiki", "")
        if not wiki_path.is_file():
            continue
        content = wiki_path.read_text(errors="replace")
        # Strip front-matter, take the first ~3 paragraphs.
        body = re.sub(r"^---.*?---\s*", "", content, count=1, flags=re.DOTALL)
        paras = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        lines.append(f"### {title}")
        lines.append("")
        for p in paras[:3]:
            lines.append(p)
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
