#!/usr/bin/env python3
"""Render animated Eikon preview videos showing all 6 states."""
import json, subprocess, os, tempfile, shutil
from PIL import Image, ImageDraw

COLS, ROWS = 48, 24
SCALE = 4

DOT_MAP = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]

def render_frame(rows, scale=SCALE):
    w, h = COLS * 2 * scale, ROWS * 4 * scale
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            code = ord(ch)
            if code < 0x2800 or code > 0x28FF:
                continue
            n = code - 0x2800
            bx, by = x * 2 * scale, y * 4 * scale
            for i, (dx, dy) in enumerate(DOT_MAP):
                if n & (1 << i):
                    x0 = bx + dx * scale
                    y0 = by + dy * scale
                    draw.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=0)
    return img

def make_video(eikon_path, output_path, fps=8):
    """Create an MP4 showing all 6 states of the Eikon."""
    with open(eikon_path) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    
    header = lines[0]
    name = header.get("title", "unknown")
    
    tmpdir = tempfile.mkdtemp()
    frame_idx = 0
    
    # Render each clip's frames
    for obj in lines:
        if obj.get("type") != "frame":
            continue
        rows = obj["rows"]
        img = render_frame(rows)
        
        # Draw state label
        from PIL import ImageDraw as ID
        draw = ID.Draw(img)
        clip_name = obj.get("clip", "?")
        draw.text((4, 2), f"{name} — {clip_name}", fill=0)
        
        path = os.path.join(tmpdir, f"frame_{frame_idx:04d}.png")
        img.save(path)
        frame_idx += 1
    
    if frame_idx == 0:
        shutil.rmtree(tmpdir)
        return
    
    # Create video with ffmpeg
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", os.path.join(tmpdir, f"frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", f"scale={COLS*3*SCALE}:{ROWS*3*SCALE}:flags=neighbor",
        output_path
    ], capture_output=True)
    
    shutil.rmtree(tmpdir)
    print(f"  → {output_path} ({frame_idx} frames)")


if __name__ == "__main__":
    import sys
    agents = sys.argv[1:] if len(sys.argv) > 1 else [
        "senter", "chizul", "klerik", "anser", "kashik", "crow", "frieza", "llmc"
    ]
    outdir = "eikons/videos"
    os.makedirs(outdir, exist_ok=True)
    
    for name in agents:
        eikon = f"profiles/{name}/{name}.eikon"
        out = f"{outdir}/{name}-animated.mp4"
        if os.path.exists(eikon):
            print(f"Rendering {name}...")
            make_video(eikon, out)
