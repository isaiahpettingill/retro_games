"""Original tile and sprite art. Output uses the NES two-bitplane format."""

from pathlib import Path
from math import sqrt
from menus import build_menus, menu_sprites

OUT = Path("build")
OUT.mkdir(exist_ok=True)


class Pic:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [[0] * w for _ in range(h)]

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def rect(self, x, y, w, h, c):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.dot(i, j, c)

    def line(self, x, y, a, b, c):
        n = max(abs(a - x), abs(b - y), 1)
        for k in range(n + 1):
            self.dot(x + round((a - x) * k / n), y + round((b - y) * k / n), c)

    def oval(self, x, y, rx, ry, c):
        for j in range(-ry, ry + 1):
            dx = int(rx * sqrt(max(0, 1 - (j / (ry + 0.25)) ** 2)))
            self.rect(x - dx, y + j, 2 * dx + 1, 1, c)

    def poly(self, points, c):
        for y in range(min(v[1] for v in points), max(v[1] for v in points) + 1):
            xs = []
            for (a, b), (d, e) in zip(points, points[1:] + points[:1]):
                if min(b, e) <= y < max(b, e):
                    xs.append(a + (d - a) * (y - b) / (e - b))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                self.rect(round(a), y, round(b) - round(a) + 1, 1, c)

    def paste(self, src, x, y, scale=1):
        for j, row in enumerate(src.p):
            for i, c in enumerate(row):
                if c:
                    self.rect(x + i * scale, y + j * scale, scale, scale, c)

    def tile(self, x, y):
        return bytes(
            sum(((self.p[y + j][x + i] >> bit) & 1) << (7 - i) for i in range(8))
            for bit in (0, 1)
            for j in range(8)
        )

    def flipped(self):
        q = Pic(self.w, self.h)
        q.p = [r[::-1] for r in self.p]
        return q


# Five-pixel capitals and numerals drawn on an eight-pixel grid.
glyphs = {
    "A": "0e11111f111111",
    "B": "1e11111e11111e",
    "C": "0f10101010100f",
    "D": "1e11111111111e",
    "E": "1f10101e10101f",
    "F": "1f10101e101010",
    "G": "0f10101711110f",
    "H": "1111111f111111",
    "I": "0e04040404040e",
    "J": "0702020212120c",
    "K": "11121418141211",
    "L": "1010101010101f",
    "M": "111b1515111111",
    "N": "11191915131311",
    "O": "0e11111111110e",
    "P": "1e11111e101010",
    "Q": "0e11111115120d",
    "R": "1e11111e141211",
    "S": "0f10100e01011e",
    "T": "1f040404040404",
    "U": "1111111111110e",
    "V": "11111111110a04",
    "W": "1111111515150a",
    "X": "11110a040a1111",
    "Y": "11110a04040404",
    "Z": "1f01020408101f",
    "0": "0e11131519110e",
    "1": "040c040404040e",
    "2": "0e11010204081f",
    "3": "1e01010e01011e",
    "4": "02060a121f0202",
    "5": "1f10101e01011e",
    "6": "0618101e11110e",
    "7": "1f010204080808",
    "8": "0e11110e11110e",
    "9": "0e11110f01020c",
    "-": "0000001f000000",
    "/": "01020204080810",
    "!": "04040404040004",
    "+": "0004041f040400",
    ".": "00000000000004",
    ":": "00000400000400",
    ">": "10080402040810",
    "<": "01020408040201",
    "?": "0e110102040004",
}
chars = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/!+. :><?".replace(". :", ".:")


def letter(p, ch, x, y, s, c):
    for j, v in enumerate(bytes.fromhex(glyphs.get(ch, "00000000000000"))):
        for i in range(5):
            if v & (16 >> i):
                p.rect(x + i * s, y + j * s, s, s, c)


def word(p, s, x, y, k, c):
    for i, ch in enumerate(s):
        letter(p, ch, x + 6 * k * i, y, k, c)


