# TODO List

## Who is this for?

- **Contributors and agents** looking for current priorities
- **Maintainers** tracking progress at a glance
- **Players** interested in upcoming features (see [MANUAL.md](MANUAL.md) for current actions)

## CRITICAL PRIORITY (Based on Parallel Run Analysis)

### Motive System Overhaul
- [ ] **fix_motive_completion_gates** - **CRITICAL**: 0% win rate across 10 games - players achieve partial success (e.g., `collection_complete`) but miss second gates (e.g., `stash_secured`). Need clearer completion paths and better success condition communication.
- [ ] **improve_motive_clarity** - **CRITICAL**: Players don't understand how to complete motives. Add explicit success condition hints and progress tracking in game state.
- [ ] **implement_motive_progress_feedback** - **HIGH**: Add real-time feedback when players make progress toward their motives (e.g., "You've collected 15/20 objects for your stash").
- [ ] **add_motive_completion_mechanisms** - **CRITICAL**: No clear mechanism for players to actually achieve their motives. Add specific actions that grant required tags (e.g., 'partner_avenged', 'cult_destroyed', 'cult_control_broken', 'justice_served').
- [ ] **make_win_conditions_achievable** - **HIGH**: Success conditions need to be more achievable within the game timeframe. Current 100-round games end without motive completion.

### Object System Fixes (High Impact)
- [ ] **fix_missing_object_types** - **CRITICAL**: "Object type 'altar' not found" and "wooden_sign" errors prevent gameplay. Audit and fix all missing object definitions.
- [ ] **improve_object_awareness** - **HIGH**: AI tries to interact with non-objects (descriptive text). Enhance room descriptions to clearly separate interactive objects from flavor text.
- [ ] **implement_object_state_management** - **HIGH**: Players try to read objects with "no readable text". Need declarative object behavior system.

### Action Validation & Player Experience
- [ ] **enhance_action_validation** - **HIGH**: Players attempt invalid actions (move to non-existent exits, whisper to non-players). Better feedback and clearer action constraints needed.
- [ ] **improve_ai_action_guidance** - **HIGH**: Add specific guidance about action syntax, available objects, and common mistakes to AI prompts.
- [ ] **fix_inventory_confusion** - **MEDIUM**: "Your inventory is empty" and "You don't see any" messages indicate UI/feedback issues.
- [ ] **prevent_premature_turn_endings** - **HIGH**: Some invalid actions caused premature turn endings. Improve error handling to prevent this penalty.
- [ ] **add_puzzle_hints_system** - **MEDIUM**: Players couldn't find ways to open hidden passages (Crypt Entrance). Provide more guidance for solving environmental puzzles.

## HIGH PRIORITY (Gameplay & Social Dynamics)

### Social Interaction Enhancements
- [ ] **implement_trade_action** - **HIGH**: Players want to exchange items but can't. Implement trade action with queued observation system.
- [ ] **enhance_whisper_system** - **MEDIUM**: Whisper is heavily used for coordination. Improve whisper mechanics and add whisper history.
- [ ] **implement_alliance_mechanics** - **MEDIUM**: Players naturally want to work together. Add formal alliance mechanics and cooperative incentives.
- [ ] **enhance_npc_response_system** - **HIGH**: The Raven never responded to player threats/interrogation. Make NPCs more reactive to player actions with meaningful dialogue.
- [ ] **implement_npc_ai_improvements** - **MEDIUM**: Enhance NPC response systems to make them more reactive to player actions.

### Character & Role Development
- [ ] **formalize_character_roles** - **HIGH**: Soft-role alignment observed (Bank: Detective+Bella, Church: Mayor+Father Marcus). Add unique character abilities and role-specific actions.
- [ ] **implement_character_specific_hints** - **MEDIUM**: Character-specific hints work well. Expand system for all characters and motives.

### Information Flow & Discovery
- [ ] **enhance_information_sharing** - **HIGH**: Players consistently share discoveries via whisper. Add structured ways to share discoveries and evidence.
- [ ] **implement_evidence_system** - **MEDIUM**: Players focus on cult symbols, evidence, and notice boards. Formalize evidence collection and sharing mechanics.

## MEDIUM PRIORITY (Core Actions & Systems)

### Core Actions Implementation
- [x] **implement_give** - ✅ COMPLETED: Implemented give action with character-to-character inventory transfer
- [x] **implement_throw** - ✅ COMPLETED: Implemented throw action with object transfer through exits
- [ ] **implement_use** - Implement generic use action with declarative object state manipulation
- [ ] **implement_look_object** - Implement look <object> with declarative object-specific descriptions
- [ ] **add_more_interactive_objects** - Add more interactive objects and clearer interaction methods beyond basic read/look actions.

### Help System Enhancement
- [ ] **help_action_syntax** - Implement help <action> syntax for detailed action information

### Inventory System
- [ ] **inventory_visibility** - Design and implement inventory visibility system (hidden items, stash action, etc.)

## LOW PRIORITY (Advanced Features)

### Game Balance & Duration
- [ ] **optimize_game_duration** - Consider 50-75 rounds for this scenario complexity instead of 100 rounds.
- [ ] **implement_multiple_endings** - Allow for different types of victories (partial success, moral victory, etc.).
- [ ] **add_dynamic_events** - Add more responsive world events based on player actions.
- [ ] **balance_information_flow** - Balance information revelation to maintain engagement throughout the game.

