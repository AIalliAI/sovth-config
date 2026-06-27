# Animated Eikon Pipeline — Comprehensive Project Plan

**Author:** Senter (via subagent delegation)  
**Date:** 2026-06-26  
**Target:** High-quality animated Braille Unicode sprites for Herm TUI character Eikons  
**Status:** Planning Phase

---

## 1. Executive Summary

This document proposes a complete rebuild of the animated Eikon pipeline for Herm TUI character sprites. The current approach (brightness-flashing static Braille frames from a single source image via `eikon-builder.py`) produces poor animation quality — all 6 signal states (idle, listening, thinking, speaking, working, error) are derived from one image with per-dot brightness modulation, yielding animation that looks "flickery" rather than expressive.

**Goal:** Create distinct, hand-designed frames for each state animation using generative AI tools (ComfyUI, FAL), producing character art that shows real poses, expressions, and motion cues — not just brightness variation of a single frame.

**Target Format:** 48×24 Braille Unicode NDJSON, 6 animated clips (one per signal state), 8–16fps, 44–100+ total frames per Eikon.

---

## 2. Current State Analysis

### 2.1 What Exists Today

#### `eikon-builder.py` v2 (`/home/sovthpaw/sovth-config/scripts/eikon-builder.py`)

| Aspect | Status |
|--------|--------|
| Input | Single PNG image → chafa → Braille rows |
| Animation | Per-dot brightness modulation (±4%–±12%) |
| States | All 6 signals generated algorithmically |
| Frame count | 44 total (8 idle, 6 listening, 8 thinking, 8 speaking, 6 working, 8 error) |
| Quality | 111–164 unique Braille chars per Eikon (good character diversity) |
| Output format | NDJSON: `{type: "header"/"clip"/"frame", ...}` with 48×24 size |
| Preview | PNG rendering via Pillow (first idle frame at 384×384) |

**Key limitation:** All animation is brightness-derived. No pose changes. No expression changes. The character stays visually identical across all states — only its dot density shifts.

#### `make-eikon-videos.py` (`/home/sovthpaw/sovth-config/scripts/make-eikon-videos.py`)

- Renders all frames of an `.eikon` file to PNG via Pillow, stitches to MP4 with ffmpeg
- Useful for demos; not for generation

#### Reference Eikon: `ares.eikon` (65-frame idle, all 6 states, 16fps)

- Production-quality reference from the Herm TUI author (kaio)
- Shows what "real" animation looks like: 65 frames for idle alone with subtle but genuine motion
- Format: `{type: "header", "clip", "frame"}` — identical to what `eikon-builder.py` produces

### 2.2 Fleet Status

All 8 fleet agents have existing Eikons in two locations:
- `sovth-config/profiles/<agent>/<agent>.eikon` (distributed copies)
- `sovth-config/eikons/output/<agent>.eikon` (build output)

All were generated via the same brightness-modulation pipeline. They all have the same visual character — the animation is uniform across agents, differing only in source image content.

---

## 3. Available Tools & Skills Survey

### 3.1 Core Tools (Installed & Verified)

| Tool | Version | Purpose |
|------|---------|---------|
| **chafa** | 1.14.0 | Image → Braille Unicode art at `--size 48x24` |
| **ffmpeg** | 6.1.1 | Video encoding, frame extraction, MP4 assembly |
| **Python 3** | 3.11.13 | Pipeline scripting (Pillow, subprocess, json) |
| **Pillow** | (via venv) | Image manipulation, PNG rendering |

### 3.2 Image Generation Tools

| Tool | Type | Pros | Cons |
|------|------|------|------|
| **FAL** (`image_generate`) | Managed API (Nous subscription) | Zero setup, fast, produces high-quality editorial art | No animation/pose control API; single-image generation only |
| **ComfyUI** | Local/Cloud generative pipeline | Full control: workflows, ControlNet, img2img, AnimateDiff, video models (Wan, Hunyuan), batch processing, parameter sweeps | Setup required; needs GPU or Cloud subscription; workflow complexity |
| **Pixel Art skill** | Local Python scripts | NES/Game Boy/PICO-8 era palettes, Floyd-Steinberg dithering, particle animation overlays | No Braille output; no multi-frame character animation; transforms existing images, doesn't generate new ones |

### 3.3 Relevant Hermes Skills

