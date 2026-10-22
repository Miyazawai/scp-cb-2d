#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SCP facility top-down environment art.

Every sprite is authored as literal 16/24/32-column pixel strings below.
The renderer only expands palette characters to RGBA pixels; it never
draws or morphs shapes with noise, gradients, or vector primitives.

Run:  python gen_tiles.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
TILE_DIR = ROOT / "tiles"
PREVIEW = ROOT / "tiles_preview.png"
MANIFEST = ROOT / "tiles_manifest.json"

PALETTE = {
    "0": (0, 0, 0, 0),
    "1": (7, 9, 11, 255),
    "2": (18, 22, 26, 255),
    "3": (27, 32, 38, 255),
    "4": (38, 45, 52, 255),
    "5": (51, 60, 69, 255),
    "6": (69, 80, 91, 255),
    "7": (93, 106, 118, 255),
    "8": (43, 58, 51, 255),
    "9": (58, 81, 72, 255),
    "a": (77, 107, 92, 255),
    "b": (107, 31, 31, 255),
    "c": (163, 42, 42, 255),
    "d": (138, 100, 32, 255),
    "e": (201, 154, 63, 255),
    "f": (240, 199, 107, 255),
    "g": (196, 105, 42, 255),
    "h": (224, 138, 60, 255),
    "i": (122, 63, 24, 255),
    "j": (201, 160, 122, 255),
    "k": (232, 226, 214, 255),
    "l": (154, 165, 173, 255),
    "m": (106, 117, 125, 255),
    "n": (60, 68, 75, 255),
    "o": (31, 75, 107, 255),
    "p": (47, 127, 184, 255),
}


# ---------------------------------------------------------------------------
# FLOORS (opaque)
# ---------------------------------------------------------------------------

FLOOR_CONCRETE_A = [
    "2222 2222 2222 2222",
    "2555 5555 5555 5443",
    "2455 5444 4444 4443",
    "2444 4444 5554 4443",
    "2444 4444 5554 4443",
    "2443 4444 4444 4443",
    "2444 5555 4444 4443",
    "2444 5555 4444 4443",
    "2444 4444 4444 4443",
    "2444 4444 4444 4443",
    "2444 4444 4333 4443",
    "2444 4444 4333 4443",
    "2444 4444 4444 4443",
    "2444 4444 4444 2223",
    "2444 4444 4444 2323",
    "2333 3333 3333 3333",
]

FLOOR_CONCRETE_B = [
    "2222 2222 2222 2222",
    "2544 4444 4444 4443",
    "2444 4444 4444 4443",
    "2444 4444 4444 4443",
    "2443 3222 2444 4443",
    "2443 2222 2444 4443",
    "2443 2223 3444 4443",
    "2444 3323 4444 4443",
    "2444 4333 4444 4443",
    "2444 4444 4444 4443",
    "2444 4444 4444 4443",
    "2444 4444 4455 4443",
    "2444 4444 4445 4443",
    "2444 4444 4444 4443",
    "2444 4444 4444 4443",
    "2333 3333 3333 3333",
]

FLOOR_CONCRETE_C = [
    "2222 2222 2222 2222",
    "2555 5555 5555 5443",
    "2444 4444 4544 4443",
    "2444 4444 4544 4443",
    "2444 4444 4445 4443",
    "2444 4444 4445 4443",
    "2444 4444 4444 4443",
    "2444 4444 4443 4443",
    "2444 4444 4443 4443",
    "2444 4444 4444 4443",
    "2444 4555 4444 4443",
    "2444 4555 4444 4443",
    "2444 4444 4444 4443",
    "2444 4444 4333 4443",
    "2444 4444 4444 4443",
    "2333 3333 3333 3333",
]

