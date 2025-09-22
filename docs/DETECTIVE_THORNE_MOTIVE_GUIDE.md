# Detective Thorne Motive Completion Guide

## Overview
Detective James Thorne's motive "avenge_partner" requires completing 8 success conditions across 4 phases. This guide outlines the clear progression paths for achieving each condition.

## Success Conditions

### Phase 1: Initial Evidence Gathering (Foundation)
**Condition:** `evidence_found: 3`

**How to Achieve:**
- **Fresh Evidence** (Town Square) - `pickup` → increments `evidence_found`
- **Partner's Evidence** (Town Square) - `pickup` → increments `evidence_found`  
- **Notice Board** (Town Square) - `look` → increments `evidence_found`

**Progression Path:**
1. Start in Town Square
2. Pick up Fresh Evidence
3. Pick up Partner's Evidence
4. Look at Notice Board
5. ✅ `evidence_found: 3` achieved

---

### Branch A: Cult Structure Investigation

#### Condition 1: `cult_hierarchy_discovered: true`
**Object:** Cult Roster (Abandoned Warehouse)
**Action:** `look` (or `read`, `examine`, `investigate` via aliases)
**Effect:** Sets `cult_hierarchy_discovered: true`

**Progression Path:**
1. Travel to Abandoned Warehouse
2. Look at Cult Roster
3. ✅ `cult_hierarchy_discovered: true` achieved

#### Condition 2: `cult_locations_mapped: true`
**Object:** Cult Hideout Map (Abandoned Warehouse)
**Action:** `look`
**Effect:** Sets `cult_locations_mapped: true`

**Progression Path:**
1. In Abandoned Warehouse (same room as Cult Roster)
2. Look at Cult Hideout Map
3. ✅ `cult_locations_mapped: true` achieved

---

### Branch B: Ritual Knowledge Investigation

#### Condition 3: `ritual_knowledge_mastered: true`
**Object:** Ritual Mastery Tome (Old Library)
**Action:** `look`
**Effect:** Sets `ritual_knowledge_mastered: true`

**Progression Path:**
1. Travel to Old Library
2. Look at Ritual Mastery Tome
3. ✅ `ritual_knowledge_mastered: true` achieved

#### Condition 4: `cult_timing_understood: true`
**Object:** Celestial Calculator (Hidden Observatory)
**Action:** `use`
**Effect:** Sets `cult_timing_understood: true`

**Progression Path:**
1. Travel to Hidden Observatory
2. Use Celestial Calculator
3. ✅ `cult_timing_understood: true` achieved

---

### Branch C: Justice Preparation

#### Condition 5: `justice_tools_acquired: true`
**Object:** Justice Weapon (Church)
**Action:** `pickup`
**Effect:** Sets `justice_tools_acquired: true`

**Progression Path:**
1. Travel to Church
2. Pick up Justice Weapon
3. ✅ `justice_tools_acquired: true` achieved

#### Condition 6: `evidence_chain_complete: true`
**Object:** Evidence Compiler (Church)
**Action:** `use`
**Effect:** Sets `evidence_chain_complete: true`

**Progression Path:**
1. In Church (same room as Justice Weapon)
2. Use Evidence Compiler
3. ✅ `evidence_chain_complete: true` achieved

---

### Final Synthesis

#### Condition 7: `final_confrontation_ready: true`
**Object:** Confrontation Planner (Hidden Observatory)
**Action:** `use`
**Effect:** Sets `final_confrontation_ready: true`

**Progression Path:**
1. Travel to Hidden Observatory (same room as Celestial Calculator)
2. Use Confrontation Planner
3. ✅ `final_confrontation_ready: true` achieved

---

## Complete Progression Path

### Optimal Route (Minimal Travel):
1. **Town Square** → Complete Phase 1 (3 evidence objects)
2. **Abandoned Warehouse** → Complete Branch A (2 objects)
3. **Old Library** → Complete Branch B part 1 (1 object)
4. **Hidden Observatory** → Complete Branch B part 2 + Final Synthesis (2 objects)
5. **Church** → Complete Branch C (2 objects)

### Total Rooms to Visit: 5
### Total Objects to Interact With: 8
### Estimated Rounds: 10-15 (depending on AP usage and exploration)

## Room Connections
- **Town Square** → connects to all other areas
- **Abandoned Warehouse** → accessible from Town Square
- **Old Library** → accessible from Town Square
- **Hidden Observatory** → accessible from Town Square
- **Church** → accessible from Town Square

## Key Success Factors
1. **Start Early:** Begin evidence collection in Town Square immediately
2. **Plan Routes:** Minimize travel between rooms to conserve AP
3. **Use Aliases:** Objects have `read`, `examine`, `investigate` aliases for `look` actions
4. **Complete Branches:** Finish each branch before moving to the next
5. **Final Synthesis:** Use Confrontation Planner only after all other conditions are met

## Failure Conditions to Avoid
- `evidence_destroyed: true` - Don't destroy evidence
- `cult_escaped: true` - Don't let cult members escape
- `dark_power_channeled: true` - Don't channel dark power

## Tips for Multi-Player Games
- **Cooperation:** Share information about object locations
- **Competition:** Race to complete branches first
- **Strategy:** Block opponents from accessing key objects
- **Alliances:** Work together to complete the final confrontation
