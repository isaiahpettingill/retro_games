"""Replay an uninterrupted controller run against the built ROM in PyBoy 2.9.0."""
import io
from pathlib import Path
import re

from pyboy import PyBoy

root = Path(__file__).resolve().parents[1]
rom = root / "build/Climb-Ducky-Climb.gbc"
symbols = {
    name: int(address, 16)
    for name, address in re.findall(r"DEF _(\w+) 0x([0-9A-Fa-f]+)", rom.with_suffix(".noi").read_text())
}
buttons = ["right", "left", "up", "down", "a", "b", "select", "start"]
trace = (root / "checks/summit.inputs").read_bytes()
assert sum(bool(bits & 32) and (i == 0 or not trace[i-1] & 32) for i, bits in enumerate(trace)) == 3
def counter(emulator, name):
    address = symbols[name]
    return int.from_bytes(bytes(emulator.memory[address:address+4]), "little")

emulator = PyBoy(str(rom), ram_file=io.BytesIO(bytes(8192)), window="null", sound_emulated=False)
emulator.set_emulation_speed(0)
previous = 0
visited = set()
icicle_landing = None
try:
    emulator.tick(130, False)
    for inputs in trace:
        for bit, button in enumerate(buttons):
            mask = 1 << bit
            if (previous ^ inputs) & mask:
                if inputs & mask:
                    emulator.button_press(button)
                else:
                    emulator.button_release(button)
        emulator.tick(1, False)
        previous = inputs
        if emulator.memory[symbols["game_mode"]] == 2:
            assert emulator.memory[symbols["tumble"]] == 0, "The duck tumbled."
            ground = emulator.memory[symbols["ground"]]
            visited.add(ground)
            if ground == 60 and icicle_landing is None:
                icicle_landing = io.BytesIO()
                emulator.save_state(icicle_landing)
    emulator.tick(30, False)
    assert emulator.memory[symbols["game_mode"]] == 4, "The duck did not reach the summit."
    assert emulator.memory[symbols["camp"]] == 7, "The duck missed a camp."
    assert set(range(112)) <= visited, "The duck skipped a pre-summit landing."
    print("Passed. The duck landed on every ledge and reached the summit with all three wingbeat jumps.")

    record = counter(emulator, "best_frames")
    assert record == counter(emulator, "run_frames") and record > 0
    battery = io.BytesIO()
    emulator.stop(save=True, ram_file=battery)
    battery.seek(0)
    emulator = PyBoy(str(rom), ram_file=battery, window="null", sound_emulated=False)
    emulator.set_emulation_speed(0)
    emulator.tick(140, False)
    assert counter(emulator, "best_frames") == record
    print("Passed. The best climb time survived a power cycle.")

    # At the first falling icicle, an ordinary jump from the safe side must
    # reach the upper ledge with no run-up, steering, or wingbeat.
    assert icicle_landing is not None
    for delay in (0, 17, 35, 64, 95, 127, 163, 231):
        icicle_landing.seek(0)
        emulator.load_state(icicle_landing)
        for button in buttons:
            emulator.button_release(button)
        emulator.tick(delay + 12, False)
        assert emulator.memory[symbols["ground"]] == 60
        emulator.button("a", delay=4)
        emulator.tick(55, False)
        assert emulator.memory[symbols["ground"]] == 61, f"Icicle jump failed after delay {delay}"
        assert emulator.memory[symbols["tumble"]] == 0
    print("Passed. A standing jump clears the first icicle at each tested timing.")
finally:
    emulator.stop(save=False)
