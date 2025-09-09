# AI Lessons

This file contains lessons learned from working on the Motive project. It serves as a living guide for maintaining high engineering quality and avoiding common pitfalls.

## Development Lessons

- **Fix code, don't change tests to pass**: When a test exposes a real defect, update the implementation first. Only adjust tests if the requirement changed or the test was incorrect.

- **Favor integration tests over heavy mocking**: Write tests that exercise real code paths and types. Mock only external services (e.g., LLM APIs, filesystem/network), not core logic.

- **Use real constructors and APIs**: Build objects with their true signatures (e.g., `GameObject(obj_id, ..., current_location_id)`, `Room(room_id, ...)`, `PlayerCharacter(char_id, name, backstory, motive, current_room_id)`), so tests mirror production.

- **Tests should prove real fixes**: Add integration tests that fail before a fix and pass after. Keep them close to real user scenarios (e.g., those seen in `game.log`).

- **Don't use inline Python for testing**: When testing functionality, create proper test files instead of running inline Python code. Inline testing is fragile, not durable, and doesn't integrate with the test suite. Always write tests that can be run with `pytest`.

- **Check import paths when writing tests**: When creating new test files, verify the correct import paths by checking where classes are actually defined (e.g., `Room` is in `motive.game_rooms`, not `motive.game_objects`).

- **UTF‑8 logging**: File handlers must specify `encoding="utf-8"` to preserve characters like `•` in logs.

- **Log invalid/unexecutable actions clearly**: Include which action failed and why. Avoid redundant full response logs.

## Motive Policy Lessons

- **Action parsing contract**: The parser only recognizes lines starting with `>` and finds actions by longest matching action name. Tests must include leading `>` and reflect multi‑word action names accurately.

- **Event distribution timing**: Distribute events immediately after each action executes, not at the start of the next turn.

- **Observation delivery and clearing**: Present queued observations in the player prompt and clear them only after the message is constructed/sent (first and subsequent turns).

- **Do not self‑observe**: The acting player should not receive their own event as an observation; they get direct feedback instead.

- **AP exhaustion is not an error**: Running out of AP should not mark the response invalid or apply penalties. Execute what fits; skip the rest and end the turn normally with confirmation.

- **Help and prompts consolidation**: Avoid duplicate prompts after `help`. Either include the prompt in the help feedback or suppress the immediate re‑prompt.

- **Standardize messages and delimiters**: Use consistent headers (e.g., `**Recent Events:**`), bullet `•`, and delimiters (`===` for major, `---` for rounds). Align multi‑line message payloads starting on a new line.

- **Action set and guidance**: Use "Example actions" in prompts; keep the full list discoverable via `help`. Avoid dumping very large action lists inline.

- **Action effects must emit observable events**: Core actions (`move`, `say`, `pickup`, `look`, `help`, `read`) should generate scoped events (e.g., `room_players`) so nearby players see them in "Recent Events."

- **Turn end confirmation**: Accept both `> continue` and `continue` (and the same for `quit`), but communicate a consistent format in prompts. `quit` should warn it counts as failing the motive.

- **Movement observations must include direction**: Exit/enter events should specify which direction players moved (e.g., "left via West Gate", "entered from North Exit"). This is crucial for strategic gameplay when multiple exits exist.

- **Turn end confirmation handling**: During turn end confirmation, only accept "continue" or "quit" actions. Warn players about any other actions submitted during confirmation and ignore them. This prevents confusion and maintains clear turn boundaries.




## Cost-aware runs and confidence policy

- **Default to tests over paid runs**: Running `python -m motive.main` triggers paid LLM calls. Prefer unit/integration tests which stub external LLMs.
- **Confidence scale (1–10) before paid runs**:
  - 9–10: Broad integration coverage of real code paths, deterministic seeds, recent green runs, and stable configs; no pending FIXME/TODOs in the touched area.
  - 7–8: Integration tests cover the new logic end-to-end with stubs, logs verified, and realistic fixtures; minor unknowns remain (config, I/O, timing).
  - 5–6: Unit tests pass but integration coverage is partial; notable unknowns or recent refactors.
  - ≤4: Significant unknowns, heavy mocking, or flakiness; do not run paid flows.
- **Gate to run `motive.main`**: Only after (a) tests are green, (b) observation/event logs look correct on fixtures, and (c) configs (`config.yaml`, theme YAMLs, API keys) are validated.
- **Cheap smoke first**: If feasible, do a quick dry run with stubbed LLMs or a “sandbox” config (lowest-cost models, single round, minimal players) before a full-cost session.
- **Logging hygiene**: Ensure UTF-8 logs and concise event/observation blocks are enabled to make any post-run debugging cheaper.
