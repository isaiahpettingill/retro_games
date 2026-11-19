"""Headless Nestopia UE frontend. Test inputs go through the NES controller ports."""

import ctypes as C, os, re
from pathlib import Path
from PIL import Image

u = C.c_uint
ptr = C.c_void_p
size = C.c_size_t
cstr = C.c_char_p


class Game(C.Structure):
    _fields_ = [("path", cstr), ("data", ptr), ("size", size), ("meta", cstr)]


class KV(C.Structure):
    _fields_ = [("key", cstr), ("value", cstr)]


class Emulator:
    def __init__(self, core=None):
        so = (
            core
            or os.environ.get("NESTOPIA_CORE")
            or next(Path(".tools").rglob("nestopia_libretro.so"))
        )
        self.lib = L = C.CDLL(str(Path(so).resolve()))
        self.cb = []
        self.buttons = [0] * 4
        self.frames = 0
        self.audio = 0
        self.pix = 0
        self.options = {}
        self.capture = False
        self.sym = {
            name: int(address, 16)
            for address, name in re.findall(
                r"al ([0-9A-Fa-f]+) \._(\w+)", Path("build/game.lbl").read_text()
            )
        }

        def callback(name, ret, args, impl):
            f = C.CFUNCTYPE(ret, *args)(impl)
            self.cb.append(f)
            getattr(L, "retro_set_" + name)(f)

        def env(cmd, data):
            cmd &= 0xFFFF
            if cmd == 10:
                self.pix = C.cast(data, C.POINTER(C.c_int))[0]
                return True
            if cmd in (9, 30, 31):
                C.cast(data, C.POINTER(cstr))[0] = b"."
                return True
            if cmd == 16:
                a = C.cast(data, C.POINTER(KV))
                for i in range(256):
                    if not a[i].key:
                        break
                    self.options[a[i].key] = a[i].value.split(b"; ")[-1].split(b"|")[0]
                self.options.update(
                    {
                        b"nestopia_select_adapter": b"ntsc",
                        b"nestopia_overscan_h": b"disabled",
                        b"nestopia_overscan_v": b"disabled",
                    }
                )
                return True
            if cmd == 15:
                a = C.cast(data, C.POINTER(KV))
                v = self.options.get(a[0].key)
                if v:
                    a[0].value = v
                    return True
            if cmd == 17:
                C.cast(data, C.POINTER(C.c_bool))[0] = False
                return True
            if cmd == 51:
                return False
            return False

        def video(data, w, h, pitch):
            if data and self.capture:
                raw = C.string_at(data, h * pitch)
                if self.pix == 1:
                    self.image = Image.frombytes(
                        "RGB", (w, h), raw, "raw", "BGRX", pitch
                    )
                else:
                    self.image = Image.frombytes(
                        "RGB", (w, h), raw, "raw", "BGR;16", pitch
                    )

        def samples(data, n):
            self.audio += n
            return n

        callback("environment", C.c_bool, [u, ptr], env)
        callback("video_refresh", None, [ptr, u, u, size], video)
        callback("audio_sample", None, [C.c_int16, C.c_int16], lambda *_: None)
        callback("audio_sample_batch", size, [ptr, size], samples)
        callback("input_poll", None, [], lambda: None)
        callback(
            "input_state",
            C.c_int16,
            [u, u, u, u],
            lambda p, d, i, b: int(p < 4 and b < 16 and (self.buttons[p] >> b) & 1),
        )
        L.retro_init()
        path = Path("release/RootRiot.nes")
        self.rom = C.create_string_buffer(path.read_bytes())
        info = Game(
            str(path).encode(), C.cast(self.rom, ptr), path.stat().st_size, None
        )
        L.retro_load_game.argtypes = [C.POINTER(Game)]
        L.retro_load_game.restype = C.c_bool
        assert L.retro_load_game(C.byref(info))
        for i in range(4):
            L.retro_set_controller_port_device(i, 1)
        L.retro_get_memory_data.argtypes = [u]
        L.retro_get_memory_data.restype = ptr
        self.ram = (C.c_uint8 * 2048).from_address(L.retro_get_memory_data(2))

    def get(self, name, index=0, word=False):
        a = self.sym[name] + index * (2 if word else 1)
        return self.ram[a] + (self.ram[a + 1] * 256 if word else 0)

    def run(self, n=1, buttons=None):
        if buttons is not None:
            self.buttons = (
                [buttons] if isinstance(buttons, int) else list(buttons)
            ) + [0] * 4
        for _ in range(n):
            self.lib.retro_run()
            self.frames += 1

    def snap(self, name):
        self.capture = True
        self.run()
        self.capture = False
        Path("build/screens").mkdir(exist_ok=True)
        self.image.resize(
            (self.image.width * 2, self.image.height * 2), Image.Resampling.NEAREST
        ).save("build/screens/" + name + ".png")

    def press(self, b, p=0):
        acts = [0] * 4
        acts[p] = b
        self.run(6, acts)
        self.run(6, 0)

    def close(self):
        self.lib.retro_unload_game()
        self.lib.retro_deinit()


B = 1
SELECT = 4
START = 8
UP = 16
DOWN = 32
LEFT = 64
RIGHT = 128
A = 256
if __name__ == "__main__":
    e = Emulator()
    e.run(100)
    e.snap("title")
    print("title", e.get("mode"), e.pix, e.options.get(b"nestopia_select_adapter"))
    e.press(START)
    e.press(SELECT)
    e.press(SELECT)
    e.press(SELECT)
    e.snap("crew")
    e.press(START)
    e.run(210, 0)
    e.snap("course")
    print(
        "game", e.get("mode"), e.get("count"), [e.get("px", i, True) for i in range(4)]
    )
    e.run(24, [A, B, LEFT, RIGHT])
    print(
        "pads",
        [e.get("pads", i) for i in range(4)],
        "x",
        [e.get("px", i, True) for i in range(4)],
        "y",
        [e.get("py", i) for i in range(4)],
    )
    e.close()