FLOOR_GRATE = [
    "7666 6666 6666 6665",
    "5755 5755 5755 5753",
    "5533 5533 5533 5533",
    "5511 5511 5511 5511",
    "6666 6666 6666 6665",
    "5755 5755 5755 5753",
    "5533 5533 5533 5533",
    "5511 5511 5511 5511",
    "6666 6666 6666 6665",
    "5755 5755 5755 5753",
    "5533 5533 5533 5533",
    "5511 5511 5511 5511",
    "6666 6666 6666 6665",
    "5755 5755 5755 5753",
    "5533 5533 5533 5533",
    "5511 5511 5511 5511",
]

FLOOR_HAZARD = [
    "3333 3333 3333 3333",
    "3fee 212f ee21 2fe3",
    "32fe e212 fee2 12e3",
    "322f ee22 1fee 2213",
    "3221 fee2 21fe e223",
    "3212 2fee 212f ee23",
    "3212 21fe e212 fee3",
    "3fee 212f ee21 2fe3",
    "32fe e212 fee2 12e3",
    "322f ee22 1fee 2213",
    "3221 fee2 21fe e223",
    "3212 2fee 212f ee23",
    "3212 21fe e212 fee3",
    "3fee 212f ee21 2fe3",
    "32fe e212 fee2 12e3",
    "3333 3333 3333 3333",
]

FLOOR_TILE = [
    "nnnn nnnn nnnn nnnn",
    "nkkk kkkm nkkk kkmn",
    "nkll lllm nkll llmn",
    "nkll lllm nkll llmn",
    "nkll lllm nkll llmn",
    "nkll lllm nkll llmn",
    "nkll lllm nkll llmn",
    "nkmm mmmn nkmm mmmn",
    "nnnn nn4n nnnn n4nn",
    "nkkk kkkm nkkk kkmn",
    "nkll lllm nkll llmn",
    "nkll ll3m nkll llmn",
    "nkll lllm nkll llmn",
    "nkll l3lm nkll ll3n",
    "nkll lllm nkll llmn",
    "nkmm mmmn nkmm mmmn",
]


# ---------------------------------------------------------------------------
# DECALS (transparent)
# ---------------------------------------------------------------------------

FLOOR_BLOOD = [
    "0000 0000 0000 0000",
    "0000 0000 0000 0000",
    "0c00 0000 0000 0000",
    "0b00 0000 000c 0000",
    "0b0b bbbb 00bc c000",
    "00bb cccc bccc bb00",
    "0bbc cccc cccc bbb0",
    "0bcc cc11 cccc cbb0",
    "0bcc c11c cccc cbb0",
    "00bc cccc cccc cb00",
    "000b cccc cccb b000",
    "0000 bccc ccbb 0000",
    "0000 0bbc cbb0 c000",
    "0000 000b c000 0000",
    "0000 0000 0000 0000",
    "0000 0000 0000 0000",
]

FLOOR_DEBRIS = [
    "0000 0000 0000 0000",
    "0000 0000 0000 0000",
    "0000 0000 0060 0000",
    "0000 0000 0676 0000",
    "0000 0000 0562 0000",
    "0000 0000 0352 0000",
    "0000 0000 0022 0000",
    "0000 0000 0000 0000",
    "0005 5500 0000 0000",
    "0057 6530 0000 k000",
    "0576 5530 00kk kk00",
    "0355 5320 0jkk kk00",
    "0023 2200 00jj jj00",
    "0000 0000 0002 2000",
    "00g0 0000 0000 0000",
    "0000 0000 0000 0000",
]

FLOOR_CRACK = [
    "0000 1000 0000 0000",
    "0000 1300 0000 0000",
    "0000 0100 0000 0000",
    "0000 0130 0000 0000",
    "0000 0010 0000 0000",
    "0000 0011 1300 0000",
    "0000 0001 0113 0000",
    "0000 0001 0001 1300",
    "0000 0000 1000 0113",
    "0000 0000 1300 0000",
    "0000 0011 0100 0000",
    "0000 1100 0100 0000",
    "0011 0000 0010 0000",
    "0000 0000 0011 0000",
    "0000 0000 0001 3000",
    "0000 0000 0001 0000",
]


