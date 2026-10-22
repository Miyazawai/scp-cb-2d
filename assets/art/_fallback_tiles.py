"""Fallback tileset for the vertical slice.

Hand-composed (not noise-driven): every tile is built from an explicit
structure -- joints, bevels, panel seams, deliberate wear marks -- so it reads
as designed pixel art rather than generated mush. If the dedicated tileset pass
lands later and overwrites these files, that is fine.
"""
import os
import random
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "tiles")

PAL = {
    "0": (0, 0, 0, 0),
    "1": (0x07, 0x09, 0x0b, 255),
    "2": (0x12, 0x16, 0x1a, 255),
    "3": (0x1b, 0x20, 0x26, 255),
    "4": (0x26, 0x2d, 0x34, 255),
    "5": (0x33, 0x3c, 0x45, 255),
    "6": (0x45, 0x50, 0x5b, 255),
    "7": (0x5d, 0x6a, 0x76, 255),
    "8": (0x2b, 0x3a, 0x33, 255),
    "9": (0x3a, 0x51, 0x48, 255),
    "a": (0x4d, 0x6b, 0x5c, 255),
    "b": (0x6b, 0x1f, 0x1f, 255),
    "c": (0xa3, 0x2a, 0x2a, 255),
    "d": (0x8a, 0x64, 0x20, 255),
    "e": (0xc9, 0x9a, 0x3f, 255),
    "f": (0xf0, 0xc7, 0x6b, 255),
    "g": (0xc4, 0x69, 0x2a, 255),
    "h": (0xe0, 0x8a, 0x3c, 255),
    "i": (0x7a, 0x3f, 0x18, 255),
    "j": (0xc9, 0xa0, 0x7a, 255),
    "k": (0xe8, 0xe2, 0xd6, 255),
    "l": (0x9a, 0xa5, 0xad, 255),
    "m": (0x6a, 0x75, 0x7d, 255),
    "n": (0x3c, 0x44, 0x4b, 255),
    "o": (0x1f, 0x4b, 0x6b, 255),
    "p": (0x2f, 0x7f, 0xb8, 255),
}


def blank(w, h, ch="0"):
    return [[ch] * w for _ in range(h)]


def render(rows, name, w=None, h=None):
    h = len(rows)
    w = len(rows[0])
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = PAL[rows[y][x]]
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name))


def floor(seed, crack=False, stain=False):
    rng = random.Random(seed)
    rows = blank(16, 16, "4")
    for y in range(16):
        for x in range(16):
            if x == 0 or y == 0:
                rows[y][x] = "3"
            elif x == 15 or y == 15:
                rows[y][x] = "3"
            elif rng.random() < 0.045:
                rows[y][x] = "5" if rng.random() < 0.5 else "3"
    # joint cross
    for x in range(1, 15):
        rows[8][x] = "3" if rows[8][x] != "2" else "2"
    for y in range(1, 15):
        rows[y][8] = "3" if rows[y][8] != "2" else "2"
    if crack:
        x = 3
        for y in range(1, 15):
            rows[y][x] = "2"
            if y % 3 == 0 and x < 12:
                x += 1
    if stain:
        cx, cy = 11, 5
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 8:
                    yy, xx = cy + dy, cx + dx
                    if 0 < yy < 15 and 0 < xx < 15:
                        rows[yy][xx] = "3"
    return rows


def wall_top():
    rng = random.Random(7)
    rows = blank(16, 16, "3")
    for y in range(16):
        for x in range(16):
            if y < 2:
                rows[y][x] = "4"
            elif y > 13:
                rows[y][x] = "2"
            elif rng.random() < 0.14:
                rows[y][x] = "4" if rng.random() < 0.7 else "2"
    # rivet row
    for x in (3, 12):
        rows[6][x] = "5"
        rows[6][x + 1] = "4"
        rows[7][x] = "2"
    return rows


def wall_face():
    rows = blank(16, 10, "5")
    for x in range(16):
        rows[0][x] = "6"
        rows[1][x] = "6"
        rows[8][x] = "4"
        rows[9][x] = "3"
    for y in range(2, 8):
        rows[y][0] = "4"
        rows[y][15] = "4"
    # panel seam down the middle-left, plus a rivet pair
    for y in range(2, 8):
        rows[y][5] = "4"
        rows[y][6] = "6"
    rows[4][2] = "7"
    rows[4][13] = "7"
    rows[5][2] = "4"
    rows[5][13] = "4"
    return rows


