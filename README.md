# 🎴 sovth-config

> **Southpaw's hermes-agent toolkit** — distributable, universal, shareable.
> Provides `/reading-list` deep-research, profile character cards, and `^<profile>` background invocation.

**TOWARDS SELF-IMPROVEMENT**

---

## What is this?

`sovth-config` is a collection of three hermes-agent plugins plus a curated library of profile character cards. It's designed to be cloned, installed, and shared — anyone with [Hermes Agent](https://github.com/hermes-agent) can drop it in and immediately get the new tools.

### The three tools

| Tool | What it does |
|---|---|
| **`reading_list`** | Deep-research wiki generator. Add links or files; each item auto-triggers a research hook that produces a per-item wiki with cross-referenced sources. Three depth levels: `low` (single pass), `high` (1-5 self-evaluated passes), `max` (high + manim podcast + Klerik content review). |
| **`character_card`** | Generate a video-game-style character card (README + pixel-art portrait) for any Hermes profile in `~/.hermes/profiles/`. Walks SOUL.md, AGENTS.md, config.yaml, skills/. Outputs a standardized card with import tutorial. |
| **`invoke_profile`** | The mechanism behind the `^<profile>` quick command. Spawn a named profile as a background agent (cron-style, persists across sessions) or ephemerally (in-context, fast). **Memory continuity is preserved per-profile** by construction. |

### The profile character cards

