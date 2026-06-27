# 🎴 sovth-config

> **An opinionated configuration for [Hermes Agent](https://github.com/NousResearch/hermes-agent).**
> Distributable profiles, skills, and tools — curated, battle-tested, and kept updated with everything useful we make.

**TOWARDS SELF-IMPROVEMENT**

---

## What is this?

`sovth-config` is an opinionated configuration layer for [Hermes Agent](https://github.com/NousResearch/hermes-agent) — the self-improving AI agent built by [Nous Research](https://nousresearch.com). It provides a curated collection of agent profiles, skills, and plugin tools that extend Hermes with deep-research, profile management, and multi-agent orchestration capabilities.

This repo is kept updated with new profiles and skills as we build them. Anything useful enough to share lands here. If it's not useful, it doesn't make the cut.

### What's inside

| Layer | What it does |
|-------|-------------|
| **Profiles** | Character cards + profile configs for a multi-agent fleet — editors, researchers, triage orchestrators, builders, and more. Each card is a game-style README with stats, lore, and import instructions. |
| **Skills** | Shareable Hermes Agent skills. First up: **turbofit** — an opinionated unified LLM backend that picks the best main + aux model for your hardware, launches them, and wires Hermes config automatically. |
| **Plugin Tools** | Three (soon four) Hermes Agent plugin tools: `/reading-list` (deep-research wiki generator), `/character_card` (profile card generator), `^<profile>` (background profile invocation), and the upcoming `skill_market` (self-improving suggestion engine). |

---

## Install

### Quick install (one command)

```bash
git clone https://github.com/SouthpawIN/sovth-config.git
ln -s $(pwd)/sovth-config/sovth_config ~/.hermes/plugins/sovth-config
```

The plugin will be picked up automatically by Hermes on next launch. Verify with:

```bash
hermes plugins
# should list: sovth-config
```

### Import profiles

```bash
# Import the whole roster (or just the ones you want)
for d in sovth-config/profiles/*/; do
    name=$(basename "$d")
    [ "$name" = "README.md" ] && continue
    ln -s "$(pwd)/$d" ~/.hermes/profiles/"$name"
done

# Or pick a few:
ln -s $(pwd)/sovth-config/profiles/klerik ~/.hermes/profiles/klerik
ln -s $(pwd)/sovth-config/profiles/nous-girl ~/.hermes/profiles/nous-girl

# Launch one
hermes -p klerik
```

### Install the turbofit skill

```bash
# If turbofit is bundled as a skill directory:
ln -s $(pwd)/sovth-config/skills/turbofit ~/.hermes/skills/turbofit

# Source the serve shim (one-time, already in ~/.bashrc after install)
source ~/.hermes/skills/turbofit/scripts/turbofit.sharco

# One-shot: pick best main model for your box, launch, wire Hermes
serve auto main
```

---

## The Profile Fleet

Character cards for a multi-agent ecosystem. Each is a game-style README — Name, Class, Stats, Skills, Lore, and a one-page import tutorial.

| Profile | Class | Role |
|---------|-------|------|
| **`klerik`** | Profile Editor | Meta-agent that reviews and surgically corrects other Hermes agent profiles. Uses DSPy + GEPA for prompt optimization. |
| **`anser`** | Tech Support + Planner | Discord tech support. Also plans projects — analyzes Hermes ecosystem to structure ideas into executable plans. |
| **`nous-girl`** | Curious Muse | Warm, intellectual, idea-driven. The creative brainstormer in the agent chain. |
| **`senter`** | Triage Orchestrator | Receives ideas, decides scope, routes to specialists. Manages the Kanban board. |
| **`chizul`** | Builder | The worker profile. Executes Kanban tasks — code, config, file operations. |
| **`kashik`** | Akashic Librarian | Silent historian — watches all agent activity, maintains per-agent wikis, preserves institutional memory across the entire Hermes lifespan. |
| **`crow`** | Deep Researcher | Deep web research agent. Uses /learn and llm-wiki to create structured "lore" that Kashik turns into guides. |
| **`frieza`** | Galactic Steward | Infrastructure automation — deploys containers, provisions VMs, manages GitOps workflows. |
| **`jestur`** | Creative Companion | Art, music, creative work. |
| **`dev-coder`** | Codewright | Engineering, code generation. |
| **`dev-orch`** | Orchestrator | Development orchestration. |
| **`dev-review`** | Reviewer | Code review and quality gates. |
| **`test-bot`** | Test Agent | Testing and experimentation. |

See [`profiles/README.md`](profiles/README.md) for the full roster with character cards.

---

## Tutorials

Deep-dive guides on using the full fleet together. Each tutorial has dark editorial imagery and walks through real workflows.

| # | Tutorial | What you'll learn |
|---|----------|-------------------|
| 1 | [Getting Started](tutorials/01-getting-started.md) | Install the fleet, understand the flow, run your first orchestration |
| 2 | [Project Planning](tutorials/02-project-planning.md) | Plan projects with Anser, read plan documents, hand off to Senter |
| 3 | [Agent Orchestration](tutorials/03-agent-orchestration.md) | Multi-agent patterns — Research→Document→Review, Build→Review→Deploy, fan-out, cron automation |
| 4 | [Fleet in Action](tutorials/04-fleet-in-action.md) | Real-world scenarios — CI monitoring bot, weekly AI research pipeline, profile creation chain, infrastructure migration |

Each tutorial stands alone but builds on the previous ones. Start with Getting Started, or jump to the scenario that matches what you're building.

---

## Skills

### turbofit

**Opinionated unified LLM backend (v5.1).** Picks the best main + aux model for your hardware — local or API — launches them detached, wires Hermes-Agent config, and adapts to live VRAM pressure via a scaling ladder.

- Three hardware tiers: Beefy (local+local), Modest (API+local), Thin (API+API)
- `serve auto main` auto-detects GPU and suggests the right setup
- API fallback always available (free: DeepSeek V4 Pro + Kimi K2.6)
- 18 named flag presets, per-model binary pinning, tier ladder
- 64K Hermes context floor enforced everywhere
- Replaces llama-launch, omni-va, and ad-hoc llama-server scripts

```bash
serve auto main          # pick best main, launch, wire Hermes — done
serve auto main --vision  # require vision
serve auto main --api     # force API mode
serve downscale           # adapt to VRAM pressure
```

See [`skills/turbofit/SKILL.md`](skills/turbofit/SKILL.md) for full documentation.

---

## Plugin Tools

### `/reading-list` — Deep-Research Wiki Generator

Add links or files; each item auto-triggers a research hook that produces a per-item wiki with cross-referenced sources. Three depth levels: `low`, `high`, `max` (with manim podcast + Klerik review).

```text
/reading-list add https://arxiv.org/abs/1706.03762 --depth high
/reading-list wiki
```

### `/character_card` — Profile Card Generator

Generate a video-game-style character card (README + pixel-art portrait) for any Hermes profile. Walks SOUL.md, AGENTS.md, config.yaml, skills/.

```text
/character_card generate klerik
/character_card generate_all
```

### `^<profile>` — Background Profile Invocation

Spawn any profile as a background agent or ephemerally in-context. Memory continuity is preserved per-profile.

```text
^klerik review this README and flag any issues
^nous-girl draft a 200-word thread about Darwin merge
^senter triage this stack trace
```

### `skill_market` *(coming soon)*

Self-improving suggestion engine. Anser checks sovth-config for matching profiles/skills when answering questions. If a gap is found, triggers a creation chain: `^nous-girl` brainstorms → `^klerik` reviews → result written to repo. Similar questions refine the same artifacts over time.

---

## Repo Structure

```
sovth-config/
├── sovth_config/              # Python plugin package
│   ├── __init__.py             # register(ctx) — Hermes Agent entry point
│   ├── plugin.yaml             # plugin manifest
│   ├── schemas.py              # tool schemas
│   ├── tools.py                # tool handlers
│   └── research/               # deep-research + utilities
│       ├── hook.py             # reading-list state machine
│       ├── runner.py           # multi-pass research orchestrator
│       ├── extract.py          # URL/file → text
│       ├── crossref.py         # source cross-referencing
│       ├── self_eval.py        # quality scoring
│       ├── klerik_review.py    # Klerik content review
│       ├── podcast.py          # manim NotebookLM-style podcast
│       ├── wiki_writer.py      # structured markdown generation
│       ├── character_card.py   # profile card generator
│       ├── profile_invoker.py  # ^<profile> invocation
│       ├── storage.py          # YAML read/write + slugify
│       └── errors.py
├── profiles/                   # Character cards (the fleet)
│   ├── README.md               # roster
│   ├── klerik/
│   ├── anser/
│   ├── nous-girl/
│   ├── crow/                   # *(new — deep researcher)*
│   ├── kashik/                 # *(updated — universal guide writer)*
│   └── ...
├── skills/                     # Shareable skills
│   └── turbofit/               # opinionated unified LLM backend
│       ├── SKILL.md
│       ├── distribution.yaml
│       ├── scripts/
│       └── references/
├── tests/
│   └── test_smoke.py
├── examples/
├── plugin.yaml                 # mirrored for discoverability
└── README.md                   # this file
```

---

## Brand & Aesthetic

- **Pixel-art portraits**: default `arcade` preset, monochrome-leaning, retro-futurist
- **Typography**: Courier Pro (monospace) for labels, Helvetica for headers, Mondwest for accents
- **Tagline**: "TOWARDS SELF-IMPROVEMENT" — footer on every character card
- **Color**: strictly monochrome by default (Nous brand rule)

---

## Development

```bash
# Run smoke tests
cd sovth-config
python3 tests/test_smoke.py

# Regenerate all character cards
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '.')
from sovth_config.research.character_card import generate_all_character_cards
generate_all_character_cards(preset='arcade', out_dir=Path('profiles'))
"
```

---

## Relationship to Hermes Agent

This is **not** Hermes Agent itself — it's an opinionated configuration layer on top of it. Hermes Agent is the self-improving AI agent built by [Nous Research](https://github.com/NousResearch), available at [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent). Go there for the core agent, CLI, documentation, and releases.

What we add:
- **Curated profiles** with tested SOUL.md, AGENTS.md, and configs
- **Skills** like turbofit that solve real infrastructure problems
- **Plugin tools** that extend Hermes with new capabilities
- **Character cards** that make profiles easy to browse and share

We keep this updated with useful stuff we make. If it's not useful, it doesn't ship.

---

## License

MIT — share, fork, remix. See [LICENSE](LICENSE).

## Credits

Built by [SouthpawIN](https://github.com/SouthpawIN) for the Hermes Agent community.
Inspired by the Nous Research brand book and the Hermes Agent project.
