# GET BACK ON TRACK

A concrete recovery plan to complete v2 migration, validate outputs, and remove v1 leftovers.

## Objectives
- Use only v2 configs and systems end-to-end
- Validate all migrated YAML files (syntax + structure)
- Update `GameMaster` to work with v2 configs directly (NO v2→v1 conversion)
- Remove all v1 config files and code once v2 is proven

## Reality Check (2025-09-16)
Recent real runs (including 5 parallel games) revealed gaps that contradict prior status. The following issues must be addressed before proceeding to Phase 3:

- CRITICAL: Motive success/failure conditions render as a single placeholder: `Player has tag 'dummy'` for all characters.
  - Impact: No motives can be won or failed; games always end with "NOT ACHIEVED" for all players.
- HIGH: LLM responses are narrative but often rejected as actions; turns end with "did not provide any actions".
  - Impact: Players fail to progress; poor gameplay loop.
- HIGH: Object/NPC interaction pathways are not wired (e.g., `look <object>`, `say to <npc>`, `pickup <object>`).
  - Impact: Exploration and interaction are effectively disabled.
- MEDIUM: Movement validation is too strict without helpful guidance; `move` often fails to resolve exits/aliases.
- MEDIUM: Observability/event scoping appears incomplete (adjacent rooms/NPC visibility uncertain).
- GOOD: Performance optimization (smart context/caching/retry) is stable; keep enabled.

The items above indicate missing integration between sim v2 concepts and the current `GameMaster` pipeline, and insufficient end-to-end tests using real YAML.

## CRITICAL ARCHITECTURAL MISUNDERSTANDING DISCOVERED
**The CLI is incorrectly converting v2 configs back to v1 format!**

- **Problem**: CLI detects v2 configs and tries to convert them back to v1 format for GameMaster
- **Why Wrong**: This is backwards - we should migrate TO v2, not convert back to v1
- **Impact**: Conversion fails because v2 configs use proper YAML structure that doesn't map to old v1 format
- **Solution**: Update GameMaster to work with v2 configs directly

**The migrated v2 configs are actually correct** - they use proper YAML structure with:
- `motives` as proper YAML lists with real conditions (`character_has_property`)
- `aliases` as proper YAML lists
- `initial_rooms` as proper YAML lists
- No string encoding of complex structures

**The issue is architectural**: GameMaster expects v1 format, but we should update it to work with v2 format directly.

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

## Phase 1: Update GameMaster to Work with v2 Configs Directly
1. Remove v2→v1 conversion logic from CLI
2. Update GameMaster to accept v2 config objects directly
3. Update GameMaster initialization to work with v2 entity definitions and action definitions
4. Add an isolated smoke test that runs a minimal v2 scenario (mock LLMs)

## Phase 2: End-to-End Validation
1. Run `motive -c configs/game.yaml --players 2 --rounds 1 --ap 5` (mock LLMs)
2. Verify initialization report shows non-zero rooms/characters for edition configs
3. Verify motive conditions show real conditions (not "dummy" tags)
4. Ensure logs are written to a temp directory in tests; enforce cleanup (even on interruption)

## Phase 3: Remove v1 "Turds"
1. Remove v1 config files and references after green e2e tests
2. Remove v1-only code paths gated by tests
3. Remove v2→v1 conversion logic from CLI

## Phase 4: Hardening
1. Add CI job to validate all configs (syntax + hierarchical load)
2. Add regression tests for migration emitter
3. Add smoke run as a gating step (mocked LLMs)

## Current Status (Updated 2025-09-16)

### 🎉 MAJOR BREAKTHROUGH ACHIEVED! (2025-09-16)
**V2 configs now work directly with GameMaster without any v2→v1 conversion!**

**Key Achievements:**
- ✅ **CLI updated** - No longer converts v2 configs back to v1 format
- ✅ **GameMaster updated** - Now accepts v2 `V2GameConfig` objects directly
- ✅ **Entity conversion** - V2 entity definitions converted to `CharacterConfig` objects for GameInitializer compatibility
- ✅ **Motive assignment working** - Characters now get real motives with proper success/failure conditions
- ✅ **Real game test passed** - Game ran successfully with v2 configs, showing real motive conditions like `position_secured`, `wealth_preserved`, `corruption_exposed`

**Technical Implementation:**
- Added `_convert_v2_entities_to_character_configs()` method to GameMaster
- Added `_convert_conditions()` method to handle v2 condition format conversion
- Updated GameMaster constructor to detect and handle v2 configs
- Removed v2→v1 conversion logic from CLI `load_config()` function

**Test Results:**
- Game ran successfully with v2 configs
- Character assigned: Captain Marcus O'Malley
- Motive displayed: "maintain_power" with real conditions
- No dummy placeholders in motive conditions
- Game loop executed without errors

### 🚨 CRITICAL ARCHITECTURAL MISTAKE DISCOVERED (2025-09-16)
**The `_convert_v2_entities_to_character_configs` method was doing v2→v1 conversion!**

**Issue**: GameMaster was converting v2 `EntityDefinition` objects back to v1 `CharacterConfig` objects, which defeats the purpose of v2 migration.

**Resolution**: 
- ✅ Removed `_convert_v2_entities_to_character_configs()` and `_convert_conditions()` methods from GameMaster
- ✅ Updated GameInitializer to store v2 `EntityDefinition` objects directly
- ✅ Updated character assignment code to handle v2 entity structure
- ✅ Updated action processing to store v2 `ActionDefinition` objects directly

**Result**: Pure v2 architecture achieved with zero v2→v1 conversion.

