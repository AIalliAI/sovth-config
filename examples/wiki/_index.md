# Example Global Wiki

This is what the global wiki looks like after running `/reading-list wiki`
on a populated list. The wiki is auto-generated from all `wiki-complete`
items and includes:

- Header with list name, generated date, item count
- Per-item index with status icons
- Cross-references (Related / See Also)
- Per-item summaries

```markdown
# examples — Reading List Wiki

_Generated 2026-06-10T12:30:00Z • 2 item(s) • schema v1_

## Index

- 📄 **Attention Is All You Need** — `https://arxiv.org/abs/1706.03762` → [wiki](2026-06-10-attention-is-all-you-need.md)
- 🎙️ **Darwin Family: Training-Free Weight-Space Recombination** — `https://arxiv.org/abs/2605.14386` → [wiki](2026-06-09-darwin-merge-paper.md)

## Related Reading

### Attention Is All You Need
- The Illustrated Transformer (Jay Alammar, 2018)
- Self-Attention GAN (Zhang et al., 2018)
- T5: Text-to-Text Transfer Transformer (Raffel et al., 2019)

### Darwin Family: Training-Free Weight-Space Recombination
- Model Soups (Wortsman et al., 2022)
- SLERP: Spherical Linear Interpolation (Shoemake, 1985)
- TIES: Trimming, Electing, Signs (Yadav et al., 2023)

---

## Summaries

### Attention Is All You Need
…

### Darwin Family: Training-Free Weight-Space Recombination
…
```

## Per-Item Wiki Pages

Each item has a separate file at `wiki/<item-id>.md` with:

- YAML front-matter (id, source, status, dates, sources)
- Summary (200 words max)
- Key Concepts
- Deep Dive (with inline citations)
- Related / See Also
- Sources

The wiki files are the authoritative knowledge artifact — the global wiki
is just an index plus summaries.

## Klerik Review (max depth only)

For `max` depth items, the wiki file gets a `## Klerik Review` footer
appended after the Klerik subagent's pass. The footer records:

- Score (0-10)
- Verdict (ship | polish | rewrite)
- Strengths
- Issues (numbered, specific, actionable)

This is permanent provenance for the review — you can see exactly what
Klerik thought and what was changed in the final pass.
