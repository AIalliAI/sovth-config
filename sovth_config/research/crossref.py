"""Cross-referencing: confirm key claims by finding 3-5 corroborating sources.

For each non-trivial factual claim in the draft wiki, search the web for
the claim (or a paraphrase) and note the source. The output is a list of
{citation, claim, source_url} dicts that the wiki_writer weaves inline.

In a real LLM-driven pass, the LLM does the search and the parsing. This
module provides the structure and helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CrossrefResult:
    claim: str
    source_url: str
    source_title: str
    excerpt: str
    confidence: float  # 0.0 - 1.0


CROSSREF_PROMPT = """\
You are a research cross-referencer. For each non-trivial factual claim
in the draft wiki below, search the web for one corroborating source.
Aim for 3-5 cross-references total. Prefer reputable sources (peer-reviewed
papers, official documentation, established news outlets, well-known blogs
in the field). Skip claims that are obvious or already cited.

For each cross-reference, output:
- claim: the original claim (paraphrase OK)
- source_url: URL of the corroborating source
- source_title: title of the source page
- excerpt: a 1-2 sentence quote or paraphrase from the source
- confidence: 0.0-1.0 (how strongly the source supports the claim)

Output as JSON list:
[{"claim": "...", "source_url": "...", "source_title": "...", "excerpt": "...", "confidence": 0.0}]
"""


def parse_crossrefs(llm_output: str) -> list[CrossrefResult]:
    """Parse the LLM's JSON crossref output into CrossrefResult objects."""
    import json
    import re

    match = re.search(r"\[.*\]", llm_output, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for item in data:
        try:
            out.append(CrossrefResult(
                claim=str(item.get("claim", "")).strip(),
                source_url=str(item.get("source_url", "")).strip(),
                source_title=str(item.get("source_title", "")).strip(),
                excerpt=str(item.get("excerpt", "")).strip(),
                confidence=float(item.get("confidence", 0.0)),
            ))
        except (TypeError, ValueError):
            continue
    return out
