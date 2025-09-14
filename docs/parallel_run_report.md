# Parallel Playtest Report: Hearth & Shadow (5 players × 30 rounds × 10 games)

## Executive Summary

- Winners: 0 across 10 games (all runs reported "No players achieved their motives").
- Motive progress: Frequent partial progress (e.g., hoarder `collection_complete` achieved in single-player test; in parallel runs, success tags observed but often missing second gate like `stash_secured`).
- Player behavior: Heavy use of `look` and `move`, substantial `say`, moderate `read`, low `whisper`, very low `give`/`throw`/`drop`/`shout`.
- Social dynamics: Cooperation attempts via `say` and occasional `whisper` around cult, crypt, and evidence; few explicit trades/hand-offs.
- Issues: Many AP-skipped actions, invalid/unexecutable actions present; narrative objects picked up as if portable; unclear success paths for multi-tag motives, leading to stalling.

## Run Configuration

- Players per game: 5
- Rounds per game: 30
- Parallel games: 10
- Game ID prefix: `parallel_test_5p_30r_10x`
- Log roots: `logs/fantasy/hearth_and_shadow/parallel_test_5p_30r_10x/parallel_test_5p_30r_10x_worker_*`

## Outcome Metrics

- Final outcomes (10/10): ❌ No players achieved their motives.
- Turn cadence: All games completed full 30 rounds with standard AP loop and turn-end confirmations.

## Action Usage (Player chat logs only)

- look: very high (≈ 3,900 occurrences) — exploration dominates early-mid game.
- move: high (≈ 2,550) — active traversal across rooms.
- say: high (≈ 3,700) — public communication common.
- read: high (≈ 2,400) — object/environment info is regularly consumed.
- help: moderate (≈ 250) — players occasionally seek menus/intents.
- pass: low (≈ 90) — mostly at endgame stalls.
- whisper: low (≈ 70) — targeted private comms exist but underused.
- pickup: high (≈ 2,400) — inventory growth consistent with hoarding tendencies.
- drop: very low (≈ 34) — little redistribution/staging of items.
- give: very low (≈ 23) — scarce direct cooperation.
- throw: rare (≈ 4) — niche or unclear use cases.
- shout: negligible (≈ 1) — not meaningfully used.

Interpretation:
- Players favor exploration and public discussion over stealth or explicit cooperation mechanisms.
- Inventory actions are common, but item exchange (give/drop) is rare, limiting cooperative puzzle resolution.

## Notable Interactions and Emergent Behavior

- Cult narrative progress via confession/evidence:
  - Example whisper (private warning and coordination):
  ```
  > whisper "mayor victoria blackwater" "mayor, i've read the confession... they plan to target you next. we must be extremely cautious."
  ```
  - Public coordination around crypt access and ritual prevention with roles (Father Marcus urging Mayor/Detective to read/act on Hearth Stone inscriptions and crypt mechanisms).
- Psychological analysis of cult symbols (Dr. Chen + Lysander): players reason about symbols’ effects and how they anchor fear/social control; proposes reading/observing inscriptions to progress.
- Hoarding patterns continue at scale: players attempt to pick up large/narrative objects (e.g., Merchant Stalls, Vault) — suggests over-permissive pickup scopes or missing constraints.
- Team intent signals without mechanics follow-through: multiple instances of “we should work together” in `say`, but few `give` or shared action sequences to materially coordinate.

## Issues and Frictions

1) Motive completion gaps
- Many motives appear to require multi-tag success (e.g., hoarder: `collection_complete` + `stash_secured`). Players often hit one tag but fail to complete the second; guidance on how to achieve the final gate is insufficient.

2) Over-permissive pickups
- Players pick up scene-scale objects (e.g., Merchant Stalls, Vault). This reduces realism and breaks puzzles/scene integrity.

3) Low cooperation tooling
- `give/trade` usage is minimal. Without incentives and clear tasks demanding item transfer, cooperation remains rhetorical.