This repo ships with **12 character cards** for the profiles in `~/.hermes/profiles/` — see [`profiles/README.md`](profiles/README.md) for the full roster. Each card has a Name, Class, Stats, Skills, Lore, and a one-page import tutorial. Standardized, game-card aesthetic, inspired by the Nous Research brand.

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
# should list: sovth-config 0.1.0  📚 🎴 ⚡
```

### Manual install (copy instead of symlink)

```bash
git clone https://github.com/SouthpawIN/sovth-config.git
cp -r sovth-config/sovth_config ~/.hermes/plugins/
```

### Use the character cards

```bash
# Import the whole roster to your profiles dir (or just the ones you want)
for d in sovth-config/profiles/*/; do
    name=$(basename "$d")
    [ "$name" = "default" ] && continue
    ln -s "$(pwd)/$d" ~/.hermes/profiles/"$name"
done

# Or pick a few:
ln -s $(pwd)/sovth-config/profiles/klerik ~/.hermes/profiles/klerik
ln -s $(pwd)/sovth-config/profiles/nous-girl ~/.hermes/profiles/nous-girl

# Launch one
hermes -p klerik
```

---

## Quick start: `/reading-list`

Once installed, the `reading_list` tool is available. In a Hermes session:

```text
/reading-list add https://arxiv.org/abs/1706.03762 --depth high
/reading-list add ~/papers/attention-is-all-you-need.pdf --depth max
/reading-list show
/reading-list wiki
/reading-list remove https://arxiv.org/abs/1706.03762
```

Storage: `~/.hermes/reading-list/<list-name>/`
- `list.yaml` — items + research state
- `wiki/<slug>.md` — per-item wiki pages
- `wiki/_index.md` — global wiki (assembled by the `wiki` action)

### Depth levels

| Level | Passes | Self-eval | Multimedia | Reviewer |
|---|---|---|---|---|
| `low` | 1 | no | wiki only | none |
| `high` | 1-5 (cap configurable) | yes — stops when min criterion ≥ 8/10 | wiki only | none |
| `max` | 1-5 | yes | wiki + manim podcast (NotebookLM-style) | Klerik (content-review mode) |

The `high` and `max` loops do NOT use a hardcoded number of passes — they keep going until the self-eval rates every criterion (accuracy, completeness, sourcing, clarity) at 8/10 or above, capped at `max_passes` (default 5).

### Klerik as reviewer

`max` mode spawns a delegate_task subagent with the Klerik persona loaded (see [`profiles/klerik/`](profiles/klerik/)). The reviewer reads the draft wiki, gives a score, and lists specific surgical issues. A final pass applies the feedback.

---

## Quick start: `/character_card`

In a Hermes session:

```text
/character_card generate klerik
/character_card generate_all
/character_card show nous-girl
/character_card tutorial klerik
```

The generated card lives at `~/.hermes/sovth-config/profiles/<name>/` (or wherever you set `--out-dir`). It includes:
- `README.md` — the character card (game-card aesthetic)
- `profile.json` — raw extracted metadata
- `portrait.png` — pixel-art portrait (placeholder until FAL is wired in)

### Customizing the pixel-art preset

Default preset is **`arcade`** (bold chunky 80s cabinet feel — most game-card energy). Available presets:

```
arcade, nes, snes, gameboy, pico8, c64, apple2,
mono_green, mono_amber, neon, pastel
```

Per-card override: `/character_card generate klerik --preset gameboy`

---

## Quick start: `^<profile>`

Once the plugin is installed, you can invoke any profile as a background agent from any other profile session:

```text
^klerik review this README and flag any issues
^nous-girl draft a 200-word Twitter thread about Darwin merge
^senter triage this stack trace
```

Behind the scenes, this calls `invoke_profile` with `mode=auto`:
- **Long/complex prompts** → background (hermes subprocess with `HERMES_HOME=~/.hermes/profiles/<name>`)
- **Short prompts** → ephemeral (delegate_task with Klerik's SOUL injected as system context)

Memory continuity is preserved **per-profile by construction**: the subprocess's `HERMES_HOME` overrides point at the target profile's storage, so its session DB and `MEMORY.md` updates land in the named profile, not the caller's.

---

## Repo structure

```
sovth-config/
├── sovth_config/                  # Python package (the plugin)
│   ├── __init__.py                # register(ctx) — hermes-agent entry point
│   ├── plugin.yaml                # manifest
│   ├── schemas.py                 # tool schemas (reading_list, character_card, invoke_profile)
│   ├── tools.py                   # tool handlers
│   └── research/                  # deep-research subsystem
│       ├── hook.py                # state machine: add/remove/list items
│       ├── runner.py              # multi-pass research orchestrator
│       ├── extract.py             # URL/file → text
│       ├── crossref.py            # 3-5 source cross-referencing
│       ├── self_eval.py           # quality scoring
│       ├── klerik_review.py       # Klerik content review
│       ├── podcast.py             # manim NotebookLM-style podcast
│       ├── wiki_writer.py         # structured markdown generation
│       ├── character_card.py      # profile character-card generator
│       ├── profile_invoker.py     # ^<profile> background invocation
│       ├── storage.py             # YAML read/write + slugify
│       └── errors.py
├── profiles/                      # 12 character cards (Phase 2)
│   ├── README.md                  # the roster
│   ├── klerik/                    # one card per profile
│   ├── nous-girl/
│   └── ...
├── tests/
│   └── test_smoke.py              # 13 smoke tests
├── examples/
│   ├── example-list.yaml          # sample reading list
│   └── wiki/
│       └── _index.md              # sample global wiki
├── plugin.yaml                    # (mirrored at repo root for discoverability)
└── README.md                      # this file
```

---

## Brand & aesthetic

- **Pixel-art portraits**: default `arcade` preset, monochrome-leaning, retro-futurist. See [`nous-brand-guide`](https://nousresearch.com) for the full brand book.
- **Typography**: Courier Pro (monospace) for labels and metadata, Helvetica for display headers, Mondwest for accents.
- **Tagline**: "TOWARDS SELF-IMPROVEMENT" — appears as a footer on every character card.
- **Color**: strictly monochrome by default (Nous brand rule). Use `mono_green` or `gameboy` preset for the most brand-aligned look; `arcade`/`pico8` for the most game-card energy.

---

## Development

```bash
# Run smoke tests
cd sovth-config
python3 tests/test_smoke.py

# 13/13 should pass.

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

## License

MIT — share, fork, remix. See [LICENSE](LICENSE).

## Credits

Built by [SouthpawIN](https://github.com/SouthpawIN) for the Hermes Agent community.
Inspired by the Nous Research brand book (Feb 2024, 1st ed.) and the
[evolutionary-model-merging](https://github.com/SouthpawIN/evolutionary-model-merging)
project.
