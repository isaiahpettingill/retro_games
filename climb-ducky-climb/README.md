# Climb Ducky Climb

## Build

Requires GBDK-2020 4.4.0 and GNU Make.

```sh
make GBDK_HOME=/path/to/gbdk
```

Output: `build/Climb-Ducky-Climb.gbc`.

The generated C assets are included. To regenerate art and course data after editing the Python tools:

```sh
uv run --with pillow --with numpy python tools/art.py
uv run python tools/course.py
make GBDK_HOME=/path/to/gbdk
```

The game source and assets use the 0BSD license (`LICENSE`). The GBDK runtime has its own license (`GBDK-LICENSE.txt`).
