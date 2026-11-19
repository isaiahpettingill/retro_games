"""Controller-only playthrough. RAM reads supply observations to the bot."""

from emulator import Emulator, A, B, START, SELECT, UP, RIGHT, LEFT
from route import plan
import argparse
from pathlib import Path
import re


class Pilot:
    def __init__(self, e):
        self.e = e
        self.previous = [0] * 4
        self.geom = [
            [int(x) for x in line.split(",")]
            for line in re.findall(
                r" geo\d+\[\]=\{([\d,]+)\}", Path("build/world.h").read_text()
            )
        ]
        self.flags = [
            [int(x) for x in line.split(",")]
            for line in re.findall(
                r" feat\d+\[\]=\{([\d,]+)\}", Path("build/world.h").read_text()
            )
        ]
        self.plans = [[] for _ in range(4)]

    def action(self, i):
        e = self.e
        g = e.get
        st = g("stage")
        x = g("px", i, True)
        y = g("py", i)
        kind = g("kind", i)
        t = g("tick")
        keys = RIGHT | B
        ground = g("grounded", i)
        c = x >> 4
        # Look for pits, rising terrain, and spikes before the front foot.
        geom = self.geom[st]
        gnd = geom[c] >> 4
        if g("boss") == 1:
            bx = g("bx", word=True)
            by = g("by")
            if kind == 3:
                keys = B
                distance = abs(bx - x)
                # Hold a firing line. Turn once to aim. Jump over an approaching
                # commander or a low projectile, then resume ground fire.
                if distance > 144 or (bx > x) != g("face", i):
                    keys |= RIGHT if bx > x else LEFT
                if ground and (
                    (distance < 47 and by > y - 28)
                    or any(
                        g("life", j)
                        and abs(x - g("fx", j, True)) < 27
                        and abs(y - 8 - g("fy", j)) < 18
                        for j in range(8, 12)
                    )
                ):
                    keys |= A
            elif kind == 0:
                keys = B | (RIGHT if bx > x + 5 else LEFT if bx + 5 < x else 0)
                if ground or (y > by - 27 and g("flight", i) and (t % 8) < 4):
                    keys |= A
            else:
                keys = B | (RIGHT if bx > x + 10 else LEFT if bx < x - 10 else 0)
                if ground and abs(bx - x) < 64:
                    keys |= A
        elif kind != 0:
            if not self.plans[i]:
                v = g("vy", i)
                v = v if v < 128 else v - 256
                self.plans[i] = plan(
                    geom,
                    self.flags[st],
                    (x, y, v, g("frac", i), bool(ground)),
                    3 if kind == 3 else 2,
                )
            keys = self.plans[i].pop(0)
        elif ground:
            look = range(c, min(len(geom), c + 4))
            # Regular jumps also reach optional platforms and avoid contact damage.
            if (
                any((geom[j] >> 4) != gnd for j in look)
                or t % 51 < 6
                or any(
                    g("ec", j) != 255 and x - 10 <= g("ex", j, True) <= x + 38
                    for j in range(5)
                )
            ):
                keys |= A
        elif (
            kind == 0
            and g("flight", i)
            and y > 172
            and (g("vy", i) < 128)
            and (t & 7) == 0
        ):
            keys |= A
        # A jump requires a fresh edge.
        if self.previous[i] & A:
            keys &= ~A
        self.previous[i] = keys
        return keys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--players", type=int, default=1)
    p.add_argument("--animal", type=int, default=3)
    p.add_argument("--sector", type=int, default=1)
    p.add_argument("--limit", type=int, default=150000)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--stop-at-clear", action="store_true")
    args = p.parse_args()
    e = Emulator()
    e.run(65)
    e.press(START)
    for _ in range(args.players - 1):
        e.press(SELECT)
    for _ in range(args.animal):
        e.press(RIGHT)
    for _ in range(args.sector - 1):
        e.press(UP)
    e.press(START)
    pilot = Pilot(e)
    last = (-1, -1)
    lasttick = -1
    buttons = [0] * 4
    seen = set()
    for f in range(args.limit):
        stage = e.get("stage")
        mode = e.get("mode")
        if (stage, mode) != last:
            print("frame", f, "stage", stage + 1, "mode", mode, flush=True)
            last = (stage, mode)
            if mode == 2 and stage >= args.sector and args.stop_at_clear:
                break
        if mode == 6:
            e.run(20, 0)
            e.press(START)
            assert e.get("mode") == 1 and e.get("stage") == 0
            print("VICTORY", flush=True)
            break
        if mode == 3:
            tick = e.get("tick")
            if tick != lasttick:
                buttons = [pilot.action(i) for i in range(args.players)]
                lasttick = tick
            e.run(1, buttons)
            if e.get("boss") == 1 and stage not in seen:
                seen.add(stage)
                print("arena", f, stage + 1, flush=True)
            if args.verbose and f % 1000 == 0:
                print(
                    f,
                    "x",
                    e.get("px", word=True),
                    "y",
                    e.get("py"),
                    "hp",
                    e.get("hp"),
                    "cp",
                    e.get("checkpoint"),
                    "boss",
                    e.get("hits"),
                    "tick",
                    tick,
                    flush=True,
                )
        else:
            e.run(1, 0)
    else:
        print(
            "TIMEOUT",
            e.get("stage") + 1,
            e.get("px", word=True),
            e.get("py"),
            e.get("boss"),
            e.get("hits"),
            flush=True,
        )
        e.snap("timeout")
        raise SystemExit(2)
    e.close()


if __name__ == "__main__":
    main()
