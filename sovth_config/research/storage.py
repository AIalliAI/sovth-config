"""Storage conventions for the reading-list plugin.

All data lives under ``~/.hermes/reading-list/<list_name>/``:

    <list_name>/
    ├── list.yaml         # active items, research state
    ├── wiki/
    │   ├── _index.md     # global wiki (per-list)
    │   └── <slug>.md     # per-item wiki pages
    └── .research-state.json  # in-flight research state (transient)
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .errors import ReadingListError


SCHEMA_VERSION = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str, max_len: int = 64) -> str:
    text = text.lower().strip()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if not text:
        text = f"item-{int(time.time())}"
    return text[:max_len].rstrip("-")


def list_file(list_dir: Path) -> Path:
    return list_dir / "list.yaml"


def wiki_dir(list_dir: Path) -> Path:
    return list_dir / "wiki"


def research_state_file(list_dir: Path) -> Path:
    return list_dir / ".research-state.json"


def load_list(list_dir: Path) -> dict[str, Any]:
    """Read list.yaml, returning a fresh structure if missing."""
    f = list_file(list_dir)
    if not f.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "list_name": list_dir.name,
            "created": now_iso(),
            "updated": now_iso(),
            "items": [],
        }
    try:
        with f.open() as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as e:
        raise ReadingListError(f"list.yaml is not valid YAML: {e}")
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("list_name", list_dir.name)
    data.setdefault("items", [])
    return data


def save_list(list_dir: Path, data: dict[str, Any]) -> None:
    data["updated"] = now_iso()
    f = list_file(list_dir)
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("w") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)


def load_research_state(list_dir: Path) -> dict[str, Any]:
    f = research_state_file(list_dir)
    if not f.exists():
        return {"in_flight": {}}
    try:
        with f.open() as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {"in_flight": {}}


def save_research_state(list_dir: Path, state: dict[str, Any]) -> None:
    f = research_state_file(list_dir)
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
