## v2 Testing Progress (2025-09-18)

- sim_v2 subset: 116 passed, 1 skipped (local `-k sim_v2`). Broader suite is green locally.
- Minimal deterministic coverage: parse; say/whisper/shout; move; inventory; read; give; throw; help; use (incl. two-object); exit travel requirements; visibility gating.
- Hearth & Shadow deterministic coverage: pickup/drop; throw; move hidden exits; whisper privacy; torch light + dark room look; investigate room object.
- Policies enforced: attributes vs properties; no `config` dicts; no `tags` in v2; observer scopes `room_characters` and `adjacent_rooms_characters`.
- Dark room gating: `underground_tunnels` `properties.dark: true` loads at runtime; `look` gates until light.
- Action parsing: two-parameter quoting fixed; `use "Key" "Chest"` resolves both targets.
- Events: `light` and `investigate` use v2 schema (`source_room_id`, `related_player_id`, ISO8601 timestamp, `room_characters`).

Open items
- AP lifecycle: tests manually reset AP between turns; enforce engine-level AP reset in the main loop everywhere it applies.
- Pydantic warnings: clean up serialization warnings for property schemas.
- End-to-end: validate `configs/game_v2.yaml` with a longer mocked-LLM session.

Next targets
- Expand H&S object interactions (investigate variants; additional two-object use cases).
- Scripted H&S session with mocked LLM transcripts.

