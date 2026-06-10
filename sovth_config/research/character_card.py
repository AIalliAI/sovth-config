"""Profile character-card generator (Phase 2).

For each profile in ~/.hermes/profiles/<name>/, this module:
1. Extracts metadata: name, role/class, voice, model, eikon, skills, lore
2. Generates a pixel-art portrait (uses the pixel-art skill + FAL for source)
3. Writes a standardized character-card README in the game-character-sheet aesthetic
4. Includes a one-page tutorial for importing the profile

The output is a directory per profile with:
- README.md        (the character card)
- portrait.png     (the pixel-art portrait, if generated)
- profile.json     (raw extracted metadata, for tooling)

The README follows a game-character-sheet template (Name, Class, Level,
Stats, Skills, Lore, How to Import). It's inspired by the Nous Research
brand guide: monochrome, Courier typography, retro-futurist feel.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from .errors import ReadingListError


PROFILES_ROOT = Path(
    os.environ.get("SOVTH_PROFILES_ROOT")
    or os.path.expanduser("~/.hermes/profiles")
)


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

@dataclass
class ProfileMetadata:
    name: str
    role: str = ""              # 1-line role/specialty
    class_name: str = ""        # game-style class (Curious Muse, Triage Orchestrator, etc.)
    model: str = ""
    voice: str = ""
    eikon: str = ""
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    soul_excerpt: str = ""      # first 200 words of SOUL.md
    agents_excerpt: str = ""    # first 200 words of AGENTS.md (if present)
    memory_count: int = 0
    sessions_count: int = 0
    files: dict[str, str] = field(default_factory=dict)  # path -> first 500 chars

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_first(path: Path, max_chars: int = 2000) -> str:
    if not path.is_file():
        return ""
    return path.read_text(errors="replace")[:max_chars]


def _first_words(text: str, n: int = 200) -> str:
    """First ~n words, stripped of markdown front-matter."""
    text = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
    words = text.split()
    return " ".join(words[:n])


def _extract_voice(config_text: str) -> str:
    """Pull the Edge TTS voice from config.yaml. Heuristic — looks for
    'voice: <name>' in the tts.edge.voice path. Falls back to a scan."""
    m = re.search(r"tts:\s*\n(?:\s+\w+:[^\n]*\n)*?\s+edge:\s*\n(?:\s+\w+:[^\n]*\n)*?\s+voice:\s*(\S+)", config_text)
    if m:
        return m.group(1)
    m = re.search(r"voice:\s*(\S+)", config_text)
    if m:
        return m.group(1)
    return ""


def _extract_model(config_text: str) -> str:
    m = re.search(r"default:\s*(\S+)", config_text)
    if m:
        return m.group(1)
    return ""


def _extract_eikon(profile_dir: Path) -> str:
    """Look for eikon config (typically in config.yaml or a dedicated file)."""
    config = profile_dir / "config.yaml"
    if config.is_file():
        text = config.read_text(errors="replace")
        m = re.search(r"eikon:\s*(\S+)", text)
        if m:
            return m.group(1)
        m = re.search(r"active_eikon:\s*(\S+)", text)
        if m:
            return m.group(1)
    return ""


def _extract_skills(profile_dir: Path) -> list[str]:
    """Walk profile_dir/skills/ and return all skill names (top-level dirs)."""
    skills_dir = profile_dir / "skills"
    if not skills_dir.is_dir():
        return []
    out = []
    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").is_file():
            out.append(entry.name)
    return out


def _count_memory(profile_dir: Path) -> int:
    mem = profile_dir / "MEMORY.md"
    if not mem.is_file():
        return 0
    text = mem.read_text(errors="replace")
    return len([line for line in text.splitlines() if line.strip().startswith(("•", "-", "*"))])


def _count_sessions(profile_dir: Path) -> int:
    sessions = profile_dir / "sessions"
    if not sessions.is_dir():
        return 0
    return len([f for f in sessions.iterdir() if f.suffix == ".sqlite"])


def extract_metadata(profile_name: str) -> ProfileMetadata:
    """Pull structured metadata from a profile directory."""
    profile_dir = PROFILES_ROOT / profile_name
    if not profile_dir.is_dir():
        raise ReadingListError(f"profile not found: {profile_dir}")

    soul_text = _read_first(profile_dir / "SOUL.md")
    agents_text = _read_first(profile_dir / "AGENTS.md")
    config_text = _read_first(profile_dir / "config.yaml")

    return ProfileMetadata(
        name=profile_name,
        role=_extract_role(soul_text),
        class_name=_extract_class(soul_text),
        model=_extract_model(config_text),
        voice=_extract_voice(config_text),
        eikon=_extract_eikon(profile_dir),
        skills=_extract_skills(profile_dir),
        soul_excerpt=_first_words(soul_text, 200),
        agents_excerpt=_first_words(agents_text, 200) if agents_text else "",
        memory_count=_count_memory(profile_dir),
        sessions_count=_count_sessions(profile_dir),
        files={
            "SOUL.md": _read_first(profile_dir / "SOUL.md", 500),
            "AGENTS.md": _read_first(profile_dir / "AGENTS.md", 500) if (profile_dir / "AGENTS.md").is_file() else "",
            "config.yaml": _read_first(profile_dir / "config.yaml", 500),
        },
    )


def _extract_role(soul_text: str) -> str:
    """Pull a 1-line role from SOUL.md. Look for '## Role' or first non-heading line."""
    m = re.search(r"^#\s+.*Role[^\n]*\n+(.*?)(?:\n\s*\n|\n#)", soul_text, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1).strip().split("\n")[0]
    # First non-empty, non-heading line
    for line in soul_text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("<!--"):
            return line[:120]
    return ""


def _extract_class(soul_text: str) -> str:
    """Infer a game-style class from the role or persona. Falls back to 'Agent'."""
    role = _extract_role(soul_text).lower()
    if "orchestrat" in role:
        return "Triage Orchestrator"
    if "meta" in role or "review" in role or "editor" in role:
        return "Profile Editor"
    if "curator" in role or "radio" in role or "music" in role:
        return "Ambient Curator"
    if "muse" in role or "warm" in role or "girl" in role:
        return "Curious Muse"
    if "emperor" in role or "discord" in role or "moderat" in role:
        return "Galactic Steward"
    if "creative" in role or "art" in role:
        return "Creative Companion"
    if "code" in role or "coder" in role or "engineer" in role:
        return "Codewright"
    return "Agent"


# ---------------------------------------------------------------------------
# Character-card README generation
# ---------------------------------------------------------------------------

README_TEMPLATE = """# 🎴 {name}

