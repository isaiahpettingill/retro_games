# Climb, Ducky, Climb!

Climb Mount Everest as a duck with one strong wingbeat. The continuous route has 112 jumps in eight sections. Land on the summit flag to finish.

## Play

Open `Climb-Ducky-Climb.gbc` in a Game Boy Color emulator, or copy the ROM to a compatible flash cartridge. Select Game Boy Color mode if the emulator asks for a system. Press **Start** for Timed mode or **Select** for Hard mode. Press **A** on the title screen to open the field guide.

| Control | Action |
| --- | --- |
| Left or Right | Walk or steer in the air. |
| A | Jump. You have a short grace period after stepping off an edge. |
| B in the air | Use one wingbeat. A quick tap after takeoff is stored until the duck can gain height. For maximum height, flap near the top of your jump. A second press of A can also flap. |
| Start | Pause or resume. |
| Hold Select in Timed | Return to the highest camp flag you have landed on. You can do this during a tumble. |
| Select while paused | Return to camp in Timed mode or end a Hard run and save its result. |
| Up while paused | Switch sound on or off. |

Existing battery saves work with the renamed ROM. If your emulator names saves after ROM files, copy your save to the new ROM basename.

## On the mountain in Timed mode

Ice has little traction. Green ledges drift sideways and carry the duck. Brown shale cracks, drops away, and forms again. A flashing mark warns of a falling icicle. At the first one, jump from the middle or left side of the rock onto the wide ice shelf above. A normal jump clears it. Wind streaks show the gust direction.

A short hop back to your ledge is a normal landing. A longer drop below your takeoff ledge starts a tumble. The duck spins, bounces, and rolls until it comes to rest. After about two seconds, it can stand once it has support. It takes no fall damage. You resume where it settles, even if the fall crosses into an earlier section.

Land on a flag to save that camp. **Start** on the title screen continues from the saved camp after a power cycle. With a save present, **B** opens the new-climb confirmation. The title screen gives **A** access to the field guide in both cases.

## Climb time

The bottom of the play screen shows your current time. The summit screen shows your time and saved best. Time runs during play, including falls and camp recall, and stops while paused. A best time must start from Base Camp and reach the summit in one session. To attempt a new record after saving at a higher camp, press **B** on the title screen and confirm a new climb. Starting a new climb keeps the best time.

## Hard mode

The camera rises on its own. Catch another ledge before the duck drops below the screen. Each run generates a new route. Higher sections have faster scrolling, more frequent gusts, and more slippery, moving, and crumbling ledges. Some jumps need the wingbeat. The bottom of the screen shows your highest landing above base, in game meters. The result screen saves your personal height record separately from the Timed record.

## Art and music

The ascent takes the scenery from dawn through midday, sunset, and moonlight. Hard mode repeats the sky cycle as you climb. The editable [duck sprite](art/duck.aseprite) has separate body and scarf layers and tags for idle, walk, jump, flap, and tumble.

The soundtrack cycles through three new Game Boy arrangements of traditional melodies. Hard mode increases their tempo as the camera speeds up.

- [The Bear Went Over the Mountain](https://abcnotation.com/tunePage?a=back.numachi.com%3A8000%2Fdtrad%2Fabc_dtrad.tar.gz%2Fabc_dtrad%2FJOLLGOOD%2F0000), using the traditional “For He's a Jolly Good Fellow” air.
- [Ducks on the Millpond](https://abcnotation.com/tunePage?a=tunearch.org%2Fwiki%2FDucks_on_the_Millpond.no-ext%2F0002), a Virginia fiddle reel.
- [Soldier's Joy](https://abcnotation.com/tunePage?a=trillian.mit.edu%2F~jc%2Fmusic%2Fbook%2FSCD%2FBook02%2F0012), a traditional fiddle tune.

## Build from source

Use GBDK-2020 4.4.0 and GNU Make. From this directory, run the following command with the path to the extracted GBDK directory.

```sh
make GBDK_HOME=/path/to/gbdk
```

The build writes `build/Climb-Ducky-Climb.gbc`. It also writes a symbol file for the emulator check. The cartridge uses MBC5, a 256 KiB ROM, and 8 KiB of battery-backed RAM. Two save slots protect the last complete camp record if a write is interrupted.

The C sources in `art/` contain the compiled tile graphics. A normal build uses these files directly. To edit the artwork or course, change the Python scripts in `tools/`, then regenerate the assets.

```sh
uv run --with pillow --with numpy python tools/art.py
uv run python tools/course.py
make GBDK_HOME=/path/to/gbdk
```

## Check the course

Run `make check-route` with a native C compiler to test the cartridge physics. It checks each of the 112 jumps from three takeoff positions at every phase of the 256-tick obstacle cycle. The check requires a five-tick launch window, a landing inside the ledge, and a wait short enough for crumbling shale.

Run `make check-hard` to exercise 64 generated routes through the highest difficulty, including camera losses and route recycling.

After a cartridge build, replay the recorded controller inputs with this command. Three upper ledges require a wingbeat. Tap **B** near the top of those jumps.

```sh
uv run --python 3.12 --with pyboy==2.9.0 python checks/replay.py
```

The check starts at power-on with a blank save. It verifies every landing and the summit screen. It reads game state for the checks and sends ordinary button input to control the duck.

The compiler runtime uses the GBDK library license in `GBDK-LICENSE.txt`.

The original game code and assets use the [0BSD license](LICENSE).