| Skill | Relevance |
|-------|-----------|
| **eikon-pipeline** | Defines the current pipeline, Chafa quirks, NDJSON format spec, 6-signal-state contract |
| **comfyui** | Full ComfyUI workflow management: setup, model install, run_workflow.py with param injection, batch sweeps |
| **fleet-design** | Character design rules, color assignments, image style guide, profile structure conventions |
| **pixel-art** | Era-accurate pixel art conversion; useful for post-processing generated art to retro style |
| **ascii-video** | ASCII/character-grid video pipeline; tonemapping, shading, encoding — potentially useful for preview/demo generation |
| **ascii-art** | Local Braille/ASCII tools (ascii-image-converter, jp2a, chafa integration) |

### 3.4 ComfyUI-Specific Capabilities (from comfyui skill)

- **Image generation:** SD 1.5, SDXL, Flux Dev, SD3, etc.
- **Animation/Video:** AnimateDiff, Wan T2V, Hunyuan Video
- **Control:** ControlNet (pose, depth, canny, openpose), IP-Adapter (style transfer)
- **Inpainting/img2img:** Variation generation from base image
- **Batch processing:** `run_batch.py` with sweeps and parallel execution
- **Custom workflows:** Full node graph; anything ComfyUI supports

---

## 4. Proposed Architecture

### 4.1 High-Level Pipeline (Option A — Recommended: ComfyUI + chafa)

```
┌──────────────────────────────────────────────────────────────────┐
│                     PHASE 1: Art Generation                       │
│                                                                    │
│  ComfyUI Workflow (per agent, per state)                          │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Base character prompt + ControlNet pose skeleton        │    │
│  │  → SDXL/Flux txt2img with pose conditioning              │    │
│  │  → Generate 1 base frame per state (6 total)            │    │
│  │  → AnimateDiff for inter-frame interpolation             │    │
│  │  → or: Manual frame-by-frame img2img pose variants       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                          ↓                                        │
│  Output: 6 animation clips (~8-16 frames each, 48×24 or larger) │
│                          ↓                                        │
│                     PHASE 2: Braille Conversion                    │
│                                                                    │
│  chafa --size 48x24 --format symbols --symbols braille             │
│  → Convert each frame to 48×24 Braille Unicode art               │
│  → Verify: 100+ unique Braille chars per frame                    │
│                          ↓                                        │
│                     PHASE 3: NDJSON Assembly                       │
│                                                                    │
│  New eikon-builder.py v3                                          │
│  → Accept multi-image input (1 image per frame per state)        │
│  → Run chafa on each frame                                       │
│  → Assemble NDJSON: header → clip definitions → frame rows       │
│  → Validate against reference format (ares.eikon)                │
│                          ↓                                        │
│                     PHASE 4: Quality & Preview                     │
│                                                                    │
│  → Render PNG previews (384×384 per first idle frame)            │
│  → Render animated MP4 demos (all 6 states cycling)              │
│  → Quality metrics: unique Braille chars, silhouette integrity   │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Alternative: FAL + Pixel Art (Option B — Simpler, Less Expressive)

```
FAL image_generate → 6 state images (different prompts for poses)
       ↓
pixel-art skill → era-correct pixel art (optional stylization)
       ↓
chafa → Braille conversion
       ↓
eikon-builder.py v3 → NDJSON assembly
```

**Trade-off:** FAL can generate distinct poses via prompts but has no temporal coherence between frames of a clip. Each frame is independent. Good for static per-state images but weak for smooth animation.

### 4.3 Alternative: ComfyUI AnimateDiff (Option C — Video-First)

```
ComfyUI AnimateDiff → short video clips (1-2 sec each state)
       ↓
ffmpeg → extract frames @ 8fps
       ↓
chafa → convert each frame to Braille
       ↓
