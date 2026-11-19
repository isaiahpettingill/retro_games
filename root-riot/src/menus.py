"""Compile artwork and static nametables for the NES front end."""


# The art compiler calls this module with its tile, pixel and font primitives.
def radish(Pic):
    # The radish uses a green palette for the leafy upper strip.
    p = Pic(64, 64)
    p.poly(
        [
            (27, 22),
            (10, 13),
            (5, 4),
            (15, 4),
            (27, 11),
            (26, 1),
            (34, 5),
            (37, 13),
            (44, 3),
            (58, 2),
            (51, 12),
            (39, 19),
        ],
        1,
    )
    p.poly([(28, 17), (12, 9), (10, 6), (19, 9), (28, 13)], 2)
    p.poly([(30, 5), (34, 9), (35, 15)], 3)
    p.poly([(37, 17), (46, 7), (53, 5), (50, 10)], 2)
    p.poly(
        [
            (7, 31),
            (16, 21),
            (30, 16),
            (44, 17),
            (53, 22),
            (58, 30),
            (56, 39),
            (49, 47),
            (37, 53),
            (23, 55),
            (17, 61),
            (8, 63),
            (13, 58),
            (15, 52),
            (8, 46),
            (5, 38),
        ],
        1,
    )
    p.oval(32, 34, 24, 16, 2)
    p.poly(
        [
            (10, 39),
            (19, 43),
            (33, 46),
            (48, 42),
            (39, 49),
            (23, 53),
            (19, 56),
            (20, 50),
            (14, 47),
        ],
        3,
    )
    p.poly([(11, 27), (26, 31), (25, 38), (21, 40), (14, 37)], 3)
    p.poly([(32, 31), (49, 24), (48, 34), (43, 38), (34, 37)], 3)
    p.rect(21, 31, 4, 6, 1)
    p.rect(34, 30, 4, 6, 1)
    p.line(10, 25, 26, 30, 1)
    p.line(32, 30, 50, 22, 1)
    p.line(24, 43, 31, 40, 1)
    p.line(31, 40, 35, 41, 1)
    p.line(43, 20, 48, 21, 3)
    p.line(48, 21, 52, 24, 3)
    return p


def planet(Pic):
    globe = Pic(48, 48)
    globe.oval(24, 24, 21, 21, 1)
    globe.oval(24, 23, 19, 18, 2)
    for pts in [
        [(7, 17), (13, 11), (20, 10), (24, 14), (20, 17), (18, 22), (13, 22)],
        [(15, 23), (21, 23), (24, 28), (21, 33), (17, 37), (17, 30)],
        [(28, 10), (35, 12), (40, 17), (36, 20), (32, 18), (29, 23), (26, 20)],
        [(33, 29), (39, 27), (39, 32), (34, 33)],
    ]:
        globe.poly(pts, 3)
    return globe