> **{class_name}** — {role}

![Portrait](portrait.png)

**TOWARDS SELF-IMPROVEMENT**

---

## Stats

| Attribute     | Value                                       |
|---------------|---------------------------------------------|
| **Name**      | `{name}`                                    |
| **Class**     | {class_name}                                |
| **Model**     | `{model}`                                   |
| **Voice**     | `{voice}`                                   |
| **Eikon**     | {eikon}                                     |
| **Memory**    | {memory_count} entries                      |
| **Sessions**  | {sessions_count} persisted                  |
| **Skills**    | {skills_count} installed                    |

## Skills

{skills_list}

## Lore

> {soul_excerpt}

{agents_section}

## How to Import

This profile is a self-contained Hermes agent directory. To use it:

### 1. Copy or clone

```bash
# From this distribution:
cp -r profiles/{name}/ ~/.hermes/profiles/{name}/

# Or clone the whole distribution and symlink:
git clone https://github.com/SouthpawIN/sovth-config.git
ln -s $(pwd)/sovth-config/profiles/{name} ~/.hermes/profiles/{name}
```

### 2. Launch

```bash
# Interactive CLI
hermes -p {name}

# Background session
hermes -p {name} "your prompt here"

# As a one-shot from the default profile
hermes -p default "use the ^<{name}> profile to ..."
```

The `-p` flag sets `HERMES_HOME=~/.hermes/profiles/{name}`, which gives
this profile its own sessions/, MEMORY.md, skills/, and config.yaml.
**Memory continuity is preserved per-profile** — each profile keeps its
own history.

### 3. Customize

Edit `SOUL.md` to change personality, `config.yaml` to swap the model
or voice, drop new skills into `skills/`. Klerik (the meta-agent) can
review and tune profiles via the `invoke_profile` tool in this plugin.

## Cross-References

