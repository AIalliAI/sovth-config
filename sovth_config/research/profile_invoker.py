"""Profile invoker (Phase 3) — the ^<profile> background agent mechanism.

Two modes:
- `background`: long-running subprocess that writes to the profile's
  sessions/ and MEMORY.md. Implemented by spawning a `hermes -p <name>
  background "<prompt>"` subprocess. Memory continuity preserved because
  the subprocess uses HERMES_HOME=~/.hermes/profiles/<name>.
- `ephemeral`: fast delegate_task with the profile's SOUL injected as
  system context. Lives only for the duration of the call.
- `auto`: heuristic — long/complex prompts get background, short get
  ephemeral.

Returns a structured spec the calling LLM agent executes. The agent does
the actual spawning; this module is the spec-builder + memory-continuity
warranty.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ReadingListError


PROFILES_ROOT = Path(os.path.expanduser("~/.hermes/profiles"))


@dataclass
class InvocationSpec:
    name: str
    mode: str
    prompt: str
    herm_cmd: list[str]
    workdir: Path
    env: dict[str, str]
    deliver: str = "origin"
    session_label: str | None = None
    soul_injection: str = ""  # for ephemeral mode

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mode": self.mode,
            "prompt": self.prompt,
            "herm_cmd": self.herm_cmd,
            "workdir": str(self.workdir),
            "env": self.env,
            "deliver": self.deliver,
            "session_label": self.session_label,
            "soul_injection_chars": len(self.soul_injection),
        }


# ---------------------------------------------------------------------------
# Profile discovery + validation
# ---------------------------------------------------------------------------

def _validate_profile(name: str) -> Path:
    profile_dir = PROFILES_ROOT / name
    if not profile_dir.is_dir():
        raise ReadingListError(
            f"profile not found: {profile_dir}\n"
            f"Available profiles: {', '.join(p.name for p in PROFILES_ROOT.iterdir() if p.is_dir())}"
        )
    if not (profile_dir / "SOUL.md").is_file():
        raise ReadingListError(
            f"profile {name!r} has no SOUL.md at {profile_dir}/SOUL.md"
        )
    return profile_dir


def _load_soul(profile_dir: Path) -> str:
    soul = profile_dir / "SOUL.md"
    return soul.read_text(errors="replace")[:8000]  # cap injection


# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------

def _pick_mode(prompt: str, requested: str) -> str:
    if requested in ("background", "ephemeral"):
        return requested
    # auto: heuristic
    word_count = len(prompt.split())
    has_keywords = bool(re.search(
        r"\b(monitor|watch|loop|continuous|daily|hourly|schedule|recurring|background|while I'm|overnight|forever)\b",
        prompt, re.IGNORECASE,
    ))
    if has_keywords or word_count > 80:
        return "background"
    return "ephemeral"


# ---------------------------------------------------------------------------
# Command builders
# ---------------------------------------------------------------------------

def _herm_bin() -> str | None:
    return shutil.which("hermes") or shutil.which("hermes-agent")


def _build_background_cmd(name: str, prompt: str, deliver: str, session_label: str | None) -> list[str]:
    """Build the hermes CLI command for a background invocation."""
    herm = _herm_bin()
    if not herm:
        # No hermes on PATH; the agent will need to run it via its own tools.
        return ["hermes", "-p", name, "background", prompt]
    cmd = [herm, "-p", name, "background"]
    if session_label:
        cmd.extend(["--session-label", session_label])
    if deliver and deliver != "origin":
        cmd.extend(["--deliver", deliver])
    cmd.append(prompt)
    return cmd


def _build_ephemeral_spec(name: str, prompt: str, soul: str, deliver: str, session_label: str | None) -> InvocationSpec:
    """Build a spec for an ephemeral invocation (no hermes subprocess;
    the calling agent does the work via delegate_task with soul injection)."""
    return InvocationSpec(
        name=name,
        mode="ephemeral",
        prompt=prompt,
        herm_cmd=[],  # empty — ephemeral doesn't spawn a subprocess
        workdir=PROFILES_ROOT / name,
        env={"HERMES_HOME": str(PROFILES_ROOT / name)},
        deliver=deliver,
        session_label=session_label,
        soul_injection=soul,
    )


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def invoke_profile(
    profile_name: str,
    prompt: str,
    mode: str = "auto",
    deliver: str = "origin",
    session_label: str | None = None,
) -> dict[str, Any]:
    """Build the invocation spec. The caller (LLM agent) executes it.

    For `background` mode: spawn `herm_cmd` as a subprocess. The subprocess
    uses HERMES_HOME=~/.hermes/profiles/<name>, so its session DB and
    MEMORY.md updates land in the named profile's storage. **Memory
    continuity is preserved per-profile by construction.**

    For `ephemeral` mode: use the calling agent's delegate_task tool with
    `soul_injection` as the system context. The result is returned
    in-context; nothing is written to the profile's session DB.
    """
    profile_dir = _validate_profile(profile_name)
    chosen_mode = _pick_mode(prompt, mode)
    soul = _load_soul(profile_dir)

    if chosen_mode == "background":
        cmd = _build_background_cmd(profile_name, prompt, deliver, session_label)
        spec = InvocationSpec(
            name=profile_name,
            mode="background",
            prompt=prompt,
            herm_cmd=cmd,
            workdir=profile_dir,
            env={"HERMES_HOME": str(profile_dir)},
            deliver=deliver,
            session_label=session_label,
        )
    else:
        spec = _build_ephemeral_spec(profile_name, prompt, soul, deliver, session_label)

    return {
        "spec": spec.to_dict(),
        "instructions": _build_instructions(spec),
        "next_step": _next_step_text(spec),
    }


def _build_instructions(spec: InvocationSpec) -> str:
    """Human-readable instructions for the calling agent."""
    if spec.mode == "background":
        return (
            f"Spawn a background subprocess for profile `{spec.name}`:\n\n"
            f"```\n"
            f"{' '.join(spec.herm_cmd)}\n"
            f"```\n\n"
            f"Workdir: {spec.workdir}\n"
            f"Hermes home: {spec.env.get('HERMES_HOME')}\n"
            f"Session label: {spec.session_label or '(none)'}\n"
        )
    return (
        f"Invoke profile `{spec.name}` ephemerally via delegate_task. "
        f"Use the following as the system context:\n\n"
        f"---\n{spec.soul_injection}\n---\n\n"
        f"User prompt: {spec.prompt}\n"
    )


def _next_step_text(spec: InvocationSpec) -> str:
    if spec.mode == "background":
        return (
            f"Run this hermes command in the background. The subprocess's "
            f"HERMES_HOME is {spec.env['HERMES_HOME']}, so session updates "
            f"and MEMORY.md writes will land in the `{spec.name}` profile."
        )
    return (
        f"Spawn a delegate_task with the soul injection as system context. "
        f"The ephemeral subagent will not write to the profile's storage."
    )
