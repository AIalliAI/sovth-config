# Eikon Pipeline — Character Art to Herm TUI Animation

![Eikon Pipeline](https://v3b.fal.media/files/b/0a9fe952/HOgNL2L-6odhLPFuC2-bg_9zi4tbwN.png)

## Overview

The Eikon pipeline turns character concepts into animated pixel art that renders in the Herm TUI. You describe what you want — a character, a symbol, an animation — and the pipeline generates frames, converts them to Braille Unicode pixel art, and produces a `.eikon` file the TUI can display.

## What's an Eikon?

Eikons are 48×24 pixel animations rendered using **Braille Unicode characters** in the terminal. Each Braille character (U+2800–U+28FF) encodes a 2×4 dot pattern — 24 characters per row × 6 rows = the full 48×24 grid. The `.eikon` file is Newline-Delimited JSON (NDJSON) with header, state, and frame data.

```
Header:  {"eikon":1, "name":"...", "width":48, "height":24, ...}
State:   {"state":"idle", "fps":16, "color":"#7aa2f7", "frame_count":N, ...}
Frame 0: {"f":0, "data":"braille string with \\n row separators"}
Frame 1: {"f":1, "data":"..."}
...
```

They're placed at `~/.bun/install/global/node_modules/herm-tui/assets/eikons/` and referenced in each profile's `herm/tui.json` via `eikonPath`.

## The Pipeline

```
Prompt → Image Generation → Eikon Converter → .eikon file → Herm TUI
```

### Step 1: Generate Character Art

Use the image generator to create a bold, high-contrast silhouette. The key requirements:

- **48×24 target** — images are downscaled, so keep shapes simple
- **High contrast** — black shapes on white background work best
- **No gradients** — Braille is monochrome, gradients become noise
- **Distinct silhouette** — recognizable at small scale

```bash
# Example: generate a character icon
hermes chat -q "Generate a bold high-contrast silhouette icon of a [description]..."
```

### Step 2: Convert to Eikon

The `eikon-convert.py` script handles the conversion:

```bash
# Single frame (static eikon)
python3 scripts/eikon-convert.py icon.png -o output.eikon --name agent-name --color "#7aa2f7"

# Multiple frames (animated eikon)
python3 scripts/eikon-convert.py frame1.png frame2.png frame3.png -o animated.eikon --name agent-name --color "#f7768e" --fps 12
```

### Step 3: Install

```bash
# Copy to herm-tui eikons directory
cp output.eikon ~/.bun/install/global/node_modules/herm-tui/assets/eikons/

# Reference in profile's herm/tui.json
{
  "eikonPath": "$HOME/.bun/install/global/node_modules/herm-tui/assets/eikons/output.eikon"
}
```

## Creating Animated Eikons

For animated eikons, generate multiple frames with slight variations:

1. **Generate base image** — the character or symbol in its default pose
2. **Generate variations** — same prompt with modifiers: "shifted slightly left", "rotated 5 degrees", "pulse effect"
3. **Convert all frames** — pass all images to `eikon-convert.py`
4. **Set FPS** — 8-16 fps works well for the TUI

### Animation Prompt Template

```
Same bold silhouette icon [description], but [variation]. Pure black silhouette on stark white background. No gradients. Same composition as reference but [movement description]. Square format.
```

## Fleet Eikons (Pre-built)

These are already installed and ready to use:

| Agent | Eikon File | Color | Symbol |
|-------|-----------|-------|--------|
| Senter | `senter.eikon` | `#7aa2f7` blue | Switchboard hub |
| Chizul | `chizul.eikon` | `#f7768e` red | Wrench + compass |
| Klerik | `klerik.eikon` | `#9ece6a` green | Magnifying glass |
| Anser | `anser.eikon` | `#e0af68` amber | Broadcast mic |
| Kashik | `kashik.eikon` | `#bb9af7` purple | Open book |
| Crow | `crow.eikon` | `#7dcfff` cyan | Bird in flight |
| Frieza | `frieza.eikon` | `#ff9e64` orange | Server rack |
| LLMC | `llmc.eikon` | `#c0caf5` ice | Musical note |

## Wiring Eikons to Profiles

Update each profile's `herm/tui.json`:

```json
{
  "mouse": true,
  "targetFps": 30,
  "theme": "tokyonight",
  "eikonPath": "$HOME/.bun/install/global/node_modules/herm-tui/assets/eikons/senter.eikon"
}
```

**Recommended theme pairings:**

| Agent | Theme | Eikon |
|-------|-------|-------|
| Senter | `tokyonight` | `senter.eikon` |
| Chizul | `orng` | `chizul.eikon` |
| Klerik | `monokai` | `klerik.eikon` |
| Anser | `catppuccin` | `anser.eikon` |
| Kashik | `nord` | `kashik.eikon` |
| Crow | `gruvbox` | `crow.eikon` |
| Frieza | `vercel` | `frieza.eikon` |
| LLMC | `lucent-orng` | `llmc.eikon` |

## Troubleshooting

**Eikon not showing in TUI:** Verify the path in `herm/tui.json` is absolute (use `$HOME`, not `~`). Check the file exists. Restart Hermes.

**Garbled output:** Ensure the image is exactly 48×24 or square (it auto-resizes). Check that the Braille font is installed (most terminals support it natively).

**Animation not playing:** Multi-frame eikons need at least 2 frames. Check the `frame_count` in the state block matches the actual number of frame objects.

---

*Part of the SouthpawIN agent fleet tutorials*