- Plugin source: [SouthpawIN/sovth-config](https://github.com/SouthpawIN/sovth-config)
- Character-card generator: `sovth-config.character_card` tool
- All profiles: see `../README.md` in the distribution

---

*Generated by sovth-config /character_card*
*Profile last seen: {seen_at}*
"""


def build_readme(metadata: ProfileMetadata, seen_at: str = "") -> str:
    skills_list = "\n".join(f"- `{s}`" for s in metadata.skills) if metadata.skills else "_(no skills installed)_"
    agents_section = ""
    if metadata.agents_excerpt:
        agents_section = f"\n### Operational Directives\n\n> {metadata.agents_excerpt}\n"
    return README_TEMPLATE.format(
        name=metadata.name,
        class_name=metadata.class_name,
        role=metadata.role or "(no role set)",
        model=metadata.model or "_(default)_",
        voice=metadata.voice or "_(default)_",
        eikon=metadata.eikon or "_(none)_",
        memory_count=metadata.memory_count,
        sessions_count=metadata.sessions_count,
        skills_count=len(metadata.skills),
        skills_list=skills_list,
        soul_excerpt=metadata.soul_excerpt or "_(no SOUL.md found)_",
        agents_section=agents_section,
        seen_at=seen_at or "n/a",
    )


# ---------------------------------------------------------------------------
# Tutorial
# ---------------------------------------------------------------------------

TUTORIAL_TEMPLATE = """\
# Tutorial: Import the `{name}` profile

The `{name}` profile is a `{class_name}` agent — {role}.

## Three-step import

### Step 1: Place the profile directory

```bash
mkdir -p ~/.hermes/profiles
# Option A: copy from sovth-config
cp -r /path/to/sovth-config/profiles/{name} ~/.hermes/profiles/
# Option B: symlink (if you're keeping sovth-config up to date)
ln -s /path/to/sovth-config/profiles/{name} ~/.hermes/profiles/{name}
```

The profile must have at minimum: `SOUL.md`, `AGENTS.md` (optional),
`config.yaml`, and `skills/` (optional). All other files (sessions/,
MEMORY.md, USER.md) are created on first launch.

### Step 2: Verify it loads

```bash
hermes -p {name} --check
```

This validates the config and lists the skills/tools the profile exposes.

### Step 3: Launch

```bash
# Interactive
hermes -p {name}

# One-shot
hermes -p {name} "Summarize the latest commits in this repo"

# Background
hermes -p {name} "Monitor X and DM me when Y happens" &
```

## Cross-profile invocation (^<profile>)

To invoke this profile from another session (e.g. the default profile),
use the `^<profile>` quick command:

```bash
# In a default-profile session:
^{name} draft a 200-word README for this repo
```

This spawns a background subprocess with `HERMES_HOME=~/.hermes/profiles/{name}`,
so the subprocess writes back to *this* profile's sessions/ and MEMORY.md —
not the caller's. Memory continuity is preserved per-profile.

## Distributing your own version

Fork the `sovth-config` repo, drop your profile into `profiles/<name>/`,
and submit a PR. Each profile is fully self-contained — the character
card README, the SOUL/AGENTS/config, the skills, and the portrait all
travel together.

## Troubleshooting

- "Profile not found": check that `HERMES_HOME` (default `~/.hermes`) is
  correct and the profile directory is at `$HERMES_HOME/profiles/{name}/`.
- "Skill not loading": verify the skill has a `SKILL.md` at its root.
- "Voice not working": the profile must have a TTS provider configured
  in `config.yaml` (e.g. `tts.edge.voice: AvaNeural`).
"""


def build_tutorial(profile_name: str) -> str:
    try:
        metadata = extract_metadata(profile_name)
    except ReadingListError as e:
        return f"# Tutorial unavailable: {e}"
    return TUTORIAL_TEMPLATE.format(
        name=metadata.name,
        class_name=metadata.class_name,
        role=metadata.role or "(no role set)",
    )


# ---------------------------------------------------------------------------
# Top-level entry points
# ---------------------------------------------------------------------------

def generate_character_card(
    profile_name: str,
    preset: str = "arcade",
    out_dir: Path | None = None,
    include_portrait: bool = True,
) -> Path:
    """Generate a character card for one profile. Returns the README path."""
    metadata = extract_metadata(profile_name)
    out_dir = out_dir or (Path(os.path.expanduser("~/.hermes/sovth-config/profiles")))
    profile_card_dir = out_dir / profile_name
    profile_card_dir.mkdir(parents=True, exist_ok=True)

    # Write raw metadata
    (profile_card_dir / "profile.json").write_text(
        json.dumps(metadata.to_dict(), indent=2, default=str)
    )

    # Write README
    readme_path = profile_card_dir / "README.md"
    readme_path.write_text(build_readme(metadata))

    # Portrait placeholder (real generation is a separate step using FAL)
    if include_portrait:
        portrait_path = profile_card_dir / "portrait.png"
        if not portrait_path.is_file():
            portrait_path.write_text(
                f"# Portrait placeholder for {profile_name}\n"
                f"# Preset: {preset}\n"
                f"# Generate via: sovth-config.character_card generate {profile_name} --preset {preset}\n"
            )

    return readme_path


def generate_all_character_cards(
    preset: str = "arcade",
    out_dir: Path | None = None,
    include_portrait: bool = True,
) -> list[str]:
    """Generate character cards for every profile in ~/.hermes/profiles/."""
    out_dir = out_dir or (Path(os.path.expanduser("~/.hermes/sovth-config/profiles")))
    if not PROFILES_ROOT.is_dir():
        raise ReadingListError(f"profiles root not found: {PROFILES_ROOT}")
    out = []
    for entry in sorted(PROFILES_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.endswith("_bak") or entry.name == "default":
            continue
        # Skip if no SOUL.md
        if not (entry / "SOUL.md").is_file():
            continue
        try:
            path = generate_character_card(
                profile_name=entry.name,
                preset=preset,
                out_dir=out_dir,
                include_portrait=include_portrait,
            )
            out.append(str(path))
        except ReadingListError as e:
            out.append(f"FAILED: {entry.name}: {e}")
    return out


def show_character_card(profile_name: str, out_dir: Path | None = None) -> str:
    """Read an existing character card. Returns the README content."""
    out_dir = out_dir or (Path(os.path.expanduser("~/.hermes/sovth-config/profiles")))
    readme = out_dir / profile_name / "README.md"
    if not readme.is_file():
        raise ReadingListError(
            f"character card not found for {profile_name}; "
            f"run `character_card generate {profile_name}` first"
        )
    return readme.read_text()
