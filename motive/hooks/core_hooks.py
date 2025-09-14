import logging
from typing import List, Dict, Any, Tuple
from motive.game_master import GameMaster # Circular import for now, will refine
from motive.character import Character
from motive.config import Event
from datetime import datetime

def generate_help_message(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Generates a help message with available actions, optionally filtered by category."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    category_filter = params.get("category")
    
    # Group actions by category
    actions_by_category = {}
    for action_id, action_cfg in game_master.game_actions.items():
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(action_cfg, 'category'):
            category = action_cfg.category or "other"
        else:
            category = action_cfg.get('category', 'other')
        if category not in actions_by_category:
            actions_by_category[category] = []
        actions_by_category[category].append(action_cfg)
    
    if category_filter:
        # Filter to specific category
        category_filter_lower = category_filter.lower()
        matching_categories = [cat for cat in actions_by_category.keys() if cat.lower() == category_filter_lower]
        
        if matching_categories:
            category = matching_categories[0]
            help_message_parts = [f"Actions in '{category}' category:"]
            for action_cfg in actions_by_category[category]:
                # Handle both Pydantic objects and dictionaries from merged config
                if hasattr(action_cfg, 'name'):
                    name = action_cfg.name
                    cost = action_cfg.cost
                    description = action_cfg.description
                else:
                    name = action_cfg.get('name', 'unknown')
                    cost_raw = action_cfg.get('cost', 0)
                    description = action_cfg.get('description', 'No description')
                    
                    # Handle cost as either integer or dictionary
                    if isinstance(cost_raw, dict):
                        cost = cost_raw.get('value', 0)  # Extract value from CostConfig dict
                    else:
                        cost = cost_raw
                help_message_parts.append(f"- {name} ({cost} AP): {description}")
        else:
            # Category not found, show available categories
            available_categories = sorted(actions_by_category.keys())
            help_message_parts = [f"Category '{category_filter}' not found."]
            help_message_parts.append(f"Available categories: {', '.join(available_categories)}")
            help_message_parts.append("Use 'help' without a category to see all actions.")
    else:
        # Show all actions grouped by category
        help_message_parts = ["Available actions by category:"]
        for category in sorted(actions_by_category.keys()):
            help_message_parts.append(f"\n{category.upper()}:")
            for action_cfg in actions_by_category[category]:
                # Handle both Pydantic objects and dictionaries from merged config
                if hasattr(action_cfg, 'name'):
                    name = action_cfg.name
                    cost = action_cfg.cost
                    description = action_cfg.description
                else:
                    name = action_cfg.get('name', 'unknown')
                    cost_raw = action_cfg.get('cost', 0)
                    description = action_cfg.get('description', 'No description')
                    
                    # Handle cost as either integer or dictionary
                    if isinstance(cost_raw, dict):
                        cost = cost_raw.get('value', 0)  # Extract value from CostConfig dict
                    else:
                        cost = cost_raw
                help_message_parts.append(f"  - {name} ({cost} AP): {description}")
        
        help_message_parts.append(f"\nUse 'help <category>' to see actions in a specific category (costs 5 AP).")
    
    full_help_message = "\n".join(help_message_parts)
    feedback_messages.append(full_help_message)

    events_generated.append(Event(
        message=f"{player_char.name} requests help{f' for {category_filter}' if category_filter else ''}.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]
    ))

    return events_generated, feedback_messages

def look_at_target(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Provides a detailed description of the current room or a specified object/character."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    target_name = params.get("target")
    event_message = ""

    if not target_name:
        # No target specified, describe the current room
        current_room = game_master.rooms.get(player_char.current_room_id)
        if current_room:
            # Use the same formatting method as initial room description
            feedback_messages.append(current_room.get_formatted_description())
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
        # Special case: look at inventory
        if target_name.lower() == "inventory":
            if not player_char.inventory:
                feedback_messages.append("Your inventory is empty.")
                event_message = f"{player_char.name} looks at their empty inventory."
            else:
                # Build inventory display
                inventory_items = []
                for item in player_char.inventory.values():
                    item_description = f"- {item.name}: {item.description}"
                    
                    # Add properties if they exist
                    if item.properties:
                        properties_text = ", ".join([f"{key}: {value}" for key, value in item.properties.items()])
                        item_description += f" (Properties: {properties_text})"
                    
                    inventory_items.append(item_description)
                
                # Create the inventory display
                inventory_text = "You are carrying:\n" + "\n".join(inventory_items)
                feedback_messages.append(inventory_text)
                event_message = f"{player_char.name} looks at their inventory."
            
            events_generated.append(Event(
                message=event_message,
                event_type="player_action",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                observers=["player"]  # Inventory is private, only the player sees it
            ))
            return events_generated, feedback_messages
        
        # Target specified, try to find it in the room or inventory
        target_object = player_char.get_item_in_inventory(target_name)
        if not target_object:
            current_room = game_master.rooms.get(player_char.current_room_id)
            if current_room:
                target_object = current_room.get_object(target_name)
        
        if target_object:
            obj_description = f"You look at the {target_object.name}. {target_object.description}"
            feedback_messages.append(obj_description)
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
                event_type="player_action_failed",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                observers=["player", "game_master"]
            ))
    
    return events_generated, feedback_messages

