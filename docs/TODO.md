# TODO List

## Who is this for?

- **Contributors and agents** looking for current priorities
- **Maintainers** tracking progress at a glance
- **Players** interested in upcoming features (see [MANUAL.md](MANUAL.md) for current actions)

## High Priority Features

### Core Actions Implementation
- [ ] **implement_give** - Implement give action with queued observation system for safe item transfer
- [ ] **implement_trade** - Implement trade action with queued observation system for item exchange  
- [ ] **implement_throw** - Implement throw action: remove object from inventory and place in adjacent room via exit
- [ ] **implement_use** - Implement generic use action with declarative object state manipulation (e.g., use torch to light/extinguish)
- [ ] **implement_look_object** - Implement look <object> with declarative object-specific descriptions and state-dependent behavior

### Help System Enhancement
- [ ] **help_action_syntax** - Implement help <action> syntax for detailed action information (parameters, conditions, scope)

## Medium Priority Features

### AI and Gameplay Improvements
- [ ] **enhance_ai_prompting** - Add motive-specific guidance to encourage strategic gameplay

### Inventory System
- [ ] **inventory_visibility** - Design and implement inventory visibility system (hidden items, stash action, etc.)

## Low Priority Features

### Advanced Object System
- [ ] **declarative_object_behavior** - Design declarative system for object behavior using when conditions (reuse hint system code)
- [ ] **object_state_management** - Implement object state management system for tags, properties, and conditional behavior

---

## Notes

- All TODOs migrated from Cursor agent system to this durable markdown file
- Items are categorized by priority and feature area
- Each item includes the original ID for reference
- Format supports better organization and tracking than the agent TODO system
