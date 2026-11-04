# Roll Streak Tracker

Separate from the arbitrage bot in the repo root. Log CSGORoll **Roll** results and see, for every
block of 100 rolls, how many times green hit 2 in a row and 3 in a row.

## Use
- Press `r` (red), `b` (black), `g` (green), `p` (bait) after each roll, or click the buttons.
- `Backspace` undoes the last roll.
- Rolls are saved to `rolls_log.csv` next to the program.

## Table columns (one row per 100 rolls)
Rolls, Greens, Green %, 2x, 2x %, 3x, 3x %, 4x+.
- 2x / 3x / 4x+ = runs of exactly 2 / exactly 3 / 4 or more consecutive greens.
- 2x % and 3x % = those runs divided by the green hits in that block.

## Get the .exe
- GitHub: Actions -> "Build Roll Tracker exe" -> Run workflow, then download the `RollTracker-windows` artifact.
- Or on Windows run `build_roll_tracker.bat` in this folder.