animal_patterns = [
    [
        "................",
        "......1111......",
        ".....122221.....",
        "....12233221....",
        "....122313111...",
        "..112222233331..",
        ".122222221111...",
        "12222222221.....",
        "112333222221....",
        ".12333222221....",
        "..122222221.....",
        "...1122221......",
        ".....11111......",
        ".....3..3.......",
        "....33..33......",
        "................",
    ],
    [
        "................",
        ".....11111......",
        "....1222221.....",
        "...122222221....",
        "..11332333211...",
        "..13231313331...",
        "...123333331....",
        "....1133311.....",
        ".11..12221......",
        "1221.123221.....",
        "12.111233221....",
        ".12222222131....",
        "..111122211.....",
        ".....12.121.....",
        "....133.133.....",
        "................",
    ],
    [
        "................",
        "...111....111...",
        "..12221..12221..",
        "...1233333321...",
        "...1333333331...",
        "..133223322331..",
        "..133213312331..",
        "..133332233331..",
        "...1333333331...",
        "..122223322221..",
        "..122333333221..",
        "...1233333321...",
        "...1223333221...",
        "....12222221....",
        "...1221..1221...",
        "................",
    ],
    [
        ".......11...11..",
        ".......121.121..",
        "........122221..",
        "........122321..",
        "........12211331",
        "........12233331",
        "........1222111.",
        "..11....12221...",
        ".132111112221...",
        "..12222222221...",
        "..12333322221...",
        "...122222221....",
        "...121111121....",
        "...121...121....",
        "..1331..1331....",
        "................",
    ],
]


def animal(k, pose):
    p = Pic(16, 16)
    for j, row in enumerate(animal_patterns[k]):
        for i, v in enumerate(row):
            if v != ".":
                p.dot(i, j, int(v))
    if pose == 1:
        for j in range(12, 16):
            p.p[j] = p.p[j][1:] + [0] if j > 13 else [0] + p.p[j][:-1]
        if k == 0:
            p.line(1, 6, 3, 2, 3)
            p.line(2, 7, 5, 3, 2)
    if pose == 2:
        if k == 0:
            p.poly([(0, 4), (2, 0), (8, 8), (4, 11)], 3)
            p.line(0, 3, 5, 9, 1)
        else:
            for j in (12, 13, 14):
                p.p[j] = [0] * 16
            p.rect(3, 12, 4, 2, 2)
            p.rect(10, 12, 4, 2, 3)
    if pose == 3:
        if k in (1, 2):
            p.oval(13, 9, 2, 3, 1)
            p.oval(13, 9, 2, 2, 3)
        if k == 3:
            p.rect(13, 5, 3, 2, 3)
        if k == 0:
            p.rect(5, 11, 5, 2, 3)
    return p