4) AP friction
- Frequent “Actions skipped due to insufficient AP” mid-response; batching is fine, but players often overshoot AP. This is acceptable, but better planning prompts or AP-aware guidance could help efficiency.

5) Invalid/unexecutable actions
- Present across runs (hundreds of instances across workers). Feedback is clear, but repeated patterns imply players need improved action guidance (contextual examples, object lists, valid parameters).

## Recommendations

### A. Narrative Config and Object System
- Add realistic constraints to large/narrative objects:
  - Tag immovable/too_heavy/magically_bound on set pieces (Vault, Stalls, Bar, etc.).
  - Ensure pickup requirements (`object_possession_allowed`) block scene-scale items.
- Make progress affordances explicit:
  - Add `readable` inscriptions on crypt/Hearth Stone with actionable clues gating success tags (e.g., `stash_secured` requires "deposit n items at Secret Drop Point in Thieves' Den").
  - Instrument success actions to emit `add_tag` effects (e.g., securing stash sets `stash_secured`).
- Introduce puzzle objects with states:
  - Keys/sigils/runes with `set_property` sequences.
  - Multi-room locks requiring coordination (e.g., simultaneous actions or staged placement).

### B. Motive Design
- Provide motive-specific hint tracks (config-controlled, not always on):
  - Early-stage: “deposit items at stash point to secure” or “use drop at Thieves' Den Lockbox”.
  - Mid-stage: progress checks (“You have 12/20 stash items; secure via Lockbox”).
- Add cooperative motives:
  - Shared success where two characters must exchange/use items before both gain tags.
  - Complementary motives (e.g., Detective needs evidence chain; Bella must deliver contraband; joint success tags).

### C. Cooperation Mechanics
- Enhance `give`/`trade`:
  - Low AP cost + structured feedback.
  - Add `accept/reject` handshake to prevent forced transfers.
  - Cooperative puzzles that are impossible without exchange (e.g., item affinity by role/class).
- Dialogue prompts:
  - Contextual `help action` suggestions encouraging `whisper` for sensitive topics; `give` when relevant parties are co-located.

### D. Guidance & UX
- Per-room object menus:
  - At `look`, list interactable objects with allowed actions (`pickup`, `read`, `use`, `give`), and highlight constraints.
- AP-aware planner hint (optional):
  - After first action, show remaining AP and recommend 1–2 feasible follow-ups that won’t overrun AP.
- Invalid-action tutoring:
  - On invalid parameters, display valid targets from room/inventory.

### E. Instrumentation & Evaluation
- Tag emissions for key progress:
  - `evidence_chain_step_n`, `crypt_mechanism_step_n`, `stash_count_n`, `stash_secured`, `ritual_disrupted`.
- Add evaluators for:
  - Cooperation (give/trade frequency, successful multi-actor tasks).
  - Social dynamics (whisper chains, alliance language, betrayal markers such as stealing/dropping others’ items if allowed).

## Sample Notable Excerpts

- Private warning whisper (Father Marcus → Mayor):
``` 
> whisper "mayor victoria blackwater" "...they plan to target you next. we must be extremely cautious."
```
- Team problem-solving at the Crypt Entrance (urging to read Hearth Stone and inspect mechanisms).
- Analytical discussion of cult symbols (Dr. Chen + Lysander) with psychological framing and next-step suggestions.

## Proposed Next Steps

1) Config updates (objects): mark immovable/too_heavy; ensure `object_possession_allowed` applies broadly.
2) Add a Thieves’ Den Lockbox object with `use`/`drop` effects to grant `stash_secured` after threshold met.
3) Add a cooperative ritual-disruption puzzle requiring two characters to perform complementary `read`/`use` actions in different rooms within 1–2 rounds.
4) Introduce optional motive guidance hints (config flag) to teach the multi-tag success path without spoiling.
5) Add tests:
  - Inventory security and constraints (cannot pickup scene fixtures).
  - Motive completion paths for hoarding and crypt/ritual storylines.
  - Cooperation-required puzzle completion.