# ---------------------------------------------------------------------------
# WALLS
# ---------------------------------------------------------------------------

WALL_TOP = [
    "2222 2222 2222 2222",
    "2666 6666 6666 6662",
    "2455 5555 5555 5542",
    "2457 5555 5557 5542",
    "2452 5555 5552 5542",
    "2444 4444 4444 4442",
    "2443 4444 4444 4442",
    "2444 4444 4444 4442",
    "2222 2222 2222 2222",
    "2666 6666 6666 6662",
    "2455 5555 5555 5542",
    "2457 5555 5557 5542",
    "2452 5555 5552 5542",
    "2444 4444 4434 4442",
    "2333 3333 3333 3332",
    "1111 1111 1111 1111",
]

WALL_FACE = [
    "7777 7777 7777 7777",
    "5555 5555 5555 5555",
    "5444 4254 4254 4445",
    "5474 4254 4254 7445",
    "5444 4254 4254 4445",
    "5444 4254 4254 4445",
    "5344 4254 4254 4435",
    "5474 4254 4254 7445",
    "5333 3333 3333 3335",
    "5222 2222 2222 2225",
]

WALL_SHADOW_MASK = [
    "0000 0000 0000 0000",
    "0001 1211 1121 1000",
    "0012 2322 2232 2100",
    "0123 4543 3454 3210",
    "1234 5655 5565 4321",
    "0123 4543 3454 3210",
    "0012 2322 2232 2100",
    "0001 1211 1121 1000",
]
SHADOW_ALPHA = {0: 0, 1: 24, 2: 48, 3: 78, 4: 112, 5: 150, 6: 185}


# ---------------------------------------------------------------------------
# DOORS / FIXTURES
# ---------------------------------------------------------------------------

DOOR_FRAME = [
    "6666 6666 6666 6666",
    "5555 555e f555 5555",
    "5777 7777 7777 7775",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2750 0000 0000 0572",
    "2570 0000 0000 0752",
    "2555 5555 5555 5552",
    "2222 2222 2222 2222",
]

DOOR_PANEL = [
    "1111 1111 1111 1111",
    "1333 3333 3333 3331",
    "13de eeef eeee ed31",
    "13de 7eef eee7 ed31",
    "13ii dddf dddd ii31",
    "13id eeef eeee di31",
    "13de eeef eeee ed31",
    "13de eeef eeee ed31",
    "13de eeef eeee ed31",
    "13de eeef eeee ed31",
    "13ii dddf dddd ii31",
    "13id eeef eeee di31",
    "13de 7eef eee7 ed31",
    "13de eeef eeee ed31",
    "1333 3333 3333 3331",
    "1111 1111 1111 1111",
]

DOOR_PANEL_OPEN = [
    "1111 1111 1111 1111",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f dddd ddi1",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f dddd ddi1",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f eeee eei1",
    "1222 212f iiii iii1",
    "1111 1111 1111 1111",
]


# ---------------------------------------------------------------------------
# PROPS
# ---------------------------------------------------------------------------

DESK = [
    "0222 2222 2222 2222 2222 2222 2222 2220",
    "0666 6666 6666 6666 6666 6666 6666 6660",
    "0554 4444 4444 4444 4444 4444 4444 4330",
    "0554 4kkk kkk4 4444 4444 4444 4444 4430",
    "0554 4k3k kkk4 4444 4444 4444 4444 4430",
    "0554 4jjj jjj4 4444 4444 4444 4444 4430",
    "0554 4444 4444 4445 4444 4444 4444 4330",
    "0554 4444 4444 4444 4444 4444 4444 4330",
    "0554 4444 4444 4444 4444 4444 4444 4330",
    "0554 4444 4444 4444 4444 4444 4444 4330",
    "0555 5555 5555 5555 5555 5555 5555 5550",
    "0233 3333 3333 3333 3255 5555 5555 5520",
    "0233 3333 3333 3333 3244 44ll l444 4420",
    "0122 2222 2222 2222 2144 4444 4444 4410",
    "0122 2222 2222 2222 2133 3333 3333 3310",
    "0011 1111 1111 1111 1111 1111 1111 1100",
]

