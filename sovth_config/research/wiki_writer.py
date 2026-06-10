"""Structured wiki-page generation.

The LLM is responsible for actually writing the prose; this module provides
the schema, the front-matter, and the structural skeleton that the writer
must fill in. The output is a markdown file with:
- YAML front-matter (id, source, status, dates, sources)
- # Title
- ## Summary (200 words max)
- ## Key Concepts (bulleted)
- ## Deep Dive (sections, with citations inline)
- ## Related / See Also
- ## Sources
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .storage import now_iso


FRONTMATTER_TEMPLATE = """---
id: {item_id}
title: {title}
source: {source}
type: {source_type}
depth: {depth}
status: wiki-complete
generated: {generated}
passes_completed: {passes}
self_eval_score: {self_eval}
sources_extracted: {sources_extracted}
sources_crossrefed: {sources_crossrefed}
facts_confirmed: {facts_confirmed}
---
"""

WIKI_SKELETON = """# {title}

## Summary

{summary}

## Key Concepts

{key_concepts}

## Deep Dive

{deep_dive}

## Related / See Also

{related}

## Sources

{sources}
"""


def build_frontmatter(item: dict[str, Any], research: dict[str, Any]) -> str:
    return FRONTMATTER_TEMPLATE.format(
        item_id=item.get("id", ""),
        title=item.get("title") or item.get("source", ""),
        source=item.get("source", ""),
        source_type=item.get("type", "url"),
        depth=item.get("depth", "low"),
        generated=now_iso(),
        passes=research.get("passes_completed", 0),
        self_eval=research.get("self_eval_score", 0.0),
        sources_extracted=research.get("sources_extracted", 0),
        sources_crossrefed=research.get("sources_crossrefed", 0),
        facts_confirmed=research.get("facts_confirmed", 0),
    )


def build_skeleton(
    title: str,
    summary: str = "",
    key_concepts: str = "",
    deep_dive: str = "",
    related: str = "",
    sources: str = "",
) -> str:
    return WIKI_SKELETON.format(
        title=title,
        summary=summary or "_(summary to be filled by research runner)_",
        key_concepts=key_concepts or "_(key concepts to be filled)_",
        deep_dive=deep_dive or "_(deep dive sections to be filled)_",
        related=related or "_(related reading to be filled)_",
        sources=sources or "_(sources to be filled)_",
    )


def assemble_wiki(
    item: dict[str, Any],
    title: str,
    summary: str,
    key_concepts: list[str],
    deep_dive: str,
    related: list[str],
    sources: list[str],
) -> str:
    """Assemble a complete wiki page from structured fields."""
    research = item.get("research", {})
    fm = build_frontmatter(item, research)
    body = WIKI_SKELETON.format(
        title=title,
        summary=summary.strip(),
        key_concepts="\n".join(f"- {c}" for c in key_concepts),
        deep_dive=deep_dive.strip(),
        related="\n".join(f"- {r}" for r in related),
        sources="\n".join(f"- {s}" for s in sources),
    )
    return fm + "\n" + body


def write_wiki(list_dir: Path, item_id: str, content: str) -> Path:
    """Write a per-item wiki file. Returns the path written."""
    out = list_dir / "wiki" / f"{item_id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content)
    return out