def wall_shadow():
    rows = blank(16, 8, "0")
    for y in range(8):
        a = 1.0 - (y / 8.0)
        if a <= 0.02:
            continue
        for x in range(16):
            v = a * (0.85 + 0.15 * ((x * 7 + y * 3) % 5) / 4.0)
            img_val = int(255 * min(1.0, v))
            rows[y][x] = "1" if img_val > 120 else ("2" if img_val > 40 else "0")
    return rows


def ceiling_lamp():
    rows = blank(16, 8, "0")
    for x in range(1, 15):
        rows[0][x] = "2"
        rows[7][x] = "2"
    for y in range(1, 7):
        rows[y][1] = "2"
        rows[y][14] = "2"
    for y in range(2, 6):
        for x in range(3, 13):
            rows[y][x] = "e" if 3 < y < 5 else "d"
    for x in range(4, 12):
        rows[3][x] = "k"
    return rows


def door_panel():
    rows = blank(16, 16, "d")
    for x in range(16):
        rows[0][x] = "3"
        rows[15][x] = "3"
    for y in range(16):
        rows[y][0] = "3"
        rows[y][15] = "3"
    # horizontal reinforcement ribs
    for y in (4, 5, 10, 11):
        for x in range(1, 15):
            rows[y][x] = "e" if y in (4, 10) else "i"
    # bright vertical seam in the middle
    for y in range(1, 15):
        rows[y][7] = "f"
        rows[y][8] = "e"
    # rivets
    for y in (2, 13):
        for x in (2, 13):
            rows[y][x] = "e"
    return rows


def door_frame():
    rows = blank(16, 16, "0")
    for x in range(16):
        rows[0][x] = "m"
        rows[1][x] = "n"
    for y in range(16):
        rows[y][0] = "m"
        rows[y][1] = "n"
        rows[y][14] = "n"
        rows[y][15] = "m"
    for x in range(16):
        rows[14][x] = "n"
        rows[15][x] = "1"
    return rows


def crate():
    rows = blank(16, 16, "i")
    for x in range(16):
        rows[0][x] = "h"
        rows[1][x] = "i"
        rows[14][x] = "2"
        rows[15][x] = "1"
    for y in range(16):
        rows[y][0] = "h"
        rows[y][1] = "i"
        rows[y][14] = "2"
        rows[y][15] = "1"
    for i in range(2, 14):
        rows[i][i] = "d"
        rows[i][15 - i] = "d"
    for x in range(4, 12):
        rows[7][x] = "d"
    return rows


def locker():
    rows = blank(16, 16, "n")
    for x in range(16):
        rows[0][x] = "m"
        rows[15][x] = "2"
    for y in range(16):
        rows[y][0] = "m"
        rows[y][15] = "2"
    for y in range(2, 14):
        rows[y][7] = "2"
        rows[y][8] = "m"
    for y in (4, 10):
        rows[y][4] = "l"
        rows[y][11] = "l"
    return rows


def desk():
    w, h = 32, 16
    rows = blank(w, h, "5")
    for x in range(w):
        for y in (0, 1):
            rows[y][x] = "6"
        for y in (13, 14):
            rows[y][x] = "3"
        rows[15][x] = "2"
    for y in range(h):
        rows[y][0] = "6"
        rows[y][w - 1] = "3"
    for y in range(3, 12):
        rows[y][8] = "4"
        rows[y][16] = "4"
        rows[y][24] = "4"
    for x in range(9, 16):
        rows[6][x] = "4"
    for x in range(18, 22):
        rows[9][x] = "o"
        rows[10][x] = "p"
    return rows


def terminal():
    rows = blank(16, 16, "0")
    for y in range(2, 12):
        for x in range(2, 14):
            rows[y][x] = "2"
    for y in range(3, 11):
        for x in range(3, 13):
            rows[y][x] = "o"
    for x in range(4, 12, 2):
        rows[5][x] = "p"
        rows[7][x] = "p"
    rows[6][5] = "k"
    for x in range(5, 11):
        rows[13][x] = "4"
        rows[14][x] = "3"
    return rows


def save_terminal():
    rows = terminal()
    for x in range(4, 12, 2):
        rows[9][x] = "k"
    rows[1][13] = "k"
    return rows


def blood():
    rng = random.Random(3)
    rows = blank(32, 32, "0")
    cx, cy = 16, 16
    for dy in range(-11, 12):
        for dx in range(-14, 15):
            d = (dx * dx) / (13.0 * 13.0) + (dy * dy) / (9.0 * 9.0)
            if d < 1.0 and rng.random() < 0.85 - d * 0.35:
                rows[cy + dy][cx + dx] = "b" if rng.random() < 0.9 else "i"
    return rows