def handle_move_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
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

    # Find the exit by name or alias (case-insensitive) from the current room's exits
    exit_data = None
    for exit_id, exit_info in current_room.exits.items():
        if exit_info.get('is_hidden', False):
            continue
            
        # Check if direction matches the exit name
        if exit_info['name'].lower() == direction.lower():
            exit_data = exit_info
            break
            
        # Check if direction matches any of the exit aliases
        aliases = exit_info.get('aliases', [])
        if any(alias.lower() == direction.lower() for alias in aliases):
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
        message=f"{player_char.name} left the room via {direction}.",
        event_type="player_exit",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]  # Only players in the source room see the exit
    ))
    
    # Generate enter event for players in the destination room
    events_generated.append(Event(
        message=f"{player_char.name} entered the room from {direction}.",
        event_type="player_enter",
        source_room_id=destination_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]  # Only players in the destination room see the enter
    ))
    
    return events_generated, feedback_messages
 

def handle_say_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
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

def handle_pass_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
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

def handle_read_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
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

def handle_whisper_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles a player whispering privately to a specific player in the same room."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    # Check for whisper parsing errors first
    if '_whisper_parse_error' in params:
        feedback_messages.append(params['_whisper_parse_error'])
        feedback_messages.append("Correct format: whisper \"player_name\" \"message\"")
        events_generated.append(Event(
            message=f"Player {player_char.name} used invalid whisper format.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages
    
    target_player_name = params.get("player")
    phrase = params.get("phrase")

    if not target_player_name or not phrase:
        feedback_messages.append("Whisper action requires both a player name and a phrase.")
        feedback_messages.append("Correct format: whisper \"player_name\" \"message\"")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to whisper without proper parameters.",
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
            message=f"Player {player_char.name} is in an unknown room ({player_char.current_room_id}) and cannot whisper.",
            event_type="system_error",
            source_room_id="unknown",
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["game_master"]
        ))
        return events_generated, feedback_messages

    # Find the target player in the current room by name or alias
    target_player = None
    for player_id in current_room.player_ids:
        if player_id in game_master.players:
            player = game_master.players[player_id]
            # Check if the player name matches
            if player.name.lower() == target_player_name.lower():
                target_player = player
                break
            
            # Check if any character alias matches
            if hasattr(player, 'character') and player.character:
                character_aliases = getattr(player.character, 'aliases', [])
                if any(alias.lower() == target_player_name.lower() for alias in character_aliases):
                    target_player = player
                    break

    if not target_player:
        feedback_messages.append(f"You don't see any player named '{target_player_name}' in this room.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to whisper to non-existent player '{target_player_name}'.",
            event_type="player_action_failed",
            source_room_id=current_room.id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    # Don't whisper to yourself
    if target_player.id == player_char.id:
        feedback_messages.append("You can't whisper to yourself.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to whisper to themselves.",
            event_type="player_action_failed",
            source_room_id=current_room.id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages

    feedback_messages.append(f"You whisper to {target_player.name}: \"{phrase}\"")
    
    # Generate separate events for the speaker and target player
    # Event for the speaker
    events_generated.append(Event(
        message=f"You whisper to {target_player.name}: \"{phrase}\"",
        event_type="player_communication",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["player"]  # Only the speaker sees this event
    ))
    
    # Event for the target player
    events_generated.append(Event(
        message=f"{player_char.name} whispers to you: \"{phrase}\"",
        event_type="player_communication",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=target_player.id,
        observers=["player"]  # Only the target player sees this event
    ))
    
    return events_generated, feedback_messages

def handle_shout_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles a player shouting loudly, potentially heard in adjacent rooms."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    phrase = params.get("phrase")

    if not phrase:
        feedback_messages.append("Shout action requires a phrase to shout.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to shout without specifying a phrase.",
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
            message=f"Player {player_char.name} is in an unknown room ({player_char.current_room_id}) and cannot shout.",
            event_type="system_error",
            source_room_id="unknown",
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["game_master"]
        ))
        return events_generated, feedback_messages

    feedback_messages.append(f"You shout: \"{phrase}\"")
    
    # Generate event for current room and adjacent rooms
    events_generated.append(Event(
        message=f"{player_char.name} shouts: \"{phrase}\"",
        event_type="player_communication",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["player", "room_players", "adjacent_rooms"]  # Heard in current room and adjacent rooms
    ))
    
    return events_generated, feedback_messages

def calculate_help_cost(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> int:
    """Calculate the actual cost for the help action based on parameters."""
    # Handle both Pydantic objects and dictionaries from merged config
    if hasattr(action_config, 'cost'):
        cost_raw = action_config.cost
    else:
        cost_raw = action_config.get('cost', 0)
    
    # Extract the base cost value from CostConfig
    if hasattr(cost_raw, 'value'):
        base_cost = cost_raw.value
    elif isinstance(cost_raw, dict):
        base_cost = cost_raw.get('value', 0)  # Extract value from CostConfig dict
    else:
        base_cost = cost_raw  # Fallback for integer costs
    
    # If a category is specified and not empty/whitespace, reduce cost by half
    category = params.get("category")
    if category and category.strip():
        return base_cost // 2  # Half cost for category-specific help
    
    return base_cost  # Full cost for general help

def handle_pickup_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handle the pickup action - move an object from room to player inventory."""
    object_name = params.get("object_name")
    if not object_name:
        return [], ["Error: No object specified to pick up."]
    
    # Get the current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        return [], [f"Error: Character is in an unknown room: {player_char.current_room_id}."]
    
    # Find the object in the room
    # Strip quotes from object_name for comparison
    clean_object_name = object_name.strip('"\'')
    
    target_object = None
    for obj_id, obj in current_room.objects.items():
        if obj.name.lower() == clean_object_name.lower():
            target_object = obj
            break
    
    if not target_object:
        return [], [f"Error: '{object_name}' not found in the room."]
    
    # Check inventory constraints using centralized system
    from motive.inventory_constraints import validate_inventory_transfer
    
    can_transfer, error_msg, error_event = validate_inventory_transfer(
        target_object, None, player_char, "pickup"
    )
    
    if not can_transfer:
        return [error_event], [error_msg]
    
    # Move object from room to player inventory
    current_room.remove_object(target_object.id)
    player_char.add_item_to_inventory(target_object)
    
    # Generate events
    events = []
    feedback_messages = []
    
    # Generate timestamp
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    
    # Event for the player who picked up the item
    pickup_event = Event(
        message=f"You pick up the {target_object.name}.",
        event_type="item_pickup",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["player"]
    )
    events.append(pickup_event)
    
    # Event for other players in the room
    room_pickup_event = Event(
        message=f"{player_char.name} picks up the {target_object.name}.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["room_players"]
    )
    events.append(room_pickup_event)
    
    # Event for adjacent rooms (optional - they might hear the pickup)
    adjacent_pickup_event = Event(
        message=f"{player_char.name} picks up something.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["adjacent_rooms"]
    )
    events.append(adjacent_pickup_event)
    
    feedback_messages.append(f"You pick up the {target_object.name}.")
    
    return events, feedback_messages


def handle_drop_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handle drop action - move object from player inventory to current room."""
    from datetime import datetime
    
    events = []
    feedback_messages = []
    
    # Get object name from parameters
    object_name = params.get("object_name")
    if not object_name:
        # Generate event for failed drop
        error_event = Event(
            message=f"{player_char.name} attempts to drop something, but no object was specified.",
            event_type="player_action",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["room_players"]
        )
        events.append(error_event)
        feedback_messages.append("Cannot perform 'drop': No object name provided.")
        return events, feedback_messages
    
    # Find the object in player's inventory (case insensitive)
    target_object = None
    target_object_id = None
    for obj_id, obj in player_char.inventory.items():
        if obj.name.lower() == object_name.lower():
            target_object = obj
            target_object_id = obj_id
            break
    
    if not target_object:
        # Generate event for failed drop
        error_event = Event(
            message=f"{player_char.name} attempts to drop the {object_name}, but it is not in their inventory.",
            event_type="player_action",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["room_players"]
        )
        events.append(error_event)
        feedback_messages.append(f"Cannot perform 'drop': Object '{object_name}' not in inventory.")
        return events, feedback_messages
    
    # Get current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append("Cannot perform 'drop': Invalid room.")
        return events, feedback_messages
    
    # Move object from inventory to room
    del player_char.inventory[target_object_id]
    current_room.objects[target_object_id] = target_object
    
    # Update object's location
    target_object.current_location_id = player_char.current_room_id
    
    # Generate timestamp
    timestamp = datetime.now().isoformat()
    
    # Event for the player who dropped the item
    drop_event = Event(
        message=f"You drop the {target_object.name}.",
        event_type="item_drop",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["player"]
    )
    events.append(drop_event)
    
    # Event for other players in the room
    room_drop_event = Event(
        message=f"{player_char.name} drops the {target_object.name}.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["room_players"]
    )
    events.append(room_drop_event)
    
    # Event for adjacent rooms (optional - they might hear the drop)
    adjacent_drop_event = Event(
        message=f"{player_char.name} drops something.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["adjacent_rooms"]
    )
    events.append(adjacent_drop_event)
    
    # Special hoarding tracking for Bella "Whisper" Nightshade
    if player_char.name == "Bella \"Whisper\" Nightshade" and player_char.current_room_id == "thieves_den":
        # Count objects in Thieves' Den
        thieves_den = game_master.rooms.get("thieves_den")
        if thieves_den:
            object_count = len(thieves_den.objects)
            
            # Add hoarding tag if collection is complete (20+ objects)
            if object_count >= 20 and not player_char.has_tag("collection_complete"):
                player_char.add_tag("collection_complete")
                hoarding_event = Event(
                    message=f"Your secret stash in the Thieves' Den has grown to an impressive {object_count} objects! Your hoarding compulsion is satisfied.",
                    event_type="motive_progress",
                    source_room_id=player_char.current_room_id,
                    timestamp=timestamp,
                    related_player_id=player_char.id,
                    observers=["player"]
                )
                events.append(hoarding_event)
                feedback_messages.append(f"Your collection now contains {object_count} objects! Your hoarding compulsion grows stronger.")
            elif object_count >= 15:
                feedback_messages.append(f"Your collection grows to {object_count} objects. You're getting close to satisfying your hoarding compulsion.")
            elif object_count >= 10:
                feedback_messages.append(f"Your stash now contains {object_count} objects. The collection is taking shape.")
    
    feedback_messages.append(f"You drop the {target_object.name}.")
    
    return events, feedback_messages


def handle_give_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles the give action - transfers an object from giver's inventory to receiver's inventory."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    # Check for give parsing errors first
    if '_give_parse_error' in params:
        feedback_messages.append(params['_give_parse_error'])
        feedback_messages.append("Correct format: give \"player_name\" \"object_name\"")
        events_generated.append(Event(
            message=f"Player {player_char.name} used invalid give format.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages
    
    target_player_name = params.get("player", "").strip()
    object_name = params.get("object_name", "").strip()
    
    # Validate parameters
    if not target_player_name:
        feedback_messages.append("You must specify a player to give to.")
        return events_generated, feedback_messages
    
    if not object_name:
        feedback_messages.append("You must specify an object to give.")
        return events_generated, feedback_messages
    
    # Check if trying to give to self
    if target_player_name.lower() == player_char.name.lower():
        feedback_messages.append("You cannot give items to yourself.")
        return events_generated, feedback_messages
    
    # Find target player
    target_player = None
    for char_id, char in game_master.player_characters.items():
        if char.name.lower() == target_player_name.lower():
            target_player = char
            break
    
    if not target_player:
        feedback_messages.append(f"{target_player_name} is not a valid player.")
        return events_generated, feedback_messages
    
    # Check if target player is in the same room
    if target_player.current_room_id != player_char.current_room_id:
        feedback_messages.append(f"{target_player_name} is not in the same room as you.")
        return events_generated, feedback_messages
    
    # Check if giver has the object in inventory
    target_object = player_char.get_item_in_inventory(object_name)
    if not target_object:
        feedback_messages.append(f"You don't have a {object_name} in your inventory.")
        return events_generated, feedback_messages
    
    # Try to transfer the object
    removed_object = player_char.remove_item_from_inventory(object_name)
    if not removed_object:
        feedback_messages.append(f"Failed to remove {object_name} from your inventory.")
        return events_generated, feedback_messages
    
    # Try to add to target player's inventory
    # Note: add_item_to_inventory doesn't return a success indicator
    # For now, assume it always succeeds (no inventory limits implemented yet)
    target_player.add_item_to_inventory(removed_object)
    
    # Success! Generate feedback and events
    feedback_messages.append(f"You give the {object_name} to {target_player_name}.")
    
    # Generate event for room observers
    event_message = f"{player_char.name} gives a {object_name} to {target_player_name}."
    events_generated.append(Event(
        message=event_message,
        event_type="item_transfer",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["player", "room_players"]
    ))
    
    return events_generated, feedback_messages


def handle_throw_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles the throw action - removes object from inventory and places it in adjacent room."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    # Check for throw parsing errors first
    if '_throw_parse_error' in params:
        feedback_messages.append(params['_throw_parse_error'])
        feedback_messages.append("Correct format: throw \"object_name\" \"exit\"")
        events_generated.append(Event(
            message=f"Player {player_char.name} used invalid throw format.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages
    
    object_name = params.get("object_name", "").strip()
    exit_direction = params.get("exit", "").strip()
    
    # Validate parameters
    if not object_name:
        feedback_messages.append("You must specify an object to throw.")
        return events_generated, feedback_messages
    
    if not exit_direction:
        feedback_messages.append("You must specify an exit direction.")
        return events_generated, feedback_messages
    
    # Get current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append(f"Error: Character is in an unknown room: {player_char.current_room_id}.")
        return events_generated, feedback_messages
    
    # Check if player has the object in inventory
    target_object = player_char.get_item_in_inventory(object_name)
    if not target_object:
        feedback_messages.append(f"You don't have a {object_name} in your inventory.")
        return events_generated, feedback_messages
    
    # Check if exit exists
    if exit_direction not in current_room.exits:
        feedback_messages.append(f"There is no exit '{exit_direction}' from this room.")
        return events_generated, feedback_messages
    
    # Get target room
    exit_info = current_room.exits[exit_direction]
    target_room_id = exit_info.get("room_id")
    if not target_room_id:
        feedback_messages.append(f"Exit '{exit_direction}' has no target room.")
        return events_generated, feedback_messages
    
    target_room = game_master.rooms.get(target_room_id)
    if not target_room:
        feedback_messages.append(f"Target room '{target_room_id}' not found.")
        return events_generated, feedback_messages
    
    # Try to remove object from inventory
    removed_object = player_char.remove_item_from_inventory(object_name)
    if not removed_object:
        feedback_messages.append(f"Failed to remove {object_name} from your inventory.")
        return events_generated, feedback_messages
    
    # Place object in target room
    target_room.add_object(removed_object)
    
    # Success! Generate feedback and events
    feedback_messages.append(f"You throw the {object_name} {exit_direction}.")
    
    # Generate event for current room observers
    current_room_event = Event(
        message=f"{player_char.name} throws a {object_name} {exit_direction}.",
        event_type="item_transfer",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["player", "room_players"]
    )
    events_generated.append(current_room_event)
    
    # Generate event for target room observers
    target_room_event = Event(
        message=f"A {object_name} is thrown into the {target_room.name} from the {current_room.name}.",
        event_type="item_transfer",
        source_room_id=target_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_players"]
    )
    events_generated.append(target_room_event)
    
    # Special hoarding tracking for Bella "Whisper" Nightshade when throwing to Thieves' Den
    if player_char.name == "Bella \"Whisper\" Nightshade" and target_room_id == "thieves_den":
        # Count objects in Thieves' Den
        thieves_den = game_master.rooms.get("thieves_den")
        if thieves_den:
            object_count = len(thieves_den.objects)
            
            # Add hoarding tag if collection is complete (20+ objects)
            if object_count >= 20 and not player_char.has_tag("collection_complete"):
                player_char.add_tag("collection_complete")
                hoarding_event = Event(
                    message=f"Your secret stash in the Thieves' Den has grown to an impressive {object_count} objects! Your hoarding compulsion is satisfied.",
                    event_type="motive_progress",
                    source_room_id=target_room_id,
                    timestamp=datetime.now().isoformat(),
                    related_player_id=player_char.id,
                    observers=["player"]
                )
                events_generated.append(hoarding_event)
                feedback_messages.append(f"Your collection now contains {object_count} objects! Your hoarding compulsion grows stronger.")
            elif object_count >= 15:
                feedback_messages.append(f"Your collection grows to {object_count} objects. You're getting close to satisfying your hoarding compulsion.")
            elif object_count >= 10:
                feedback_messages.append(f"Your stash now contains {object_count} objects. The collection is taking shape.")
    
    return events_generated, feedback_messages

