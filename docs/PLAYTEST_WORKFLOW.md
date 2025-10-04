# Playtest Workflow

This workflow captures how we run narrative playtests with live LLM players, synthesize findings, and feed them back into content iterations. It complements – but does not duplicate – the analysis details in [`LOG_ANALYSIS_GUIDE.md`](LOG_ANALYSIS_GUIDE.md).

## When to Use
- You have authored new or revised content (rooms, objects, character motives) and want to evaluate the in-fiction experience end-to-end.
- You need to confirm that story-driven hints, progress pings, or UX tweaks are landing with real players before committing to larger rollouts.

## Preparation
1. **Review the target content.** Skim the relevant YAML (characters, motive objects, rooms) so you know the intended story beats.
2. **Plan the run.** Decide which character(s) to play, desired rounds/AP, and any overrides (e.g., `--character-motives detective_thorne:avenge_partner`).
3. **Keep notes handy.** Open a scratch buffer for observations you’ll later migrate into `RUN_ANALYSIS.md`.

## Running the Game
Use the CLI with the same environment as the main project. Example:
```
venv/bin/python -m motive.cli \
    --config configs/game.yaml \
    --rounds 20 \
    --ap 40 \
    --players 1 \
    --character-motives detective_thorne:avenge_partner
```
- Stick to production settings (real LLM provider, standard logging). The playtest relies on genuine model behavior to expose narrative gaps.
- If you adjust rounds/AP, note it in the eventual analysis.

## Immediately After the Run
1. **Open the player transcript first.** Start with `logs/.../Player_*_chat.log` to mirror what the participant experienced.
2. **Write the round-by-round analysis.** Follow the template in `LOG_ANALYSIS_GUIDE.md`. Use headings `Round N` with line references and capture actions, reasoning, better option, and proposed adjustment.
3. **Record supporting sections.** Note communications, non-action text (invalid commands, passes, complaints), suspected bugs, and the “Fixes BEFORE Next Run” checklist.
4. **Save the analysis.** Store the report as `logs/<theme>/<edition>/<game_id>/RUN_ANALYSIS.md` and commit the path to memory for your recap.

## Feeding Findings Back Into Content
- **Narrative focus.** Translate problems into in-world adjustments (copy updates, new hints, progress pings) rather than mechanical gates where possible.
- **Check hint coverage.** Verify that existing progress prompts fired. If the player stalled, decide whether to add a new ping, strengthen existing text, or accept the failure as valid.
- **Respect exploration.** Avoid turning guidance into rails; offer clues that reward investigation (e.g., “The Sacred Map might illuminate the hideouts”) instead of force-marching the player.
- **Keep the engine generic.** If a playtest requires story-specific hints or progress pings, implement them in YAML content (rooms, objects, motive progress messages). Never hard-code edition-specific logic in Python; future themes should be able to reuse the engine untouched.
- **Log the lessons.** When the run reveals a reusable insight (movement copy, inventory messaging, ritual pacing), update `LOG_ANALYSIS_GUIDE.md` so future reviewers look for the same pattern.

## Recap Checklist
- [ ] `RUN_ANALYSIS.md` created or updated beside the logs.
- [ ] Follow-up tasks captured in the repo (code changes, YAML edits, docs updates).
- [ ] Mention the analysis path and high-level outcome in your recap message.
- [ ] Queue another playtest if the adjustments materially change the narrative path.
