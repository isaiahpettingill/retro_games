"""Compile eight courses from authored sixteen-column obstacle sequences."""

from pathlib import Path

# Height digits are 16-pixel rows. A dot is a pit. Platforms and special
# features use a separate layer so there is always a route for the panda.
pieces = {
    "field": ("ccccccbbbbbbbbcc", [(5, 8, 8)], [], [(7, 0), (14, 0)]),
    "steps": ("cccbbbaaaabbbccc", [(12, 14, 8)], [], [(5, 1), (13, 0)]),
    "bridge": ("ccc..cccccc..ccc", [(2, 5, 9), (10, 13, 9)], [], [(7, 0)]),
    "ladder": (
        "ccccccbbbaaabbbb",
        [(2, 5, 9), (8, 11, 7)],
        [(4, 1)],
        [(8, 1), (14, 2)],
    ),
    "beds": ("bbbccc..cccbbbbb", [(5, 8, 9)], [(12, 2)], [(2, 2), (11, 0)]),
    "trench": ("ccc...ccccc...cc", [(4, 6, 10), (9, 12, 9)], [], [(8, 3)]),
    "pipes": (
        "cccbbb..aabbbccc",
        [(5, 8, 8), (12, 15, 9)],
        [(1, 1)],
        [(3, 2), (13, 3)],
    ),
    "needles": (
        "ccccccccbbbccccc",
        [(3, 6, 9), (11, 13, 8)],
        [(4, 2), (5, 2), (12, 2)],
        [(8, 4), (15, 0)],
    ),
    "towers": (
        "ccbbbaaa...bbccc",
        [(1, 4, 8), (8, 11, 8)],
        [(3, 1)],
        [(5, 4), (12, 5)],
    ),
    "wires": ("ccc..bbbccc..bbb", [(2, 5, 8), (8, 11, 8)], [(7, 2)], [(6, 5), (13, 3)]),
    "bulwark": (
        "ccbb..aaaa..bbcc",
        [(4, 6, 9), (9, 12, 8)],
        [(2, 2), (14, 2)],
        [(7, 6), (13, 4)],
    ),
    "orbit": ("ccc...bbb...aabb", [(4, 6, 9), (9, 11, 8)], [(7, 2)], [(3, 5), (12, 7)]),
    "heart": (
        "cbb..aaa..bbbccc",
        [(2, 4, 8), (8, 10, 8), (13, 15, 9)],
        [(6, 2), (14, 2)],
        [(5, 6), (11, 7)],
    ),
}
# A different order changes the approach, enemy combinations, and jump timing.
routes = [
    ("field steps bridge field ladder".split(), [0, 1]),
    ("field ladder beds bridge steps trench".split(), [1, 0, 2]),
    ("steps pipes trench ladder beds pipes".split(), [2, 3, 1]),
    ("ladder trench towers beds needles pipes bridge".split(), [3, 1, 4]),
    ("beds needles towers pipes trench wires steps".split(), [4, 2, 3, 5]),
    ("steps wires trench towers needles wires pipes beds".split(), [5, 3, 2, 4]),
    ("pipes bulwark needles wires towers bulwark trench orbit".split(), [6, 4, 5, 3]),
    (
        "ladder orbit bulwark wires heart towers needles orbit heart".split(),
        [7, 6, 3, 5, 4],
    ),
]


def arr(name, v):
    return (
        "static const unsigned char " + name + "[]={" + ",".join(map(str, v)) + "};\n"
    )


s = ""
lengths = []
attrs = []
for n, (route, crew) in enumerate(routes):
    geometry = [0xCC] * 8
    flags = [0] * 8  # introductory runway
    for idx, key in enumerate(route):
        shape, platforms, features, spawns = pieces[key]
        base = len(geometry)
        gs = [(15 if c == "." else int(c, 16)) * 16 + 15 for c in shape]
        fs = [0] * 16
        for a, b, h in platforms:
            for j in range(a, b + 1):
                gs[j] = (gs[j] & 240) | h
        for j, k in features:
            fs[j] = k
        for ii, (j, k) in enumerate(spawns):
            enemy = crew[(idx + ii) % len(crew)] if n < 2 or ii == 0 else k
            fs[j] |= (1 + enemy) << 4
        geometry.extend(gs)
        flags.extend(fs)
        if idx % 2 == 1 and idx + 1 < len(route):
            geometry.extend([0xCF] * 8)
            flags.extend([0, 0, 0, 3, 0, 0, 0, 0])
    geometry += [0xCF] * 6
    flags += [0, 0, 3, 0, 0, 0]
    # The last 16 columns form a closed, flat boss arena.
    arena = len(geometry)
    geometry += [0xCF] * 18
    flags += [0] * 18
    for i in range(8):
        geometry[i] = 0xCF
    for i in range(3, len(flags) - 18):
        if flags[i] == 0 and geometry[i] >> 4 < 15 and i % 9 == 6:
            flags[i] = 4
    codes = []

    def palette(c, r):
        g = geometry[min(c, len(geometry) - 1)]
        floor, plat = g >> 4, g & 15
        f = flags[min(c, len(flags) - 1)] & 15
        if r >= floor and floor < 15:
            return 1
        if r == plat and plat < 15:
            return 1
        if f == 1 and 5 <= r < floor:
            return 2
        if r + 1 == floor and f in (2, 3, 4):
            return 3 if f == 3 else 2
        return 0

    for col in range(0, len(geometry), 2):
        a = tuple(
            sum(palette(col + (q & 1), r + (q >> 1)) << (2 * q) for q in range(4))
            for r in range(0, 16, 2)
        )
        if a not in attrs:
            attrs.append(a)
        codes.append(attrs.index(a))
    s += arr("att" + str(n), codes)
    lengths.append(arena)
    s += arr("geo" + str(n), geometry) + arr("feat" + str(n), flags)
s += arr("arena_cols", lengths)
s += arr("attributes", [v for a in attrs for v in a])
for k in ["geo", "feat", "att"]:
    s += (
        "static const unsigned char* const "
        + k
        + "_list[]={"
        + ",".join(k + str(i) for i in range(8))
        + "};\n"
    )
Path("build/world.h").write_text(s)
print("Course lengths in 16-pixel columns, before arenas:", lengths)