eikon-builder.py v3 → NDJSON assembly
```

**Best for:** Smooth, consistent animation with temporal coherence. AnimateDiff ensures frames transition naturally.

### 4.4 Recommendation: Hybrid (Option A + C)

1. **Use ComfyUI AnimateDiff** for smooth base animations (8-16 frames per state)
2. **Extract frames** via ffmpeg
3. **Optional:** Apply pixel-art stylization for retro aesthetic
4. **Convert to Braille** via chafa
5. **Assemble NDJSON** via enhanced eikon-builder.py

---

## 5. Detailed Design

### 5.1 State Animation Design (Per Signal)

Each of the 6 signal states needs distinct visual characterization. The existing brightness-only approach must be replaced with pose/expression-aware design:

| Signal | Clip | Frame Count | Visual Design Intent |
|--------|------|-------------|---------------------|
| `state.idle` | `idle` | 16–24 | Gentle breathing cycle, subtle body sway, eyes blinking slowly. Character at rest but alive. |
| `state.listening` | `listening` | 8–12 | Slight lean forward, head tilt, attentive posture. Enhanced brightness in eye/head area. |
| `state.thinking` | `thinking` | 12–16 | Processing animation: gears turning, runes glowing, eyes narrowed. Horizontal ripple + pose shift. |
| `state.speaking` | `speaking` | 12–16 | Mouth/mandible opening, gesturing appendages, energetic posture. Most active animation. |
| `state.working` | `working` | 8–12 | Busy tool-use animation: hands/appendages moving, tools appearing. Vertical rhythm. |
| `state.error` | `error` | 8–12 | Alert state: red-flag posture, defensive stance, warning glow. Bold flash pattern. |

### 5.2 Character Design Rules (from fleet-design)

- Each agent MUST have a unique esoteric/fantasy character (no overlap, no Nous Girl)
- Dark vintage editorial newsprint aesthetic: sepia tones, halftone texture, deep shadows
- Bold silhouettes read well at 48×24 resolution
- Source images should be square aspect ratio for best chafa results

### 5.3 NDJSON Format Contract (from eikon-pipeline + ares.eikon)

```json
{"type":"header","eikon":1,"id":"southpawin/senter","version":"1.0","title":"Senter","author":{"name":"sovthpaw"},"size":{"cols":48,"rows":24},"defaultSignal":"state.idle","signals":{"state.idle":{"clip":"idle"},"state.listening":{"clip":"listening","fallback":"state.idle"},...}}
{"type":"clip","name":"idle","fps":8,"frameCount":24,"loopFrom":0}
{"type":"frame","clip":"idle","index":0,"rows":["48-char Braille string",...24 rows total]}
...
```

**Critical requirements:**
- `ensure_ascii=False` in Python `json.dumps`
- Each frame: exactly 24 rows of exactly 48 Braille characters (U+2800–U+28FF)
- All 6 signal states MUST be defined with fallback to `state.idle`

### 5.4 Chafa Invocation (Critical)

```bash
chafa --size 48x24 --format symbols --symbols braille --colors none --fill solid <image.png>
```

**Both** `--format symbols` AND `--symbols braille` are REQUIRED. Omitting `--symbols braille` silently produces block art instead of Braille.

### 5.5 Frame Quality Targets

| Metric | Target |
|--------|--------|
| Unique Braille chars per frame | 100–170 |
| Silhouette recognition | Character must be identifiable at 48×24 |
| Animation smoothness | No jarring jumps between frames |
| State distinctiveness | Each state must be visually different from idle |
| File size | 40–150 frames, ~100KB–~400KB per .eikon |

---

## 6. Implementation Plan

### Phase 1: ComfyUI Workflow Design (Week 1)

**Goal:** Create reusable ComfyUI workflows that generate per-state animation frames.

**Tasks:**
1. **Pose/Expression Map** — Define visual direction for each state per agent (8 agents × 6 states = 48 pose descriptions)
2. **Base Workflow** — Build SDXL/Flux txt2img workflow with ControlNet (OpenPose or Canny) for pose conditioning
3. **AnimateDiff Workflow** — Build AnimateDiff workflow that takes a base image + motion parameters to generate 8-16 frame clips
4. **Style Consistency** — Ensure generated frames maintain the dark editorial vintage-newsprint aesthetic across all states
5. **Test Run** — Generate one agent's worth of frames (e.g., Senter: 6 states × 12 frames = 72 images)

**Scripts needed:**
- ComfyUI workflow JSON files (one for base generation, one for animation)
- `run_batch.py` invocations for per-agent per-state generation

**Dependencies:**
- ComfyUI installed (local or Cloud)
- Models: SDXL base or Flux Dev, ControlNet OpenPose/Canny, AnimateDiff motion module
- `comfy-cli` for lifecycle management

### Phase 2: Build eikon-builder.py v3 (Week 1-2)

**Goal:** Enhance `eikon-builder.py` to accept multi-frame input (one image per frame) instead of a single source image.

**Tasks:**
1. **Multi-image input mode** — `build --frames-dir` flag accepting a directory of frame images
2. **Per-frame chafa conversion** — Convert each frame PNG to Braille rows
3. **Clip assembly** — Accept mapping of clip names to frame directories
4. **NDJSON assembly** — Generate header → clip → frame records
5. **Validation** — Verify Braille character range, row counts, unique char diversity
6. **Backward compatibility** — Keep existing `--image` single-source mode

**New CLI:**
```bash
python3 scripts/eikon-builder.py build-v3 \
  --name senter \
  --id southpawin/senter \
  --frames-dir eikons/frames/senter \
  --states '{"idle": [0,24], "listening": [24,36], ...}'
  --output profiles/senter/senter.eikon
