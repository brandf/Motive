## v2 Minimal Integration Test Coverage — Actions and Observer Events

Tracking matrix for minimal, isolated v2 integration tests that verify each action’s effects produce expected events and observer scopes. Each test uses mocked LLM with canned actions and self-contained configs under `tests/configs/v2/<action>/`.

Legend:
- [x] Implemented and passing
- [ ] Not implemented

### Implemented (green)
- [x] look: self observation only (player)
- [x] move: exit by name/alias; observers: player, room_players
- [x] inventory: pickup/drop; observers: player (+ room_players for drop)
- [x] motives: success condition via set_property; private feedback only
- [x] say: broadcast to room_players; non-actors in same room observe event
- [x] whisper: private; actor observes; target receives player-scoped message
- [x] shout: adjacent_rooms observation across an exit
- [x] read: player-only feedback when reading object
- [x] give: transfer object to target; observers: player, room_players
- [x] throw: object thrown through exit; observers: player, room_players, adjacent_rooms
- [x] investigate: player-only feedback
- [x] use: player and room_players feedback
- [x] help: player-only; dynamic cost via code_binding
- [x] light: set object property and notify room_players

### Pending (to add now)
- [ ] Negative cases and variants (aliases, invalid targets, costs)
  - [x] throw: invalid exit → no adjacent/throw event; inventory unchanged
  - [x] use: missing target → no room_players use event; inventory unchanged

### Notes
- Tests assert both: (1) action feedback returned to acting player, and (2) events distributed to appropriate observers (via `GameMaster.player_observations`).
- Where scopes aren’t modeled yet (e.g., whisper target delivery), tests assert current behavior to prevent regressions and will be updated with scope support.


