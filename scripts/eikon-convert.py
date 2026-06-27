#!/usr/bin/env python3
"""Convert images to Herm TUI Eikon format (48x24 Braille Unicode pixel art).

Usage:
    python3 eikon-convert.py <input.png> <output.eikon> [--name NAME] [--color HEX] [--fps N]

The Eikon format is NDJSON:
    Line 1: header {"eikon":1, "name":"...", "width":48, "height":24, ...}
    Line 2: state {"state":"idle", "fps":16, "color":"#7aa2f7", "frame_count":N, ...}
    Lines 3+: frame data {"f":N, "data":"braille string with \\n row separators"}

Each input image is downscaled to 48x24, thresholded to monochrome, then
converted to Braille Unicode characters (each character encodes a 2x4 dot block).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image


def pixels_to_braille(block_2x4: list[list[bool]]) -> str:
    """Convert a 2-column x 4-row block of monochrome pixels to a Braille character.
    
    Braille dot numbering (U+2800 + bit offsets):
        1  4
        2  5
        3  6
        7  8
    
    Bit offsets: dot1=0, dot2=1, dot3=2, dot4=3, dot5=4, dot6=5, dot7=6, dot8=7
    """
    # block[col][row] — 2 columns, 4 rows each
    dots = 0
    if block_2x4[0][0]: dots |= 1 << 0   # dot 1
    if block_2x4[0][1]: dots |= 1 << 1   # dot 2
    if block_2x4[0][2]: dots |= 1 << 2   # dot 3
    if block_2x4[1][0]: dots |= 1 << 3   # dot 4
    if block_2x4[1][1]: dots |= 1 << 4   # dot 5
    if block_2x4[1][2]: dots |= 1 << 5   # dot 6
    if block_2x4[0][3]: dots |= 1 << 6   # dot 7
    if block_2x4[1][3]: dots |= 1 << 7   # dot 8
    return chr(0x2800 + dots)


def image_to_braille_frame(img: Image.Image) -> str:
    """Convert a 48x24 monochrome PIL Image to a Braille frame string.
    
    Returns a single string with embedded newlines, 24 rows of 24 Braille chars each.
    The image grid is processed in 2x4 blocks: 24 blocks wide (48 cols / 2), 6 blocks tall (24 rows / 4).
    """
    img = img.resize((48, 24), Image.LANCZOS).convert('1')
    pixels = img.load()
    
    out_rows = []
    for block_row in range(6):  # 6 blocks of 4 rows each
        row_start = block_row * 4
        chars = []
        for block_col in range(24):  # 24 blocks of 2 columns each
            col_start = block_col * 2
            block = [[False]*4 for _ in range(2)]  # [col][row]
            for r in range(4):
                block[0][r] = bool(pixels[col_start, row_start + r])
                block[1][r] = bool(pixels[col_start + 1, row_start + r])
            chars.append(pixels_to_braille(block))
        out_rows.append(''.join(chars))
    
    return '\n'.join(out_rows)


def image_to_eikon(
    image_path: str,
    name: str = None,
    color: str = "#7aa2f7",
    fps: int = 16,
) -> str:
    """Convert a single image to NDJSON Eikon format string."""
    img = Image.open(image_path)
    frame_data = image_to_braille_frame(img)
    
    if name is None:
        name = Path(image_path).stem
    
    header = {
        "eikon": 1,
        "name": name,
        "width": 48,
        "height": 24,
        "author": "sovth-config eikon pipeline",
        "created": datetime.now(timezone.utc).isoformat(),
        "source_url": "",
    }
    
    state = {
        "state": "idle",
        "fps": fps,
        "color": color,
        "frame_count": 1,
        "loop_from": 0,
    }
    
    frame = {"f": 0, "data": frame_data}
    
    return (
        json.dumps(header) + "\n" +
        json.dumps(state) + "\n" +
        json.dumps(frame) + "\n"
    )


def multi_frame_to_eikon(
    image_paths: list[str],
    name: str = None,
    color: str = "#7aa2f7",
    fps: int = 16,
    loops: list[int] = None,
) -> str:
    """Convert multiple images to a multi-frame animated Eikon.
    
    Each image becomes one frame. Supports multiple animation states
    by specifying loop ranges via the 'loops' parameter.
    If loops is None, all frames are in a single "idle" state.
    """
    if loops is None:
        loops = []
    
    frames_data = []
    for path in image_paths:
        img = Image.open(path)
        frames_data.append(image_to_braille_frame(img))
    
    if name is None:
        name = Path(image_paths[0]).stem
    
    header = {
        "eikon": 1,
        "name": name,
        "width": 48,
        "height": 24,
        "author": "sovth-config eikon pipeline",
        "created": datetime.now(timezone.utc).isoformat(),
        "source_url": "",
    }
    
    lines = [json.dumps(header)]
    
    if not loops:
        # Single state, all frames
        state = {
            "state": "idle",
            "fps": fps,
            "color": color,
            "frame_count": len(frames_data),
            "loop_from": 0,
        }
        lines.append(json.dumps(state))
        for i, fd in enumerate(frames_data):
            lines.append(json.dumps({"f": i, "data": fd}))
    else:
        # Multiple states with loop ranges
        for state_idx, (start, end) in enumerate(loops):
            state_name = "idle" if state_idx == 0 else f"state_{state_idx}"
            state = {
                "state": state_name,
                "fps": fps,
                "color": color,
                "frame_count": end - start,
                "loop_from": 0,
            }
            lines.append(json.dumps(state))
            for i in range(start, end):
                lines.append(json.dumps({"f": i - start, "data": frames_data[i]}))
    
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert images to Herm TUI Eikon format")
    parser.add_argument("input", nargs="+", help="Input image file(s). Multiple files = animated Eikon")
    parser.add_argument("-o", "--output", required=True, help="Output .eikon file")
    parser.add_argument("--name", help="Eikon name (default: input filename stem)")
    parser.add_argument("--color", default="#7aa2f7", help="Hex color for the eikon (default: #7aa2f7)")
    parser.add_argument("--fps", type=int, default=16, help="Frames per second (default: 16)")
    
    args = parser.parse_args()
    
    if len(args.input) == 1:
        result = image_to_eikon(args.input[0], name=args.name, color=args.color, fps=args.fps)
    else:
        result = multi_frame_to_eikon(args.input, name=args.name, color=args.color, fps=args.fps)
    
    with open(args.output, 'w') as f:
        f.write(result)
    
    print(f"Created {args.output} ({len(args.input)} frame(s), 48x24 Braille pixel art)")