CHAIR = [
    "0000 0000 0000 0000",
    "0001 1111 1111 1000",
    "0001 8888 8888 1000",
    "0001 8999 9998 1000",
    "0001 8aaa aa98 1000",
    "0251 9aaa aa98 1520",
    "0251 9aaa aa98 1520",
    "0251 8999 9998 1520",
    "0001 9aaa aa98 1000",
    "0001 8888 8888 1000",
    "0001 2222 2222 1000",
    "0000 0025 5200 0000",
    "0035 6522 2256 5300",
    "0025 2030 0302 5200",
    "0012 2222 2222 2100",
    "0000 0000 0000 0000",
]

LOCKER = [
    "0000 0000 0000 0000",
    "0222 2222 2222 2220",
    "0666 6666 6666 6660",
    "0544 4442 2444 4450",
    "0523 3324 2233 3250",
    "0521 1124 2211 1250",
    "0523 3324 2233 3250",
    "0521 1124 2211 1250",
    "0544 4442 2444 4450",
    "0266 6666 6666 6620",
    "0255 5552 2555 5520",
    "0255 7752 2775 5520",
    "025l 5552 2555 l520",
    "0233 3333 3333 3320",
    "0011 1111 1111 1100",
    "0000 0000 0000 0000",
]

CRATE = [
    "0000 0000 0000 0000",
    "0111 1111 1111 1110",
    "01j7 jjjj jjjj 7j10",
    "01jj gidd iggi dj10",
    "01jg jidd iggi dj10",
    "01jg gjdd iggi dj10",
    "01jg gijd iggi dj10",
    "01jg gidj iggi dj10",
    "01jg gidd jggi dj10",
    "01jg gidd ijgi dj10",
    "01jg gidd igji dj10",
    "01jg gidd iggj dj10",
    "01jg gidd iggi jj10",
    "01d7 dddd dddd 7d10",
    "0111 1111 1111 1110",
    "0000 0000 0000 0000",
]

BARREL = [
    "0000 0000 0000 0000",
    "0000 0011 1100 0000",
    "0000 1hhh hhh1 0000",
    "001h gggg gggg h100",
    "01hg 1ggg ggg1 gh10",
    "01hg 1ggg ggg1 gh10",
    "01hg 1g1d d1g1 gh10",
    "01hg 1g1e e1g1 gh10",
    "01hg 1g1e e1g1 gh10",
    "01hg 1g11 11g1 gh10",
    "01gh 1ggg ggg1 h110",
    "001g gggg gggi 1000",
    "0001 iiii iii1 0000",
    "0000 0011 1100 0000",
    "0000 0000 0000 0000",
    "0000 0000 0000 0000",
]

BODYBAG = [
    "0000 0000 0000 0000 0000 0000",
    "0000 0001 1111 1111 1000 0000",
    "0000 1133 3333 3333 3311 0000",
    "0013 3555 5555 5555 5553 3100",
    "0133 3333 3333 3333 3333 3310",
    "0133 2222 2222 2222 2222 3310",
    "013l lll3 3lll 33ll l33l 3310",
    "0133 2225 3222 5322 2532 2310",
    "0133 2223 3222 3322 2332 2310",
    "0013 3333 3333 3333 3333 3100",
    "0001 1111 1111 1111 1111 1000",
    "0000 0000 0000 0000 0000 0000",
]

