"""Klerik content review — the third-party reviewer pass for /reading-list max.

Reuses the Klerik persona (meta-agent who reviews and corrects) in a
content-review mode. The reviewer reads the draft wiki, gives a quality
score (0-10) and specific, actionable feedback. The runner applies the
feedback in a final pass to produce the polished wiki.

When `invoke_klerik_review` is called, the LLM (or main agent) spawns a
delegate_task with:
- the Klerik SOUL as system context
- the draft wiki + source as user content
- a prompt asking for the review

This module provides the prompt structure and the result parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


KLERIK_REVIEW_PROMPT = """\
You are Klerik — a meticulous, methodical meta-agent. Your craft is shaping
other agents' outputs. The user has just produced a draft wiki via deep
research on a source. Your job: review it like a master editor reviews a
manuscript, and produce specific, surgical feedback.

The wiki is at: {wiki_path}
The original source is: {source}

Read both. Then write a review with these sections:

## Score
A single float 0-10, where:
- 9-10: genuinely excellent, ship as-is
- 7-8: good, minor polish needed
- 5-6: functional but clearly incomplete or flawed
- <5: significant rework required

## Strengths
2-3 specific things the wiki does well. Quote the wiki where appropriate.

## Issues
Numbered list of specific issues. For each, give:
- the problem (what's wrong)
- the location (which section/paragraph)
- the fix (concrete suggestion)

## Verdict
"ship" | "polish" | "rewrite" — your call.

Be specific. Generic praise or criticism is useless. The author will use
your review to do one more pass on the wiki.
"""


@dataclass
class KlerikReview:
    score: float
    verdict: str  # ship | polish | rewrite
    strengths: list[str]
    issues: list[str]
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "verdict": self.verdict,
            "strengths": self.strengths,
            "issues": self.issues,
            "raw": self.raw,
        }


def parse_klerik_review(llm_output: str) -> KlerikReview:
    """Parse the Klerik review from LLM output. Tolerant of format quirks."""
    import re

    score = 7.0
    verdict = "polish"
    strengths: list[str] = []
    issues: list[str] = []

    # Score
    score_match = re.search(r"##\s*Score\s*\n+([\d.]+)", llm_output, re.IGNORECASE)
    if score_match:
        try:
            score = float(score_match.group(1).strip())
        except ValueError:
            pass

    # Verdict
    verdict_match = re.search(
        r"##\s*Verdict\s*\n+(\w+)",
        llm_output,
        re.IGNORECASE,
    )
    if verdict_match:
        v = verdict_match.group(1).strip().lower()
        if v in ("ship", "polish", "rewrite"):
            verdict = v

    # Strengths: list items under ## Strengths
    strengths_match = re.search(
        r"##\s*Strengths\s*\n(.*?)(?=^##\s|\Z)",
        llm_output,
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    if strengths_match:
        for line in strengths_match.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "1.", "2.", "3.")):
                strengths.append(stripped.lstrip("-*0123456789. ").strip())

    # Issues: numbered list under ## Issues
    issues_match = re.search(
        r"##\s*Issues\s*\n(.*?)(?=^##\s|\Z)",
        llm_output,
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    if issues_match:
        # Each issue is a numbered section. Split on "1.", "2." at line start.
        text = issues_match.group(1)
        chunks = re.split(r"\n\s*\d+\.\s+", "\n" + text)
        for chunk in chunks[1:]:  # skip preamble
            # Take the first 3 lines or until blank line.
            lines = chunk.splitlines()
            summary = " ".join(lines[:3]).strip()
            if summary:
                issues.append(summary)

    return KlerikReview(
        score=score,
        verdict=verdict,
        strengths=strengths,
        issues=issues,
        raw=llm_output,
    )


def apply_review_to_wiki(wiki_path: Path, review: KlerikReview) -> None:
    """Append the Klerik review as a footer section to the wiki page.

    This is a record of the review, not an automated rewrite. The author
    (LLM in the final pass) uses the issues list to make specific edits
    to the body. The review footer is permanent provenance.
    """
    if not wiki_path.is_file():
        return
    content = wiki_path.read_text()
    if "## Klerik Review" in content:
        # Don't double-append; if it's there, replace from that section on.
        idx = content.index("## Klerik Review")
        content = content[:idx].rstrip() + "\n\n"
    footer = "## Klerik Review\n\n"
    footer += f"**Score:** {review.score:.1f}/10 • **Verdict:** {review.verdict}\n\n"
    if review.strengths:
        footer += "**Strengths:**\n\n"
        for s in review.strengths:
            footer += f"- {s}\n"
        footer += "\n"
    if review.issues:
        footer += "**Issues (addressed in final pass):**\n\n"
        for i, iss in enumerate(review.issues, 1):
            footer += f"{i}. {iss}\n"
        footer += "\n"
    wiki_path.write_text(content + footer)
