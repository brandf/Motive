import logging
from typing import List, Dict, Any, Tuple
from motive.game_master import GameMaster # Circular import for now, will refine
from motive.player import PlayerCharacter
from motive.config import Event
from datetime import datetime

def generate_help_message(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Generates a help message with available actions and their costs/descriptions."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []

    help_message_parts = ["Available actions:"]
    for action_id, action_cfg in game_master.game_actions.items():
        help_message_parts.append(f"- {action_cfg.name} ({action_cfg.cost} AP): {action_cfg.description}")
    
    # Add action prompt to consolidate the message
    help_message_parts.append("")
    help_message_parts.append("Example actions: look, move, say, pickup, pass, help (for more available actions).")
    
    full_help_message = "\n".join(help_message_parts)
    feedback_messages.append(full_help_message)

    events_generated.append(Event(
        message=f"{player_char.name} requests help.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]
    ))

    return events_generated, feedback_messages

def look_at_target(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Provides a detailed description of the current room or a specified object/character."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    target_name = params.get("target")
    event_message = ""

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
            event_message = f"{player_char.name} looks around the room."
            events_generated.append(Event(
                message=event_message,
                event_type="player_action",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                observers=["room_players"]
            ))
        else:
            feedback_messages.append("You are in an unknown location.")
            event_message = f"Player {player_char.name} looked around an unknown location."
    else:
        # Target specified, try to find it in the room or inventory
        target_object = player_char.get_item_in_inventory(target_name)
        if not target_object:
            current_room = game_master.rooms.get(player_char.current_room_id)
            if current_room:
                target_object = current_room.get_object(target_name)
        
        if target_object:
            obj_description = f"You look at the {target_object.name}. {target_object.description}"
            feedback_messages.append(obj_description)
            if target_object.properties:
                props = ", ".join([f"{k}: {v}" for k, v in target_object.properties.items()])
                feedback_messages.append(f"It has properties: {props}.")
            event_message = f"Player {player_char.name} looked at {target_object.name}."
            events_generated.append(Event(
                message=event_message,
                event_type="player_action",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                related_object_id=target_object.id,
                observers=["player", "room_players", "game_master"]
            ))
        else:
            feedback_messages.append(f"You don't see any '{target_name}' here or in your inventory.")
            event_message = f"Player {player_char.name} tried to look at non-existent object '{target_name}'."

    events_generated.append(Event(
        message=event_message,
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["player", "game_master"]
    ))
    
    return events_generated, feedback_messages

def handle_move_action(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles the player character movement between rooms."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    direction = params.get("direction")

    if not direction:
        feedback_messages.append("Move action requires a direction.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to move without specifying a direction.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append(f"Error: Player is in an unknown room (ID: {player_char.current_room_id}).")
        events_generated.append(Event(
            message=f"Player {player_char.name} is in an unknown room ({player_char.current_room_id}) and cannot move.",
            event_type="system_error",
            source_room_id="unknown",
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["game_master"]
        ))
        return events_generated, feedback_messages

    # Find the exit by name (case-insensitive) from the current room's exits
    exit_data = None
    for exit_id, exit_info in current_room.exits.items():
        if exit_info['name'].lower() == direction.lower() and not exit_info.get('is_hidden', False):
            exit_data = exit_info
            break

    if not exit_data:
        feedback_messages.append(f"Cannot move '{player_char.name}': No visible exit in the '{direction}' direction.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to move '{direction}' but no exit was found.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    destination_room_id = exit_data['destination_room_id']
    destination_room = game_master.rooms.get(destination_room_id)

    if not destination_room:
        feedback_messages.append(f"Error: Destination room '{destination_room_id}' not found.")
        events_generated.append(Event(
            message=f"System error: Destination room '{destination_room_id}' not found for move action.",
            event_type="system_error",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["game_master"]
        ))
        return events_generated, feedback_messages

    # Move player from current room to destination room
    current_room.remove_player(player_char.id)
    destination_room.add_player(player_char)

    # Generate destination room description (like a free look action)
    destination_description_parts = [destination_room.description]
    if destination_room.objects:
        object_names = [obj.name for obj in destination_room.objects.values()]
        destination_description_parts.append(f"You also see: {', '.join(object_names)}.")
    if destination_room.exits:
        exit_names = [exit_data['name'] for exit_data in destination_room.exits.values() if not exit_data.get('is_hidden', False)]
        if exit_names:
            destination_description_parts.append(f"Exits: {', '.join(exit_names)}.")
    destination_description = " ".join(destination_description_parts)

    feedback_messages.append(f"You move to the '{destination_room.name}'.")
    feedback_messages.append(f"Destination: {destination_description}")
    
    # Generate exit event for players in the source room
    events_generated.append(Event(
        message=f"{player_char.name} left the room.",
        event_type="player_exit",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]  # Only players in the source room see the exit
    ))
    
    # Generate enter event for players in the destination room
    events_generated.append(Event(
        message=f"{player_char.name} entered the room.",
        event_type="player_enter",
        source_room_id=destination_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]  # Only players in the destination room see the enter
    ))
    
    return events_generated, feedback_messages
 
def handle_pickup_action(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles a player picking up an object from the current room."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    object_name = params.get("object_name")

    if not object_name:
        feedback_messages.append("Pickup action requires an object name.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to pick up an object without specifying its name.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append(f"Error: Player is in an unknown room (ID: {player_char.current_room_id}).")
        events_generated.append(Event(
            message=f"Player {player_char.name} is in an unknown room ({player_char.current_room_id}) and cannot pick up.",
            event_type="system_error",
            source_room_id="unknown",
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["game_master"]
        ))
        return events_generated, feedback_messages

    obj_to_pickup = current_room.get_object(object_name)
    if not obj_to_pickup:
        feedback_messages.append(f"You don't see any '{object_name}' here to pick up.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to pick up non-existent object '{object_name}'.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            related_object_id=object_name,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    # Remove from room and add to player inventory
    current_room.remove_object(obj_to_pickup.id)
    player_char.add_item_to_inventory(obj_to_pickup)

    feedback_messages.append(f"You pick up the {obj_to_pickup.name}.")
    events_generated.append(Event(
        message=f"{player_char.name} picked up the {obj_to_pickup.name}.",
        event_type="object_pickup",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        related_object_id=obj_to_pickup.id,
        observers=["room_players"]  # Only other players in the room see the pickup
    ))
    
    return events_generated, feedback_messages

def handle_say_action(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles a player saying something to other players in the room."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    phrase = params.get("phrase")

    if not phrase:
        feedback_messages.append("Say action requires a phrase to say.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to say nothing.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    feedback_messages.append(f"You say: \'{phrase}\'.")
    events_generated.append(Event(
        message=f"{player_char.name} says: \"{phrase}\".",
        event_type="player_communication",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]  # Only other players in the room hear the speech
    ))
    
    return events_generated, feedback_messages

def handle_pass_action(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles the player passing their turn."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    # Pass action costs 0 AP and ends the turn
    feedback_messages.append("You pass your turn.")
    
    event_message = f"Player {player_char.name} passed their turn."
    events_generated.append(Event(
        message=event_message,
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["player", "game_master"]
    ))
    
    return events_generated, feedback_messages

def handle_read_action(game_master: Any, player_char: PlayerCharacter, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles a player reading text from an object."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    object_name = params.get("object_name")

    if not object_name:
        feedback_messages.append("Read action requires an object name.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to read without specifying an object name.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append(f"Error: Player is in an unknown room (ID: {player_char.current_room_id}).")
        events_generated.append(Event(
            message=f"Player {player_char.name} is in an unknown room ({player_char.current_room_id}) and cannot read.",
            event_type="system_error",
            source_room_id="unknown",
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["game_master"]
        ))
        return events_generated, feedback_messages

    obj_to_read = current_room.get_object(object_name)
    if not obj_to_read:
        feedback_messages.append(f"You don't see any '{object_name}' here to read.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to read non-existent object '{object_name}'.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            related_object_id=object_name,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    # Check if the object has readable text
    if "text" in obj_to_read.properties:
        text_content = obj_to_read.properties["text"]
        feedback_messages.append(f"You read the {obj_to_read.name}: \"{text_content}\"")
        event_message = f"{player_char.name} reads the {obj_to_read.name}."
    else:
        feedback_messages.append(f"The {obj_to_read.name} has no readable text.")
        event_message = f"{player_char.name} attempts to read the {obj_to_read.name}, but it has no text."

    events_generated.append(Event(
        message=event_message,
        event_type="player_action",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        related_object_id=obj_to_read.id,
        observers=["room_players"]
    ))
    
    return events_generated, feedback_messages