### 🎉 ARCHITECTURAL SUCCESS ACHIEVED! (2025-09-16)
**V2 configs now work directly with GameMaster and GameInitializer without ANY v2→v1 conversion!**

**Key Achievements:**
- ✅ **Removed all v2→v1 conversion** - No more conversion methods in GameMaster or GameInitializer
- ✅ **GameInitializer updated** - Now works with v2 `EntityDefinition` and `ActionDefinition` objects directly
- ✅ **Character assignment working** - Characters properly assigned with real motives from v2 configs
- ✅ **Motive conditions working** - Real properties like `cult_plans_discovered`, `intelligence_network_active` displayed
- ✅ **Game runs successfully** - Complete game loop executed without errors

**Technical Changes Made:**
- GameMaster: Removed v2→v1 conversion methods
- GameInitializer: Updated to work with v2 structures directly
- Character assignment: Updated to handle v2 entity structure
- Action processing: Updated to store v2 objects directly

**Test Results:**
- Game ran successfully with v2 configs
- Character assigned: Guild Master Elena
- Motive displayed: "gather_intelligence" with real conditions
- No dummy placeholders in motive conditions
- Game loop executed without errors
- **ZERO v2→v1 conversion** - Pure v2 architecture achieved!

## Previous Status (Updated 2025-09-15)

### ✅ COMPLETED
- [x] Fix migration output (done)
- [x] Re-run migration
- [x] Add migration artefact validation tests
- [x] Add hierarchical v2 load tests
- [x] **CRITICAL: Fix motives migration - all character motives preserved!** ✅ FIXED
- [x] **MAJOR PROGRESS: Fix failing tests** ✅ 76% REDUCTION IN FAILURES
- [x] **ARCHITECTURAL UNDERSTANDING: Identified v2→v1 conversion as wrong approach** ✅ FIXED

### ✅ COMPLETED (MAJOR MILESTONE!)
- [x] **MAJOR BREAKTHROUGH: Update GameMaster to work with v2 configs directly** ✅ COMPLETED
- [x] Remove v2→v1 conversion logic from CLI ✅ COMPLETED
- [x] Update GameMaster initialization to work with v2 entity definitions ✅ COMPLETED
- [x] Update GameMaster to work with v2 action definitions ✅ COMPLETED
- [x] **CRITICAL SUCCESS: Motive assignment working with real conditions** ✅ COMPLETED
- [x] **ARCHITECTURAL SUCCESS: V2 configs work directly without conversion** ✅ COMPLETED

### 🔄 IN PROGRESS
- [ ] **CURRENT PRIORITY: Add isolated smoke test for v2 scenarios**

### ❌ CANCELLED (Wrong Approach)
- [x] ~~Make CLI path select v2 → loader → initializer (no GM fork)~~ - WRONG: Should update GameMaster
- [x] ~~Green run with `game_migrated.yaml` (conversion working, game running successfully!)~~ - WRONG: Should work with v2 directly
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

## New Critical Work Items (from real runs)

1) Fix motive condition parsing (v2→v1 conversion and runtime)
- Problem: `success_conditions`/`failure_conditions` end up as placeholder `player_has_tag: dummy`.
- Hypothesis: Coercion of list-based condition groups to Pydantic falls back to default.
- Plan:
  - In CLI conversion (`motive/cli.py::_convert_character_definition`) build `MotiveConfig` with parsed condition groups (done).
  - Add integration test: `tests/v2_e2e/test_motives_conditions_integration.py` with minimal v2 config and tag toggles to assert WIN/FAIL/NOT_ACHIEVED.
  - Verify in a deterministic run that condition trees show real tags (e.g., `found_mayor`).

2) Action parsing and acceptance of LLM outputs
- Problem: Turns end with "did not provide any actions" despite sensible LLM text.
- Plan:
  - Improve `action_parser` to extract `> verb ...` from mixed prose; accept fenced or inline `>` commands.
  - Tests: `tests/v2_e2e/test_action_parsing_from_llm_text.py` with representative LLM outputs.

3) Wire basic object/NPC interactions (look/say/pickup/read)
- Problem: Requirement params not bound; objects/NPCs not resolved by name/alias.
- Plan:
  - Align parser param names with requirements (`object_name`, `direction`, `player`).
  - Extend `_check_requirements` to resolve by aliases/case-insensitive.
  - Tests: `tests/v2_e2e/test_object_npc_interactions.py` minimal v2 room with one object and one NPC.

4) Movement via exits with aliases
- Problem: `move` fails to resolve exits/aliases.
- Plan:
  - Normalize exit aliases during v2→v1 conversion; ensure exits carry `name` and `aliases`.
  - Tests: `tests/v2_e2e/test_movement_exits.py` with multiple exits and alias forms.

5) Observability scope checks (room/adjacent)
- Problem: Event scoping breadth unclear.
- Plan:
  - Add tests for scopes: originator, room, adjacent.
  - Tests: `tests/v2_e2e/test_event_scopes.py` asserting recipients.

## Immediate Priority (order)
1. Motive condition parsing (fix + tests)
2. Action parsing robustness (tests)
3. Object/NPC interaction requirements binding (tests)
4. Movement/exit alias normalization (tests)
5. Event scope validation (tests)

## Definition of Done (updated)
- All new v2 e2e tests green with minimal, isolated v2 configs.
- Real motive run (2 players, 2 rounds) shows non-dummy motive conditions and at least one validated action per player.
- Parallel games run completes without systemic invalid-action patterns.

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