def bodybag():
    w, h = 24, 12
    rows = blank(w, h, "0")
    for y in range(2, 10):
        for x in range(1, 23):
            rows[y][x] = "1" if y < 3 or y > 8 else "2"
    for x in range(4, 20, 3):
        rows[6][x] = "3"
    for x in range(2, 7):
        rows[5][x] = "3"
    return rows


def vent():
    rows = blank(16, 16, "3")
    for y in range(2, 14):
        for x in range(2, 14):
            rows[y][x] = "5" if y % 3 else "2"
    for x in range(2, 14):
        rows[2][x] = "6"
        rows[13][x] = "2"
    return rows


def keycard_reader():
    rows = blank(16, 16, "0")
    for y in range(4, 13):
        for x in range(4, 12):
            rows[y][x] = "n"
    for x in range(5, 11):
        rows[3][x] = "m"
    rows[6][6] = "p"
    rows[6][7] = "o"
    rows[9][6] = "2"
    rows[9][7] = "2"
    return rows


def hazard_sign():
    rows = blank(16, 16, "0")
    for y in range(1, 15):
        for x in range(1, 15):
            rows[y][x] = "e"
    for i in range(15):
        for k in range(2):
            yy = i
            xx = 3 + ((i + k) % 10)
            if 2 < yy < 14 and 2 < xx < 14:
                rows[yy][xx] = "2"
    rows[7][7] = "2"
    rows[8][8] = "2"
    return rows


def debris():
    rng = random.Random(11)
    rows = blank(16, 16, "0")
    for _ in range(14):
        x, y = rng.randint(2, 13), rng.randint(2, 13)
        rows[y][x] = "4"
        if rng.random() < 0.5:
            rows[y][x + 1 if x < 14 else x] = "3"
    return rows


def chair():
    rows = blank(16, 16, "0")
    for y in range(5, 12):
        for x in range(5, 11):
            rows[y][x] = "5"
    for x in range(5, 11):
        rows[4][x] = "6"
    for y in range(12, 15):
        rows[y][7] = "3"
    return rows


def barrel():
    rows = blank(16, 16, "0")
    for y in range(1, 15):
        for x in range(2, 14):
            d = ((x - 7.5) ** 2) / 36.0 + ((y - 7.5) ** 2) / 49.0
            if d < 1.0:
                rows[y][x] = "m" if x < 8 else "n"
    for x in range(3, 13):
        rows[4][x] = "4"
        rows[11][x] = "4"
    rows[5][5] = "l"
    rows[6][5] = "l"
    return rows


def corpse():
    w, h = 24, 16
    rows = blank(w, h, "0")
    # torso
    for y in range(6, 11):
        for x in range(7, 17):
            rows[y][x] = "g" if y > 6 else "h"
    # head
    for y in range(4, 9):
        for x in range(17, 22):
            rows[y][x] = "j" if 5 < y < 8 else "i"
    # legs bent
    for x in range(2, 8):
        rows[8][x] = "g"
        rows[9][x] = "i"
    rows[10][3] = "g"
    rows[10][4] = "g"
    # arm
    for x in range(10, 16):
        rows[11][x] = "h"
    # blood pool
    for x in range(6, 20):
        rows[12][x] = "b"
        rows[13][x] = "b"
    rows[13][8] = "c"
    return rows


def main():
    render(floor(1), "floor_concrete_a.png")
    render(floor(2, stain=True), "floor_concrete_b.png")
    render(floor(3, crack=True), "floor_concrete_c.png")
    render(wall_top(), "wall_top.png")
    render(wall_face(), "wall_face.png")
    render(wall_shadow(), "wall_shadow.png")
    render(ceiling_lamp(), "ceiling_lamp.png")
    render(door_panel(), "door_panel.png")
    render(door_frame(), "door_frame.png")
    render(crate(), "crate.png")
    render(locker(), "locker.png")
    render(desk(), "desk.png")
    render(terminal(), "terminal.png")
    render(save_terminal(), "save_terminal.png")
    render(blood(), "blood_splat.png")
    render(bodybag(), "bodybag.png")
    render(vent(), "vent.png")
    render(keycard_reader(), "keycard_reader.png")
    render(hazard_sign(), "hazard_sign.png")
    render(debris(), "floor_debris.png")
    render(chair(), "chair.png")
    render(barrel(), "barrel.png")
    render(corpse(), "corpse.png")
    print("wrote tiles to", OUT)


if __name__ == "__main__":
    main()