```

### Phase 3: Braille Conversion & Validation (Week 2)

**Goal:** Ensure high-quality Braille output from generated frames.

**Tasks:**
1. **Batch conversion script** — Convert all frames via chafa with correct flags
2. **Quality checker script** — Count unique Braille chars per frame, flag if < 80
3. **Silhouette checker** — Optional: overlay comparison to detect quality degradation
4. **Frame consistency check** — Ensure all frames in a clip have the same row/col counts

### Phase 4: Animation Rendering & Preview (Week 2-3)

**Goal:** Generate previews and demo videos for all Eikons.

**Tasks:**
1. **Update `make-eikon-videos.py`** — Handle longer frame counts, improved label rendering
2. **Batch render all 8 agents** — Generate MP4 and PNG previews
3. **Quality review** — Visual inspection of animations, state distinctiveness check
4. **Comparison tool** — Side-by-side old vs new animation for each agent

### Phase 5: Fleet Integration & Testing (Week 3)

**Goal:** Deploy new Eikons to all 8 fleet agents.

**Tasks:**
1. **Generate all 8 agents** — Run pipeline for Senter, Chizul, Klerik, Anser, Kashik, Crow, Frieza, LLMC
2. **Profile installation** — Copy `.eikon` files to `sovth-config/profiles/<agent>/` and `sovth-config/eikons/output/`
3. **TUI testing** — Verify Eikon loading and animation in Herm TUI
4. **Documentation** — Update fleet-design skill, eikon-pipeline skill, and this plan document

### Phase 6: Automation & CI (Week 3-4)

**Goal:** Make the pipeline repeatable and automated.

**Tasks:**
1. **Master build script** — `scripts/build-all-eikons.sh` that orchestrates the full pipeline
2. **Config file** — `eikons/eikon-config.yaml` mapping agents to their character descriptions, colors, and frame parameters
3. **Regression test** — Verify rebuilt Eikons pass format validation and quality checks
4. **Skill update** — Update `eikon-pipeline` skill to document the new v3 pipeline

---

## 7. Key Decisions & Trade-Offs

| Decision | Recommended | Alternative | Rationale |
|----------|-------------|-------------|-----------|
| Generation tool | **ComfyUI** (AnimateDiff) | FAL + per-state prompts | AnimateDiff gives temporal coherence between frames; FAL produces independent images with no motion continuity |
| Frame source | **Larger images (512×512)** → chafa downscale | Native 48×24 generation | chafa's dithering produces better Braille character diversity at 48×24 than generating at native resolution |
| Frame count per state | **8–24 frames** at 8fps | 65 frames at 16fps (like ares) | 65-frame idle is production quality but heavy. Start with 8-24 for practical generation; increase later |
| Art style | **Dark editorial vintage-newsprint** (existing convention) | Pixel-art retro | Consistency with existing fleet design and profile images |
| chafa vs custom converter | **chafa** (existing, proven) | Custom Python Braille conversion | chafa handles dithering, edge detection, and Braille symbol selection far better than any hand-written threshold-based converter |

---

## 8. Risk Analysis & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| ComfyUI unavailable (no GPU) | High | Use Comfy Cloud or fall back to FAL with static per-state prompts |
| AnimateDiff flicker between frames | Medium | Increase frame count, reduce motion strength, add frame interpolation |
| Poor Braille readability of generated frames | Medium | Test source image resolution/size; 512×512 source with chafa dithering is proven |
| Style inconsistency between generations | Medium | Use IP-Adapter or consistent seed range; same prompt template across all agents |
| Time to generate all 8 agents | Medium | Batch process; parallel generation per agent using ComfyUI queue |
| Character art not reading at 48×24 | High | Test renders early; adjust art direction (bolder silhouettes, less detail) before full generation |

---

## 9. Success Metrics

- [ ] All 8 fleet agents have regenerated Eikons with distinct state animations
- [ ] Each Eikon has 6 states with 8+ frames each (48+ total frames per agent)
- [ ] Animation is perceptibly different from brightness-only approach
- [ ] Each state animation conveys the intended agent activity (idle, listening, thinking, speaking, working, error)
- [ ] Format validation passes: correct NDJSON structure, Braille character range, row/col counts
- [ ] Unique Braille character count ≥ 100 per frame
- [ ] Animated MP4 demos produced for all agents
- [ ] PNG character card previews regenerated
- [ ] Documentation updated (eikon-pipeline skill, fleet-design skill, tutorials)

---

## 10. File Map

| File | Purpose | Status |
|------|---------|--------|
| `scripts/eikon-builder.py` | Current v2 pipeline (single-image brightness animation) | EXISTS — to be superseded by v3 |
| `scripts/eikon-builder-v3.py` | New multi-image pipeline with per-frame chafa conversion | TO BUILD |
| `scripts/make-eikon-videos.py` | MP4 preview renderer | EXISTS — needs minor update |
| `scripts/build-all-eikons.sh` | Master orchestration script | TO BUILD |
| `eikons/eikon-config.yaml` | Per-agent generation config | TO BUILD |
| `eikons/frames/<agent>/<state>/frame_NNN.png` | Generated frame images | TO GENERATE |
| `eikons/workflows/animate_eikon.json` | ComfyUI workflow for Eikon frame generation | TO BUILD |
| `profiles/<agent>/<agent>.eikon` | Final Eikon files | TO REGENERATE |

---

## 11. Next Steps (Immediate Action Items)

1. **Verify ComfyUI availability:** Run `python3 scripts/hardware_check.py` from the comfyui skill. If `verdict: cloud`, set up Comfy Cloud or pivot to FAL pipeline.
2. **Design ComfyUI workflow:** Create a reusable AnimateDiff workflow for character animation focused on 48×24 Braille output.
3. **Build eikon-builder.py v3:** Add multi-image input mode supporting frame-per-image conversion.
4. **Generate test agent (Senter):** Run full pipeline for one agent end-to-end before scaling to all 8.
5. **Validate against ares.eikon:** Ensure format compatibility with the Herm TUI renderer.

---

## Appendix A: Agent Character Reference

| Agent | Character | Color | Description |
|-------|-----------|-------|-------------|
| Senter | Three-eyed owl spirit guardian | `#7aa2f7` blue | Ancient owl with glowing cyan third eye, perched on switchboard console |
| Chizul | Stone golem builder | `#f7768e` red | Forge-fire heart in chest, crossed wrench+compass hands, blueprint scrolls |
| Klerik | Many-eyed floating watcher orb | `#9ece6a` green | Crystalline sphere with dozens of unblinking eyes, geometric halos |
| Anser | Brass herald angel automaton | `#e0af68` amber | Copper/brass mechanical angel with spiraling horn, planning table |
| Kashik | Moth librarian | `#bb9af7` purple | Giant esoteric moth with rune-covered wings, scroll-like antennae |
| Crow | Dark corvid spirit | `#7dcfff` cyan | Raven shadow-creature with burning coal eyes, trapped star in beak |
| Frieza | Final Form Frieza (DBZ) | `#ff9e64` orange | White/purple final form before server rack control panel |
| LLMC | Cosmic siren | `#c0caf5` ice | Feminine figure of nebula gas and sound waves, broadcast microphones |

## Appendix B: Chafa Braille Reference

- Chafa v1.14.0 REQUIRES: `--format symbols --symbols braille --colors none --fill solid`
- Braille dot encoding: U+2800 + N where N encodes 8 dots as bit flags
- Dot positions: 2 columns × 4 rows per Braille character
- Target: 100+ unique Braille chars per frame (good dithering), min 80 acceptable
- Frame format: 48 characters wide × 24 rows tall = exactly 48×24 Braille grid

## Appendix C: NDJSON Format Quick Reference

```
Line 1: {"type":"header","eikon":1,"id":"...","version":"1.0","title":"...","author":{"name":"..."},"size":{"cols":48,"rows":24},"defaultSignal":"state.idle","signals":{...}}
Line 2+: {"type":"clip","name":"idle","fps":8,"frameCount":24,"loopFrom":0}
... {"type":"frame","clip":"idle","index":0,"rows":["...", ...24 strings]}
```

- Study `projects/herm-tui/assets/eikons/ares/ares.eikon` for authoritative format
- All 6 states required: idle, listening, thinking, speaking, working, error
- Each non-idle state must have `"fallback":"state.idle"`
- `json.dumps(obj, ensure_ascii=False)` — NEVER omit this flag
