# Content Creator Guide

This guide explains how Motive’s YAML-driven content system works and how to craft compelling rooms, objects, characters, and motives. Use it alongside the playtest and log analysis workflows to keep narrative iterations tight.

## 1. Repository Layout
- `configs/core*.yaml` – shared default actions/objects.
- `configs/themes/<theme>/<...>.yaml` – theme-level overrides.
- `configs/themes/<theme>/editions/<edition>/` – edition-specific content:
  - `*_rooms.yaml` – room entity definitions.
  - `*_objects.yaml` – generic objects used across motives.
  - `*_motive_objects.yaml` – motive-specific artifacts (e.g., shrine altars, Saint’s Bone).
  - `*_characters.yaml` – character definitions, properties, motives.
  - `*_actions.yaml` – edition-specific action tweaks (rare).
  - `*_v2.yaml` – consolidated include entry point used by `configs/game.yaml`.

## 2. Entity Definitions
Each YAML file follows the same top-level schema:
```yaml
entity_definitions:
  <entity_id>:
    behaviors: [object|room|character]
    attributes: {...}
    properties: {...}
    interactions: {...}
    action_aliases: {...}
```
- **Rooms** (`behaviors: [room]`): define `description`, `exits`, and optional `objects` seeded in the room.
- **Objects**: use `properties` to mark `pickupable`, `usable`, `size`, custom traits, etc. `interactions` map action verbs to effects.
- **Characters**: hold metadata (`name`, `backstory`), gameplay `properties`, and `motives` (see below).

### Interaction Effects
Effects drive gameplay without writing code:
- `set_property` / `increment_property` – mutate player, object, or room properties.
- `generate_event` – send narrative text to targeted observers (`player`, `room_characters`, etc.).
- Conditionals (with `when:`) gate effects based on existing properties (e.g., only cleanse the altar when it’s tainted).

Tips:
- Keep interaction text in-world (“The angel statue weeps tar…”) vs. mechanical (“set property to true”).
- Use `action_aliases` to accommodate intuitive verbs (`read`, `investigate`, `sanctify`).

## 3. Character Motives
Character entries in `*_characters.yaml` define motive state:
```yaml
properties:
  cult_locations_mapped: { type: boolean, default: false }
  ...
computed:
  ... (optional expressions)
motives:
  - id: avenge_partner
    description: ...
    success_conditions:
      - operator: AND
      - type: character_has_property
        property: cult_locations_mapped
        value: true
        progress_message: "You know their meeting points..."
    failure_conditions:
      ...
```
- Use boolean/number `properties` to track player progress.
- `success_conditions` and `failure_conditions` combine these into motive logic. Every success condition may include a `progress_message` that fires once when satisfied.
- Keep `progress_message` narrative (e.g., “The graves rest easy again…”) so players receive in-fiction reinforcement.
- Add `status_prompts` to surface an in-fiction status summary each turn. The engine evaluates prompts top-to-bottom, delivering the first message whose optional `condition` passes—include a final unconditional prompt as the default.

## 4. Motive Objects
The `*_motive_objects.yaml` file collects specialized props used only by motives. Pattern:
- Provide `look` text that hints at how to interact.
- Gate `use` interactions by checking prerequisite properties (`target_has_property`, `player_has_property`, etc.).
- Emit narrative follow-ups that point to remaining steps (“Shrine cleansed! Gather the evidence compiler…”).

## 5. Writing Interesting Content
- **Ground every clue** in a physical object or room description. Players should discover goals organically.
- **Layer breadcrumbs.** Diary entries point to maps, maps to hideouts, hideouts to tools. Avoid one-and-done hints; reinforce through multiple objects.
- **Use progress pings** (`progress_message` or extra `generate_event` effects) after key milestones to steer players without forcing them.
- **Balance gating vs. exploration.** Prefer narrative nudges over hard blocks. Let players fail if they ignore clues, but ensure the clues exist.
- **Mind inventory friction.** Set `size` thoughtfully and consider post-pickup messaging when an item can be dropped.

## 6. Validating Content
1. **Unit coverage (optional but encouraged).** Add targeted tests under `tests/` if you introduce new property logic.
2. **Playtest.** Use the workflow in `docs/PLAYTEST_WORKFLOW.md` to run LLM-driven games and capture insights.
3. **Log analysis.** Follow `docs/LOG_ANALYSIS_GUIDE.md` to turn transcripts into concrete fixes.
4. **Iterate.** Update YAML copy/logic, re-run playtests, and repeat until the experience feels self-directed and winnable.

## 7. Helpful Conventions
- Use emojis and bold headings for high-signal feedback (e.g., `**🧭 Case Outlook:**`).
- Keep YAML ASCII (no smart quotes) for consistency.
- When in doubt, mock a player turn by filling properties manually to ensure interactions fire as expected.

Happy worldbuilding!
