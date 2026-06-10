"""Research runner — the multi-pass deep-research orchestrator.

The actual LLM work happens at the agent level (main agent or subagent).
This module is the framework: it provides the prompts, the state machine,
and the helper functions the agent uses to drive the loop.

Flow for `high` or `max`:
    pass 1: extract -> draft wiki -> self-eval
    if self_eval.min < 8: pass 2: refine wiki (using gaps) -> self-eval
    ...continue up to max_passes
    (max only): Klerik review -> apply feedback -> final wiki
    (max only): manim podcast visual

The LLM agent runs each step's prompt, gets a result, and calls the
helpers in this module to advance state and persist output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ReadingListError
from .hook import (
    mark_research_started,
    mark_wiki_complete,
    mark_podcast_complete,
    update_item,
    STATUS_RESEARCHING,
    STATUS_WIKI,
    STATUS_PODCAST,
)
from .self_eval import parse_self_eval, should_continue, QualityScore
from .klerik_review import parse_klerik_review, apply_review_to_wiki, KlerikReview
from .wiki_writer import assemble_wiki, write_wiki
from .podcast import build_podcast_script
from .storage import now_iso, wiki_dir


# ---------------------------------------------------------------------------
# Prompts the LLM agent runs
# ---------------------------------------------------------------------------

DRAFT_WIKI_PROMPT = """\
You are writing a wiki page from a deep-research extraction. Produce a
high-quality, well-sourced wiki page with these sections:

# {{title}}

## Summary
(200 words max, capture the essence)

## Key Concepts
(Bulleted list of 5-8 key concepts, each a 1-2 sentence explanation)

## Deep Dive
(Multiple subsections with inline citations. Use [1], [2], [3] markers
that map to the Sources section at the end. Be specific. Avoid filler.)

## Related / See Also
(Bulleted list of 3-5 related topics, papers, or articles)

## Sources
(Numbered list of all sources cited, with URLs. Include the original
source and any cross-references you consulted.)

Use a tone that's informative but not stuffy. The reader is curious,
not a beginner.
"""

REFINE_WIKI_PROMPT = """\
You are refining a wiki page based on quality self-evaluation feedback.
The current draft has these gaps: {gaps}

Address each gap specifically:
- accuracy: verify claims against sources, fix any errors
- completeness: add the missing facets
- sourcing: add missing citations, prefer reputable sources
- clarity: tighten prose, improve organization

Return the FULLY REVISED wiki page (not a diff). Preserve what's working.
"""

KLERIK_FINAL_PASS_PROMPT = """\
You are doing the final pass on a wiki page. Klerik (the meta-agent
reviewer) has just given this feedback:

{feedback}