### Benchmarking & Evaluation
- [ ] **benchmarks_baselines_v1** - Define initial benchmark suite and publish baseline agents
- [ ] **scorecards_leaderboards** - Create scorecards and leaderboard for tracking progress

### Instrumentation & Verifiable Data
- [ ] **instrumentation_verifiable_qa** - Implement graders and Q/A generators from game state
- [ ] **causal_logging_schema** - Design structured logging schema for dataset publication

### Privacy & Safety
- [ ] **privacy_safety_policy** - Document data retention and consent policy
- [ ] **content_safety_filters** - Add configurable content filters

### Onboarding & UX
- [ ] **instant_play_templates** - Provide quickstart scenarios
- [ ] **memory_summarization_utilities** - Add checkpointing and chapter-summary utilities

## PARALLEL RUN ANALYSIS INSIGHTS

### Key Findings from 10-Game Analysis
- **Win Rate**: 0% (0/10 games) - all ended with "No players achieved their motives"
- **Action Patterns**: Heavy use of `look` (1,247), `move` (1,156), `say` (892), `read` (445), `pickup` (423)
- **Social Behavior**: Low `whisper` (89), very low `give` (23), `throw` (15), `drop` (12)
- **Cooperation**: Players naturally want to work together but lack mechanics to do so effectively

## SINGLE GAME ANALYSIS INSIGHTS (2025-09-13 Game)

### Key Findings from 100-Round Game
- **Duration**: ~1 hour 5 minutes for 100 rounds (may be too long)
- **Character Development**: Strong alliance formation between Detective Thorne and Captain O'Malley
- **Investigation Progression**: Systematic exploration through 5+ locations with evidence gathering
- **Final Confrontation**: Players reached Thieves' Den but NPC (The Raven) remained unresponsive
- **Technical Performance**: Game completed successfully despite API rate limiting issues

### Observed Player Behaviors
- **Collaborative**: Players worked together effectively despite different motives
- **Methodical**: Systematic investigation approach following logical leads
- **Persistent**: Continued trying different approaches when initial attempts failed
- **Roleplay**: Maintained character consistency throughout the game
- **Strategic**: Used observability mechanics to coordinate actions

### Critical Issues Identified
- **NPC Unresponsiveness**: The Raven never responded to player threats/interrogation
- **Puzzle Resolution**: Players couldn't find ways to open hidden passages (Crypt Entrance)
- **Motive Completion**: No clear mechanism for players to achieve their motives
- **Game Balance**: 100 rounds may be too long for this scenario complexity
- **Action Validation**: Some invalid actions caused premature turn endings

### Emergent Behaviors Observed
- **Information-first openings**: Players spend R1-R2 on look/read actions before moving
- **Soft-role alignment**: Natural clustering around thematic areas
- **Cooperative information sharing**: Frequent sharing of discoveries via whisper
- **Strategic positioning**: Players position near key NPCs and objects

### Technical Issues Identified
- **Object type errors**: Missing object definitions prevent gameplay
- **Action validation gaps**: Players attempt invalid actions
- **Empty object interactions**: Objects with "no readable text"
- **Inventory confusion**: UI/feedback issues

### Design Recommendations
- **Enhance object system**: Fix missing types and improve state management
- **Improve action validation**: Better feedback and clearer constraints
- **Strengthen information flow**: More structured ways to share discoveries
- **Role-based mechanics**: Formalize character roles and unique abilities
- **Cooperative incentives**: Mechanics that reward cooperation

## BACKLOG (Future Improvements)

### Advanced Object System
- [ ] **declarative_object_behavior** - Design declarative system for object behavior
- [ ] **object_state_management** - Implement object state management system

### Community & Multimodality
- [ ] **ugc_portal_sharing** - Add edition/scenario publishing hooks
- [ ] **co_op_sessions** - Provide minimal co-op session support
- [ ] **instruction_templates_transfer** - Standardize instruction templates
- [ ] **multimodal_transfer_prep** - Draft mappings for other modalities
- [ ] **sandboxing_isolation** - Strengthen sandboxing for agent operations

### Procedural Generation & Curriculum
- [ ] **procedural_generators_seeding** - Add parameterized generators
- [ ] **curriculum_difficulty_tracks** - Define progressive difficulty tracks

### Social Reasoning & Dialogue
- [ ] **persona_conditioning_social_goals** - Add structured personas
- [ ] **social_commonsense_probes** - Create tasks for deception handling

### Architecture & Ops
- [ ] **pluggable_model_backends** - Abstract LLM backends
- [ ] **power_user_controls_presets** - Expose advanced sampling controls
- [ ] **admin_ops_tooling** - Add management commands and dev tools
- [ ] **improve_api_rate_limiting** - Implement better API rate limit handling with exponential backoff for Google Gemini API.

### Task Schemas & Exploration
- [ ] **task_schemas_verifiers** - Define task schemas with verifiable success
- [ ] **exploration_stress_tests** - Add sparse-signal scenarios
- [ ] **task_suites_micro** - Add micro task suites for testing

## Notes

- **Priority reprioritized** based on parallel run analysis findings
- **Critical issues** identified from 0% win rate and technical errors
- **High-impact improvements** focused on motive system and object handling
- **Social dynamics** prioritized based on observed player behavior
- **All TODOs** migrated from Cursor agent system to this durable markdown file
- **Format supports** better organization and tracking than agent TODO system