CORPSE = [
    "0000 0000 0000 0000 0000 0000",
    "0000 0000 0000 0000 0000 0000",
    "0001 3310 1hhh hhhj 1000 0000",
    "0013 3331 hhhh hhhj 1000 0000",
    "001j jj31 hggg gggg 1hgg g221",
    "0012 j2j1 hggg ggii 1hgg g221",
    "0b01 jj10 gggg ggii 1ggg g221",
    "0bc0 0011 gggg giii 1hgg g221",
    "0000 0001 gggg giii 1ggg g221",
    "0000 0000 1ggg gggj 1000 0000",
    "0011 1111 1111 1111 1100 0000",
    "0000 0000 0000 0000 0000 0000",
]

TERMINAL = [
    "0000 0000 0000 0000",
    "0001 1111 1111 1000",
    "0016 6666 6666 6100",
    "0015 3222 2223 5100",
    "0015 22op po22 5100",
    "0015 2opp ppo2 5100",
    "0015 2ppp ppp2 5100",
    "0015 22op po22 5100",
    "0015 3333 3333 5100",
    "0016 6666 6666 6100",
    "0013 3333 3333 3100",
    "0001 1111 1111 1000",
    "0014 5555 5555 4100",
    "0014 5533 3555 4100",
    "0014 4444 4444 4100",
    "0001 1111 1111 1000",
]

SAVE_TERMINAL = [
    "0000 0000 0000 0000",
    "0000 1111 1111 0000",
    "0001 6666 66ak 1000",
    "0001 5111 1115 1000",
    "0001 51a9 99a5 1000",
    "0001 519a aaa5 1000",
    "0001 51a9 9aa5 1000",
    "0001 5111 1115 1000",
    "0001 5555 5555 1000",
    "0001 55aa aa55 1000",
    "0001 559a a955 1000",
    "0001 5l11 1115 1000",
    "0001 5555 5555 1000",
    "0002 2222 2222 2000",
    "0000 0000 0000 0000",
    "0000 0000 0000 0000",
]

KEYCARD_READER = [
    "0000 0000 0000 0000",
    "0000 6666 6666 0000",
    "0001 7555 5op7 2000",
    "0001 5222 2225 1000",
    "0001 52op 2225 1000",
    "0001 5222 2p25 1000",
    "0001 7333 3337 1000",
    "0001 5333 3335 1000",
    "0001 5636 3635 1000",
    "0001 5333 3335 1000",
    "0001 5636 3635 1000",
    "0001 5333 3335 1000",
    "0001 5l11 1115 1000",
    "0001 7555 5557 1000",
    "0000 5555 5555 0000",
    "0000 0000 0000 0000",
]

VENT = [
    "0000 0000 0000 0000",
    "0111 1111 1111 1110",
    "0175 5555 5555 5710",
    "0156 6666 6666 6510",
    "0151 1111 1111 1510",
    "0157 6666 6666 7510",
    "0151 1111 1111 1510",
    "0156 6666 6666 6510",
    "0151 1111 1111 1510",
    "0157 6666 6666 7510",
    "0151 1111 1111 1510",
    "0156 6666 6666 6510",
    "0151 1111 1111 1510",
    "0156 6666 6666 6510",
    "0122 2222 2222 2210",
    "0000 0000 0000 0000",
]

HAZARD_SIGN = [
    "0000 0000 0000 0000",
    "0000 0000 0000 0000",
    "0015 5555 5555 5100",
    "001l eeee eeee l100",
    "001e e4ee eeee d100",
    "001e eee1 1eee d100",
    "001e eee1 1eee d100",
    "001e eee1 1eee d100",
    "001e eee1 1eee d100",
    "001e eeee eeee d100",
    "001e eee1 1eee d100",
    "001e eee4 eeee d100",
    "001l 5555 5555 l100",
    "0001 1111 1111 1000",
    "0000 0000 0000 0000",
    "0000 0000 0000 0000",
]

