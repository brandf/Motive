### AI Lessons Learned (for future runs)

- **Fix code, don’t change tests to pass**: When a test exposes a real defect, update the implementation first. Only adjust tests if the requirement changed or the test was incorrect.

- **Favor integration tests over heavy mocking**: Write tests that exercise real code paths and types. Mock only external services (e.g., LLM APIs, filesystem/network), not core logic.

- **Use real constructors and APIs**: Build objects with their true signatures (e.g., `GameObject(obj_id, ..., current_location_id)`, `Room(room_id, ...)`, `PlayerCharacter(char_id, name, backstory, motive, current_room_id)`), so tests mirror production.

- **Action parsing contract**: The parser only recognizes lines starting with `>` and finds actions by longest matching action name. Tests must include leading `>` and reflect multi‑word action names accurately.

- **Event distribution timing**: Distribute events immediately after each action executes, not at the start of the next turn.

- **Observation delivery and clearing**: Present queued observations in the player prompt and clear them only after the message is constructed/sent (first and subsequent turns).

- **Do not self‑observe**: The acting player should not receive their own event as an observation; they get direct feedback instead.

- **AP exhaustion is not an error**: Running out of AP should not mark the response invalid or apply penalties. Execute what fits; skip the rest and end the turn normally with confirmation.

- **Log invalid/unexecutable actions clearly**: Include which action failed and why. Avoid redundant full response logs.

- **UTF‑8 logging**: File handlers must specify `encoding="utf-8"` to preserve characters like `•` in logs.

- **Help and prompts consolidation**: Avoid duplicate prompts after `help`. Either include the prompt in the help feedback or suppress the immediate re‑prompt.

- **Standardize messages and delimiters**: Use consistent headers (e.g., `**Recent Events:**`), bullet `•`, and delimiters (`===` for major, `---` for rounds). Align multi‑line message payloads starting on a new line.

- **Action set and guidance**: Use “Example actions” in prompts; keep the full list discoverable via `help`. Avoid dumping very large action lists inline.

- **Action effects must emit observable events**: Core actions (`move`, `say`, `pickup`, `look`, `help`, `read`) should generate scoped events (e.g., `room_players`) so nearby players see them in “Recent Events.”

- **Turn end confirmation**: Accept both `> continue` and `continue` (and the same for `quit`), but communicate a consistent format in prompts. `quit` should warn it counts as failing the motive.

- **Tests should prove real fixes**: Add integration tests that fail before a fix and pass after. Keep them close to real user scenarios (e.g., those seen in `game.log`).