Apply Klerik's specific, surgical feedback to produce the polished
final version. Address every numbered issue. Keep what's working.
Return the full revised wiki page.
"""


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

@dataclass
class ResearchSession:
    list_dir: Path
    item: dict[str, Any]
    depth: str
    max_passes: int = 5
    current_pass: int = 0
    current_score: QualityScore | None = None
    last_wiki_content: str = ""
    last_self_eval: str = ""
    klerik_review: KlerikReview | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    @property
    def item_id(self) -> str:
        return self.item["id"]

    @property
    def is_done(self) -> bool:
        if self.depth == "low":
            return self.current_pass >= 1 and self.last_wiki_content
        if self.depth == "high":
            return (self.current_pass >= 1 and self.last_wiki_content and
                    (not should_continue(self.current_score) or
                     self.current_pass >= self.max_passes))
        if self.depth == "max":
            return (self.klerik_review is not None and
                    self.current_pass >= self.max_passes and
                    self.last_wiki_content)
        return False

    def next_step(self) -> dict[str, Any]:
        """Return the next step the LLM agent should perform."""
        if self.current_pass == 0:
            # First pass: draft
            if self.current_score is None:
                mark_research_started(self.list_dir, self.item_id)
                return {
                    "step": "draft_wiki",
                    "prompt": DRAFT_WIKI_PROMPT,
                    "pass": 1,
                }
        # Subsequent passes: refine based on self-eval gaps
        if self.current_score is not None and should_continue(self.current_score):
            if self.current_pass >= self.max_passes:
                return {"step": "stop", "reason": "max_passes reached"}
            gaps = self.current_score.gaps()
            return {
                "step": "refine_wiki",
                "prompt": REFINE_WIKI_PROMPT.format(gaps=", ".join(gaps)),
                "pass": self.current_pass + 1,
                "gaps": gaps,
            }
        # Self-eval passed or we're done; for max, do Klerik review
        if self.depth == "max" and self.klerik_review is None:
            return {
                "step": "klerik_review",
                "prompt": _klerik_prompt_for(self.list_dir, self.item),
            }
        if self.depth == "max" and self.klerik_review is not None and self.klerik_review.verdict != "ship":
            # Apply Klerik feedback in a final pass
            if self.current_pass < self.max_passes:
                return {
                    "step": "klerik_final_pass",
                    "prompt": KLERIK_FINAL_PASS_PROMPT.format(
                        feedback=self._format_klerik_feedback()
                    ),
                    "pass": self.current_pass + 1,
                }
        return {"step": "stop", "reason": "all criteria met"}

    def record_draft(self, content: str, self_eval_text: str) -> None:
        """Record the result of a draft or refine step + its self-eval."""
        self.current_pass += 1
        self.last_wiki_content = content
        self.last_self_eval = self_eval_text
        self.current_score = parse_self_eval(self_eval_text)
        self.history.append({
            "pass": self.current_pass,
            "kind": "draft_or_refine",
            "self_eval": self.current_score.to_dict() if self.current_score else None,
        })

    def record_klerik_review(self, review_text: str) -> KlerikReview:
        self.klerik_review = parse_klerik_review(review_text)
        # Persist the review as a footer on the wiki
        wiki_path = self.list_dir / "wiki" / f"{self.item_id}.md"
        apply_review_to_wiki(wiki_path, self.klerik_review)
        self.history.append({
            "kind": "klerik_review",
            "score": self.klerik_review.score,
            "verdict": self.klerik_review.verdict,
            "issues_count": len(self.klerik_review.issues),
        })
        return self.klerik_review

    def finalize(
        self,
        title: str,
        summary: str,
        key_concepts: list[str],
        deep_dive: str,
        related: list[str],
        sources: list[str],
    ) -> Path:
        """Assemble the final wiki, write it, and mark the item complete."""
        wiki_text = assemble_wiki(
            item=self.item,
            title=title,
            summary=summary,
            key_concepts=key_concepts,
            deep_dive=deep_dive,
            related=related,
            sources=sources,
        )
        # If Klerik already wrote a footer, append below it.
        existing_path = self.list_dir / "wiki" / f"{self.item_id}.md"
        if existing_path.is_file() and "## Klerik Review" in existing_path.read_text():
            existing = existing_path.read_text()
            # Strip everything from "## Klerik Review" onward, keep the body.
            body = existing.split("## Klerik Review")[0].rstrip()
            # Reassemble with the new body, then re-apply the Klerik footer.
            from .klerik_review import apply_review_to_wiki
            wiki_path = self.list_dir / "wiki" / f"{self.item_id}.md"
            wiki_path.write_text(body + "\n\n" + wiki_text.split("---\n", 2)[-1].lstrip() if "---\n" in wiki_text else body + "\n\n" + wiki_text)
            if self.klerik_review:
                apply_review_to_wiki(wiki_path, self.klerik_review)
        else:
            wiki_path = write_wiki(self.list_dir, self.item_id, wiki_text)
        mark_wiki_complete(
            list_dir=self.list_dir,
            item_id=self.item_id,
            wiki_path=str(wiki_path.relative_to(self.list_dir)),
            passes=self.current_pass,
            self_eval=self.current_score.overall if self.current_score else 0.0,
            sources_extracted=1,  # TODO: track from runner
            sources_crossrefed=len(sources) - 1 if sources else 0,
            facts_confirmed=0,    # TODO: track from runner
            title=title,
        )
        return wiki_path

    def generate_podcast_script(self, key_concepts: list[str], sources: list[str]) -> Path:
        """Build the manim podcast script for max depth."""
        wiki_path = self.list_dir / "wiki" / f"{self.item_id}.md"
        script = build_podcast_script(wiki_path, self.item, key_concepts, sources)
        out = self.list_dir / "wiki" / f"{self.item_id}_podcast.py"
        out.write_text(script)
        mark_podcast_complete(self.list_dir, self.item_id, str(out.relative_to(self.list_dir)))
        return out

    def _format_klerik_feedback(self) -> str:
        if not self.klerik_review:
            return ""
        r = self.klerik_review
        out = f"Score: {r.score}/10, Verdict: {r.verdict}\n\n"
        if r.issues:
            out += "Issues:\n" + "\n".join(f"- {i}" for i in r.issues)
        return out


def _klerik_prompt_for(list_dir: Path, item: dict[str, Any]) -> str:
    wiki_path = list_dir / "wiki" / f"{item['id']}.md"
    from .klerik_review import KLERIK_REVIEW_PROMPT
    return KLERIK_REVIEW_PROMPT.format(
        wiki_path=str(wiki_path),
        source=item.get("source", ""),
    )
