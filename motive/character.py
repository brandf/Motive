from typing import List, Dict, Any, Optional, Tuple
import random
import json
from motive.game_object import GameObject
from motive.config import MotiveConfig, MotiveConditionGroup, ActionRequirementConfig, MotiveStatusPrompt


class Character:
    """Represents the in-game state of a character."""
    def __init__(
        self,
        char_id: str,
        name: str,
        backstory: str,
        motive: Optional[str] = None,  # Legacy single motive
        motives: Optional[List[MotiveConfig]] = None,  # New multiple motives
        selected_motive: Optional[MotiveConfig] = None,  # The randomly selected motive
        current_room_id: str = "",
        inventory: Optional[Dict[str, GameObject]] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        action_points: int = 3, # Default action points
        aliases: Optional[List[str]] = None,
        deterministic: bool = False,  # Use deterministic selection instead of random
        short_name: Optional[str] = None  # Short display name for observations
    ):
        self.id = char_id
        self.name = name
        self.backstory = backstory
        self.current_room_id = current_room_id
        self.inventory = inventory if inventory else {}
        self.tags = set(tags) if tags else set()
        self.properties = properties if properties else {}
        self.action_points = action_points
        self.aliases = aliases if aliases else []
        self.short_name = short_name
        
        # Initialize evidence system properties
        self._initialize_evidence_properties()

        # Track per-condition motive progress to emit narrative updates once
        self._motive_condition_state: Dict[str, bool] = {}
        
        # Handle motive assignment - prioritize selected_motive, then motives, then legacy motive
        if selected_motive:
            self.selected_motive = selected_motive
            self.motive = selected_motive.description  # For backward compatibility
        elif motives and len(motives) > 0:
            # Select a motive - use deterministic selection if requested, otherwise random
            if deterministic:
                self.selected_motive = motives[0]  # Always pick first motive in deterministic mode
            else:
                self.selected_motive = random.choice(motives)
            self.motive = self.selected_motive.description  # For backward compatibility
        elif motive:
            # Legacy single motive
            self.motive = motive
            self.selected_motive = None
        else:
            self.motive = "No motive assigned"
            self.selected_motive = None

    def add_item_to_inventory(self, item: GameObject):
        self.inventory[item.id] = item
        item.current_location_id = self.id

    def remove_item_from_inventory(self, item_id: str) -> Optional[GameObject]:
        # Try to remove by ID first
        if item_id in self.inventory:
            return self.inventory.pop(item_id)
        
        # If not found by ID, try to find by name (case-insensitive) and remove
        for game_obj_id, game_obj in list(self.inventory.items()): # Use list() to allow modification during iteration
            if game_obj.name.lower() == item_id.lower():
                return self.inventory.pop(game_obj_id)
        return None

    def has_item_in_inventory(self, item_name_or_id: str) -> bool:
        """Checks if an item is in the inventory by its ID or name (case-insensitive)."""
        return self.get_item_in_inventory(item_name_or_id) is not None

    def get_item_in_inventory(self, item_name_or_id: str) -> Optional[GameObject]:
        """Gets a GameObject from inventory by its ID or name (case-insensitive)."""
        # Try to find by ID first
        item = self.inventory.get(item_name_or_id)
        if item:
            return item
        
        # If not found by ID, try to find by name (case-insensitive)
        for game_obj in self.inventory.values():
            if game_obj.name.lower() == item_name_or_id.lower():
                return game_obj
        return None

    def get_display_name(self) -> str:
        """Gets the display name for this character (short name if available, otherwise full name)."""
        # Check if we have a short_name property
        if hasattr(self, 'short_name') and self.short_name:
            return self.short_name
        return self.name

    def add_tag(self, tag: str):
        self.tags.add(tag)

    def remove_tag(self, tag: str):
        self.tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def set_property(self, key: str, value: Any):
        self.properties[key] = value

    def get_property(self, key: str, default: Any = None) -> Any:
        # First check the properties dictionary
        if key in self.properties:
            return self.properties[key]
        
        # Then check if it's a computed property (class attribute with @property decorator)
        if hasattr(self.__class__, key):
            attr = getattr(self.__class__, key)
            if hasattr(attr, 'fget'):  # This indicates it's a property
                return getattr(self, key)
        
        # Fall back to default
        return default

    def get_introduction_message(self) -> str:
        """Generate a character introduction message for the player."""
        return f"**👤 Character:**\nYou are {self.name}, {self.backstory}\n\n**🎯 Motive:**\n{self.motive}"

    def _evaluate_condition_group(self, condition_group, game_master) -> bool:
        """Evaluate a single condition or condition group."""
        if isinstance(condition_group, MotiveConditionGroup):
            # Multiple conditions with explicit operator
            results = []
            for condition in condition_group.conditions:
                success = self._evaluate_single_condition(condition, game_master)
                results.append(success)
            
            if condition_group.operator == "AND":
                return all(results)
            elif condition_group.operator == "OR":
                return any(results)
        else:
            return self._evaluate_single_condition(condition_group, game_master)

    def _evaluate_single_condition(self, condition, game_master) -> bool:
        """Evaluate a single condition requirement."""
        requirement_payload = condition.model_dump(exclude={'progress_message'}, exclude_none=True)
        condition_dict = {
            'type': condition.type,
            'requirements': [requirement_payload]
        }
        success, _, _ = game_master._check_requirements(self, condition_dict, {})
        return success

    def check_motive_success(self, game_master) -> bool:
        """Check if the character's selected motive has been achieved."""
        if not self.selected_motive or not self.selected_motive.success_conditions:
            return False
        
        return self._evaluate_condition_group(self.selected_motive.success_conditions, game_master)

    def check_motive_failure(self, game_master) -> bool:
        """Check if the character's selected motive has failed."""
        if not self.selected_motive or not self.selected_motive.failure_conditions:
            return False
        
        return self._evaluate_condition_group(self.selected_motive.failure_conditions, game_master)

    def get_motive_debug_info(self, game_master) -> Dict[str, Any]:
        """Get detailed debugging information about motive conditions."""
        if not self.selected_motive:
            return {"motive_id": "none", "success": False, "failure": False, "details": "No motive assigned"}
        
        success_result = self.check_motive_success(game_master)
        failure_result = self.check_motive_failure(game_master)
        
        return {
            "motive_id": self.selected_motive.id,
            "motive_description": self.selected_motive.description,
            "success": success_result,
            "failure": failure_result,
            "final_status": "WIN" if (success_result and not failure_result) else ("FAIL" if failure_result else "NOT_ACHIEVED")
        }

    def get_motive_condition_tree(self, game_master) -> str:
        """Get a detailed condition tree showing the nested structure with checkmarks/X's."""
        if not self.selected_motive:
            return "No motive assigned"
        
        lines = []
        lines.append(f"🎯 Motive: {self.selected_motive.id}")
        lines.append(f"  {self.selected_motive.description}")
        lines.append("")
        
        # Success conditions tree
        if self.selected_motive.success_conditions:
            lines.append("👍 SUCCESS CONDITIONS:")
            success_tree = self._build_condition_tree(self.selected_motive.success_conditions, game_master, "  ")
            lines.extend(success_tree)
        else:
            lines.append("👍 SUCCESS CONDITIONS: None defined")
        
        lines.append("")
        
        # Failure conditions tree
        if self.selected_motive.failure_conditions:
            lines.append("👎 FAILURE CONDITIONS:")
            failure_tree = self._build_condition_tree(self.selected_motive.failure_conditions, game_master, "  ")
            lines.extend(failure_tree)
        else:
            lines.append("👎 FAILURE CONDITIONS: None defined")
        
        lines.append("")
        
        # Overall status
        success_result = self.check_motive_success(game_master)
        failure_result = self.check_motive_failure(game_master)
        
        if success_result and not failure_result:
            lines.append("🏆 FINAL STATUS: WIN (Success achieved, no failures)")
        elif failure_result:
            lines.append("💔 FINAL STATUS: FAIL (Failure conditions met)")
        else:
            lines.append("⏳ FINAL STATUS: NOT ACHIEVED (Neither success nor failure)")
        
        return "\n".join(lines)

    def _build_condition_tree(self, condition_group, game_master, indent="") -> List[str]:
        """Build a tree representation of conditions with checkboxes."""
        from motive.config import MotiveConditionGroup
        
        lines = []
        
        if isinstance(condition_group, MotiveConditionGroup):
            # Multiple conditions with operator - check if the group passes
            group_passes = self._evaluate_condition_group(condition_group, game_master)
            group_checkbox = "☑️" if group_passes else "☐"
            
            operator_desc = "all must pass" if condition_group.operator == "AND" else "any must pass"
            lines.append(f"{indent}{group_checkbox} {condition_group.operator} ({operator_desc})")
            
            for i, condition in enumerate(condition_group.conditions):
                # Check if this individual condition passes
                success = self._evaluate_single_condition(condition, game_master)
                
                # Get condition description
                condition_desc = self._get_condition_description(condition)
                
                # Add checkbox
                status_checkbox = "☑️" if success else "☐"
                lines.append(f"{indent}  {status_checkbox} {condition_desc}")
        else:
            # Single condition
            success = self._evaluate_single_condition(condition_group, game_master)
            
            condition_desc = self._get_condition_description(condition_group)
            status_checkbox = "☑️" if success else "☐"
            lines.append(f"{indent}{status_checkbox} {condition_desc}")
        
        return lines

    def _get_condition_description(self, condition) -> str:
        """Get a human-readable description of a condition."""
        if condition.type == "player_has_tag":
            return f"Player has tag '{condition.tag}'"
        elif condition.type == "object_in_room":
            return f"Object '{condition.object_name_param}' is in room"
        elif condition.type == "object_in_inventory":
            return f"Object '{condition.object_name_param}' is in inventory"
        elif condition.type == "player_in_room":
            return f"Player '{condition.target_player_param}' is in room"
        elif condition.type == "exit_exists":
            return f"Exit '{condition.direction_param}' exists"
        elif condition.type == "object_property_equals":
            return f"Object property '{condition.property}' equals '{condition.value}'"
        else:
            return f"{condition.type}: {condition.model_dump()}"

    def _ensure_status_prompts_initialized(self) -> List[MotiveStatusPrompt]:
        """Lazily hydrate status prompts from raw config when missing."""
        if not self.selected_motive:
            return []

        prompts = getattr(self.selected_motive, 'status_prompts', []) or []
        if prompts:
            return prompts

        raw_map = getattr(self, '_raw_status_prompts', {}) or {}
        raw_prompts = raw_map.get(self.selected_motive.id)
        if not raw_prompts:
            return []

        converted: List[MotiveStatusPrompt] = []
        for prompt in raw_prompts:
            if isinstance(prompt, MotiveStatusPrompt):
                converted.append(prompt)
                continue

            if not isinstance(prompt, dict):
                continue

            raw_condition = prompt.get('condition')
            condition_obj = None

            if isinstance(raw_condition, (ActionRequirementConfig, MotiveConditionGroup)):
                condition_obj = raw_condition
            elif isinstance(raw_condition, dict):
                if 'type' in raw_condition:
                    condition_obj = ActionRequirementConfig(**raw_condition)
                elif 'operator' in raw_condition:
                    operator = raw_condition['operator']
                    raw_conditions = raw_condition.get('conditions', []) or []
                    condition_obj = MotiveConditionGroup(
                        operator=operator,
                        conditions=[
                            cond if isinstance(cond, ActionRequirementConfig)
                            else ActionRequirementConfig(**cond)
                            for cond in raw_conditions
                        ]
                    )
            elif isinstance(raw_condition, list):
                if raw_condition and isinstance(raw_condition[0], dict) and 'operator' in raw_condition[0]:
                    operator = raw_condition[0]['operator']
                    condition_obj = MotiveConditionGroup(
                        operator=operator,
                        conditions=[
                            cond if isinstance(cond, ActionRequirementConfig)
                            else ActionRequirementConfig(**cond)
                            for cond in raw_condition[1:]
                        ]
                    )

            message = prompt.get('message')
            if not message:
                continue

            converted.append(MotiveStatusPrompt(condition=condition_obj, message=message))

        self.selected_motive.status_prompts = converted
        return converted

    def get_motive_status_message(self, game_master) -> Optional[str]:
        """Get a status message for the player about their current motive state."""
        if not self.selected_motive:
            return None

        status_prompts = self._ensure_status_prompts_initialized()
        for prompt in status_prompts:
            condition = getattr(prompt, 'condition', None)
            if condition and not self._evaluate_condition_group(condition, game_master):
                continue
            return prompt.message

        # Fall back to generic narrative beats if no prompts match
        success_result = self.check_motive_success(game_master)
        failure_result = self.check_motive_failure(game_master)

        if failure_result:
            return "⚠️ **Case Outlook:** Something vital slipped through your grasp—recover the missing thread quickly."
        if success_result:
            return "✅ **Case Outlook:** Your plan is converging; stay vigilant until the final move."

        return None  # Neither succeeding nor failing - no status update needed

    def collect_motive_progress_updates(self, game_master) -> List[str]:
        """Return newly satisfied success-condition messages for this motive."""
        updates: List[str] = []

        if not self.selected_motive or not self.selected_motive.success_conditions:
            return updates

        for identifier, passed, message in self._iter_success_conditions(self.selected_motive.success_conditions, game_master):
            previous = self._motive_condition_state.get(identifier, False)
            if passed and not previous and message:
                updates.append(message)
            self._motive_condition_state[identifier] = passed

        return updates

    def _iter_success_conditions(
        self,
        condition_group,
        game_master,
        path: Tuple[int, ...] = (),
    ) -> List[Tuple[str, bool, Optional[str]]]:
        """Yield (identifier, passed, message) for each leaf success condition."""
        results: List[Tuple[str, bool, Optional[str]]] = []

        if isinstance(condition_group, MotiveConditionGroup):
            for idx, condition in enumerate(condition_group.conditions):
                results.extend(self._iter_success_conditions(condition, game_master, path + (idx,)))
        else:
            success = self._evaluate_single_condition(condition_group, game_master)
            condition_payload = condition_group.model_dump(exclude_none=True)
            # Ensure progress_message does not influence requirement evaluation but does influence identifier uniqueness
            message = condition_payload.get('progress_message')
            condition_payload.pop('progress_message', None)
            identifier = json.dumps(
                {
                    "motive": self.selected_motive.id if self.selected_motive else "unknown",
                    "path": path,
                    "condition": condition_payload,
                },
                sort_keys=True,
            )
            results.append((identifier, success, message))

        return results

    def _initialize_evidence_properties(self):
        """Initialize evidence system properties with unique flags for each piece of evidence."""
        # Individual evidence flags - each piece of evidence gets its own unique flag
        evidence_flags = [
            'notice_board_found',
            'fresh_evidence_found',
            'partner_evidence_found',
            'cult_history_found',
            'ritual_timing_found',
            'church_records_found',
            'witness_testimony_found',
            'town_records_found',
            'missing_persons_log_found',
            'local_newspaper_found',
            'editor_notes_found',
            'graveyard_epitaphs_found',
            'priest_diary_found',
            'sacred_map_found',
            'ritual_texts_found',
            'astronomers_notes_found',
            'ancient_calendar_found',
            'ritual_schedule_found'
        ]
        
        # Initialize all evidence flags to False if not already set
        for flag in evidence_flags:
            if flag not in self.properties:
                self.properties[flag] = False

    @property
    def evidence_found(self) -> int:
        """Computed property that counts the number of unique evidence pieces found.
        This prevents 'cheesing' by looking at the same evidence multiple times."""
        evidence_flags = [
            'notice_board_found',
            'fresh_evidence_found',
            'partner_evidence_found',
            'cult_history_found',
            'ritual_timing_found',
            'church_records_found',
            'witness_testimony_found',
            'town_records_found',
            'missing_persons_log_found',
            'local_newspaper_found',
            'editor_notes_found',
            'graveyard_epitaphs_found',
            'priest_diary_found',
            'sacred_map_found',
            'ritual_texts_found',
            'astronomers_notes_found',
            'ancient_calendar_found',
            'ritual_schedule_found'
        ]
        
        return sum(1 for flag in evidence_flags if self.properties.get(flag, False))

    @property
    def inventory_space_used(self) -> int:
        """Computed property that calculates the total inventory space used by all items."""
        total_space = 0
        for item in self.inventory.values():
            # Get the size property from the item's properties dict, default to medium (3) if not specified
            size_value = item.properties.get('size', 'medium')
            
            # Convert size string to numeric value
            size_map = {
                'tiny': 1,
                'small': 2, 
                'medium': 3,
                'large': 4,
                'huge': 6
            }
            total_space += size_map.get(size_value, 3)  # Default to medium if unknown size
        
        return total_space

    @property
    def inventory_space_available(self) -> int:
        """Computed property that calculates remaining inventory space."""
        max_space = self.properties.get('inventory_size', 12)  # Default to 12 spaces
        return max_space - self.inventory_space_used

    def __repr__(self):
        return f"Character(id='{self.id}', name='{self.name}', room='{self.current_room_id}', ap={self.action_points})"
