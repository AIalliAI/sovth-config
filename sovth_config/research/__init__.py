"""research package — the deep-research hook and its sub-modules.

Public surface:
- trigger_research_hook(list_dir, target, depth, max_passes) -> item dict
- build_global_wiki(list_dir, list_name) -> markdown str
- list_items_with_status(list_dir) -> list of dicts
- cancel_research(list_dir, target) -> bool
- ReadingListError

Sub-modules:
- extract: URL/file -> text
- crossref: confirm-key-claims search
- wiki_writer: structured markdown generation
- klerik_review: third-party review pass (max depth)
- podcast: manim NotebookLM-style podcast (max depth)
- self_eval: quality scoring for the high/max loop
- runner: multi-pass research orchestrator (low/high/max)
- character_card: profile character-card generator (Phase 2)
- profile_invoker: ^<profile> background agent (Phase 3)
- storage: filesystem conventions + YAML read/write
"""

from __future__ import annotations

from .hook import (
    trigger_research_hook,
    build_global_wiki,
    list_items_with_status,
    cancel_research,
)
from .errors import ReadingListError

__all__ = [
    "trigger_research_hook",
    "build_global_wiki",
    "list_items_with_status",
    "cancel_research",
    "ReadingListError",
]
