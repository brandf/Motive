# TODO List

## Who is this for?

- **Contributors and agents** looking for current priorities
- **Maintainers** tracking progress at a glance
- **Players** interested in upcoming features (see [MANUAL.md](MANUAL.md) for current actions)

## High Priority Features

### Core Actions Implementation
- [x] **implement_give** - ✅ COMPLETED: Implemented give action with character-to-character inventory transfer, comprehensive error handling, and room-scoped observability
- [x] **implement_throw** - ✅ COMPLETED: Implemented throw action with object transfer through exits, comprehensive error handling, and cross-room observability
- [ ] **implement_trade** - Implement trade action with queued observation system for item exchange  
- [ ] **implement_use** - Implement generic use action with declarative object state manipulation (e.g., use torch to light/extinguish)
- [ ] **implement_look_object** - Implement look <object> with declarative object-specific descriptions and state-dependent behavior

### Help System Enhancement
- [ ] **help_action_syntax** - Implement help <action> syntax for detailed action information (parameters, conditions, scope)

### Benchmarking & Evaluation
- [ ] **benchmarks_baselines_v1** - Define initial benchmark suite (seeded tasks, metrics, scoring) and publish two baseline agents (heuristic + LLM)
- [ ] **scorecards_leaderboards** - Create scorecards and a simple leaderboard doc for tracking progress per theme/edition

### Instrumentation & Verifiable Data
- [ ] **instrumentation_verifiable_qa** - Implement graders and Q/A generators from introspectable game state with causal logs per turn
- [ ] **causal_logging_schema** - Design a structured logging schema capturing perceptions, actions, rewards, and observations suitable for dataset publication

### Privacy & Safety
- [ ] **privacy_safety_policy** - Document data retention, redaction, and consent policy for logs/datasets; add redaction utility
- [ ] **content_safety_filters** - Add configurable content filters and safe-mode presets for open-ended chat

### Onboarding & UX
- [ ] **instant_play_templates** - Provide quickstart scenarios and a `motive --quickstart` flow for instant play
- [ ] **memory_summarization_utilities** - Add checkpointing and chapter-summary utilities to manage long-context sessions

## Medium Priority Features

### AI and Gameplay Improvements
- [ ] **enhance_ai_prompting** - Add motive-specific guidance to encourage strategic gameplay

### Inventory System
- [ ] **inventory_visibility** - Design and implement inventory visibility system (hidden items, stash action, etc.)

### Procedural Generation & Curriculum
- [ ] **procedural_generators_seeding** - Add parameterized generators for rooms/quests/objects with strict seeding for reproducibility
- [ ] **curriculum_difficulty_tracks** - Define progressive difficulty tracks (navigation, deception, alliance-building) with evaluators

### Social Reasoning & Dialogue
- [ ] **persona_conditioning_social_goals** - Add structured personas and social objectives to characters; expose in prompts and logs
- [ ] **social_commonsense_probes** - Create small tasks/datasets to evaluate beliefs, intentions, deception handling

### Architecture & Ops
- [ ] **pluggable_model_backends** - Abstract LLM backends (providers, parameters) with config-based selection and local-first support
- [ ] **power_user_controls_presets** - Expose advanced sampling/constraint controls and support saving/sharing config presets
- [ ] **admin_ops_tooling** - Add management commands (e.g., seed reset, log export), live-reload dev loop, and a minimal web client shell

### Task Schemas & Exploration
- [ ] **task_schemas_verifiers** - Define task schemas with verifiable success conditions and pluggable graders
- [ ] **exploration_stress_tests** - Add sparse-signal, long-horizon scenarios to stress planning/exploration
- [ ] **task_suites_micro** - Add micro task suites for ablative testing of capabilities

## Low Priority Features

### Advanced Object System
- [ ] **declarative_object_behavior** - Design declarative system for object behavior using when conditions (reuse hint system code)
- [ ] **object_state_management** - Implement object state management system for tags, properties, and conditional behavior

### Community & Multimodality
- [ ] **ugc_portal_sharing** - Add edition/scenario publishing and discovery hooks to enable community UGC loops
- [ ] **co_op_sessions** - Provide minimal co-op session support for multi-user playtests
- [ ] **instruction_templates_transfer** - Standardize instruction templates for better generalization and future transfer studies
- [ ] **multimodal_transfer_prep** - Draft mappings between text actions and other modalities for future ALFWorld-style experiments
- [ ] **sandboxing_isolation** - Strengthen sandboxing and isolation for agent operations inspired by web-agent benchmarks

---

## Game Design Learnings (from 5-game parallel analysis)

### Emergent Behaviors Observed
- **Information-first openings**: Players consistently spend R1-R2 on look/read actions (boards, symbols, ledgers) before moving, creating slow-burn discovery phase
- **Soft-role alignment**: Natural clustering around thematic areas (Bank: Detective+Bella, Church: Mayor+Father Marcus+Dr. Chen, Guild/Tavern: Guild Master+Tavern Keeper)
- **Cooperative information sharing**: Players frequently share discoveries via whisper, especially about cult symbols and evidence
- **Strategic positioning**: Players position themselves near key NPCs and objects for optimal information gathering

### Technical Issues Identified
- **Object type errors**: "Object type 'altar' not found" and "wooden_sign" errors suggest missing object definitions
- **Action validation gaps**: Players attempt invalid actions (move to non-existent exits, whisper to non-players, pickup non-existent objects)
- **Empty object interactions**: Players try to read objects with "no readable text" - need better object state management
- **Inventory confusion**: "Your inventory is empty" and "You don't see any" messages indicate UI/feedback issues

### Design Recommendations for H&S
- **Enhance object system**: Fix missing object types and improve object state management
- **Improve action validation**: Better feedback for invalid actions and clearer action constraints
- **Strengthen information flow**: The information-sharing patterns suggest players want more structured ways to share discoveries
- **Role-based mechanics**: The soft-role alignment suggests formalizing character roles and their unique abilities
- **Cooperative incentives**: Players naturally want to work together - consider mechanics that reward cooperation

### Critical Action Parsing Fixes (from 5-game analysis)
- [ ] **improve_object_awareness** - Enhance room descriptions to clearly separate actual interactive objects from descriptive text (high impact - AI tries to interact with non-objects)
- [ ] **improve_ai_action_guidance** - Add specific guidance about action syntax, available objects, and common mistakes to AI prompts (medium impact - prevents errors)

### Cross-Game Trends
- **Consistent pacing**: All games followed similar discovery → investigation → action patterns
- **NPC interaction patterns**: Players consistently engage with key NPCs (Detective, Father Marcus, Guild Master)
- **Object interaction priorities**: Cult symbols, evidence, and notice boards are primary interaction targets
- **Communication strategies**: Whisper is heavily used for coordination and information sharing

## Backlog (Future Improvements)

### Give Action Enhancements
- [ ] **improve_give_system** - Enhance give action with queued acceptance system: receiving player should control their inventory via `> accept <give_id>` or `> reject <give_id>` on their next turn (medium impact - better player agency)

## Notes

- All TODOs migrated from Cursor agent system to this durable markdown file
- Items are categorized by priority and feature area
- Each item includes the original ID for reference
- Format supports better organization and tracking than the agent TODO system
