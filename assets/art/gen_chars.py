#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCP Facility 2D - hand-authored character sprites.

Every animation frame below is a literal character grid.  One character is one
pixel, mapped through PALETTE.  There is no shape generation, no noise, no
ellipses, no rounded rectangles: the PNGs are only a transcription of these
grids.

Run:
    python assets/art/gen_chars.py

Outputs:
    assets/art/chars/*.png
    assets/art/chars_preview.png   (1x layout, then nearest-neighbour x4)
    assets/art/chars_manifest.json
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import OrderedDict

from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
CHARS_DIR = BASE / "chars"
PREVIEW_PATH = BASE / "chars_preview.png"
MANIFEST_PATH = BASE / "chars_manifest.json"

# ---------------------------------------------------------------------------
# Palette (the only colours allowed in sprite PNGs)
# ---------------------------------------------------------------------------
PALETTE = OrderedDict([
    ("0", None),                 # transparent
    ("1", (0x07, 0x09, 0x0b)),   # black
    ("2", (0x12, 0x16, 0x1a)),
    ("3", (0x1b, 0x20, 0x26)),
    ("4", (0x26, 0x2d, 0x34)),
    ("5", (0x33, 0x3c, 0x45)),
    ("6", (0x45, 0x50, 0x5b)),
    ("7", (0x5d, 0x6a, 0x76)),
    ("8", (0x2b, 0x3a, 0x33)),
    ("9", (0x3a, 0x51, 0x48)),
    ("a", (0x4d, 0x6b, 0x5c)),
    ("b", (0x6b, 0x1f, 0x1f)),
    ("c", (0xa3, 0x2a, 0x2a)),
    ("d", (0x8a, 0x64, 0x20)),
    ("e", (0xc9, 0x9a, 0x3f)),
    ("f", (0xf0, 0xc7, 0x6b)),
    ("g", (0xc4, 0x69, 0x2a)),
    ("h", (0xe0, 0x8a, 0x3c)),
    ("i", (0x7a, 0x3f, 0x18)),
    ("j", (0xc9, 0xa0, 0x7a)),
    ("k", (0xe8, 0xe2, 0xd6)),
    ("l", (0x9a, 0xa5, 0xad)),
    ("m", (0x6a, 0x75, 0x7d)),
    ("n", (0x3c, 0x44, 0x4b)),
    ("o", (0x1f, 0x4b, 0x6b)),
    ("p", (0x2f, 0x7f, 0xb8)),
])

# ---------------------------------------------------------------------------
# PLAYER - D-9341, orange jumpsuit.  16 x 24, feet on row 23.
# ---------------------------------------------------------------------------

PLAYER_DOWN_0 = [
    "0000000000000000",
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122112210000",
    "00001djjjjd10000",
    "00001djjjjd10000",
    "000001dddd100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gghhhhgg1000",
    "001g1gghhgg1g100",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "0000455115540000",
]

PLAYER_DOWN_1 = [
    "0000000000000000",
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122112210000",
    "00001djjjjd10000",
    "00001djjjjd10000",
    "000001dddd100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gghhhhgg1000",
    "001g1gghhgg1g100",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "0001ggg11gg10000",
    "0001ggg11gg10000",
    "0001ggg11gg10000",
    "0001ggg114510000",
    "0001455100000000",
]

PLAYER_DOWN_2 = [
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122112210000",
    "00001djjjjd10000",
    "00001djjjjd10000",
    "000001dddd100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gghhhhgg1000",
    "001g1gghhgg1g100",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "0000144114410000",
    "0000455115540000",
]

PLAYER_DOWN_3 = [
    "0000000000000000",
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122112210000",
    "00001djjjjd10000",
    "00001djjjjd10000",
    "000001dddd100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gghhhhgg1000",
    "001g1gghhgg1g100",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "0001gg11ggg10000",
    "0001gg11ggg10000",
    "0001gg11ggg10000",
    "00014411ggg10000",
    "0000000014551000",
]

PLAYER_UP_0 = [
    "0000000000000000",
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122222210000",
    "0000122222210000",
    "0000122122210000",
    "0000012222100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gh3hh3hg1000",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "0000455115540000",
]

PLAYER_UP_1 = [
    "0000000000000000",
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122222210000",
    "0000122222210000",
    "0000122122210000",
    "0000012222100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gh3hh3hg1000",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "0001ggg11gg10000",
    "0001ggg11gg10000",
    "0001ggg11gg10000",
    "0001ggg114410000",
    "0001445100000000",
]

PLAYER_UP_2 = [
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122222210000",
    "0000122222210000",
    "0000122122210000",
    "0000012222100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gh3hh3hg1000",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "00001gg11gg10000",
    "0000144114410000",
    "0000455115540000",
]

PLAYER_UP_3 = [
    "0000000000000000",
    "0000011111100000",
    "0000122222210000",
    "0000123333210000",
    "0000123333210000",
    "0000122222210000",
    "0000122222210000",
    "0000122122210000",
    "0000012222100000",
    "0000001dd1000000",
    "0001111111111000",
    "0001gh3hh3hg1000",
    "001g1g3hh3g1g100",
    "001g1g3hh3g1g100",
    "001g1gghhgg1g100",
    "001g1gghhgg1g100",
    "01kk1gggggg1kk10",
    "01kk1g3333g1kk10",
    "0001g333333g1000",
    "0001gg11ggg10000",
    "0001gg11ggg10000",
    "0001gg11ggg10000",
    "00014411ggg10000",
    "0000000014451000",
]

# Side views.  These are authored separately; the right side is not a flipped
# bitmap.  The glove on the right hand sits 1 px higher and the boots break at
# different pixels.
PLAYER_LEFT_0 = [
    "0000000000000000",
    "0000001111100000",
    "0000012222210000",
    "0000122333221000",
    "0000123333221000",
    "0001223333221000",
    "001jjj2233221000",
    "001jjj2222221000",
    "001djj1222210000",
    "0001dd1111100000",
    "0000001dd1000000",
    "0000111111110000",
    "0001gghhhgg10000",
    "001g1gghhgg10000",
    "001g1gghhgg10000",
    "001k1gghhgg10000",
    "001k1gggggg10000",
    "0001g3333g100000",
    "00001ggggg100000",
    "00001gg1gg100000",
    "00001gg1gg100000",
    "00001gg1gg100000",
    "0001441144100000",
    "0014550145500000",
]

PLAYER_LEFT_1 = [
    "0000000000000000",
    "0000001111100000",
    "0000012222210000",
    "0000122333221000",
    "0000123333221000",
    "0001223333221000",
    "001jjj2233221000",
    "001jjj2222221000",
    "001djj1222210000",
    "0001dd1111100000",
    "0000001dd1000000",
    "0000111111110000",
    "0001gghhhgg10000",
    "001g1gghhgg10000",
    "001g1gghhgg10000",
    "001k1gghhgg10000",
    "001k1gggggg10000",
    "0001g3333g100000",
    "00001ggggg100000",
    "0001ggg11gg10000",
    "0001ggg11gg10000",
    "0001ggg11gg10000",
    "0014551144100000",
    "0145510145510000",
]

PLAYER_LEFT_2 = [
    "0000001111100000",
    "0000012222210000",
    "0000122333221000",
    "0000123333221000",
    "0001223333221000",
    "001jjj2233221000",
    "001jjj2222221000",
    "001djj1222210000",
    "0001dd1111100000",
    "0000001dd1000000",
    "0000111111110000",
    "0001gghhhgg10000",
    "001g1gghhgg10000",
    "001g1gghhgg10000",
    "001k1gghhgg10000",
    "001k1gggggg10000",
    "0001g3333g100000",
    "00001ggggg100000",
    "00001gg1gg100000",
    "00001gg1gg100000",
    "00001gg1gg100000",
    "00001gg1gg100000",
    "0001441144100000",
    "0014550145500000",
]

PLAYER_LEFT_3 = [
    "0000000000000000",
    "0000001111100000",
    "0000012222210000",
    "0000122333221000",
    "0000123333221000",
    "0001223333221000",
    "001jjj2233221000",
    "001jjj2222221000",
    "001djj1222210000",
    "0001dd1111100000",
    "0000001dd1000000",
    "0000111111110000",
    "0001gghhhgg10000",
    "001g1gghhgg10000",
    "001g1gghhgg10000",
    "001k1gghhgg10000",
    "001k1gggggg10000",
    "0001g3333g100000",
    "00001ggggg100000",
    "0001gg11ggg10000",
    "0001gg11ggg10000",
    "0001gg11ggg10000",
    "00014411ggg10000",
    "0000000014551000",
]

PLAYER_RIGHT_0 = [
    "0000000000000000",
    "0000011111000000",
    "0000122222100000",
    "0001223332210000",
    "0001223333210000",
    "0001223333221000",
    "0001223322jjj100",
    "0001222222jjj100",
    "0000122221jjd100",
    "0000011111dd1000",
    "0000001dd1000000",
    "0000111111110000",
    "00001gghhhgg1000",
    "00001gghhgg1g100",
    "00001gghhgg1k100",
    "00001gghhgg1k100",
    "00001gggggg10000",
    "00001g3333g10000",
    "000001ggggg10000",
    "000001gg1gg10000",
    "000001gg1gg10000",
    "000001gg1gg10000",
    "0000014411441000",
    "0000014550145500",
]

PLAYER_RIGHT_1 = [
    "0000000000000000",
    "0000011111000000",
    "0000122222100000",
    "0001223332210000",
    "0001223333210000",
    "0001223333221000",
    "0001223322jjj100",
    "0001222222jjj100",
    "0000122221jjd100",
    "0000011111dd1000",
    "0000001dd1000000",
    "0000111111110000",
    "00001gghhhgg1000",
    "00001gghhgg1g100",
    "00001gghhgg1k100",
    "00001gghhgg1k100",
    "00001gggggg10000",
    "00001g3333g10000",
    "000001ggggg10000",
    "000001gg1ggg1000",
    "000001gg1ggg1000",
    "000001gg1ggg1000",
    "0000014411gg1000",
    "0000000000145510",
]

PLAYER_RIGHT_2 = [
    "0000011111000000",
    "0000122222100000",
    "0001223332210000",
    "0001223333210000",
    "0001223333221000",
    "0001223322jjj100",
    "0001222222jjj100",
    "0000122221jjd100",
    "0000011111dd1000",
    "0000001dd1000000",
    "0000111111110000",
    "00001gghhhgg1000",
    "00001gghhgg1g100",
    "00001gghhgg1k100",
    "00001gghhgg1k100",
    "00001gggggg10000",
    "00001g3333g10000",
    "000001ggggg10000",
    "000001gg1gg10000",
    "000001gg1gg10000",
    "000001gg1gg10000",
    "000001gg1gg10000",
    "0000014411441000",
    "0000014550145500",
]

PLAYER_RIGHT_3 = [
    "0000000000000000",
    "0000011111000000",
    "0000122222100000",
    "0001223332210000",
    "0001223333210000",
    "0001223333221000",
    "0001223322jjj100",
    "0001222222jjj100",
    "0000122221jjd100",
    "0000011111dd1000",
    "0000001dd1000000",
    "0000111111110000",
    "00001gghhhgg1000",
    "00001gghhgg1g100",
    "00001gghhgg1k100",
    "00001gghhgg1k100",
    "00001gggggg10000",
    "00001g3333g10000",
    "000001ggggg10000",
    "000001gg11gg1000",
    "000001gg11gg1000",
    "000001gg11gg1000",
    "000001gg11441000",
    "0000014551000000",
]

# ---------------------------------------------------------------------------
# SCP-173 - 24 x 24.  Concrete, black pitting, very sparse rust.
# ---------------------------------------------------------------------------

SCP173_IDLE = [
    "000000000000000000000000",
    "000000000000000000000000",
    "000000000111111000000000",
    "000000001lmmmmn100000000",
    "00000001lmmmmmn100000000",
    "0000001l1mmmmmn100000000",
    "0000001lmmmm1nn100000000",
    "00000001mmmmnn1000000000",
    "000000001mnnm10000000000",
    "0000000001mm100000000000",
    "000000111111111110000000",
    "00001lmmmmmmmmmmmmn10000",
    "0001lmmcmmmmmmmmmmmn1000",
    "0001mm0mmmnnnnmnn0mm1000",
    "0001mm0mmnnnnnmmm0mm1000",
    "0001mm0mmm2nnnnmm0mm1000",
    "001mmm0mmnnnnmmmm0mmm100",
    "001m101mmmmmmmmmm101m100",
    "000001mnm00mnnm10000000",
    "000001mmm00mmnm10000000",
    "000001mnm00mnnm10000000",
    "000001mmm00mmnm10000000",
    "000001mmmmm001mmmmm10000",
    "000001lmmm1001lmmm100000",
]

SCP173_STEP = [
    "000000001111110000000000",
    "00000011llllll1100000000",
    "00001llllmmmmnnn10000000",
    "00001lllmmm1nnnn10000000",
    "0001llmmmmnn1nnm10000000",
    "00001lmmmmn1nnnm10000000",
    "000001mmmnnnnnm100000000",
    "0000001mmnnnnm1000000000",
    "000000001mmmm10000000000",
    "000001111111111110000000",
    "00001lll1mmmm1lll1000000",
    "00001ll1mmmmmm1ll1000000",
    "0001ll1mm1mmmm1ll1000000",
    "0001ll1mmmmmmmm1ll100000",
    "0001l1mmmmmmmmmm1l100000",
    "001ll1mmmmmmmmmm1ll10000",
    "001ll1mmmmmmmmmm1ll10000",
    "001l1mmmmmmmmmmmm1l10000",
    "001l1mmmm1001mmmm1l10000",
    "00011mmmm1001mmmm1100000",
    "000001mm1001mmmm10000000",
    "00001lll1001llll10000000",
    "0001llll1001lllll1000000",
    "001llll100001lllll100000",
]

SCP173_LUNGE = [
    "000000000000000000000000",
    "000000000000000000000000",
    "000000000111111000000000",
    "000000111llllll111000000",
    "000001llllmmmmmmll100000",
    "00001lllmmmmnnmmmmll1000",
    "0001lllmmmnnnnnnmmml1000",
    "0001llmmmmnnnnnnmmml1000",
    "0001lmmmmmnnnnnmmmmm1000",
    "00001mmmmmnnnnnmmmm10000",
    "001111mmmmmmmmmmmm111100",
    "01llll11mmmmmmmm11llll10",
    "1lllll1mmmmmmmmmm1lllll1",
    "1llll1mmmmmmmmmmmm1llll1",
    "1llll1mmmm1mmmm1mm1llll1",
    "1lll1mmmmmmmmmmmmmm1lll1",
    "01ll1mmmmmmmmmmmmmm1ll10",
    "00111mmmmmmmmmmmmmm11100",
    "00001mmmm100001mmmm10000",
    "00001mmm10000001mmm10000",
    "00001mm1000000001mm10000",
    "0001lll1000000001lll1000",
    "001llll1000000001llll100",
    "01lllll1000000001lllll10",
]

# ---------------------------------------------------------------------------
# Corpse - D-class, side-lying, 24 x 16.
# ---------------------------------------------------------------------------

CORPSE_DCLASS = [
    "000000000000000000000000",
    "000000000000000000000000",
    "000000000011110000000000",
    "0000000011jjjj1100000000",
    "00000111jjjjjjjj11000000",
    "00001222jjjjjjjjj1100000",
    "000122222jjjjjj111000000",
    "000122222211111110000000",
    "0011gg111111111111000000",
    "01gghhgggggggg1111100000",
    "01ghhhgggggggggggg110000",
    "01gghhgggggg111111110000",
    "001iigggggg1100111111000",
    "00011ii11110000111111000",
    "000001110000000011111000",
    "000000000000000001110000",
]

# ---------------------------------------------------------------------------
# MTF soldier - 16 x 24, four idle/scan frames.  Background option only.
# ---------------------------------------------------------------------------

MTF_SOLDIER_0 = [
    "0000000000000000",
    "0000011111100000",
    "0000144444410000",
    "0001455555541000",
    "0001451111541000",
    "0001456116541000",
    "0001455555541000",
    "0000144444410000",
    "0000014444100000",
    "0000001441000000",
    "0011111111111100",
    "0013333333333100",
    "0013444444443100",
    "0013155555513100",
    "0013155555513100",
    "0013444444443100",
    "0013333333333100",
    "0001344444431000",
    "0001233333321000",
    "0000122112210000",
    "0000122112210000",
    "0000122112210000",
    "0000144114410000",
    "0000455115540000",
]

MTF_SOLDIER_1 = [
    "0000000000000000",
    "0000011111100000",
    "0000144444410000",
    "0001455555541000",
    "0001451111541000",
    "0001456116541000",
    "0001455555541000",
    "0000144444410000",
    "0000014444100000",
    "0000001441000000",
    "0011111111111100",
    "0013333333333100",
    "0013444444443100",
    "0013155555513100",
    "0013155555513100",
    "0013444444443100",
    "0013333333333100",
    "0001344444431000",
    "0001233333321000",
    "0000122112210000",
    "0000122112210000",
    "0000122112210000",
    "0000144114410000",
    "0000455115540000",
]

MTF_SOLDIER_2 = [
    "0000011111100000",
    "0000144444410000",
    "0001455555541000",
    "0001451111541000",
    "0001456116541000",
    "0001455555541000",
    "0000144444410000",
    "0000014444100000",
    "0000001441000000",
    "0011111111111100",
    "0013333333333100",
    "0013444444443100",
    "0013155555513100",
    "0013155555513100",
    "0013444444443100",
    "0013333333333100",
    "0001344444431000",
    "0001233333321000",
    "0000122112210000",
    "0000122112210000",
    "0000122112210000",
    "0000122112210000",
    "0000144114410000",
    "0000455115540000",
]

MTF_SOLDIER_3 = [
    "0000000000000000",
    "0000011111100000",
    "0000144444410000",
    "0001455555541000",
    "0001451111541000",
    "0001456116541000",
    "0001455555541000",
    "0000144444410000",
    "0000014444100000",
    "0000001441000000",
    "0011111111111100",
    "0013333333333100",
    "0013444444443100",
    "0013155555513100",
    "0013155555513100",
    "0013444444443100",
    "0013333333333100",
    "0001344444431000",
    "0001233333321000",
    "0000122112210000",
    "0000122112210000",
    "0000122112210000",
    "0000144114410000",
    "0000455115540000",
]

# ---------------------------------------------------------------------------
# Sprite registry
# ---------------------------------------------------------------------------
SPRITES = OrderedDict()
for _i, _g in enumerate([PLAYER_DOWN_0, PLAYER_DOWN_1, PLAYER_DOWN_2, PLAYER_DOWN_3]):
    SPRITES[f"player_down_{_i}"] = (_g, 16, 24, "down", _i)
for _i, _g in enumerate([PLAYER_UP_0, PLAYER_UP_1, PLAYER_UP_2, PLAYER_UP_3]):
    SPRITES[f"player_up_{_i}"] = (_g, 16, 24, "up", _i)
for _i, _g in enumerate([PLAYER_LEFT_0, PLAYER_LEFT_1, PLAYER_LEFT_2, PLAYER_LEFT_3]):
    SPRITES[f"player_left_{_i}"] = (_g, 16, 24, "left", _i)
for _i, _g in enumerate([PLAYER_RIGHT_0, PLAYER_RIGHT_1, PLAYER_RIGHT_2, PLAYER_RIGHT_3]):
    SPRITES[f"player_right_{_i}"] = (_g, 16, 24, "right", _i)
for _name, _idx, _g in [
    ("scp173_idle", 0, SCP173_IDLE),
    ("scp173_step", 1, SCP173_STEP),
    ("scp173_lunge", 2, SCP173_LUNGE),
]:
    SPRITES[_name] = (_g, 24, 24, "front", _idx)
SPRITES["corpse_dclass"] = (CORPSE_DCLASS, 24, 16, "side", 0)
for _i, _g in enumerate([MTF_SOLDIER_0, MTF_SOLDIER_1, MTF_SOLDIER_2, MTF_SOLDIER_3]):
    SPRITES[f"mtf_soldier_{_i}"] = (_g, 16, 24, "down", _i)

# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def validate_grid(name: str, grid: list[str], w: int, h: int) -> None:
    if len(grid) != h:
        raise ValueError(f"{name}: {len(grid)} rows, expected {h}")
    for y, row in enumerate(grid):
        if len(row) != w:
            raise ValueError(f"{name}: row {y} has {len(row)} columns, expected {w}: {row!r}")
        for x, ch in enumerate(row):
            if ch not in PALETTE:
                raise ValueError(f"{name}: bad palette char {ch!r} at {x},{y}")


def grid_to_image(grid: list[str]) -> Image.Image:
    h = len(grid)
    w = len(grid[0])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            rgba = PALETTE[ch]
            if rgba is not None:
                px[x, y] = (*rgba, 255)
    return img


def build_sprites() -> dict[str, Image.Image]:
    CHARS_DIR.mkdir(parents=True, exist_ok=True)
    images: dict[str, Image.Image] = {}
    for name, (grid, w, h, _d, _f) in SPRITES.items():
        validate_grid(name, grid, w, h)
        img = grid_to_image(grid)
        # Feet/baseline check for standing characters.
        if name.startswith(("player_", "scp173_", "mtf_")):
            alpha = img.getchannel("A")
            bbox = alpha.getbbox()
            if bbox is None or bbox[3] != h:
                raise ValueError(f"{name}: silhouette does not reach the bottom row ({bbox})")
        img.save(CHARS_DIR / f"{name}.png")
        images[name] = img
    return images


# ---------------------------------------------------------------------------
# Preview sheet
# ---------------------------------------------------------------------------
FONT = {
    " ": ["000","000","000","000","000","000","000"],
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "B": ["11110","10001","10001","11110","10001","10001","11110"],
    "C": ["01111","10000","10000","10000","10000","10000","01111"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
    "E": ["11111","10000","10000","11110","10000","10000","11111"],
    "F": ["11111","10000","10000","11110","10000","10000","10000"],
    "G": ["01111","10000","10000","10111","10001","10001","01111"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "I": ["11111","00100","00100","00100","00100","00100","11111"],
    "J": ["00111","00010","00010","00010","10010","10010","01100"],
    "K": ["10001","10010","10100","11000","10100","10010","10001"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "M": ["10001","11011","10101","10101","10001","10001","10001"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "P": ["11110","10001","10001","11110","10000","10000","10000"],
    "Q": ["01110","10001","10001","10001","10101","10010","01101"],
    "R": ["11110","10001","10001","11110","10100","10010","10001"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "U": ["10001","10001","10001","10001","10001","10001","01110"],
    "V": ["10001","10001","10001","10001","10001","01010","00100"],
    "W": ["10001","10001","10001","10101","10101","10101","01010"],
    "X": ["10001","10001","01010","00100","01010","10001","10001"],
    "Y": ["10001","10001","01010","00100","00100","00100","00100"],
    "Z": ["11111","00001","00010","00100","01000","10000","11111"],
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00010","00100","01000","11111"],
    "3": ["11110","00001","00001","01110","00001","00001","11110"],
    "4": ["00010","00110","01010","10010","11111","00010","00010"],
    "5": ["11111","10000","10000","11110","00001","00001","11110"],
    "6": ["01110","10000","10000","11110","10001","10001","01110"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "9": ["01110","10001","10001","01111","00001","00001","01110"],
    "-": ["00000","00000","00000","11111","00000","00000","00000"],
    "/": ["00001","00010","00010","00100","01000","01000","10000"],
    ".": ["00000","00000","00000","00000","00000","00110","00110"],
    ":": ["00000","00110","00110","00000","00110","00110","00000"],
    "(": ["00010","00100","01000","01000","01000","00100","00010"],
    ")": ["01000","00100","00010","00010","00010","00100","01000"],
    "+": ["00000","00100","00100","11111","00100","00100","00000"],
}

C_BG = PALETTE["2"]
C_PANEL = PALETTE["3"]
C_PANEL_ALT = (0x17, 0x1c, 0x21)
C_LINE = PALETTE["4"]
C_TEXT = PALETTE["k"]
C_DIM = PALETTE["l"]
C_MUTE = PALETTE["6"]
C_ACCENT = PALETTE["g"]
C_ACCENT_HI = PALETTE["h"]


def text_width(s: str) -> int:
    return len(s) * 6 - 1


def draw_text(draw: ImageDraw.ImageDraw, x: int, y: int, s: str, color) -> None:
    cx = x
    for ch in s:
        pattern = FONT.get(ch.upper() if ch.upper() in FONT else ch)
        if pattern is None:
            pattern = FONT[" "]
        for py, row in enumerate(pattern):
            for px, bit in enumerate(row):
                if bit == "1":
                    draw.point((cx + px, y + py), fill=color)
        cx += 6


def load_font(*_a, **_k):
    return None


def build_preview(images: dict[str, Image.Image]) -> None:
    M = 8
    LABEL_W = 104
    CELL_W = 38
    cols = 4
    COLS_W = CELL_W * cols
    W = M + LABEL_W + COLS_W + M
    H = 334

    img = Image.new("RGBA", (W, H), (*C_BG, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, W - 1, 17], fill=PALETTE["3"])
    draw.line([(0, 17), (W, 17)], fill=PALETTE["4"])
    draw_text(draw, M, 5, "SCP FACILITY / CHARACTER SHEET", C_TEXT)
    draw_text(draw, W - M - text_width("4X"), 5, "4X", C_ACCENT_HI)
    draw_text(draw, M, 21, "D-CLASS D-9341   SCP-173   CORPSE   MTF", C_DIM)
    draw_text(draw, M, 30, "ROWS = FACING    COLUMNS = ANIMATION FRAME", C_MUTE)

    players = [
        ("PLAYER DOWN", "player_down"),
        ("PLAYER LEFT", "player_left"),
        ("PLAYER RIGHT", "player_right"),
        ("PLAYER UP", "player_up"),
    ]

    def sprite_cell(name: str, x: int, y: int, h: int, idx_text: str, alt: bool = False) -> None:
        panel_h = h + 6
        draw.rectangle([x, y, x + CELL_W - 3, y + panel_h - 1],
                       fill=C_PANEL_ALT if alt else C_PANEL)
        draw.rectangle([x, y, x + CELL_W - 3, y + panel_h - 1], outline=PALETTE["4"])
        # frame tick
        draw_text(draw, x + 2, y + 2, idx_text, C_MUTE)
        sprite = images[name]
        sx = x + (CELL_W - 3 - sprite.width) // 2
        sy = y + panel_h - 3 - sprite.height
        img.alpha_composite(sprite, (sx, sy))
        # baseline
        draw.line([(x + 4, y + panel_h - 3), (x + CELL_W - 8, y + panel_h - 3)],
                  fill=PALETTE["5"])
        # corner ticks
        draw.point((x, y), fill=C_ACCENT)
        draw.point((x + CELL_W - 4, y), fill=C_ACCENT)

    # Player rows
    row_y = 40
    cell_h = 27
    for ri, (label, prefix) in enumerate(players):
        draw_text(draw, M, row_y + 9, label, C_TEXT)
        draw.point((M, row_y + 21), fill=C_ACCENT)
        for i in range(4):
            x = M + LABEL_W + i * CELL_W
            sprite_cell(f"{prefix}_{i}", x, row_y, 24, str(i), alt=(ri % 2 == 1))
        row_y += 34

    # SCP-173
    draw.rectangle([0, row_y + 1, W - 1, row_y + 1], fill=PALETTE["3"])
    draw_text(draw, M, row_y + 5, "SCP-173 / CONCRETE", C_ACCENT_HI)
    draw_text(draw, M, row_y + 15, "NO FACE / NO EYES", C_MUTE)
    scp = [("scp173_idle", "I"), ("scp173_step", "S"), ("scp173_lunge", "L")]
    for i, (name, tick) in enumerate(scp):
        x = M + LABEL_W + i * CELL_W
        sprite_cell(name, x, row_y + 4, 24, tick, alt=(i == 1))
    row_y += 35

    # corpse
    draw.rectangle([0, row_y + 1, W - 1, row_y + 1], fill=PALETTE["3"])
    draw_text(draw, M, row_y + 5, "CORPSE / D-CLASS", C_TEXT)
    draw_text(draw, M, row_y + 15, "SIDE-LYING", C_MUTE)
    sprite_cell("corpse_dclass", M + LABEL_W, row_y + 2, 16, "0")
    row_y += 26

    # MTF
    draw.rectangle([0, row_y + 1, W - 1, row_y + 1], fill=PALETTE["3"])
    draw_text(draw, M, row_y + 5, "MTF SOLDIER", C_DIM)
    draw_text(draw, M, row_y + 15, "BACKGROUND IDLE", C_MUTE)
    for i in range(4):
        x = M + LABEL_W + i * CELL_W
        sprite_cell(f"mtf_soldier_{i}", x, row_y + 2, 24, str(i), alt=(i % 2 == 1))
    row_y += 36

    # Footer palette strip
    draw.line([(M, row_y), (W - M, row_y)], fill=PALETTE["4"])
    draw_text(draw, M, row_y + 4, "PALETTE", C_MUTE)
    px = M + 48
    for key, rgb in PALETTE.items():
        if rgb is None:
            continue
        draw.rectangle([px, row_y + 4, px + 5, row_y + 9], fill=(*rgb, 255))
        px += 7

    # 4x nearest-neighbour enlargement; everything above is 1x pixel-exact.
    out = img.resize((W * 4, H * 4), Image.NEAREST)
    out.save(PREVIEW_PATH)


def write_manifest() -> None:
    data = OrderedDict()
    for name, (_grid, w, h, direction, idx) in SPRITES.items():
        data[f"{name}.png"] = {
            "w": w,
            "h": h,
            "朝向": direction,
            "帧序": idx,
        }
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    images = build_sprites()
    build_preview(images)
    write_manifest()
    print(f"wrote {len(images)} sprites to {CHARS_DIR}")
    print(f"wrote preview   {PREVIEW_PATH}")
    print(f"wrote manifest  {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