BLOOD_SPLAT = [
    "0000 0000 0000 0000 0000 0000 0000 0000",
    "0000 0000 0000 0000 0000 0000 0000 0000",
    "0000 0000 0000 0000 0000 0000 0000 0000",
    "0000 c000 0000 0000 0000 00b0 000c 0000",
    "0000 b000 0000 0000 0000 0cc0 000b 0000",
    "0000 0b00 0000 0000 0000 0bcc 000c 0000",
    "0000 0000 00bb bbbb bbb0 cc00 0000 0000",
    "0000 0000 bbbb bbbb bbbb bccc cc00 0000",
    "0000 00bb bccc cccc cccc cccc b000 000b",
    "0000 bbcc cccc cccc cccc cccc bb00 00c0",
    "000b bccc cccc cccc cccc cccc cbb0 000b",
    "00bb cccc cccc cccc cccc cccc ccbb 0000",
    "0bbc cccc cccc c1cc cccc cccc c1cc cbb0",
    "0bbc cccc ccc1 cccc cc1c ccc1 cccc cbb0",
    "bbcc cccc cc1c cccc cccc ccc1 cccc cbb0",
    "bbcc cccc cccc cc1c c1cc cccc cccc cb00",
    "0bbc cccc cccc cccc c1cc cccc cccb 0000",
    "00bb cccc cc1c cccc cccc cccc ccbb 0000",
    "000b bccc c1cc cccc cccc cccc cbb0 0000",
    "0000 bbcc cccc cccc cccc cccc bb00 0000",
    "0000 0bbc cccc cccc cccc cccc b000 0000",
    "0000 00bb cccc cccc cccc ccbb 0000 0000",
    "0000 0000 bbcc cccc ccbb 0000 0000 0000",
    "0000 0000 0bbc cccc cbb0 0000 0000 0000",
    "0000 0000 00bb cccc bb00 0000 0000 0000",
    "0000 0000 000b cccc bb00 0000 0000 0000",
    "0000 0000 0000 bbbb bb00 0000 0000 0000",
    "0000 0000 0000 0bbc b000 0000 0000 0000",
    "0000 0000 0000 00bc 0000 0000 0000 0000",
    "0000 0000 0000 000c 0000 0b00 0000 0000",
    "0000 0000 0000 0000 0000 0000 0000 0000",
    "0000 0000 0000 0000 0000 0000 0000 0000",
]


# ---------------------------------------------------------------------------
# ASSET REGISTRY
# ---------------------------------------------------------------------------