def crop(k, walk=0):
    p = Pic(16, 16)
    p.rect(2 + walk, 13, 4, 2, 1)
    p.rect(10 - walk, 13, 4, 2, 1)
    if k == 2:
        p.poly([(2, 4), (14, 3), (12, 11), (5, 14)], 1)
        p.poly([(3, 5), (13, 4), (10, 11), (6, 13)], 2)
    elif k == 3:
        p.rect(6, 7, 5, 6, 1)
        p.rect(7, 7, 3, 6, 3)
        for x, y in [(4, 6), (8, 4), (11, 6)]:
            p.oval(x, y, 4, 4, 1)
            p.oval(x, y - 1, 3, 3, 2)
    elif k == 5:
        p.poly([(2, 4), (7, 3), (13, 5), (14, 11), (11, 13), (3, 13), (6, 10)], 1)
        p.poly([(3, 5), (8, 4), (12, 6), (13, 10), (10, 12), (5, 12), (7, 9)], 2)
    elif k == 6:
        p.oval(8, 8, 5, 7, 1)
        p.oval(8, 8, 4, 6, 2)
        for x in (6, 9):
            p.line(x, 3, x, 10, 3)
        p.poly([(1, 7), (8, 12), (14, 6), (12, 13), (6, 15)], 1)
    else:
        rx, ry = (6, 5) if k in (0, 4) else (6, 6)
        p.oval(8, 9, rx + 1, ry, 1)
        p.oval(8, 8, rx, ry - 1, 2)
        p.line(4, 7, 6, 5, 3)
        if k == 1:
            p.line(7, 4, 9, 2, 2)
            p.line(7, 12, 6, 14, 3)
        if k == 7:
            p.oval(10, 5, 3, 4, 2)
    if k == 4:
        # The beet carries a plated shell and hooked side horns.
        p.poly([(0, 5), (5, 8), (3, 10), (0, 9)], 3)
        p.poly([(15, 4), (11, 8), (13, 10), (15, 8)], 3)
        p.line(4, 12, 12, 12, 1)
        p.line(7, 13, 10, 13, 3)
    if k == 7:
        p.line(6, 4, 11, 2, 1)
        p.rect(11, 0, 2, 3, 1)
    if k in (0, 2, 4, 5, 7):
        p.line(8, 4, 6, 0, 1)
        p.line(8, 4, 11, 0, 3)
        p.line(8, 4, 13, 2, 1)
    p.rect(4, 7 + walk, 3, 3, 3)
    p.rect(10, 7 + walk, 3, 3, 3)
    p.dot(5, 8 + walk, 1)
    p.dot(11, 8 + walk, 1)
    p.line(3, 6 + walk, 6, 7 + walk, 1)
    p.line(10, 7 + walk, 13, 6 + walk, 1)
    p.line(7, 11 + walk, 9, 11 + walk, 1)
    return p


def king(k):
    p = Pic(32, 32)
    p.paste(crop(k), 0, 1, 2)
    if k % 3 == 0:
        p.poly([(7, 5), (6, 0), (12, 3), (16, 0), (20, 3), (25, 0), (24, 6)], 3)
        p.rect(7, 5, 18, 2, 1)
        p.dot(15, 3, 2)
    if k % 3 == 1:
        p.rect(3, 12, 26, 3, 1)
        p.rect(5, 12, 8, 2, 3)
        p.rect(18, 12, 8, 2, 3)
    if k % 3 == 2:
        p.poly([(2, 12), (0, 5), (7, 9), (12, 12)], 3)
        p.poly([(21, 12), (30, 5), (28, 12)], 3)
    p.rect(13, 24, 2, 3, 3)
    p.rect(18, 24, 2, 3, 3)
    return p


class Tiles:
    def __init__(self):
        self.t = [bytes(16)]

    def add(self, t):
        if t not in self.t:
            self.t.append(t)
        return self.t.index(t)

    def bytes(self):
        assert len(self.t) <= 256, len(self.t)
        return b"".join(self.t) + bytes((256 - len(self.t)) * 16)


def array(name, data, ty="unsigned char"):
    return (
        "static const "
        + ty
        + " "
        + name
        + "[]={"
        + ",".join(str(x) for x in data)
        + "};\n"
    )


header = ""
title = Tiles()
for ch in chars[1:]:
    p = Pic(8, 8)
    letter(p, ch, 1, 0, 1, 3)
    title.t.append(p.tile(0, 0))


header += build_menus(title, Pic, chars, array)


