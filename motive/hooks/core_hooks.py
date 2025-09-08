import logging
from typing import List, Dict, Any
from motive.game_master import GameMaster # Circular import for now, will refine
from motive.player import PlayerCharacter

def generate_help_message(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> List[str]:
    """Generates a help message with available actions and their costs/descriptions."""
    help_message_parts = ["Available actions:"]
    for action_id, action_cfg in game_master.game_actions.items():
        help_message_parts.append(f"- {action_cfg.name} ({action_cfg.cost} AP): {action_cfg.description}")
    
    return ["\n".join(help_message_parts)]

def look_at_target(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> List[str]:
    """Provides a detailed description of the current room or a specified object/character."""
    feedback_messages: List[str] = []
    target_name = params.get("target")

    if not target_name:
        # No target specified, describe the current room
        current_room = game_master.rooms.get(player_char.current_room_id)
        if current_room:
            room_description_parts = [current_room.description]
            if current_room.objects:
                object_names = [obj.name for obj in current_room.objects.values()]
                room_description_parts.append(f"You also see: {', '.join(object_names)}.")
            if current_room.exits:
                exit_names = [exit_data['name'] for exit_data in current_room.exits.values() if not exit_data.get('is_hidden', False)]
                if exit_names:
                    room_description_parts.append(f"Exits: {', '.join(exit_names)}.")
            feedback_messages.append(" ".join(room_description_parts))
        else:
            feedback_messages.append("You are in an unknown location.")
    else:
        # Target specified, try to find it in the room or inventory
        target_object = player_char.get_item_in_inventory(target_name)
        if not target_object:
            current_room = game_master.rooms.get(player_char.current_room_id)
            if current_room:
                target_object = current_room.get_object(target_name)
        
        if target_object:
            feedback_messages.append(f"You look at the {target_object.name}. {target_object.description}")
            if target_object.properties:
                props = ", ".join([f"{k}: {v}" for k, v in target_object.properties.items()])
                feedback_messages.append(f"It has properties: {props}.")
        else:
            feedback_messages.append(f"You don't see any '{target_name}' here or in your inventory.")

    return feedback_messages

def handle_move_action(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> List[str]:
    """Handles the player character movement between rooms."""
    feedback_messages: List[str] = []
    direction = params.get("direction")

    if not direction:
        feedback_messages.append("Move action requires a direction.")
        return feedback_messages

    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append(f"Error: Player is in an unknown room (ID: {player_char.current_room_id}).")
        return feedback_messages

    # Find the exit by name (case-insensitive) from the current room's exits
    exit_data = None
    for exit_id, exit_info in current_room.exits.items():
        if exit_info['name'].lower() == direction.lower() and not exit_info.get('is_hidden', False):
            exit_data = exit_info
            break

    if not exit_data:
        feedback_messages.append(f"Cannot move '{player_char.name}': No visible exit in the '{direction}' direction.")
        return feedback_messages

    destination_room_id = exit_data['destination_room_id']
    destination_room = game_master.rooms.get(destination_room_id)

    if not destination_room:
        feedback_messages.append(f"Error: Destination room '{destination_room_id}' not found.")
        return feedback_messages

    # Move player from current room to destination room
    current_room.remove_player(player_char.id)
    destination_room.add_player(player_char)

    feedback_messages.append(f"You move to the '{destination_room.name}'.")
    return feedback_messages

def handle_pickup_action(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> List[str]:
    """Handles a player picking up an object from the current room."""
    feedback_messages: List[str] = []
    object_name = params.get("object_name")

    if not object_name:
        feedback_messages.append("Pickup action requires an object name.")
        return feedback_messages

    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append(f"Error: Player is in an unknown room (ID: {player_char.current_room_id}).")
        return feedback_messages

    obj_to_pickup = current_room.get_object(object_name)
    if not obj_to_pickup:
        feedback_messages.append(f"You don't see any '{object_name}' here to pick up.")
        return feedback_messages

    # Remove from room and add to player inventory
    current_room.remove_object(obj_to_pickup.id)
    player_char.add_item_to_inventory(obj_to_pickup)

    feedback_messages.append(f"You pick up the {obj_to_pickup.name}.")
    return feedback_messages