ASSETS = [
    # name, pixels, purpose, transparent background
    ("floor_concrete_a", FLOOR_CONCRETE_A, "冷灰混凝土地砖 A，脏污靠右下，可平铺", False),
    ("floor_concrete_b", FLOOR_CONCRETE_B, "冷灰混凝土地砖 B，左中油渍变体", False),
    ("floor_concrete_c", FLOOR_CONCRETE_C, "冷灰混凝土地砖 C，细裂缝与磨损变体", False),
    ("floor_grate", FLOOR_GRATE, "金属排水格栅，重叠拼接地板", False),
    ("floor_hazard", FLOOR_HAZARD, "黄黑斜纹警戒地砖", False),
    ("floor_tile", FLOOR_TILE, "浅色实验室瓷砖，十字砖缝与磨痕", False),
    ("floor_blood", FLOOR_BLOOD, "干涸血迹贴花，叠在地面上", True),
    ("floor_debris", FLOOR_DEBRIS, "碎石与纸屑贴花", True),
    ("floor_crack", FLOOR_CRACK, "地面裂缝贴花", True),
    ("wall_top", WALL_TOP, "俯视墙体顶面，带面板接缝与铆钉", False),
    ("wall_face", WALL_FACE, "墙体正立面，带面板分缝与顶部高光", False),
    ("wall_shadow", WALL_SHADOW_MASK, "墙脚投影，上半部 alpha 渐隐", True),
    ("door_frame", DOOR_FRAME, "门框，中空可叠放门板", True),
    ("door_panel", DOOR_PANEL, "关闭的琥珀色门板，横向加强筋与亮缝", False),
    ("door_panel_open", DOOR_PANEL_OPEN, "半开琥珀色门板，左侧露出黑暗门洞", False),
    ("keycard_reader", KEYCARD_READER, "墙上读卡器，蓝色指示灯", True),
    ("vent", VENT, "通风格栅，金属横百叶", True),
    ("ceiling_lamp", [
        "0000 0000 0000 0000",
        "0111 1111 1111 1110",
        "0157 5555 5555 7510",
        "0157 ffff ffff 7510",
        "0157 eeee eeee 7510",
        "0157 dddd dddd 7510",
        "0155 5555 5555 5510",
        "0111 1111 1111 1110",
    ], "琥珀色灯管，透明背景", True),
    ("hazard_sign", HAZARD_SIGN, "琥珀色三角警示牌，带磨损与螺钉", True),
    ("desk", DESK, "32x16 金属办公桌，桌面纸张与右侧抽屉", True),
    ("chair", CHAIR, "俯视办公椅，磨损绿色坐垫与五星脚", True),
    ("locker", LOCKER, "俯视双门金属储物柜，带通风与把手", True),
    ("crate", CRATE, "木箱顶面，木板与斜撑，钢钉", True),
    ("barrel", BARREL, "俯视锈蚀铁桶，双层桶盖", True),
    ("bodybag", BODYBAG, "黑色运尸袋，拉链与束带", True),
    ("corpse", CORPSE, "穿橙色囚服的尸体，头朝左俯卧", True),
    ("terminal", TERMINAL, "CRT 显示器终端，蓝色屏幕与键盘", True),
    ("save_terminal", SAVE_TERMINAL, "存档终端，绿色数据显示与指示灯", True),
    ("blood_splat", BLOOD_SPLAT, "32x32 大面积血泊，带喷溅与离滴", True),
]


def clean(rows: list[str]) -> list[str]:
    return [row.replace(" ", "") for row in rows]


def validate_rows(name: str, rows: list[str], w: int, h: int) -> list[str]:
    rows = clean(rows)
    if len(rows) != h:
        raise ValueError(f"{name}: expected {h} rows, got {len(rows)}")
    for y, row in enumerate(rows):
        if len(row) != w:
            raise ValueError(f"{name}: row {y} has {len(row)} columns, expected {w}: {row!r}")
        for ch in row:
            if ch not in PALETTE:
                raise ValueError(f"{name}: bad palette char {ch!r} at row {y}")
    return rows


# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------

def render_asset(name: str, rows: list[str], w: int, h: int) -> Image.Image:
    if name == "wall_shadow":
        rows = validate_rows(name, rows, w, h)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        px = im.load()
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                level = int(ch)
                alpha = SHADOW_ALPHA[level]
                if alpha:
                    px[x, y] = (7, 9, 11, alpha)
        return im

    rows = validate_rows(name, rows, w, h)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            px[x, y] = PALETTE[ch]
    return im


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def checker_board(w: int, h: int) -> Image.Image:
    im = Image.new("RGB", (w, h), (14, 19, 23))
    d = ImageDraw.Draw(im)
    cell = 10
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if (x // cell + y // cell) % 2 == 0:
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(18, 24, 29))
    return im