# All gameplay banks use equal metatile IDs. Palettes provide local materials.
def terrain(name, stage):
    p = Pic(16, 16)
    if name in ("turf", "dirt", "stone"):
        p.rect(0, 0, 16, 16, 1)
        p.line(1, 9, 5, 9, 2)
        p.line(5, 9, 6, 8, 2)
        p.line(10, 13, 12, 13, 2)
        p.dot(9, 3, 2)
        p.line(1, 2, 3, 2, 2)
        if name == "turf":
            p.rect(0, 0, 16, 4, 3)
            p.line(0, 4, 15, 4, 2)
            for x in (1, 5, 6, 11, 14):
                p.rect(x, 3, 1, 3 + (x & 1), 2)
        elif name == "stone":
            p.line(0, 7, 15, 7, 2)
            p.line(5, 1, 5, 6, 2)
            p.line(13, 8, 13, 15, 2)
    if name in ("ledge", "rail"):
        p.rect(0, 0, 16, 3, 3)
        p.rect(0, 3, 16, 4, 1)
        p.line(0, 3, 15, 3, 2)
        for x in (1, 9):
            p.line(x, 5, x + 3, 7, 2)
            p.dot(x, 2, 1)
        if name == "rail":
            p.line(2, 7, 8, 13, 1)
            p.line(8, 13, 15, 6, 1)
    if name == "vine":
        p.line(8, 0, 6, 15, 2)
        p.line(9, 0, 7, 15, 1)
        p.poly([(8, 6), (2, 2), (3, 7), (8, 9)], 3)
        p.poly([(7, 11), (14, 6), (13, 11)], 2)
    if name == "spikes":
        for x in (0, 8):
            p.poly([(x, 16), (x + 4, 5), (x + 7, 16)], 1)
            p.line(x + 1, 14, x + 4, 6, 3)
            p.line(x + 4, 9, x + 5, 15, 2)
    if name == "flag":
        p.rect(3, 0, 2, 16, 3)
        p.poly([(5, 0), (15, 2), (13, 8), (5, 6)], 2)
        p.line(7, 2, 9, 5, 3)
        p.line(9, 5, 12, 2, 3)
    if name == "grass":
        for x, y in [(0, 7), (4, 10), (9, 5), (15, 9)]:
            p.line(7, 15, x, y, 2)
        p.rect(8, 5, 3, 2, 3)
    if name == "beacon":
        p.rect(7, 0, 2, 16, 1)
        p.rect(3, 2, 10, 7, 2)
        p.line(6, 5, 11, 5, 3)
        p.dot(9, 3, 3)
        p.dot(9, 7, 3)
    if stage in (2, 4, 6, 7) and name in ("turf", "dirt", "stone", "ledge", "rail"):
        p = Pic(16, 16)
        if name in ("turf", "dirt", "stone"):
            p.rect(0, 0, 16, 16, 1)
            p.rect(1, 1, 14, 13, 2)
            p.rect(2, 2, 12, 10, 1)
            p.line(3, 3, 10, 3, 2)
            p.dot(12, 10, 3)
            p.dot(2, 13, 1)
            if name == "turf":
                p.rect(0, 0, 16, 4, 3)
                for x in range(-4, 20, 8):
                    p.line(x, 3, x + 3, 0, 1)
                    p.line(x + 1, 3, x + 4, 0, 1)
            elif name == "stone":
                for y in (4, 7, 10):
                    p.line(3, y, 12, y, 2)
        else:
            p.rect(0, 0, 16, 3, 3)
            p.rect(0, 3, 16, 3, 1)
            p.line(0, 5, 15, 5, 2)
            p.line(0, 6, 8, 12, 2)
            p.line(8, 12, 15, 6, 2)
    if stage == 5 and name in ("turf", "dirt", "stone"):
        p = Pic(16, 16)
        p.rect(0, 0, 16, 16, 1)
        p.line(0, 8, 7, 8, 2)
        p.line(7, 8, 9, 6, 2)
        p.line(9, 6, 15, 6, 2)
        p.line(2, 12, 6, 12, 2)
        if name == "turf":
            p.rect(0, 0, 16, 3, 3)
            p.line(0, 3, 7, 4, 2)
            p.line(8, 4, 15, 3, 2)
    return p


names = "blank turf dirt stone ledge rail vine spikes flag grass beacon".split()


