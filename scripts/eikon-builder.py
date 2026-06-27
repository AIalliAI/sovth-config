#!/usr/bin/env python3
"""Eikon builder v2: image → chafa Braille → multi-signal NDJSON Eikon.

Fixed: preserves original Braille character diversity in state variations.
"""

import json
import subprocess
import sys
import os
import argparse
import math
from pathlib import Path

COLS = 48
ROWS = 24
FPS = 8

def image_to_braille(image_path: str) -> list[str]:
    """Convert image to Braille art rows using chafa."""
    result = subprocess.run(
        ["chafa", "--size", f"{COLS}x{ROWS}", "--format", "symbols",
         "--symbols", "braille", "--colors", "none", "--fill", "solid",
         image_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"chafa failed: {result.stderr}")
    
    rows = result.stdout.rstrip("\n").split("\n")
    while len(rows) < ROWS:
        rows.append(" " * COLS)
    return rows[:ROWS]


def char_to_dots(ch: str) -> list[bool]:
    """Convert a Braille char to its 8-dot pattern."""
    code = ord(ch)
    if code < 0x2800 or code > 0x28FF:
        return [False] * 8
    n = code - 0x2800
    return [bool(n & (1 << i)) for i in range(8)]


def dots_to_char(dots: list[bool]) -> str:
    """Convert 8-dot pattern back to Braille char."""
    n = sum((1 << i) for i, d in enumerate(dots) if d)
    return chr(0x2800 + n)


def dot_count(dots: list[bool]) -> int:
    return sum(dots)


def modify_frame(base_rows: list[str], dot_modifier) -> list[str]:
    """Apply a per-character dot modifier to create a new frame.
    
    dot_modifier(dots, y, x) returns modified dots.
    """
    result = []
    for y, row in enumerate(base_rows):
        new_row = []
        for x, ch in enumerate(row):
            dots = char_to_dots(ch)
            new_dots = dot_modifier(dots, y, x)
            new_row.append(dots_to_char(new_dots))
        result.append("".join(new_row))
    return result


def generate_variations(base_rows: list[str]) -> dict[str, list[list[str]]]:
    """Generate 6 signal-state clips with subtle animation."""
    states = {}
    
    # Pre-compute dot matrix
    dot_matrix = [[char_to_dots(ch) for ch in row] for row in base_rows]
    
    # idle: subtle breathing pulse (brightness oscillation)
    idle = []
    for i in range(8):
        phase = 2 * math.pi * i / 8
        brightness = 1.0 + 0.04 * math.sin(phase)
        def idle_mod(dots, y, x):
            count = dot_count(dots)
            target = min(8, max(0, int(count * brightness + 0.5)))
            # Keep same pattern shape, just adjust density
            if target >= count:
                # Add dots where missing, starting from top
                new = list(dots)
                added = 0
                for j in range(8):
                    if not new[j] and added < target - count:
                        new[j] = True
                        added += 1
                return new
            else:
                # Remove dots
                new = list(dots)
                removed = 0
                for j in range(8):
                    if new[j] and removed < count - target:
                        new[j] = False
                        removed += 1
                return new
        idle.append(modify_frame(base_rows, idle_mod))
    states["idle"] = idle
    
    # listening: slightly brighter with subtle pulse
    listening = []
    for i in range(6):
        phase = 2 * math.pi * i / 6
        brightness = 1.0 + 0.08 * math.sin(phase)
        def listen_mod(dots, y, x):
            count = dot_count(dots)
            target = min(8, max(0, int(count * brightness + 0.5)))
            if target >= count:
                new = list(dots)
                added = 0
                for j in range(8):
                    if not new[j] and added < target - count:
                        new[j] = True
                        added += 1
                return new
            else:
                new = list(dots)
                removed = 0
                for j in range(8):
                    if new[j] and removed < count - target:
                        new[j] = False
                        removed += 1
                return new
        listening.append(modify_frame(base_rows, listen_mod))
    states["listening"] = listening
    
    # thinking: processing ripple (horizontal wave)
    thinking = []
    for i in range(8):
        phase = 2 * math.pi * i / 8
        def think_mod(dots, y, x):
            count = dot_count(dots)
            ripple = 1.0 + 0.06 * math.sin(phase + x * 0.4)
            target = min(8, max(0, int(count * ripple + 0.5)))
            if target >= count:
                new = list(dots)
                added = 0
                for j in range(8):
                    if not new[j] and added < target - count:
                        new[j] = True
                        added += 1
                return new
            else:
                new = list(dots)
                removed = 0
                for j in range(8):
                    if new[j] and removed < count - target:
                        new[j] = False
                        removed += 1
                return new
        thinking.append(modify_frame(base_rows, think_mod))
    states["thinking"] = thinking
    
    # speaking: active brighter pulse
    speaking = []
    for i in range(8):
        phase = 2 * math.pi * i / 8
        brightness = 1.0 + 0.12 * math.sin(phase)
        def speak_mod(dots, y, x):
            count = dot_count(dots)
            target = min(8, max(0, int(count * brightness + 0.5)))
            if target >= count:
                new = list(dots)
                added = 0
                for j in range(8):
                    if not new[j] and added < target - count:
                        new[j] = True
                        added += 1
                return new
            else:
                new = list(dots)
                removed = 0
                for j in range(8):
                    if new[j] and removed < count - target:
                        new[j] = False
                        removed += 1
                return new
        speaking.append(modify_frame(base_rows, speak_mod))
    states["speaking"] = speaking
    
    # working: busy short-cycle flicker
    working = []
    for i in range(6):
        phase = 2 * math.pi * i / 6
        def work_mod(dots, y, x):
            count = dot_count(dots)
            flicker = 1.0 + 0.05 * math.sin(phase + y * 0.5)
            target = min(8, max(0, int(count * flicker + 0.5)))
            if target >= count:
                new = list(dots)
                added = 0
                for j in range(8):
                    if not new[j] and added < target - count:
                        new[j] = True
                        added += 1
                return new
            else:
                new = list(dots)
                removed = 0
                for j in range(8):
                    if new[j] and removed < count - target:
                        new[j] = False
                        removed += 1
                return new
        working.append(modify_frame(base_rows, work_mod))
    states["working"] = working
    
    # error: alert flash (alternating bright/dim)
    error = []
    for i in range(8):
        if i % 3 < 2:  # 2 bright, 1 dim
            def err_mod(dots, y, x):
                count = dot_count(dots)
                target = min(8, max(0, int(count * 1.15 + 0.5)))
                new = list(dots)
                added = 0
                for j in range(8):
                    if not new[j] and added < target - count:
                        new[j] = True
                        added += 1
                return new
        else:
            def err_mod(dots, y, x):
                return list(dots)
        error.append(modify_frame(base_rows, err_mod))
    states["error"] = error
    
    return states


def build_eikon(name: str, eikon_id: str, image_path: str, output_path: str,
                author: str = "sovthpaw", title: str | None = None):
    """Build a full multi-signal Eikon from an image."""
    
    print(f"  Converting {name} image to Braille...")
    base_rows = image_to_braille(image_path)
    
    # Verify quality
    chars = set()
    for row in base_rows:
        chars.update(row)
    non_space = [c for c in chars if c != ' ' and c != '\u2800']
    print(f"  → {len(non_space)} unique Braille characters (non-empty)")
    
    print(f"  Generating state variations...")
    states = generate_variations(base_rows)
    
    title = title or name.title()
    lines = []
    
    signals = {
        "state.idle": {"clip": "idle"},
        "state.listening": {"clip": "listening", "fallback": "state.idle"},
        "state.thinking": {"clip": "thinking", "fallback": "state.idle"},
        "state.speaking": {"clip": "speaking", "fallback": "state.idle"},
        "state.working": {"clip": "working", "fallback": "state.idle"},
        "state.error": {"clip": "error", "fallback": "state.idle"},
    }
    
    header = {
        "type": "header",
        "eikon": 1,
        "id": eikon_id,
        "version": "1.0",
        "title": title,
        "author": {"name": author},
        "size": {"cols": COLS, "rows": ROWS},
        "defaultSignal": "state.idle",
        "signals": signals
    }
    lines.append(json.dumps(header, ensure_ascii=False))
    
    clip_names = ["idle", "listening", "thinking", "speaking", "working", "error"]
    for clip_name in clip_names:
        frames = states[clip_name]
        clip = {
            "type": "clip",
            "name": clip_name,
            "fps": FPS,
            "frameCount": len(frames),
            "loopFrom": 0
        }
        lines.append(json.dumps(clip, ensure_ascii=False))
        
        for idx, frame in enumerate(frames):
            frame_obj = {
                "type": "frame",
                "clip": clip_name,
                "index": idx,
                "rows": frame
            }
            lines.append(json.dumps(frame_obj, ensure_ascii=False))
    
    output = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(output)
    
    total_frames = sum(len(states[c]) for c in clip_names)
    size_kb = len(output.encode('utf-8')) / 1024
    print(f"  → {output_path}: {total_frames} frames, {size_kb:.0f} KB")
    return output_path


def render_eikon_preview(eikon_path: str, output_path: str, scale: int = 4):
    """Render the first idle frame as a PNG image using Pillow."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not available")
        return
    
    with open(eikon_path) as f:
        lines = f.readlines()
    
    frame_rows = None
    for line in lines:
        obj = json.loads(line)
        if obj.get("type") == "frame" and obj.get("clip") == "idle" and obj.get("index") == 0:
            frame_rows = obj["rows"]
            break
    
    if not frame_rows:
        print(f"No idle frame in {eikon_path}")
        return
    
    pixel_w = COLS * 2 * scale
    pixel_h = ROWS * 4 * scale
    
    img = Image.new("L", (pixel_w, pixel_h), 255)
    draw = ImageDraw.Draw(img)
    
    # Dot positions in a 2×4 Braille cell:
    #   1 4
    #   2 5
    #   3 6
    #   7 8
    dot_map = [
        (0, 0), (0, 1), (0, 2),  # dots 1,2,3
        (1, 0), (1, 1), (1, 2),  # dots 4,5,6
        (0, 3), (1, 3),           # dots 7,8
    ]
    
    for row_idx, row_str in enumerate(frame_rows):
        for col_idx, ch in enumerate(row_str):
            code = ord(ch)
            if code < 0x2800 or code > 0x28FF:
                continue
            n = code - 0x2800
            base_x = col_idx * 2 * scale
            base_y = row_idx * 4 * scale
            
            for dot_idx, (dx, dy) in enumerate(dot_map):
                if n & (1 << dot_idx):
                    x0 = base_x + dx * scale
                    y0 = base_y + dy * scale
                    draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=0)
    
    img.save(output_path, "PNG")
    print(f"  → Preview saved: {output_path} ({pixel_w}×{pixel_h})")


def main():
    parser = argparse.ArgumentParser(description="Eikon builder v2")
    sub = parser.add_subparsers(dest="cmd")
    
    build = sub.add_parser("build")
    build.add_argument("--name", required=True)
    build.add_argument("--id", required=True)
    build.add_argument("--image", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--author", default="sovthpaw")
    build.add_argument("--title", default=None)
    
    render = sub.add_parser("render")
    render.add_argument("--eikon", required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--scale", type=int, default=4)
    
    render_all = sub.add_parser("render-all")
    render_all.add_argument("--dir", required=True)
    render_all.add_argument("--output", required=True)
    
    args = parser.parse_args()
    
    if args.cmd == "build":
        build_eikon(args.name, args.id, args.image, args.output,
                    author=args.author, title=args.title)
    elif args.cmd == "render":
        render_eikon_preview(args.eikon, args.output, args.scale)
    elif args.cmd == "render-all":
        os.makedirs(args.output, exist_ok=True)
        for f in sorted(Path(args.dir).glob("*.eikon")):
            name = f.stem
            out = os.path.join(args.output, f"{name}-preview.png")
            print(f"Rendering {name}...")
            render_eikon_preview(str(f), out)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
