# Root Riot

Mutant vegetables have invaded Earth. Take one to four animals from Sprout County to the Orbital Greenhouse. Defeat the commander at the end of each course to reach the next sector.

## Play

Open `release/RootRiot.nes` in an NES emulator. The game uses NTSC timing and the CNROM cartridge mapper. To use three or four controllers, enable the NES Four Score adapter and assign a gamepad to each active port. In the RetroArch Nestopia core, set **4 Player Adapter** to **NTSC**.

Press **Start** on the title screen to choose your crew. Press **Select** to open the optional field guide. Use **Left** or **Right** to see another animal and **Start** to return. Player 1 can use **Select** to set the crew size. An additional controller can join the crew on this screen with **Start**. Each active player can press **Left** or **Right** to swap animals. Player 1 presses **Start** to launch.

The first sector starts the full campaign. Use **Up** or **Down** on Crew Select to start at another sector. To resume after switching the system off, select the sector you reached. Checkpoints apply to the current session.

## Field guide

| Animal | Health | Controls |
| --- | ---: | --- |
| Bird | 3 | Press **A** to jump. Tap **A** up to three more times in the air to flap. Land to restore flight. Press **B** to drop poop from above. |
| Monkey | 4 | Press **B** for a quick melee strike. Hold **Up** or **Down** on a vine to climb. Release the direction and press **A** to jump away. |
| Panda | 6 | Press **B** for a heavy punch. The punch reaches farther and hits harder than the monkey's strike. |
| Llama | 3 | Press **B** to spit in the direction you face. Hold **B** while moving to run at full speed. To fire from one position, face the target and release the D-pad. |

All animals can move with the D-pad, jump with **A**, and stomp enemies. Hold **B** to repeat an attack. Player 1 can pause or resume with **Start**.

Flags restore the crew's health and set a checkpoint. If one animal falls, it returns while an ally is still standing. If the entire crew falls, everyone restarts together. Entering a boss arena sets another checkpoint. The boss health bar appears below the crew's health meters. An exclamation mark warns of an attack.

## Sectors

| Sector | Course | Commander |
| ---: | --- | --- |
| 1 | Sprout County | Radish Rex |
| 2 | Onion Terraces | Onion Oracle |
| 3 | Carrot Foundry | Captain Carrot |
| 4 | Midnight Canopy | Baron Broccoli |
| 5 | Beet Refinery | Battle Beet |
| 6 | Pepper Badlands | Serrano Cyclone |
| 7 | Kernel Reactor | Kernel Panic |
| 8 | Orbital Greenhouse | Emperor Eggplant |

## Build

Install Python 3, GNU Make 4.3 or later, and cc65. From this directory, run:

```sh
make
```

The build creates `release/RootRiot.nes`. If the linker cannot locate the cc65 NES runtime, supply its full path with `make NESLIB=/path/to/nes.lib`. The Python art and course compilers use the standard library.

| File | Purpose |
| --- | --- |
| `src/game.c` | Movement, collisions, combat, boss scripts, co-op recovery, menus, and music |
| `src/hardware.s` | NES startup, Four Score input, graphics transfers, sprite output, and CHR bank selection |
| `src/art.py` | Original pixel art, font, terrain, scenery, and sprite tiles |
| `src/menus.py` | Title art, crew portraits, field guide, and menu screen maps |
| `src/world.py` | Course layouts, enemy placements, platforms, vines, hazards, and checkpoints |
| `src/cart.cfg` | Cartridge memory layout |

## Emulator checks

The release passed seven full campaigns in Nestopia UE. Each animal finished alone. Crews of two, three, and four also finished. Each run entered all eight arenas and reached the victory screen through controller input. Tests ran with the normal sprite limit. The separate controls test also uses prepared game states to check revival and team recovery.

To run the checks, first build the ROM and its symbol file. Set `NESTOPIA_CORE` to the path of a Nestopia UE libretro shared library. The test frontend uses Pillow for screen captures.

```sh
export NESTOPIA_CORE=/path/to/nestopia_libretro.so
uv run --with pillow test/controls.py
uv run --with pillow test/campaign.py --players 4 --animal 0
```

For solo tests, set `--players 1`. Use `--animal 0` for bird, `1` for monkey, `2` for panda, or `3` for llama.