# Gameplay panoramas reuse eight-pixel tiles across stages within each bank.
# Objects are anchored to a horizon; all silhouettes remain behind the actors.
def panorama(stage):
    p = Pic(256, 208)

    def cloud(x, y, size=1):
        p.rect(x, y + 4, 23, 3, 3)
        p.rect(x + 4, y + 2, 15, 2, 3)
        p.rect(x + 7, y, 8, 3, 3)
        p.rect(x + 3, y + 7, 17, 1, 2)

    def windows(x, y, w, h):
        for j in range(y, y + h, 12):
            for i in range(x, x + w, 8):
                p.rect(i, j, 3, 3, 2)

    def trees(x, y):
        p.rect(x + 3, y, 2, 7, 1)
        p.poly([(x - 2, y + 1), (x + 4, y - 10), (x + 10, y + 1)], 1)

    if stage in (0, 1, 5):
        for x, y in [(7, 55), (89, 37), (156, 71), (207, 25)]:
            cloud(x, y)
        if stage == 5:
            p.oval(133, 58, 19, 19, 3)
            for y in (63, 67, 71):
                p.rect(112, y, 42, 2, 0)
            # Sandstone mesas with steep shoulders in the hot pepper desert.
            for x, y, w in [
                (-12, 115, 57),
                (55, 124, 70),
                (155, 103, 38),
                (217, 120, 47),
            ]:
                p.poly(
                    [
                        (x - 9, 157),
                        (x, y + 10),
                        (x + 5, y + 9),
                        (x + 7, y),
                        (x + w - 12, y),
                        (x + w - 9, y + 13),
                        (x + w + 5, 157),
                    ],
                    1,
                )
            p.rect(0, 153, 256, 55, 2)
            for x, y in [(20, 151), (60, 166), (174, 157), (220, 145)]:
                p.rect(x, y - 17, 3, 18, 1)
                p.rect(x - 4, y - 9, 5, 3, 1)
                p.rect(x - 5, y - 13, 2, 6, 1)
        else:
            for x in range(256):
                # Broad rolling hills with vertical accents in the foreground.
                hill = 123 - (abs((x + 9) % 128 - 64) * 3 // 8)
                front = 161 - (abs((x + 52) % 128 - 64) // 4)
                p.rect(x, hill, 1, 208 - hill, 1)
                p.rect(x, front, 1, 208 - front, 2)
            if stage == 0:
                p.poly([(68, 132), (80, 120), (94, 132)], 2)
                p.rect(72, 132, 18, 12, 2)
                p.rect(78, 137, 5, 7, 1)
                p.rect(84, 133, 3, 3, 3)
                p.rect(96, 128, 6, 17, 2)
                p.oval(99, 128, 3, 3, 2)
                for x, y in [(19, 141), (141, 144), (149, 142), (205, 139)]:
                    trees(x, y)
            else:
                # Windmill with sails above the onion terraces.
                p.poly([(78, 147), (84, 107), (90, 107), (96, 147)], 2)
                for dx, dy in [(16, -10), (10, 16), (-16, 10), (-10, -16)]:
                    p.line(87, 109, 87 + dx, 109 + dy, 3)
                    p.line(88, 109, 88 + dx, 109 + dy, 3)
                for x, y in [(15, 142), (130, 136), (184, 142), (202, 139)]:
                    trees(x, y)
            for x in range(0, 256, 32):
                p.line(x, 180, x + 13, 174, 1)
                p.line(x + 16, 180, x + 29, 174, 1)
    elif stage in (2, 4, 6):
        for x, y in [(16, 45), (71, 25), (174, 42), (225, 29)]:
            p.line(x, y, x + 9, y, 2)
        base = [
            (0, 102, 24),
            (24, 124, 24),
            (48, 139, 32),
            (80, 117, 24),
            (104, 133, 48),
            (152, 108, 40),
            (192, 132, 32),
            (224, 110, 32),
        ]
        for x, y, w in base:
            p.rect(x, y, w, 208 - y, 1)
            p.rect(x + 2, y - 3, w - 4, 3, 1)
            windows(x + 3, y + 9, w - 6, 32)
        if stage == 2:
            for x, y in [(28, 89), (36, 82), (44, 94), (202, 77)]:
                p.rect(x, y, 4, 62, 1)
                p.rect(x - 1, y, 6, 3, 2)
                p.line(x, y - 3, x + 10, y - 10, 1)
        elif stage == 4:
            for x, y in [(54, 93), (113, 77), (161, 96)]:
                p.oval(x, y, 14, 6, 2)
                p.rect(x - 14, y, 29, 43, 2)
                p.rect(x - 14, y + 9, 29, 3, 1)
                p.rect(x - 14, y + 27, 29, 3, 1)
                p.rect(x - 1, y - 11, 3, 7, 2)
        else:
            for x in (54, 145):
                p.poly(
                    [
                        (x, 149),
                        (x + 8, 116),
                        (x + 6, 95),
                        (x + 29, 95),
                        (x + 26, 116),
                        (x + 36, 149),
                    ],
                    2,
                )
                p.rect(x + 5, 94, 26, 3, 3)
                p.rect(x + 8, 121, 19, 2, 1)
        p.rect(0, 160, 256, 3, 2)
        p.rect(0, 166, 256, 2, 2)
        for x in range(0, 256, 16):
            p.line(x, 166, x + 10, 174, 2)
    else:
        for x, y in [
            (7, 26),
            (25, 63),
            (42, 13),
            (71, 48),
            (92, 85),
            (112, 29),
            (137, 57),
            (164, 17),
            (180, 71),
            (201, 38),
            (230, 16),
            (240, 94),
        ]:
            p.dot(x, y, 3)
            if x % 3 == 1:
                p.line(x - 1, y, x + 1, y, 2)
                p.line(x, y - 1, x, y + 1, 2)
        if stage == 3:
            p.oval(171, 65, 16, 16, 2)
            p.oval(177, 59, 14, 14, 0)
            for x in range(0, 256, 32):
                top = 111 + ((x >> 3) & 16)
                p.poly([(x - 18, 177), (x + 5, top), (x + 25, 177)], 1)
                p.poly([(x - 8, 158), (x + 5, top - 10), (x + 18, 158)], 1)
        else:
            p.oval(82, 80, 25, 25, 1)
            p.oval(74, 71, 6, 3, 2)
            p.oval(90, 85, 4, 4, 2)
            p.line(46, 94, 117, 65, 2)
            p.line(47, 96, 118, 67, 2)
            # Glass dome with radial glazing on the orbiting seed station.
            for x in (0, 144):
                p.oval(x + 56, 162, 46, 40, 1)
                p.line(x + 12, 147, x + 100, 147, 2)
                for d in (-29, 0, 29):
                    p.line(x + 56, 122, x + 56 + d, 162, 2)
        p.rect(0, 166, 256, 42, 1)
        p.rect(0, 172, 256, 2, 2)
    return p


banks = []
maps = {}
panos = {}
groups = [[0, 1, 5], [2, 4, 6], [3, 7]]
for b, stages in enumerate(groups, 1):
    t = Tiles()
    for stage in stages:
        m = []
        for name in names:
            a = terrain(name, stage)
            m.extend(t.add(a.tile(x, y)) for y in (0, 8) for x in (0, 8))
        maps[stage] = m
        p = panorama(stage)
        pano = [t.add(p.tile(x, y)) for y in range(0, 208, 8) for x in range(0, 256, 8)]
        panos[stage] = pano
    banks.append(t)
for st in range(8):
    header += array("meta" + str(st), maps[st])
header += (
    "static const unsigned char* const metamaps[]={"
    + ",".join("meta" + str(i) for i in range(8))
    + "};\n"
)
# Intern the 26-tile vertical sky strips so flat sky and ground cost little PRG.
columns = []
for st in range(8):
    ids = []
    pano = panos[st]
    for x in range(32):
        col = pano[x::32]
        if col not in columns:
            columns.append(col)
        ids.append(columns.index(col))
    header += array("skycols" + str(st), ids)
header += array("skydata", [v for col in columns for v in col])
header += (
    "static const unsigned char* const skymaps[]={"
    + ",".join("skycols" + str(i) for i in range(8))
    + "};\n"
)


# 8x16 hardware sprites use adjacent pairs of CHR tiles in the second table.
def sprites(bank):
    if bank == 0:
        return menu_sprites(Pic, animal)
    slots = []

    def add(p):
        off = len(slots)
        for y in range(0, p.h, 16):
            for x in range(0, p.w, 8):
                slots.append(p.tile(x, y) + p.tile(x, y + 8))
        return off

    for k in range(4):
        for pose in range(4):
            add(animal(k, pose))
    for k in range(8):
        for pose in range(2):
            add(crop(k, pose))
    bosses = {0: [0, 1, 2], 1: [0, 1, 5], 2: [2, 4, 6], 3: [3, 7, 0]}[bank]
    for k in bosses:
        add(king(k))
    for kind in (
        "poop",
        "spit",
        "fist",
        "heavy",
        "seed",
        "fire",
        "alert",
        "spark",
        "leaf",
        "pause",
    ):
        p = Pic(8, 16)
        if kind == "poop":
            p.oval(4, 6, 3, 3, 1)
            p.oval(4, 7, 2, 2, 3)
            p.line(4, 2, 5, 5, 3)
        if kind == "spit":
            p.oval(4, 7, 3, 2, 3)
            p.line(0, 9, 4, 7, 2)
        if kind in ("fist", "heavy"):
            p.oval(3, 7, 3, 4, 1)
            p.oval(4, 7, 3, 3, 3)
            p.line(3, 5, 3, 7, 2)
            p.line(5, 5, 5, 7, 2)
        if kind in ("seed", "fire"):
            p.oval(4, 7, 3, 3, 1)
            p.oval(4, 7, 2, 2, 3)
            p.dot(3, 6, 2)
            if kind == "fire":
                p.line(4, 6, 6, 1, 2)
        if kind == "alert":
            p.rect(3, 1, 2, 7, 3)
            p.rect(3, 11, 2, 2, 3)
        if kind == "spark":
            for x, y in [(0, 1), (7, 1), (0, 13), (7, 13)]:
                p.line(4, 7, x, y, 3)
        if kind == "leaf":
            p.poly([(0, 12), (1, 5), (7, 2), (6, 9)], 2)
            p.line(0, 12, 5, 5, 3)
        if kind == "pause":
            p.rect(1, 2, 2, 11, 3)
            p.rect(5, 2, 2, 11, 3)
        add(p)
    for k in range(4):
        p = Pic(8, 16)
        p.rect(0, 2, 8, 12, 1)
        letter(p, str(k + 1), 1, 4, 1, 3)
        add(p)
    for hp in range(7):
        p = Pic(8, 16)
        p.rect(0, 2, 7, 12, 1)
        p.rect(1, 3, 5, 10, 2)
        for j in range(hp):
            p.rect(1, 12 - j * 2, 5, 1, 3)
        add(p)
    for n in range(9):
        p = Pic(8, 16)
        p.rect(0, 4, 8, 6, 1)
        p.rect(0, 5, n, 3, 3)
        add(p)
    assert len(slots) <= 128, len(slots)
    return b"".join(slots) + bytes(32 * (128 - len(slots)))


# Use a common text range on stage cards while displaying the native level panorama.
for tilebank in banks:
    assert len(tilebank.t) <= 202
    tilebank.t += [bytes(16)] * (202 - len(tilebank.t))
    tilebank.t.extend(title.t[: len(chars)])
    for z in range(2):
        p = Pic(8, 8)
        p.rect(1, 2, 6, 4, 2)
        p.rect(2, 3, 4, 2, 3 if z else 0)
        tilebank.t.append(p.tile(0, 0))
header += f"#define STAGE_FONT 202\n#define ROUTE_PIP {202 + len(chars)}\n"
(OUT / "art.chr").write_bytes(
    b"".join(t.bytes() + sprites(i) for i, t in enumerate([title] + banks))
)
(OUT / "art.h").write_text(header)
print("BG tiles per bank:", [len(t.t) for t in [title] + banks])
