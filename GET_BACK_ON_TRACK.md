# GET BACK ON TRACK

A concrete recovery plan to complete v2 migration, validate outputs, and remove v1 leftovers.

## Objectives
- Use only v2 configs and systems end-to-end
- Validate all migrated YAML files (syntax + structure)
- Keep `GameMaster` as orchestrator; avoid forking engines
- Remove all v1 config files and code once v2 is proven

## CRITICAL ISSUE DISCOVERED: Massive Content Loss
**The migration system has completely lost the multiple motives system!**

- **Original v1**: Characters had 3-4 complex motives each with success/failure conditions, descriptions, etc.
- **Migrated v2**: All characters have only a single empty `motive: default: ''` property
- **Impact**: The migrated configs are unusable for actual gameplay - all motive content lost

**Examples of lost content:**
- `detective_thorne`: Lost `investigate_mayor`, `protect_daughter`, `avenge_partner` motives
- `father_marcus`: Lost `protect_flock`, `seek_redemption`, `expose_cult_safely` motives  
- `bella_whisper_nightshade`: Lost `profit_from_chaos`, `protect_her_network`, `choose_a_side`, `build_secret_stash` motives

**This is a complete failure of the migration system and must be fixed before proceeding.**

## IMPORTANT DESIGN DECISION: Tags → Properties Migration
**Tags are deprecated in v2 in favor of the new entity property system.**
- v1 `tags` arrays should be converted to boolean properties in v2
- Do NOT preserve `tags` as arrays in v2 - convert them to individual boolean properties
- Example: `tags: ["hidden", "underground"]` → `hidden: true, underground: true` properties

## Phase 0: Stop the Bleeding (Today)
1. Fix migration emitter
   - Remove invalid header map-keys and empty `": null"` lines (done)
2. Re-run migration for all targets
3. Add artefact validation tests (yaml.safe_load on all `*_migrated.yaml`)
4. Add hierarchical load tests (`V2ConfigLoader.load_hierarchical_config` on fantasy/hearth)

## Phase 1: Make the CLI Load v2 Configs Safely
1. Detect v2 (standalone or hierarchical) in CLI
2. Load via `V2ConfigLoader.load_hierarchical_config` (when includes present) then `load_v2_config`
3. Adapt only the initialization boundary so `GameMaster` gets what it needs without forking the game loop
4. Add an isolated smoke test that runs a minimal v2 scenario (mock LLMs)

## Phase 2: End-to-End Validation
1. Run `motive -c configs/game_migrated.yaml --players 2 --rounds 1 --ap 5` (mock LLMs)
2. Verify initialization report shows non-zero rooms/characters for edition configs
3. Ensure logs are written to a temp directory in tests; enforce cleanup (even on interruption)

## Phase 3: Remove v1 “Turds”
1. Replace `configs/game.yaml` to include v2 migrated main
2. Remove v1 config files and references after green e2e tests
3. Remove v1-only code paths gated by tests

## Phase 4: Hardening
1. Add CI job to validate all configs (syntax + hierarchical load)
2. Add regression tests for migration emitter
3. Add smoke run as a gating step (mocked LLMs)

## Execution Order (Checklist)
- [x] Fix migration output (done)
- [x] Re-run migration
- [x] Add migration artefact validation tests
- [x] Add hierarchical v2 load tests
- [x] Make CLI path select v2 → loader → initializer (no GM fork)
- [x] Add minimal v2 smoke test (mocked LLMs)
- [x] Green run with `game_migrated.yaml` (conversion working, game running successfully!)
- [x] End-to-end validation complete (comprehensive tests + real game run)
- [x] **CRITICAL: Fix motives migration - all character motives lost!** ✅ FIXED
- [x] **MAJOR PROGRESS: Fix failing tests** ✅ 76% REDUCTION IN FAILURES
  - [x] Migrate integration tests to v2 configs
  - [x] Update test configs to v2 structure (character_types, action_definitions, etc.)
  - [x] Fix test expectations to match v2 config structure
  - [x] Validate v2 integration tests
  - [x] Fix action effect mapping (property_name → property, target_entity → target)
  - [x] Fix motive CLI tests to use character_types
  - [x] Fix character override tests to use character_types
  - [x] Fix util hierarchical tests to expect migrated config names
  - [x] Fix v2 smoke tests to treat config objects as objects not dictionaries
  - [x] Fix permission errors and Windows file locking issues
  - [x] Fix GameMaster attributes (game_state, game_settings)
  - [x] Fix PlayerConfig character field assignment
  - [x] Fix config structure mismatches between v1 and v2
  - [ ] **REMAINING: Fix 5 failed tests** (down from 21!)
    - [ ] Action validation test (actions marked as invalid)
    - [ ] LLM credential mocking (patch not applied early enough)
    - [ ] File locking issues (Windows cleanup problems)
- [ ] Switch `configs/game.yaml` to v2 main
- [ ] Remove v1 configs
- [ ] Remove v1-only code paths
- [ ] Add CI guardrails

## Risks & Mitigations
- Risk: Broken includes paths → Add path validation tests and fail fast
- Risk: YAML syntax drift → Centralize emission; parse immediately after write
- Risk: GameMaster coupling → Adapt at initialization boundary only
- Risk: Flaky tests on Windows → ensure log handlers closed and temp dirs used
- **Risk: Content loss during migration → Validate content preservation, not just structure**

## Definition of Done
- All tests green (unit + integration + e2e smoke)
- `motive` runs using v2 configs by default
- No v1 configs, no v1-only code paths
- CI validates configs and blocks regressions
