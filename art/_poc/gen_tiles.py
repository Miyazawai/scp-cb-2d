#!/usr/bin/env python3
"""
SCP facility pixel-art feasibility probe.

Generates a 16x16 top-down tileset, a 4-direction x 2-frame 16x16 character,
a fixed 16-colour palette, a contact sheet, and a 20x12 assembled room preview.

Everything is drawn from code with Pillow. No external art or downloads.
Run:  python gen_tiles.py
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
TILE = 16
SCALE = 4
TRANSPARENT = (0, 0, 0, 0)

# ---------------------------------------------------------------------------
# Fixed 16-colour palette. No other RGB value is permitted in any asset.
# ---------------------------------------------------------------------------
PALETTE = [
    ("ink", "#0A0B0E"),
    ("shadow", "#171A20"),
    ("wall_dark", "#2A2E36"),
    ("concrete_dark", "#3B414B"),
    ("concrete", "#59606B"),
    ("concrete_light", "#7F8792"),
    ("metal", "#A8AEB4"),
    ("bone", "#DAD4C2"),
    ("skin_shadow", "#9B6A4C"),
    ("rust", "#8A4C2F"),
    ("hazard", "#C46B2E"),
    ("orange", "#D97A27"),
    ("orange_light", "#F2A94A"),
    ("blood_dark", "#4A1018"),
    ("blood", "#931F27"),
    ("green", "#4F806A"),
]
PALETTE_RGB = {name: tuple(int(h[i : i + 2], 16) for i in (1, 3, 5)) for name, h in PALETTE}
PALETTE_SET = set(PALETTE_RGB.values())
FONT = ImageFont.load_default()


def rgba(name: str) -> tuple[int, int, int, int]:
    r, g, b = PALETTE_RGB[name]
    return (r, g, b, 255)


def solid(color: str) -> Image.Image:
    return Image.new("RGBA", (TILE, TILE), rgba(color))


def blank() -> Image.Image:
    return Image.new("RGBA", (TILE, TILE), TRANSPARENT)


def put(img: Image.Image, x: int, y: int, color: str) -> None:
    if 0 <= x < TILE and 0 <= y < TILE:
        img.putpixel((x, y), rgba(color))


def rect(img: Image.Image, x: int, y: int, w: int, h: int, color: str) -> None:
    if w <= 0 or h <= 0:
        return
    ImageDraw.Draw(img).rectangle((x, y, x + w - 1, y + h - 1), fill=rgba(color))


def hline(img: Image.Image, x0: int, x1: int, y: int, color: str) -> None:
    for x in range(x0, x1 + 1):
        put(img, x, y, color)


def vline(img: Image.Image, x: int, y0: int, y1: int, color: str) -> None:
    for y in range(y0, y1 + 1):
        put(img, x, y, color)


def line(img: Image.Image, pts: list[tuple[int, int]], color: str) -> None:
    ImageDraw.Draw(img).line(pts, fill=rgba(color), width=1)


def poly(img: Image.Image, pts: list[tuple[int, int]], color: str) -> None:
    ImageDraw.Draw(img).polygon(pts, fill=rgba(color))


# ---------------------------------------------------------------------------
# FLOOR FAMILY
# ---------------------------------------------------------------------------
def floor_base(seed: int, variant: int = 0) -> Image.Image:
    """Quiet concrete. A 16 px tile is repeated hundreds of times in a room,
    so even five stray pixels per tile become a field of visual static."""
    img = solid("concrete")

    if variant == 0:
        # Two low-contrast marks only.
        for x, y in ((3, 4), (4, 4)):
            put(img, x, y, "concrete_dark")
        put(img, 11, 6, "concrete_dark")
    elif variant == 1:
        # Worn variant: a faded repair patch and a small oil stain.
        for x, y in ((2, 10), (4, 10), (3, 11), (5, 11), (2, 12), (4, 12)):
            put(img, x, y, "concrete_dark")
        for x, y in ((11, 2), (12, 2), (12, 3)):
            put(img, x, y, "concrete_dark")
        put(img, 11, 3, "concrete_light")
        put(img, 13, 12, "concrete_dark")
    else:
        # Untouched pour. Most of the room uses this tile.
        pass
    return img


def tile_floor_a() -> Image.Image:
    return floor_base(101, 0)


def tile_floor_b() -> Image.Image:
    return floor_base(202, 1)


def tile_floor_c() -> Image.Image:
    return floor_base(303, 2)


def tile_grate() -> Image.Image:
    img = floor_base(303)
    # Recessed frame.
    rect(img, 1, 1, 14, 14, "shadow")
    hline(img, 1, 14, 1, "concrete_light")
    vline(img, 1, 1, 14, "concrete_light")
    hline(img, 1, 14, 14, "concrete_dark")
    vline(img, 14, 1, 14, "concrete_dark")
    rect(img, 3, 3, 10, 10, "ink")
    # Metal bars, lit on their top/left edge.
    for x in (4, 6, 8, 10, 12):
        vline(img, x, 4, 12, "concrete_light")
        put(img, x + 1, 4, "concrete_dark")
    for y in (7,):
        hline(img, 4, 11, y, "concrete_light")
        hline(img, 4, 11, y + 1, "concrete_dark")
    # Corner screws.
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(img, x, y, "metal")
    # Rust bleed on one side.
    for x, y in ((13, 7), (13, 8), (12, 9), (13, 10)):
        put(img, x, y, "rust")
    return img


def tile_blood() -> Image.Image:
    img = floor_base(404)
    # Smear/drag mark from upper right into the pool.
    trail = [(13, 1), (12, 2), (11, 3), (12, 4), (10, 4), (9, 5)]
    for x, y in trail:
        put(img, x, y, "blood_dark")
        put(img, x - 1, y, "blood")
    # Irregular pool: dark outer edge plus a smaller wet core.
    outer = [
        (2, 9), (3, 8), (5, 7), (7, 8), (9, 7), (11, 9), (12, 11),
        (11, 13), (9, 14), (6, 14), (4, 13), (3, 11), (2, 10),
    ]
    poly(img, outer, "blood_dark")
    inner = [
        (4, 10), (5, 9), (7, 9), (9, 8), (10, 10), (10, 12),
        (8, 13), (6, 13), (4, 12),
    ]
    poly(img, inner, "blood")
    # Drier edge and a few directional spatters.
    line(img, [(3, 10), (4, 13), (7, 14), (10, 12)], "rust")
    for x, y in ((13, 6), (14, 7), (12, 7), (8, 2), (7, 3), (5, 5), (1, 8)):
        put(img, x, y, "blood")
    put(img, 13, 6, "blood_dark")
    put(img, 8, 2, "blood_dark")
    # Wet glints: two dull pixels only, no shiny cartoon highlights.
    put(img, 7, 10, "skin_shadow")
    put(img, 8, 12, "rust")
    return img


def tile_debris() -> Image.Image:
    img = floor_base(505)
    # Concrete chunks with a light top edge and a dropped shadow.
    chunks = [
        (3, 4, 3, 2), (11, 10, 3, 2), (6, 12, 2, 2), (13, 3, 2, 1),
    ]
    for x, y, w, h in chunks:
        rect(img, x + 1, y + 1, w, h, "shadow")
        rect(img, x, y, w, h, "concrete_dark")
        hline(img, x, x + w - 1, y, "concrete_light")
        put(img, x, y, "metal")
    # Bent rebar, rusted.
    line(img, [(8, 5), (11, 6), (12, 8), (14, 7)], "shadow")
    line(img, [(8, 4), (11, 5), (12, 7), (14, 6)], "rust")
    put(img, 11, 5, "hazard")
    # Torn paper scrap.
    rect(img, 2, 9, 3, 3, "shadow")
    rect(img, 1, 8, 3, 3, "bone")
    put(img, 2, 9, "concrete_light")
    put(img, 2, 10, "concrete_light")
    # Loose screws / dust.
    for x, y in ((5, 2), (10, 14), (14, 12), (4, 14)):
        put(img, x, y, "metal")
    for x, y in ((7, 3), (9, 10), (13, 14), (3, 13)):
        put(img, x, y, "concrete_dark")
    return img


def tile_hazard() -> Image.Image:
    img = floor_base(606)
    # Painted caution patch, heavily worn.
    patch = blank()
    pd = ImageDraw.Draw(patch)
    for k in range(-20, 40, 6):
        pd.line([(k, 16), (k + 16, 0)], fill=rgba("hazard"), width=3)
        pd.line([(k, 15), (k + 16, -1)], fill=rgba("orange_light"), width=1)
    mask = Image.new("L", (TILE, TILE), 0)
    ImageDraw.Draw(mask).rectangle((2, 4, 13, 12), fill=255)
    img.paste(patch, (0, 0), mask)

    # Border and wear.
    rect(img, 1, 3, 14, 1, "shadow")
    rect(img, 1, 13, 14, 1, "shadow")
    vline(img, 1, 3, 13, "shadow")
    vline(img, 14, 3, 13, "shadow")
    hline(img, 1, 14, 3, "concrete_light")
    for x, y in ((4, 5), (5, 5), (9, 8), (10, 8), (11, 9), (6, 11), (7, 11), (12, 12)):
        put(img, x, y, "concrete")
    for x, y in ((3, 12), (13, 5), (8, 12)):
        put(img, x, y, "concrete_dark")
    for x, y in ((2, 4), (13, 4), (2, 12), (13, 12)):
        put(img, x, y, "metal")
    return img


# ---------------------------------------------------------------------------
# WALL FAMILY (flat top-down slabs; the light band is the lit top edge)
# ---------------------------------------------------------------------------
def wall_base(seed: int) -> Image.Image:
    img = solid("wall_dark")
    # Keep the slab mostly flat; the lit cap and floor-contact shadow carry the
    # form. Repeated texture detail on every tile reads as damage, not material.
    for x, y in ((2, 7), (3, 7), (3, 8)):
        put(img, x, y, "concrete_dark")
    put(img, 6, 11, "shadow")
    put(img, 7, 11, "shadow")
    # Lit top cap and a dark floor-contact edge.
    hline(img, 0, 15, 0, "concrete_light")
    hline(img, 0, 15, 1, "concrete")
    hline(img, 0, 15, 2, "concrete_dark")
    hline(img, 0, 15, 13, "shadow")
    hline(img, 0, 15, 14, "shadow")
    hline(img, 0, 15, 15, "ink")
    # A single chipped spot, deliberately off-centre.
    put(img, 5, 6, "concrete_dark")
    put(img, 5, 7, "shadow")
    put(img, 10, 9, "concrete_dark")
    return img


def tile_wall() -> Image.Image:
    return wall_base(701)


def tile_wall_corner() -> Image.Image:
    img = wall_base(702)
    # A chamfered interior corner exposes a triangular sliver of floor.
    poly(img, [(11, 15), (15, 11), (15, 15)], "concrete")
    line(img, [(10, 15), (15, 10)], "metal")
    line(img, [(11, 15), (15, 11)], "shadow")
    put(img, 13, 14, "concrete_dark")
    put(img, 14, 13, "concrete_dark")
    put(img, 12, 13, "concrete_light")
    put(img, 13, 12, "concrete_light")
    return img


def tile_door() -> Image.Image:
    img = wall_base(703)
    # Jambs, 3 px each, with a strong metal edge so the opening reads at 4x.
    for x0 in (2, 11):
        rect(img, x0, 0, 3, 16, "concrete_dark")
        vline(img, x0, 1, 15, "metal")
        vline(img, x0 + 1, 2, 15, "concrete_light")
        vline(img, x0 + 2, 2, 15, "shadow")
    # Dark passage, opening onto a lit threshold.
    rect(img, 5, 0, 6, 16, "shadow")
    rect(img, 6, 0, 4, 7, "ink")
    rect(img, 6, 7, 4, 8, "concrete_dark")
    hline(img, 6, 9, 7, "concrete")
    # Threshold plate.
    rect(img, 5, 12, 6, 3, "concrete_dark")
    hline(img, 5, 10, 12, "concrete_light")
    hline(img, 5, 10, 14, "shadow")
    for x in (6, 8, 10):
        put(img, x, 13, "metal")
    # Hazard chips and wear.
    for y in (8, 9):
        put(img, 2, y, "hazard")
        put(img, 13, y, "hazard")
    put(img, 3, 9, "orange_light")
    put(img, 12, 9, "orange_light")
    put(img, 4, 3, "rust")
    put(img, 12, 12, "rust")
    return img


def tile_keycard() -> Image.Image:
    img = wall_base(704)
    # Conduit.
    vline(img, 8, 2, 5, "shadow")
    vline(img, 9, 2, 5, "concrete_dark")
    # Reader mounting plate, with cast shadow.
    rect(img, 5, 5, 8, 10, "shadow")
    rect(img, 4, 4, 8, 10, "concrete_dark")
    hline(img, 4, 11, 4, "concrete_light")
    vline(img, 4, 4, 13, "concrete_light")
    hline(img, 4, 11, 13, "shadow")
    vline(img, 11, 4, 13, "shadow")
    # Screen.
    rect(img, 5, 5, 6, 3, "ink")
    hline(img, 6, 9, 6, "green")
    put(img, 9, 5, "bone")
    # Card slot and keypad.
    hline(img, 5, 10, 8, "ink")
    hline(img, 5, 10, 9, "metal")
    for y in (10, 12):
        for x in (6, 8):
            put(img, x, y, "metal")
            put(img, x, y + 1, "shadow")
    put(img, 10, 11, "orange_light")
    put(img, 4, 13, "rust")
    return img


def tile_vent() -> Image.Image:
    img = wall_base(705)
    # Duct mouth, larger and more legible than a row of hairline slats.
    rect(img, 4, 5, 9, 8, "shadow")
    rect(img, 3, 4, 9, 8, "concrete_dark")
    hline(img, 3, 11, 4, "concrete_light")
    vline(img, 3, 4, 11, "concrete_light")
    hline(img, 3, 11, 11, "shadow")
    vline(img, 11, 4, 11, "shadow")
    rect(img, 5, 6, 5, 5, "ink")
    for y in (7, 9):
        hline(img, 5, 9, y, "metal")
        hline(img, 5, 9, y + 1, "wall_dark")
    # Screws and rust streaks from the bottom corners.
    for x, y in ((3, 4), (11, 4), (3, 11), (11, 11)):
        put(img, x, y, "metal")
    for x, y in ((4, 12), (4, 13), (10, 12), (2, 9)):
        put(img, x, y, "rust")
    return img


def tile_light() -> Image.Image:
    img = blank()
    # A suspended twin-tube fixture seen from above.
    rect(img, 2, 5, 12, 6, "ink")
    rect(img, 1, 6, 14, 4, "metal")
    hline(img, 2, 13, 6, "concrete_light")
    hline(img, 2, 13, 9, "shadow")
    # Two tubes with a hot core and a warm edge.
    hline(img, 3, 12, 7, "orange_light")
    hline(img, 3, 12, 8, "bone")
    # End caps and hangers.
    rect(img, 1, 6, 1, 4, "concrete_dark")
    rect(img, 14, 6, 1, 4, "concrete_dark")
    put(img, 1, 6, "metal")
    put(img, 14, 6, "metal")
    put(img, 1, 9, "shadow")
    put(img, 14, 9, "shadow")
    for x in (5, 10):
        vline(img, x, 3, 5, "shadow")
        put(img, x, 2, "concrete_dark")
    # A little grime so it is not a clean UI bar.
    put(img, 4, 7, "hazard")
    put(img, 11, 8, "hazard")
    put(img, 13, 7, "concrete_dark")
    return img


def tile_pipe() -> Image.Image:
    img = wall_base(706)
    # Vertical conduit with brackets. Horizontal use = rotate 90 degrees.
    rect(img, 6, 0, 4, 16, "shadow")
    vline(img, 6, 0, 15, "concrete_dark")
    vline(img, 7, 0, 15, "metal")
    vline(img, 8, 0, 15, "concrete_light")
    vline(img, 9, 0, 15, "shadow")
    for y in (3, 12):
        rect(img, 4, y, 8, 2, "concrete_dark")
        hline(img, 4, 11, y, "metal")
        put(img, 4, y, "concrete_light")
        put(img, 11, y, "shadow")
        put(img, 7, y + 1, "rust")
    # Grime at joints.
    for x, y in ((8, 4), (9, 5), (7, 13), (9, 13), (6, 7)):
        put(img, x, y, "rust")
    return img


# ---------------------------------------------------------------------------
# CHARACTER (D-class, orange jumpsuit)
# ---------------------------------------------------------------------------
def draw_character(direction: str, frame: int) -> Image.Image:
    img = blank()

    def down_up(is_down: bool) -> None:
        # Six-row head; the body gets one more row than the first pass so the
        # character stops reading as a head on a stub.
        head_rows = [(1, 5, 10), (2, 4, 11), (3, 4, 11), (4, 4, 11),
                     (5, 4, 11), (6, 5, 10)]
        for y, x0, x1 in head_rows:
            hline(img, x0, x1, y, "bone")
        if is_down:
            # Fringe and temples.
            hline(img, 5, 10, 1, "shadow")
            hline(img, 4, 11, 2, "shadow")
            hline(img, 4, 11, 3, "shadow")
            put(img, 5, 2, "wall_dark")
            put(img, 6, 2, "wall_dark")
            put(img, 9, 2, "concrete_dark")
            for y in (4, 5):
                put(img, 4, y, "shadow")
                put(img, 11, y, "shadow")
            # Eyes and a small mouth.
            put(img, 6, 5, "ink")
            put(img, 9, 5, "ink")
            put(img, 7, 6, "skin_shadow")
            put(img, 8, 6, "skin_shadow")
            put(img, 5, 6, "skin_shadow")
            put(img, 10, 6, "skin_shadow")
        else:
            # Back of the head, with a crown light and a visible neck.
            hline(img, 5, 10, 1, "shadow")
            hline(img, 4, 11, 2, "shadow")
            hline(img, 5, 10, 3, "wall_dark")
            hline(img, 4, 11, 4, "shadow")
            hline(img, 5, 10, 5, "shadow")
            hline(img, 6, 9, 6, "shadow")
            put(img, 7, 6, "skin_shadow")
            put(img, 8, 6, "skin_shadow")
            put(img, 7, 3, "concrete_dark")
            put(img, 8, 4, "wall_dark")
            put(img, 5, 3, "concrete_dark")

        # Collar and shoulders.
        hline(img, 5, 10, 7, "rust")
        hline(img, 3, 12, 7, "orange")
        put(img, 6, 7, "wall_dark")
        put(img, 9, 7, "wall_dark")

        # Torso: 8 px of visible chest, with 2 px arms stepped out below the
        # shoulder. The dark-orange side seams keep the arms from merging.
        for y in range(8, 11):
            hline(img, 4, 11, y, "orange")
            hline(img, 2, 3, y, "orange")
            hline(img, 12, 13, y, "orange")
            put(img, 4, y, "rust")
            put(img, 11, y, "rust")
            put(img, 2, y, "orange_light" if y == 8 else "orange")
            put(img, 13, y, "rust")
        # Suit seam and chest label.
        vline(img, 8, 8, 10, "rust")
        put(img, 6, 8, "bone")
        put(img, 6, 9, "concrete_light")
        # Waist / belt.
        hline(img, 4, 11, 11, "rust")
        put(img, 7, 11, "metal")
        put(img, 8, 11, "metal")

        # Hands. The second frame swings them by one pixel.
        left_hand_y = 11 if frame == 0 else 10
        right_hand_y = 10 if frame == 0 else 11
        put(img, 2, left_hand_y, "bone")
        put(img, 3, left_hand_y, "skin_shadow")
        put(img, 13, right_hand_y, "bone")
        put(img, 12, right_hand_y, "skin_shadow")

        # Legs. The step frame has a clear lift and a wider stance.
        if frame == 0:
            left_x, right_x = 4, 9
            left_boot_y = right_boot_y = 14
        else:
            left_x, right_x = 3, 10
            left_boot_y = 14
            right_boot_y = 13
        for x0 in (left_x, right_x):
            rect(img, x0, 12, 3, 2, "orange")
            put(img, x0, 12, "orange_light")
            put(img, x0 + 2, 12, "rust")
            put(img, x0 + 1, 13, "rust")
        hline(img, left_x, left_x + 2, left_boot_y, "shadow")
        hline(img, right_x, right_x + 2, right_boot_y, "shadow")
        put(img, left_x, left_boot_y, "ink")
        put(img, right_x, right_boot_y, "ink")

    def side() -> None:
        # Profile head, facing right. The left frame is mirrored later.
        head_rows = [(1, 5, 9), (2, 4, 10), (3, 4, 10), (4, 4, 10),
                     (5, 4, 10), (6, 5, 10)]
        for y, x0, x1 in head_rows:
            hline(img, x0, x1, y, "bone")
        # Hair covers the back half.
        hline(img, 5, 9, 1, "shadow")
        hline(img, 4, 10, 2, "shadow")
        hline(img, 4, 10, 3, "shadow")
        for y in (4, 5):
            put(img, 4, y, "shadow")
            put(img, 5, y, "shadow")
        put(img, 4, 6, "shadow")
        put(img, 5, 6, "shadow")
        put(img, 5, 2, "wall_dark")
        put(img, 6, 2, "wall_dark")
        # Face: brow, eye, nose, lip, ear.
        put(img, 8, 4, "skin_shadow")
        put(img, 9, 5, "ink")
        put(img, 10, 4, "bone")
        put(img, 11, 5, "bone")
        put(img, 12, 5, "skin_shadow")  # protruding nose
        put(img, 10, 6, "skin_shadow")
        put(img, 7, 5, "skin_shadow")
        put(img, 6, 6, "skin_shadow")

        # Collar.
        hline(img, 6, 10, 7, "rust")

        # Slim profile torso: 6 px deep, with the near arm on the front edge.
        for y in range(8, 11):
            hline(img, 5, 10, y, "orange")
        for y in range(8, 11):
            put(img, 5, y, "rust")
            put(img, 10, y, "orange_light")
        vline(img, 8, 8, 10, "rust")
        put(img, 9, 8, "bone")
        hline(img, 6, 9, 11, "rust")
        put(img, 8, 11, "metal")

        # Near arm, hanging over the chest; the far arm is a single back pixel.
        if frame == 0:
            rect(img, 11, 8, 2, 3, "orange")
            put(img, 11, 8, "orange_light")
            put(img, 12, 11, "bone")
            put(img, 11, 11, "skin_shadow")
        else:
            rect(img, 11, 8, 2, 2, "orange")
            put(img, 11, 8, "orange_light")
            put(img, 12, 10, "bone")
            put(img, 11, 10, "skin_shadow")
        put(img, 4, 9, "orange")

        # Legs: contact vs. passing pose.
        if frame == 0:
            back_x, front_x = 4, 8
            back_boot_y, front_boot_y = 14, 14
        else:
            back_x, front_x = 3, 9
            back_boot_y, front_boot_y = 13, 14
        for x0 in (back_x, front_x):
            rect(img, x0, 12, 3, 2, "orange")
            put(img, x0, 12, "orange_light")
            put(img, x0 + 2, 12, "rust")
            put(img, x0 + 1, 13, "rust")
        hline(img, back_x, back_x + 2, back_boot_y, "shadow")
        hline(img, front_x, front_x + 2, front_boot_y, "shadow")
        put(img, back_x, back_boot_y, "ink")
        put(img, front_x, front_boot_y, "ink")

    if direction == "down":
        down_up(True)
    elif direction == "up":
        down_up(False)
    else:
        side()
        if direction == "left":
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    # Auto one-pixel dark silhouette. This is what makes small sprites read.
    src = img.copy()
    for y in range(TILE):
        for x in range(TILE):
            if src.getpixel((x, y))[3] != 0:
                continue
            neighbours = ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if any(0 <= nx < TILE and 0 <= ny < TILE and src.getpixel((nx, ny))[3] != 0 for nx, ny in neighbours):
                put(img, x, y, "ink")
    return img


# ---------------------------------------------------------------------------
# BUILD / VALIDATION / SAVING
# ---------------------------------------------------------------------------
TILE_BUILDERS = [
    ("floor_concrete_a", "FLOOR  /  CONCRETE A", tile_floor_a),
    ("floor_concrete_b", "FLOOR  /  WORN B", tile_floor_b),
    ("floor_concrete_c", "FLOOR  /  CONCRETE C", tile_floor_c),
    ("floor_grate", "FLOOR  /  DRAIN GRATE", tile_grate),
    ("floor_blood", "FLOOR  /  BLOOD", tile_blood),
    ("floor_debris", "FLOOR  /  DEBRIS", tile_debris),
    ("floor_hazard", "FLOOR  /  CAUTION", tile_hazard),
    ("wall", "WALL  /  SEGMENT", tile_wall),
    ("wall_corner", "WALL  /  CORNER", tile_wall_corner),
    ("door_frame", "WALL  /  DOOR FRAME", tile_door),
    ("keycard_reader", "WALL  /  CARD READER", tile_keycard),
    ("vent", "WALL  /  VENT", tile_vent),
    ("ceiling_light", "CEILING  /  LIGHT", tile_light),
    ("wall_pipe", "WALL  /  PIPE", tile_pipe),
]
CHAR_DIRS = ("down", "up", "left", "right")


def make_tiles() -> dict[str, Image.Image]:
    return {name: builder() for name, _label, builder in TILE_BUILDERS}


def make_characters() -> dict[tuple[str, int], Image.Image]:
    return {(d, f): draw_character(d, f) for d in CHAR_DIRS for f in (0, 1)}


def validate(images: dict[str, Image.Image]) -> None:
    bad: dict[str, set[tuple[int, int, int]]] = {}
    for name, img in images.items():
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = img.getpixel((x, y))
                if a not in (0, 255):
                    bad.setdefault(name, set()).add((r, g, b))
                elif a == 255 and (r, g, b) not in PALETTE_SET:
                    bad.setdefault(name, set()).add((r, g, b))
    if bad:
        raise ValueError(f"off-palette pixels: {bad}")
    print(f"[ok] palette check: {len(images)} images, every opaque pixel is in the 16 colours")


def upscale(img: Image.Image, scale: int = SCALE) -> Image.Image:
    return img.resize((img.width * scale, img.height * scale), Image.Resampling.NEAREST)


def text_bitmap(text: str, color: str, scale: int = 2) -> Image.Image:
    """Default Pillow font, thresholded to hard pixels, then nearest-scaled."""
    tmp = Image.new("L", (max(1, len(text) * 12), 20), 0)
    ImageDraw.Draw(tmp).text((0, 0), text, font=FONT, fill=255)
    bbox = tmp.getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), TRANSPARENT)
    tmp = tmp.crop(bbox)
    tmp = tmp.point(lambda v: 255 if v >= 120 else 0)
    tile = Image.new("RGBA", tmp.size, rgba(color))
    tile.putalpha(tmp)
    if scale > 1:
        tile = tile.resize((tile.width * scale, tile.height * scale), Image.Resampling.NEAREST)
    return tile


def paste_text(dst: Image.Image, xy: tuple[int, int], text: str, color: str, scale: int = 2, center: bool = False) -> None:
    glyphs = text_bitmap(text, color, scale)
    x, y = xy
    if center:
        x -= glyphs.width // 2
    dst.alpha_composite(glyphs, (x, y))


def contact_sheet(tiles: dict[str, Image.Image], chars: dict[tuple[str, int], Image.Image]) -> Image.Image:
    margin = 48
    gap = 8
    cols = len(TILE_BUILDERS)
    cell_w = 108
    grid_w = cols * cell_w + (cols - 1) * gap
    width = grid_w + margin * 2
    tile_rows = (len(TILE_BUILDERS) + cols - 1) // cols

    # Vertical layout.
    top = 30
    title_h = 32
    rule_y = top + title_h + 10
    tiles_heading_y = rule_y + 20
    tiles_y = tiles_heading_y + 30
    tile_row_h = 112
    char_heading_y = tiles_y + tile_rows * tile_row_h + 8
    char_y = char_heading_y + 30
    palette_heading_y = char_y + 112
    palette_y = palette_heading_y + 28
    height = palette_y + 64 + 34

    img = Image.new("RGBA", (width, height), rgba("ink"))
    d = ImageDraw.Draw(img)

    # Header.
    paste_text(img, (margin, top), "SCP FACILITY / PIXEL ASSET PROBE", "bone", 3)
    paste_text(img, (margin, top + 34), "16x16 TILES + D-CLASS SPRITES / FIXED 16-COLOUR PALETTE / 4x NEAREST", "concrete_light", 1)
    d.line((margin, rule_y, width - margin, rule_y), fill=rgba("concrete_dark"), width=1)
    d.line((margin, rule_y + 1, width - margin, rule_y + 1), fill=rgba("shadow"), width=1)

    # Section 1: all tiles in one row.
    paste_text(img, (margin, tiles_heading_y), f"TILESET  /  {len(tiles)} TILES  /  16x16  /  4x", "orange", 2)
    for i, (name, label, _fn) in enumerate(TILE_BUILDERS):
        row = i // cols
        col = i % cols
        x = margin + col * (cell_w + gap)
        y = tiles_y + row * tile_row_h
        panel = Image.new("RGBA", (cell_w, 96), rgba("shadow"))
        pd = ImageDraw.Draw(panel)
        pd.rectangle((0, 0, cell_w - 1, 95), outline=rgba("wall_dark"), width=1)
        pd.line((1, 1, cell_w - 2, 1), fill=rgba("concrete_dark"))
        panel.alpha_composite(upscale(tiles[name]), ((cell_w - 64) // 2, 6))
        img.alpha_composite(panel, (x, y))
        paste_text(img, (x + cell_w // 2, y + 76), label, "bone", 1, center=True)

    # Section 2: eight character cells, centred as one row.
    paste_text(
        img,
        (margin, char_heading_y),
        "D-CLASS  /  4 DIRECTIONS  /  2 FRAMES  /  16x16  /  4x",
        "orange",
        2,
    )
    char_cell_w = 126
    char_gap = 8
    char_total = 8 * char_cell_w + 7 * char_gap
    char_x0 = (width - char_total) // 2
    labels = {
        ("down", 0): "DOWN  F0",
        ("down", 1): "DOWN  F1",
        ("up", 0): "UP  F0",
        ("up", 1): "UP  F1",
        ("left", 0): "LEFT  F0",
        ("left", 1): "LEFT  F1",
        ("right", 0): "RIGHT  F0",
        ("right", 1): "RIGHT  F1",
    }
    for i, direction in enumerate(CHAR_DIRS):
        for f in (0, 1):
            idx = i * 2 + f
            x = char_x0 + idx * (char_cell_w + char_gap)
            canvas = Image.new("RGBA", (char_cell_w, 96), rgba("concrete_dark"))
            cd = ImageDraw.Draw(canvas)
            cd.rectangle((0, 0, char_cell_w - 1, 95), outline=rgba("wall_dark"), width=1)
            canvas.alpha_composite(upscale(chars[(direction, f)]), ((char_cell_w - 64) // 2, 6))
            img.alpha_composite(canvas, (x, char_y))
            paste_text(img, (x + char_cell_w // 2, char_y + 70), labels[(direction, f)], "bone", 2, center=True)

    # Section 3. Palette strip.
    paste_text(img, (margin, palette_heading_y), "FIXED PALETTE  /  HEX VALUES IN palette.json", "orange", 2)
    swatch_w = 52
    swatch_gap = 6
    total = len(PALETTE) * swatch_w + (len(PALETTE) - 1) * swatch_gap
    sx = (width - total) // 2
    for i, (name, hex_value) in enumerate(PALETTE):
        x = sx + i * (swatch_w + swatch_gap)
        d.rectangle((x, palette_y, x + swatch_w - 1, palette_y + 26), fill=rgba(name))
        d.rectangle((x, palette_y, x + swatch_w - 1, palette_y + 26), outline=rgba("concrete_dark"))
        paste_text(img, (x + swatch_w // 2, palette_y + 30), hex_value.upper(), "concrete_light", 1, center=True)

    # Footer.
    paste_text(
        img,
        (width // 2, height - 22),
        "GENERATED BY gen_tiles.py  /  PILLOW  /  NO EXTERNAL ASSETS",
        "concrete_dark",
        1,
        center=True,
    )
    return img


def add_dither_light(scene: Image.Image, cx: int, cy: int, rx: int, ry: int) -> None:
    """Scene-only fluorescent pool. A single smooth, hash-dithered falloff;
    hard threshold bands made the first version look like a radar sweep."""
    for y in range(scene.height):
        for x in range(scene.width):
            dx = (x - cx) / rx
            dy = (y - cy) / ry
            dist = math.sqrt(dx * dx + dy * dy)
            if dist >= 1.0:
                continue
            r, g, b, a = scene.getpixel((x, y))
            if a == 0 or (r, g, b) not in {
                PALETTE_RGB["concrete"],
                PALETTE_RGB["concrete_dark"],
                PALETTE_RGB["concrete_light"],
            }:
                continue
            power = (1.0 - dist) ** 2.0
            n = ((x * 73856093) ^ (y * 19349663) ^ (cx * 83492791)) & 0xFFFFFFFF
            n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
            n ^= n >> 16
            h = (n & 0xFFFF) / 65535.0
            if h < 0.18 * power:
                scene.putpixel((x, y), rgba("concrete_light"))
            elif h > 0.9985 and power > 0.30:
                scene.putpixel((x, y), rgba("metal"))


def add_room_shadow(scene: Image.Image) -> None:
    """A thin dithered contact shadow where floor meets the wall ring."""
    for x in range(1, 19):
        if x % 2 == 0:
            scene.putpixel((x, 1), rgba("shadow"))
        if x % 3 == 0:
            scene.putpixel((x, 2), rgba("shadow"))
    for y in range(1, 11):
        if y % 2 == 0:
            scene.putpixel((1, y), rgba("shadow"))
        if y % 3 == 0:
            scene.putpixel((2, y), rgba("shadow"))
        if y % 2 == 1:
            scene.putpixel((18, y), rgba("shadow"))
        if y % 3 == 0:
            scene.putpixel((17, y), rgba("shadow"))


def _floor_px(scene: Image.Image, x: int, y: int) -> bool:
    if not (16 <= x < 304 and 16 <= y < 176):
        return False
    r, g, b, a = scene.getpixel((x, y))
    return (r, g, b) in {
        PALETTE_RGB["concrete"],
        PALETTE_RGB["concrete_dark"],
        PALETTE_RGB["concrete_light"],
        PALETTE_RGB["metal"],
    }


def add_floor_grunge(scene: Image.Image) -> None:
    """A small scene-level decal pass. This is deliberately not part of the
    tileset: it proves how much of the 'assembled' look comes from large-scale
    grime and decals rather than from 16 px tiles."""
    stains = [
        (34, 104, 25, 9),
        (226, 139, 33, 10),
        (168, 30, 20, 8),
        (68, 150, 22, 7),
        (246, 80, 17, 7),
    ]
    for sx, sy, sw, sh in stains:
        for yy in range(sh):
            for xx in range(sw):
                if ((xx - sw / 2) ** 2) / ((sw / 2) ** 2) + ((yy - sh / 2) ** 2) / ((sh / 2) ** 2) > 1:
                    continue
                if (xx * 7 + yy * 11 + sx) % 5 > 1:
                    continue
                x, y = sx + xx, sy + yy
                if _floor_px(scene, x, y):
                    scene.putpixel((x, y), rgba("concrete_dark"))

    cracks = [
        [(28, 168), (36, 160), (42, 162), (50, 151), (60, 147)],
        [(282, 91), (274, 99), (276, 108), (266, 116), (264, 128)],
    ]
    for pts in cracks:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            steps = max(abs(x1 - x0), abs(y1 - y0))
            for k in range(steps + 1):
                x = round(x0 + (x1 - x0) * k / max(1, steps))
                y = round(y0 + (y1 - y0) * k / max(1, steps))
                if _floor_px(scene, x, y):
                    scene.putpixel((x, y), rgba("concrete_dark"))
                if i == 0 and k % 4 == 2 and _floor_px(scene, x, y - 1):
                    scene.putpixel((x, y - 1), rgba("concrete_light"))

    for x, y, w in ((118, 143, 5), (196, 83, 4), (46, 38, 4), (280, 160, 6)):
        for k in range(w):
            if _floor_px(scene, x + k, y):
                scene.putpixel((x + k, y), rgba("concrete_light"))


def add_contact_shadow(scene: Image.Image, x: int, y: int, w: int = 11, h: int = 3) -> None:
    """Sparse, palette-only contact shadow under the character."""
    for yy in range(h):
        span = w - abs(yy - (h - 1) // 2) * 2
        for xx in range(max(1, span)):
            if (xx + yy) % 3 == 0:
                continue
            sx = x + (w - span) // 2 + xx
            sy = y + yy
            if 0 <= sx < scene.width and 0 <= sy < scene.height:
                scene.putpixel((sx, sy), rgba("shadow"))


def preview_scene(tiles: dict[str, Image.Image], chars: dict[tuple[str, int], Image.Image]) -> Image.Image:
    cols, rows = 20, 12
    scene = Image.new("RGBA", (cols * TILE, rows * TILE), rgba("ink"))

    # Floor. Use the plain C pour in the scene: repeated chips reveal the
    # 16 px grid immediately. Variants live in the tileset for decoration.
    for y in range(1, 11):
        for x in range(1, 19):
            scene.alpha_composite(tiles["floor_concrete_c"], (x * TILE, y * TILE))

    # Light pools on the floor, then room/mood shadows, then props.
    for lx, ly in ((4, 3), (14, 3)):
        add_dither_light(scene, lx * TILE + 8, ly * TILE + 8, 44, 30)
    add_room_shadow(scene)
    add_floor_grunge(scene)

    # Special floor patches.
    special = {
        (9, 1): "floor_hazard",
        (8, 2): "floor_blood",
        (3, 8): "floor_grate",
        (16, 9): "floor_grate",
        (5, 9): "floor_debris",
        (14, 5): "floor_debris",
    }
    for (x, y), key in special.items():
        scene.alpha_composite(tiles[key], (x * TILE, y * TILE))

    def rot(tile: Image.Image, angle: int) -> Image.Image:
        return tile.rotate(angle, expand=False, resample=Image.Resampling.NEAREST)

    wall = tiles["wall"]
    corner = tiles["wall_corner"]
    # Top and bottom walls.
    for x in range(cols):
        if x == 0:
            scene.alpha_composite(corner, (x * TILE, 0))
        elif x == cols - 1:
            scene.alpha_composite(rot(corner, 90), (x * TILE, 0))
        else:
            scene.alpha_composite(wall, (x * TILE, 0))
    for x in range(cols):
        if x == 0:
            scene.alpha_composite(rot(corner, 270), (x * TILE, 11 * TILE))
        elif x == cols - 1:
            scene.alpha_composite(rot(corner, 180), (x * TILE, 11 * TILE))
        else:
            scene.alpha_composite(rot(wall, 180), (x * TILE, 11 * TILE))
    # Side walls: rotate so the lit top edge faces outward.
    for y in range(1, 11):
        scene.alpha_composite(rot(wall, 270), (0, y * TILE))
        scene.alpha_composite(rot(wall, 90), (19 * TILE, y * TILE))

    # Wall features / opening.
    scene.alpha_composite(tiles["vent"], (4 * TILE, 0))
    scene.alpha_composite(rot(tiles["wall_pipe"], 90), (14 * TILE, 0))
    scene.alpha_composite(tiles["door_frame"], (9 * TILE, 0))
    scene.alpha_composite(tiles["keycard_reader"], (10 * TILE, 0))

    # Ceiling fixtures; they live on a layer above the floor.
    for lx, ly in ((4, 3), (14, 3)):
        add_contact_shadow(scene, lx * TILE + 3, ly * TILE + 10, 11, 2)
        scene.alpha_composite(tiles["ceiling_light"], (lx * TILE, ly * TILE))

    # Character, dead centre, facing down.
    cx = 9 * TILE + 4
    cy = 6 * TILE + 0
    add_contact_shadow(scene, cx + 1, cy + 14, 11, 2)
    scene.alpha_composite(chars[("down", 0)], (cx, cy))

    out = scene.resize((cols * TILE * SCALE, rows * TILE * SCALE), Image.Resampling.NEAREST)
    return out


def save_outputs() -> dict[str, Path]:
    tiles = make_tiles()
    chars = make_characters()

    tile_dir = ROOT / "tiles"
    sprite_dir = ROOT / "sprites"
    tile_dir.mkdir(exist_ok=True)
    sprite_dir.mkdir(exist_ok=True)

    palette_doc = {
        "name": "SCP Facility 16",
        "count": len(PALETTE),
        "colors": [
            {"index": i, "name": name, "hex": hex_value.upper()}
            for i, (name, hex_value) in enumerate(PALETTE)
        ],
    }
    palette_path = ROOT / "palette.json"
    palette_path.write_text(json.dumps(palette_doc, indent=2) + "\n", encoding="utf-8")

    for name, img in tiles.items():
        img.save(tile_dir / f"{name}.png")
    for (direction, f), img in chars.items():
        img.save(sprite_dir / f"dclass_{direction}_{f}.png")

    sheet = contact_sheet(tiles, chars)
    sheet_path = ROOT / "contact_sheet.png"
    sheet.save(sheet_path)

    scene = preview_scene(tiles, chars)
    scene_path = ROOT / "preview_scene.png"
    scene.save(scene_path)

    # Validate every asset and the two composites. Label rendering is thresholded,
    # so the sheets must also be palette-clean.
    all_images = {f"tile:{k}": v for k, v in tiles.items()}
    all_images.update({f"char:{d}:{f}": v for (d, f), v in chars.items()})
    all_images["contact_sheet"] = sheet
    all_images["preview_scene"] = scene
    validate(all_images)

    print(f"[ok] palette.json       {palette_path}")
    print(f"[ok] contact_sheet.png  {sheet.width}x{sheet.height}")
    print(f"[ok] preview_scene.png  {scene.width}x{scene.height}")
    print(f"[ok] {len(tiles)} tiles, {len(chars)} character frames")
    return {
        "palette": palette_path,
        "sheet": sheet_path,
        "scene": scene_path,
    }


def main() -> None:
    start = time.perf_counter()
    paths = save_outputs()
    elapsed = time.perf_counter() - start
    print(f"[done] all assets generated in {elapsed:.3f}s")
    for key, path in paths.items():
        print(f"  {key:8s} {path}")


if __name__ == "__main__":
    main()
