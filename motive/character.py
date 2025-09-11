from typing import List, Dict, Any, Optional
import random
from motive.game_object import GameObject
from motive.config import MotiveConfig


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
        aliases: Optional[List[str]] = None
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
        
        # Handle motive assignment - prioritize selected_motive, then motives, then legacy motive
        if selected_motive:
            self.selected_motive = selected_motive
            self.motive = selected_motive.description  # For backward compatibility
        elif motives and len(motives) > 0:
            # Randomly select a motive if none was pre-selected
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

    def add_tag(self, tag: str):
        self.tags.add(tag)

    def remove_tag(self, tag: str):
        self.tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def set_property(self, key: str, value: Any):
        self.properties[key] = value

    def get_property(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)

    def get_introduction_message(self) -> str:
        """Generate a character introduction message for the player."""
        return f"**👤 Character:**\nYou are {self.name}, {self.backstory}.\n\n**🎯 Motive:**\n{self.motive}"

    def _evaluate_condition_group(self, condition_group, game_master) -> bool:
        """Evaluate a single condition or condition group."""
        from motive.config import MotiveConditionGroup
        
        if isinstance(condition_group, MotiveConditionGroup):
            # Multiple conditions with explicit operator
            results = []
            for condition in condition_group.conditions:
                condition_dict = {
                    'type': condition.type,
                    'requirements': [condition.model_dump()]
                }
                success, _, _ = game_master._check_requirements(self, condition_dict, {})
                results.append(success)
            
            if condition_group.operator == "AND":
                return all(results)
            elif condition_group.operator == "OR":
                return any(results)
        else:
            # Single condition
            condition_dict = {
                'type': condition_group.type,
                'requirements': [condition_group.model_dump()]
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
                condition_dict = {
                    'type': condition.type,
                    'requirements': [condition.model_dump()]
                }
                success, _, _ = game_master._check_requirements(self, condition_dict, {})
                
                # Get condition description
                condition_desc = self._get_condition_description(condition)
                
                # Add checkbox
                status_checkbox = "☑️" if success else "☐"
                lines.append(f"{indent}  {status_checkbox} {condition_desc}")
        else:
            # Single condition
            condition_dict = {
                'type': condition_group.type,
                'requirements': [condition_group.model_dump()]
            }
            success, _, _ = game_master._check_requirements(self, condition_dict, {})
            
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

    def get_motive_status_message(self, game_master) -> Optional[str]:
        """Get a status message for the player about their current motive state."""
        if not self.selected_motive:
            return None
        
        success_result = self.check_motive_success(game_master)
        failure_result = self.check_motive_failure(game_master)
        
        if failure_result:
            return f"⚠️ **MOTIVE STATUS**: Your motive '{self.selected_motive.id}' is currently FAILING. You must resolve this before the game ends to avoid failure."
        elif success_result:
            return f"✅ **MOTIVE STATUS**: Your motive '{self.selected_motive.id}' is currently SUCCEEDING and not failing. Keep it up!"
        
        return None  # Neither succeeding nor failing - no status update needed

    def __repr__(self):
        return f"Character(id='{self.id}', name='{self.name}', room='{self.current_room_id}', ap={self.action_points})"
