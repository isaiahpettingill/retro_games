# Retro Games

Original games for retro consoles.

| Game | Console | Source and build | ROM |
| --- | --- | --- | --- |
| Climb, Ducky, Climb! | Game Boy Color | [C and GBDK-2020](everest-little-wings) | [Climb-Ducky-Climb.gbc](everest-little-wings/Climb-Ducky-Climb.gbc) |
| Root Riot | NES | [C and ca65](root-riot) | [RootRiot.nes](root-riot/release/RootRiot.nes) |
| Spud Squad | NES | ROM only in this repository | [SpudSquad.nes](spud-squad/SpudSquad.nes) |

Each game with source has its own build and test instructions. Root Riot's ca65 macros handle repeated PPU transfers and controller reads. Its build links them with cc65-generated code. Climb, Ducky, Climb! uses GBDK's C runtime and banked asset build.
