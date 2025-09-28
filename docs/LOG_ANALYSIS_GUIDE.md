# Log Analysis Guide

## Purpose
Consistent log analysis helps us understand how live LLM players interpret the game, spot bugs, and plan follow-up content updates. This guide captures the required workflow so every run review produces actionable insight without re-reading the entire process from scratch.

## Standard Workflow
1. **Start from the player’s POV.** Open `logs/<theme>/<edition>/<game_id>/Player_*_chat.log` before `game.log` to mirror what the player actually saw.
2. **Work round-by-round.** For each round, capture:
   - Actions performed (in order).
   - The likely reasoning based on prior observations.
   - A better alternative the player could have taken, given their knowledge.
   - Concrete code/content adjustments that would make the better action more likely.
3. **Flag supporting details.** After the round breakdown, summarize:
   - Interesting player communications.
   - Non-action text (e.g., passes, invalid commands) that reveal UX friction.
   - Suspected bugs or problematic content surfaced during the run.
   - A prioritized “Fixes before next run” checklist.
4. **Store the analysis with the run.** Create `logs/<theme>/<edition>/<game_id>/RUN_ANALYSIS.md` in the same directory as `game.log`. Use the template below so future reviewers can find everything quickly.
5. **Report the path.** After saving the file, note the exact path (e.g., `logs/.../RUN_ANALYSIS.md`) in your recap so teammates can open it immediately.

## RUN_ANALYSIS.md Template
```
# Run Analysis — <character(s) or run label> (<game_id>)

## Overview
- Players / characters
- Settings (rounds, AP, overrides)
- Outcome (win / quit / failure)
- Notes (e.g., source logs inspected first)

## Round-by-Round (Player_X – Character)
#### Round N — `Player_*_chat.log:<line>`
- **Actions:** …
- **Why:** …
- **Better:** …
- **Adjustment:** …

…repeat for each round…

## Notable Character Communications
- …

## Notable Non-Action Text
- …

## Potential Bugs / Content Risks
- …

## Fixes BEFORE Next Run
- …
```

## Example Analysis
A complete example for Father Marcus’ single-player test on 2025-09-28 is stored in
`logs/fantasy/hearth_and_shadow/2025-09-28_08hr_30min_53sec_14d1b863/RUN_ANALYSIS.md`.
Use that file as a reference for the level of detail expected, especially the round-by-round structure and closing checklists.

On future runs, always create or update the corresponding `RUN_ANALYSIS.md` beside that run’s logs and leave this guide untouched.