def build_preview(items: list[tuple[str, Image.Image]]) -> Image.Image:
    cols = 5
    rows_n = math.ceil(len(items) / cols)
    cell_w, cell_h = 180, 184
    margin, header_h, footer_h = 28, 74, 66
    width = margin * 2 + cols * cell_w
    height = header_h + rows_n * cell_h + footer_h + margin

    bg = (9, 12, 15)
    panel = (12, 16, 20)
    border = (30, 37, 43)
    img_bg = checker_board(148, 144)

    im = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(im)
    title_font = font(25, True)
    sub_font = font(12)
    label_font = font(12, False)
    tiny_font = font(9)

    d.text((margin, 20), "SCP FACILITY // TILE & PROP SHEET", font=title_font, fill=(240, 199, 107))
    d.text((margin + 1, 52), "HAND-PIXELLED LITERAL STRINGS / FIXED 16-COLOR PALETTE / 4X NEAREST", font=sub_font, fill=(106, 117, 125))
    d.line([(margin, 68), (width - margin, 68)], fill=(51, 60, 69), width=1)

    for i, (name, image) in enumerate(items):
        c = i % cols
        r = i // cols
        x0 = margin + c * cell_w
        y0 = header_h + r * cell_h
        d.rectangle([x0, y0, x0 + cell_w - 2, y0 + cell_h - 2], fill=panel, outline=border)

        ix = x0 + 16
        iy = y0 + 12
        im.paste(img_bg, (ix, iy))
        scale = 4
        scaled = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        ox = ix + (148 - scaled.width) // 2
        oy = iy + (144 - scaled.height) // 2
        im.paste(scaled, (ox, oy), scaled)

        label = name
        bbox = d.textbbox((0, 0), label, font=label_font)
        tw = bbox[2] - bbox[0]
        d.text((x0 + (cell_w - 2 - tw) // 2, y0 + 158), label, font=label_font, fill=(200, 210, 217))
        dims = f"{image.width}x{image.height}  {'ALPHA' if image.getextrema()[3][0] < 255 else 'OPAQUE'}"
        bbox = d.textbbox((0, 0), dims, font=tiny_font)
        tw = bbox[2] - bbox[0]
        d.text((x0 + (cell_w - 2 - tw) // 2, y0 + 172), dims, font=tiny_font, fill=(106, 117, 125))

    fy = header_h + rows_n * cell_h + 8
    d.line([(margin, fy), (width - margin, fy)], fill=(51, 60, 69), width=1)
    palette_label = "PALETTE LOCK // 0 TRANSPARENT + 15 OPAQUE"
    d.text((margin, fy + 8), palette_label, font=tiny_font, fill=(154, 165, 173))
    sw_x = margin
    sw_y = fy + 24
    for ch, rgba in PALETTE.items():
        rgb = rgba[:3]
        if ch == "0":
            d.rectangle([sw_x, sw_y, sw_x + 22, sw_y + 18], fill=(9, 12, 15), outline=(51, 60, 69))
            d.line([(sw_x + 3, sw_y + 15), (sw_x + 19, sw_y + 3)], fill=(93, 106, 118), width=1)
        else:
            d.rectangle([sw_x, sw_y, sw_x + 22, sw_y + 18], fill=rgb, outline=(30, 37, 43))
        d.text((sw_x + 8, sw_y + 21), ch, font=tiny_font, fill=(93, 106, 118))
        sw_x += 26
    d.text((width - margin - 170, fy + 8), f"{len(items)} ASSETS / INCREMENTAL BUILD", font=tiny_font, fill=(93, 106, 118))

    return im


def main() -> None:
    TILE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    rendered: list[tuple[str, Image.Image]] = []

    for name, pixels, purpose, transparent in ASSETS:
        rows = clean(pixels)
        w = len(rows[0])
        h = len(rows)
        image = render_asset(name, rows, w, h)
        path = TILE_DIR / f"{name}.png"
        image.save(path)
        rendered.append((name, image))
        manifest[f"{name}.png"] = {
            "w": w,
            "h": h,
            "用途": purpose,
            "是否透明背景": bool(transparent),
        }

    preview = build_preview(rendered)
    preview.save(PREVIEW)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"rendered {len(ASSETS)} assets -> {TILE_DIR}")
    print(f"preview -> {PREVIEW}")
    print(f"manifest -> {MANIFEST}")


if __name__ == "__main__":
    main()
