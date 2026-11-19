"""Verify the field guide, pad routing, animal powers, pause and co-op recovery."""

from emulator import Emulator, A, B, LEFT, RIGHT, UP, DOWN, SELECT, START


def launch(e, players=1, animal=0, sector=1):
    e.run(80, 0)
    e.press(SELECT)
    e.press(A)
    e.press(START)
    assert e.get("mode") == 1
    for _ in range(players - 1):
        e.press(SELECT)
    for _ in range(animal):
        e.press(RIGHT)
    if sector == 8:
        e.press(DOWN)
    e.press(START)
    e.run(240, 0)
    assert e.get("mode") == 3 and e.get("stage") == sector - 1


def write(e, key, n, i=0, wide=False):
    address = e.sym[key] + i * (1 + wide)
    e.ram[address] = n & 255
    if wide:
        e.ram[address + 1] = n >> 8


def pixels(e):
    e.capture = True
    e.run(2, 0)
    e.capture = False
    return e.image.tobytes()


def verify_menus():
    e = Emulator()
    e.run(80, 0)
    e.press(SELECT)
    first = pixels(e)
    pages = {first}
    for _ in range(3):
        e.press(RIGHT)
        pages.add(pixels(e))
    assert len(pages) == 4
    e.press(RIGHT)
    assert pixels(e) == first
    e.press(B)
    e.press(START)
    solo = pixels(e)
    e.press(LEFT)
    assert e.get("kind") == 3 and pixels(e) != solo
    e.press(RIGHT)
    assert pixels(e) == solo
    e.press(START, 3)
    assert e.get("count") == 4 and pixels(e) != solo
    e.press(SELECT)
    assert e.get("count") == 1 and pixels(e) == solo
    e.press(UP)
    assert e.get("stage") == 1 and pixels(e) != solo
    e.press(DOWN)
    assert pixels(e) == solo
    e.close()


def verify():
    verify_menus()
    e = Emulator()
    launch(e, 4)
    assert [e.get("hp", i) for i in range(4)] == [3, 4, 6, 3]
    e.run(5, [A, B, LEFT, RIGHT])
    assert [e.get("pads", i) for i in range(4)] == [128, 64, 2, 1]
    assert e.get("py", 0) < 192 and e.get("swing", 1) > 0
    e.run(3, 0)
    e.run(4, [A, 0, B, B | RIGHT])
    assert e.get("flight", 0) == 2 and e.get("swing", 2) > 0
    assert e.get("life", 3) > 0 and e.get("style", 3) == 1
    e.run(3, 0)
    e.run(4, B)
    assert e.get("life", 0) > 0 and e.get("style", 0) == 0
    e.press(START)
    tick = e.get("tick")
    e.run(20, RIGHT)
    assert e.get("paused") and e.get("tick") == tick
    e.press(START)
    assert not e.get("paused") and e.get("tick") != tick
    # Seed a downed ally and a later team wipe. The ROM handles both recoveries.
    e.run(4, 0)
    write(e, "hp", 0, 2)
    write(e, "down", 8, 2)
    e.run(24, 0)
    assert e.get("hp", 2) == 6 and not e.get("down", 2)
    write(e, "checkpoint", 43)
    for i in range(4):
        write(e, "down", 25, i)
        write(e, "hp", 0, i)
    e.run(70, 0)
    assert e.get("checkpoint") == 43 and e.get("camera", word=True) == 43 * 16
    assert [e.get("hp", i) for i in range(4)] == [3, 4, 6, 3]
    e.close()
    e = Emulator()
    launch(e, 1, 1, 8)
    while e.get("px", word=True) < 194 and e.frames < 1500:
        e.run(1, RIGHT)
    assert e.get("px", word=True) // 16 == 12
    e.run(18, UP)
    assert e.get("py") < 170 and e.get("vy") == 0
    e.close()
    print(
        "PASS: field guide, four pads, four powers, pause, ally revival, checkpoint restart, vine climbing"
    )


if __name__ == "__main__":
    verify()
