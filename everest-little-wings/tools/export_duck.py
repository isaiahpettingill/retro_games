"""Write the game duck as a layered, editable Aseprite animation."""
from pathlib import Path
from struct import pack
from zlib import compress

from art import duck_pixels

def string(value):
    encoded = value.encode("utf-8")
    return pack("<H", len(encoded)) + encoded

def chunk(kind, data):
    return pack("<IH", len(data) + 6, kind) + data

def layer(name):
    return chunk(0x2004, pack("<HHHHHHB3x", 3, 0, 0, 16, 16, 0, 255) + string(name))

def cel(index, rgba):
    data = pack("<HhhBHh5xHH", index, 0, 0, 255, 2, 0, 16, 16)
    return chunk(0x2005, data + compress(rgba))

def tags():
    ranges = ((0,0,"Idle"), (1,2,"Walk"), (3,3,"Jump"), (4,4,"Flap"), (5,12,"Tumble"))
    data = pack("<H8x", len(ranges))
    for first, last, name in ranges:
        data += pack("<HHBH10x", first, last, 0, 0) + string(name)
    return chunk(0x2018, data)

def export(path):
    palette = ((0,0,0,0), (16,41,58,255), (247,239,181,255), (255,165,49,255), (247,66,41,255))
    frames = []
    for pose in range(13):
        pixels = duck_pixels(pose).ravel()
        body = bytes(c for p in pixels for c in palette[1 if p == 4 else p])
        scarf = bytes(c for p in pixels for c in palette[4 if p == 4 else 0])
        chunks = ([layer("Duck"), layer("Scarf"), tags()] if pose == 0 else []) + [cel(0, body), cel(1, scarf)]
        data = b"".join(chunks)
        frames.append(pack("<IHHH2xI", 16 + len(data), 0xf1fa, len(chunks), 100, 0) + data)
    data = b"".join(frames)
    header = pack("<IHHHHHIH8xB3xHBBhhHH", 128 + len(data), 0xa5e0, 13, 16, 16, 32, 1, 100, 0, 0, 1, 1, 0, 0, 16, 16)
    path.write_bytes(header.ljust(128, b"\0") + data)

if __name__ == "__main__":
    export(Path(__file__).resolve().parents[1] / "art" / "duck.aseprite")
