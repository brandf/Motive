"""Inventory constraint system for objects and players."""

from typing import Dict, Any, List, Tuple, Optional
from motive.game_object import GameObject
from motive.character import Character
from motive.config import Event
from datetime import datetime


class InventoryConstraintError(Exception):
    """Raised when an inventory constraint is violated."""
    pass


def check_inventory_constraints(
    object_to_add: GameObject, 
    target_player: Character, 
    action_name: str = "inventory operation"
) -> Tuple[bool, Optional[str], Optional[Event]]:
    """
    Check if an object can be added to a player's inventory.
    
    Args:
        object_to_add: The object being added to inventory
        target_player: The player receiving the object
        action_name: The name of the action being performed (for error messages)
    
    Returns:
        Tuple of (can_add, error_message, error_event)
        - can_add: True if the object can be added, False otherwise
        - error_message: Human-readable error message if can_add is False
        - error_event: Event to broadcast if can_add is False
    """
    
    # Check basic immovable constraints
    if "immovable" in object_to_add.tags:
        error_msg = f"Cannot perform '{action_name}': Cannot add '{object_to_add.name}' to inventory - it is immovable."
        error_event = Event(
            message=f"{target_player.name} attempts to add the {object_to_add.name} to their inventory, but it is immovable.",
            event_type="player_action",
            source_room_id=target_player.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_object_id=object_to_add.id,
            related_player_id=target_player.id,
            observers=["room_characters"]
        )
        return False, error_msg, error_event
    
    # Check weight constraints
    if "too_heavy" in object_to_add.tags:
        error_msg = f"Cannot perform '{action_name}': Cannot add '{object_to_add.name}' to inventory - it is too heavy."
        error_event = Event(
            message=f"{target_player.name} attempts to add the {object_to_add.name} to their inventory, but it is too heavy.",
            event_type="player_action",
            source_room_id=target_player.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_object_id=object_to_add.id,
            related_player_id=target_player.id,
            observers=["room_characters"]
        )
        return False, error_msg, error_event
    
    # Check magical binding constraints
    if "magically_bound" in object_to_add.tags:
        error_msg = f"Cannot perform '{action_name}': Cannot add '{object_to_add.name}' to inventory - it is magically bound to its location."
        error_event = Event(
            message=f"{target_player.name} attempts to add the {object_to_add.name} to their inventory, but it is magically bound to this location.",
            event_type="player_action",
            source_room_id=target_player.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_object_id=object_to_add.id,
            related_player_id=target_player.id,
            observers=["room_characters"]
        )
        return False, error_msg, error_event
    
    # Check size-based constraints
    if "requires_size" in object_to_add.tags:
        required_size = object_to_add.properties.get("required_size", "medium")
        player_size = target_player.properties.get("size", "medium")
        
        # Define size hierarchy (larger numbers = bigger)
        size_hierarchy = {
            "tiny": 1,
            "small": 2, 
            "medium": 3,
            "large": 4,
            "huge": 5,
            "gargantuan": 6
        }
        
        player_size_value = size_hierarchy.get(player_size, 3)  # Default to medium
        required_size_value = size_hierarchy.get(required_size, 3)
        
        if player_size_value < required_size_value:
            error_msg = f"Cannot perform '{action_name}': Cannot add '{object_to_add.name}' to inventory - requires size {required_size} or larger, but {target_player.name} is {player_size}."
            error_event = Event(
                message=f"{target_player.name} attempts to add the {object_to_add.name} to their inventory, but they are too small ({player_size} < {required_size}).",
                event_type="player_action",
                source_room_id=target_player.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_object_id=object_to_add.id,
                related_player_id=target_player.id,
                observers=["room_characters"]
            )
            return False, error_msg, error_event
    
    # Check class-based constraints
    if "requires_class" in object_to_add.tags:
        required_class = object_to_add.properties.get("required_class", "")
        player_class = target_player.properties.get("class", "")
        
        if player_class.lower() != required_class.lower():
            error_msg = f"Cannot perform '{action_name}': Cannot add '{object_to_add.name}' to inventory - requires class {required_class}, but {target_player.name} is {player_class}."
            error_event = Event(
                message=f"{target_player.name} attempts to add the {object_to_add.name} to their inventory, but they are the wrong class ({player_class} != {required_class}).",
                event_type="player_action",
                source_room_id=target_player.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_object_id=object_to_add.id,
                related_player_id=target_player.id,
                observers=["room_characters"]
            )
            return False, error_msg, error_event
    
    # Check level-based constraints
    if "requires_level" in object_to_add.tags:
        required_level = object_to_add.properties.get("required_level", 1)
        player_level = target_player.properties.get("level", 1)
        
        if player_level < required_level:
            error_msg = f"Cannot perform '{action_name}': Cannot add '{object_to_add.name}' to inventory - requires level {required_level}, but {target_player.name} is level {player_level}."
            error_event = Event(
                message=f"{target_player.name} attempts to add the {object_to_add.name} to their inventory, but they are not high enough level ({player_level} < {required_level}).",
                event_type="player_action",
                source_room_id=target_player.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_object_id=object_to_add.id,
                related_player_id=target_player.id,
                observers=["room_characters"]
            )
            return False, error_msg, error_event
    
    # Check custom constraints defined in object properties
    if "custom_constraints" in object_to_add.properties:
        custom_constraints = object_to_add.properties["custom_constraints"]
        for constraint in custom_constraints:
            constraint_type = constraint.get("type")
            constraint_value = constraint.get("value")
            player_value = target_player.properties.get(constraint_type, "")
            
            if str(player_value).lower() != str(constraint_value).lower():
                error_msg = f"Cannot perform '{action_name}': Cannot add '{object_to_add.name}' to inventory - requires {constraint_type} {constraint_value}, but {target_player.name} has {constraint_type} {player_value}."
                error_event = Event(
                    message=f"{target_player.name} attempts to add the {object_to_add.name} to their inventory, but they don't meet the requirements ({constraint_type}: {player_value} != {constraint_value}).",
                    event_type="player_action",
                    source_room_id=target_player.current_room_id,
                    timestamp=datetime.now().isoformat(),
                    related_object_id=object_to_add.id,
                    related_player_id=target_player.id,
                    observers=["room_characters"]
                )
                return False, error_msg, error_event
    
    # All constraints passed
    return True, None, None


def validate_inventory_transfer(
    object_to_transfer: GameObject,
    from_player: Optional[Character],
    to_player: Character,
    action_name: str = "inventory transfer"
) -> Tuple[bool, Optional[str], Optional[Event]]:
    """
    Validate that an object can be transferred from one player to another.
    
    Args:
        object_to_transfer: The object being transferred
        from_player: The player giving the object (None for pickup from room)
        to_player: The player receiving the object
        action_name: The name of the action being performed
    
    Returns:
        Tuple of (can_transfer, error_message, error_event)
    """
    
    # Check if the receiving player can have this object in their inventory
    can_add, error_msg, error_event = check_inventory_constraints(
        object_to_transfer, to_player, action_name
    )
    
    if not can_add:
        return False, error_msg, error_event
    
    # Additional transfer-specific constraints could go here
    # For example, checking if the object is bound to the original player
    
    return True, None, None
