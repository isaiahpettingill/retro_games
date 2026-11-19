from emulator import *


def benchmark():
    for players in (1, 2, 3, 4):
        e = Emulator()
        e.run(60)
        e.press(START)
        for _ in range(players - 1):
            e.press(SELECT)
        e.press(START)
        e.run(200, 0)
        e.run(90, 0)
        counts = []
        for i in range(600):
            f = e.get("tick")
            e.run(1, [B | RIGHT | ((i % 46 == 0) * A)] * players)
            counts.append((e.get("tick") - f) % 256)
        print(players, "physics ticks/600 NTSC frames", sum(counts), flush=True)
        e.close()


if __name__ == "__main__":
    benchmark()