def build_menus(tiles, Pic, chars, array):
    def tile(draw):
        p = Pic(8, 8)
        draw(p)
        return tiles.add(p.tile(0, 0))

    def corner(p):
        p.line(4, 1, 7, 1, 2)
        p.line(1, 4, 1, 7, 2)
        p.line(1, 4, 4, 1, 2)

    def corners():
        p = Pic(8, 8)
        corner(p)
        result = []
        for v in [False, True]:
            for h in [False, True]:
                a = Pic(8, 8)
                a.p = [r[::-1] if h else r[:] for r in (p.p[::-1] if v else p.p)]
                result.append(tiles.add(a.tile(0, 0)))
        return result

    tl, tr, bl, br = corners()
    top = tile(lambda p: p.line(0, 1, 7, 1, 2))
    bottom = tile(lambda p: p.line(0, 6, 7, 6, 2))
    left = tile(lambda p: p.line(1, 0, 1, 7, 2))
    right = tile(lambda p: p.line(6, 0, 6, 7, 2))
    star = tile(
        lambda p: (p.line(2, 3, 6, 3, 2), p.line(4, 1, 4, 5, 2), p.dot(4, 3, 3))
    )
    dust = tile(lambda p: p.dot(3, 2, 1))
    dot = tile(lambda p: p.rect(3, 3, 2, 2, 2))
    hatch = tile(lambda p: (p.dot(1, 2, 1), p.dot(5, 6, 1)))
    switch = tile(
        lambda p: (
            p.line(2, 2, 0, 4, 3),
            p.line(0, 4, 2, 6, 3),
            p.line(5, 2, 7, 4, 3),
            p.line(7, 4, 5, 6, 3),
        )
    )
    stages = tile(
        lambda p: (
            p.poly([(3, 0), (6, 3), (1, 3)], 3),
            p.poly([(1, 5), (6, 5), (3, 8)], 3),
        )
    )

    class Screen:
        def __init__(self):
            self.nt = [0] * 960
            self.pal = [[0] * 16 for _ in range(16)]

        def put(self, x, y, n):
            self.nt[y * 32 + x] = n

        def text(self, x, y, s):
            for i, ch in enumerate(s):
                self.put(x + i, y, chars.index(ch))

        def centered(self, y, s):
            self.text((32 - len(s)) // 2, y, s)

        def tint(self, x, y, w, h, pal):
            for j in range(y // 2, (y + h + 1) // 2):
                for i in range(x // 2, (x + w + 1) // 2):
                    self.pal[j][i] = pal

        def frame(self, x, y, w, h):
            for i in range(1, w - 1):
                self.put(x + i, y, top)
                self.put(x + i, y + h - 1, bottom)
            for j in range(1, h - 1):
                self.put(x, y + j, left)
                self.put(x + w - 1, y + j, right)
            for i, j, k in [
                (0, 0, tl),
                (w - 1, 0, tr),
                (0, h - 1, bl),
                (w - 1, h - 1, br),
            ]:
                self.put(x + i, y + j, k)

        def stamp(self, x, y, pic):
            for j in range(pic.h // 8):
                for i in range(pic.w // 8):
                    self.put(x + i, y + j, tiles.add(pic.tile(i * 8, j * 8)))

        def attributes(self):
            return [
                sum(
                    self.pal[ay * 2 + (q >> 1)][ax * 2 + (q & 1)] << (q * 2)
                    for q in range(4)
                )
                for ay in range(8)
                for ax in range(8)
            ]

        def encode(self):
            raw = self.nt + self.attributes()
            out = []
            literals = []

            def flush():
                while literals:
                    part = literals[:127]
                    del literals[: len(part)]
                    out.extend([len(part), *part])

            i = 0
            while i < len(raw):
                n = 1
                while n < 127 and i + n < len(raw) and raw[i + n] == raw[i]:
                    n += 1
                if n >= 3:
                    flush()
                    out.extend([128 + n, raw[i]])
                    i += n
                else:
                    literals.append(raw[i])
                    i += 1
            flush()
            return out + [0]

    def title_logo():
        p = Pic(144, 88)
        # Broad, connected arcade capitals with a slant and a two-color face.
        masks = {
            "R": [62, 63, 51, 62, 60, 54, 51],
            "O": [30, 63, 51, 51, 51, 63, 30],
            "T": [63, 63, 12, 12, 12, 12, 12],
            "I": [30, 30, 12, 12, 12, 30, 30],
        }
        for y0, s in [(2, "ROOT"), (42, "RIOT")]:
            for dx, dy, color in [(2, 5, 1), (1, 3, 2), (0, 0, 3)]:
                for idx, ch in enumerate(s):
                    for r, m in enumerate(masks[ch]):
                        for c in range(6):
                            if m & (32 >> c):
                                p.rect(
                                    5 + idx * 32 + c * 5 + (6 - r) + dx,
                                    y0 + r * 5 + dy,
                                    5,
                                    5,
                                    2 if color == 3 and r >= 5 else color,
                                )
        return p

    def ridge():
        p = Pic(128, 32)
        p.poly(
            [
                (0, 19),
                (12, 16),
                (25, 17),
                (42, 13),
                (66, 18),
                (86, 14),
                (109, 16),
                (128, 19),
                (128, 32),
                (0, 32),
            ],
            1,
        )
        for x, y in [(20, 16), (84, 13), (90, 14)]:
            p.rect(x, y - 2, 2, 4, 1)
            p.poly([(x - 3, y - 2), (x + 1, y - 9), (x + 5, y - 2)], 1)
        p.rect(0, 23, 128, 2, 2)
        p.rect(0, 25, 128, 7, 1)
        for x in range(0, 128, 16):
            p.line(x, 27, x + 6, 27, 2)
            p.dot(x + 9, 30, 2)
        return p

    title = Screen()
    title.stamp(2, 5, title_logo())
    leaves = radish(Pic)
    leaves.h = 16
    title.stamp(20, 6, leaves)
    title.tint(20, 6, 8, 2, 3)
    for x, y, n in [
        (4, 3, star),
        (19, 5, dust),
        (21, 3, dot),
        (26, 2, dust),
        (29, 6, star),
        (21, 15, star),
        (2, 16, dust),
        (28, 17, dot),
        (10, 2, dust),
    ]:
        title.put(x, y, n)
    title.stamp(0, 17, ridge())
    title.stamp(16, 17, ridge())
    title.tint(0, 17, 32, 5, 3)
    title.frame(8, 22, 16, 3)
    title.centered(23, "PRESS START")
    title.tint(8, 22, 16, 3, 1)
    title.centered(27, "SELECT  GUIDE")
    title.tint(0, 26, 32, 2, 2)
    crew = Screen()
    crew.text(3, 3, "CREW")
    crew.put(8, 3, switch)
    crew.text(19, 3, "SELECT")
    crew.text(27, 3, "P")
    crew.tint(18, 2, 12, 3, 2)
    for i in range(4):
        x = 2 + (i & 1) * 14
        y = 6 + (i >> 1) * 8
        crew.frame(x, y, 14, 7)
        crew.text(x + 7, y + 2, "P" + str(i + 1))
        for yy in range(y + 1, y + 6):
            for xx in range(x + 1, x + 6):
                crew.put(xx, yy, hatch)
    crew.put(3, 25, stages)
    crew.text(5, 25, "STAGE")
    crew.text(18, 25, "START PLAY")
    crew.tint(2, 24, 12, 3, 2)
    crew.tint(16, 24, 14, 3, 1)
    guide = Screen()
    guide.centered(3, "FIELD GUIDE")
    guide.frame(9, 6, 14, 11)
    for y in range(8, 15):
        for x in range(12, 20):
            guide.put(x, y, hatch)
    guide.put(7, 11, chars.index("<"))
    guide.put(24, 11, chars.index(">"))
    guide.tint(8, 6, 16, 12, 2)
    guide.centered(27, "START  BACK")
    guide.tint(4, 26, 24, 3, 2)
    end = Screen()
    earth = planet(Pic)
    end.stamp(13, 8, earth)
    end.tint(12, 8, 8, 6, 2)
    for x, y in [(6, 6), (21, 4), (26, 13), (9, 15), (4, 19), (20, 19)]:
        end.put(x, y, star)
    end.centered(3, "EARTH SAVED!")
    end.stamp(0, 20, ridge())
    end.stamp(16, 20, ridge())
    end.tint(0, 20, 32, 4, 3)
    end.centered(26, "START  REPLAY")
    end.tint(0, 25, 32, 3, 1)
    crew_ink = []
    for size in range(1, 5):
        for i in range(4):
            crew.tint(2 + (i & 1) * 14, 6 + (i >> 1) * 8, 14, 7, 0 if i < size else 2)
        crew_ink.extend(crew.attributes())
    return array("crew_ink", crew_ink) + "".join(
        array(name, screen.encode())
        for name, screen in [
            ("title_screen", title),
            ("crew_screen", crew),
            ("guide_screen", guide),
            ("ending_screen", end),
        ]
    )


def menu_sprites(Pic, animal):
    slots = []

    def add(p):
        for y in range(0, p.h, 16):
            for x in range(0, p.w, 8):
                slots.append(p.tile(x, y) + p.tile(x, y + 8))

    for k in range(4):
        for pose in range(4):
            add(animal(k, pose))

    def portrait(k):
        p = Pic(32, 32)

        def oval(x, y, rx, ry, fill):
            p.oval(x, y, rx, ry, 1)
            p.oval(x, y - 1, max(1, rx - 2), max(1, ry - 2), fill)

        if k == 0:
            p.poly(
                [
                    (3, 24),
                    (0, 18),
                    (7, 20),
                    (10, 10),
                    (12, 6),
                    (21, 4),
                    (26, 8),
                    (27, 15),
                    (30, 17),
                    (24, 25),
                    (18, 28),
                    (8, 27),
                ],
                1,
            )
            p.oval(16, 19, 10, 7, 2)
            p.oval(19, 12, 7, 7, 2)
            p.poly([(6, 19), (15, 16), (12, 23), (8, 23)], 3)
            p.poly([(24, 13), (32, 16), (25, 18)], 3)
            p.rect(21, 9, 3, 4, 3)
            p.dot(23, 11, 1)
            p.line(10, 26, 9, 29, 3)
            p.line(18, 26, 18, 29, 3)
        elif k == 1:
            oval(6, 13, 5, 6, 2)
            oval(25, 13, 5, 6, 2)
            oval(16, 15, 11, 12, 2)
            p.oval(12, 15, 4, 4, 3)
            p.oval(20, 15, 4, 4, 3)
            p.oval(16, 21, 7, 4, 3)
            p.rect(13, 13, 2, 4, 1)
            p.rect(20, 13, 2, 4, 1)
            p.line(14, 22, 17, 23, 1)
            p.line(17, 23, 20, 21, 1)
            p.poly([(9, 8), (12, 2), (13, 6), (18, 1), (18, 7)], 2)
        elif k == 2:
            oval(7, 7, 5, 5, 2)
            oval(25, 7, 5, 5, 2)
            oval(16, 17, 13, 11, 3)
            p.oval(10, 15, 4, 4, 1)
            p.oval(22, 15, 4, 4, 1)
            p.rect(11, 14, 2, 2, 3)
            p.rect(21, 14, 2, 2, 3)
            p.poly([(13, 19), (19, 19), (16, 22)], 1)
            p.line(16, 21, 16, 23, 1)
            p.dot(15, 24, 1)
            p.dot(17, 24, 1)
        else:
            p.poly(
                [
                    (6, 30),
                    (9, 18),
                    (8, 5),
                    (11, 0),
                    (15, 8),
                    (18, 8),
                    (21, 0),
                    (24, 1),
                    (24, 12),
                    (29, 14),
                    (31, 18),
                    (26, 22),
                    (21, 22),
                    (21, 30),
                ],
                1,
            )
            p.poly(
                [
                    (8, 29),
                    (11, 17),
                    (10, 5),
                    (12, 3),
                    (14, 11),
                    (19, 10),
                    (22, 3),
                    (22, 14),
                    (28, 16),
                    (29, 18),
                    (25, 20),
                    (19, 20),
                    (19, 29),
                ],
                2,
            )
            p.oval(25, 17, 5, 3, 3)
            p.rect(19, 12, 2, 3, 1)
            p.dot(27, 16, 1)
            p.line(10, 24, 18, 27, 3)
        return p

    for k in range(4):
        add(portrait(k))
    add(radish(Pic))
    cross = Pic(8, 16)
    cross.line(1, 7, 5, 7, 3)
    cross.line(3, 5, 3, 9, 3)
    add(cross)
    assert len(slots) <= 128
    return b"".join(slots) + bytes(32 * (128 - len(slots)))
