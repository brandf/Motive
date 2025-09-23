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
        observers=["room_characters"]
    ))

    return events_generated, feedback_messages

def look_at_target(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Provides a detailed description of the current room or a specified object/character."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    target_name = params.get("target")
    event_message = ""

    if not target_name:
        # No target specified, describe the current room, but gate on visibility
        current_room = game_master.rooms.get(player_char.current_room_id)
        if current_room:
            # Visibility gating: if room is dark and no lit light sources in room inventories, it's too dark
            is_dark = bool(getattr(current_room, 'properties', {}) and current_room.properties.get('dark', False))
            has_light = False
            if is_dark:
                for p in game_master.players:
                    pc = getattr(p, 'character', None)
                    if not pc or pc.current_room_id != current_room.id:
                        continue
                    for obj in pc.inventory.values():
                        try:
                            if obj.get_property('is_lit', False):
                                has_light = True
                                break
                        except Exception:
                            continue
                    if has_light:
                        break
            if is_dark and not has_light:
                # Too dark to see objects, but show exits for navigation
                feedback_messages.append("It's too dark to see anything here.")
                
                # Still show exits so players can navigate out, but only to lit rooms
                if current_room.exits:
                    visible_exits = []
                    for exit_id, exit_data in current_room.exits.items():
                        if exit_data.get('is_hidden', False):
                            continue
                        
                        # Check if destination room is lit
                        dest_room_id = exit_data.get('destination_room_id')
                        if dest_room_id:
                            dest_room = game_master.rooms.get(dest_room_id)
                            if dest_room:
                                dest_is_dark = bool(getattr(dest_room, 'properties', {}) and dest_room.properties.get('dark', False))
                                if not dest_is_dark:
                                    # Destination is lit, so we can see this exit
                                    visible_exits.append(exit_data['name'])
                    
                    if visible_exits:
                        feedback_messages.append(f"\n\n**🚪 Exits:**")
                        for exit_name in visible_exits:
                            feedback_messages.append(f"\n  • {exit_name}")
                
                events_generated.append(Event(
                    message=f"{player_char.name} struggles to see in the darkness.",
                    event_type="player_action_failed",
                    source_room_id=player_char.current_room_id,
                    timestamp=datetime.now().isoformat(),
                    related_player_id=player_char.id,
                    observers=["room_characters"]
                ))
                return events_generated, feedback_messages
            # Visible: show formatted description with proper exit visibility
            room_description_parts = [current_room.description]
            
            if current_room.objects:
                object_names = [obj.name for obj in current_room.objects.values()]
                room_description_parts.append(f"\n\n**📦 Objects in the room:**")
                for obj_name in object_names:
                    room_description_parts.append(f"\n  • {obj_name}")
            
            if current_room.exits:
                # Show exits based on lighting: from lit rooms, show all exits
                # From dark rooms, only show exits to lit rooms (handled above)
                exit_names = [exit_data['name'] for exit_data in current_room.exits.values() if not exit_data.get('is_hidden', False)]
                if exit_names:
                    room_description_parts.append(f"\n\n**🚪 Exits:**")
                    for exit_name in exit_names:
                        room_description_parts.append(f"\n  • {exit_name}")
            
            feedback_messages.append("".join(room_description_parts))
            event_message = f"{player_char.name} looks around the room."
            events_generated.append(Event(
                message=event_message,
                event_type="player_action",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                observers=["room_characters"]
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
                # Debug logging
                print(f"DEBUG: Looking for '{target_name}' in room '{player_char.current_room_id}'")
                print(f"DEBUG: Found target_object: {target_object}")
                if target_object:
                    print(f"DEBUG: Target object interactions: {getattr(target_object, 'interactions', 'NO INTERACTIONS')}")
        
        if target_object:
            obj_description = f"You look at the {target_object.name}. {target_object.description}"
            feedback_messages.append(obj_description)
            event_message = f"{player_char.get_display_name()} looked at {target_object.name}."
            
            # Check for interactions on the target object
            if hasattr(target_object, 'interactions') and target_object.interactions:
                look_interaction = target_object.interactions.get('look')
                if look_interaction and 'effects' in look_interaction:
                        # Process the interaction effects
                        for effect in look_interaction['effects']:
                            if effect.get('type') == 'increment_property':
                                property_name = effect.get('property')
                                increment_value = effect.get('increment_value', 1)
                                if property_name:
                                    current_value = player_char.get_property(property_name, 0)
                                    new_value = current_value + increment_value
                                    player_char.set_property(property_name, new_value)
                                    feedback_messages.append(f"You found important information! {property_name.replace('_', ' ').title()}: {new_value}")
                            elif effect.get('type') == 'set_property':
                                property_name = effect.get('property')
                                property_value = effect.get('value')
                                if property_name:
                                    player_char.set_property(property_name, property_value)
                                    feedback_messages.append(f"You discovered crucial information! {property_name.replace('_', ' ').title()}: {property_value}")
                            elif effect.get('type') == 'generate_event':
                                message_template = effect.get('message', '')
                                if message_template:
                                    # Replace template variables
                                    message = message_template.replace('{{player_name}}', player_char.get_display_name())
                                    # Replace player property templates
                                    import re
                                    property_pattern = r'\{\{player_property:(\w+)\}\}'
                                    def replace_property(match):
                                        prop_name = match.group(1)
                                        # Get the updated value after increment
                                        return str(player_char.get_property(prop_name, 0))
                                    message = re.sub(property_pattern, replace_property, message)
                                    observers = effect.get('observers', ['room_characters'])
                                    events_generated.append(Event(
                                        message=message,
                                        event_type="action_event",
                                        source_room_id=player_char.current_room_id,
                                        timestamp=datetime.now().isoformat(),
                                        related_player_id=player_char.id,
                                        related_object_id=str(getattr(target_object, 'id', 'unknown')),
                                        observers=observers
                                    ))
            
            events_generated.append(Event(
                message=event_message,
                event_type="player_action",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                related_object_id=str(getattr(target_object, 'id', 'unknown')),
                observers=["player", "room_characters", "game_master"]
            ))
        else:
            feedback_messages.append(f"You don't see any '{target_name}' here or in your inventory.")
            event_message = f"{player_char.get_display_name()} tried to look at non-existent object '{target_name}'."
            events_generated.append(Event(
                message=event_message,
                event_type="player_action_failed",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                observers=["player", "game_master"]
            ))
    
    return events_generated, feedback_messages

def handle_talk_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles talking to NPCs or characters."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    target_name = params.get("target")
    
    if not target_name:
        feedback_messages.append("Talk action requires a target.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to talk without specifying a target.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages
    
    # Find the target character in the current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    target_character = None
    
    if current_room:
        # Check if the room has characters
        if hasattr(current_room, 'characters') and current_room.characters:
            for char_id, char_data in current_room.characters.items():
                if char_data.get('name', '').lower() == target_name.lower():
                    target_character = char_data
                    break
    
    if target_character:
        # Check for talk interactions on the target character
        if 'interactions' in target_character:
            talk_interaction = target_character['interactions'].get('talk')
            if talk_interaction and 'effects' in talk_interaction:
                # Process the interaction effects
                for effect in talk_interaction['effects']:
                    if effect.get('type') == 'increment_property':
                        property_name = effect.get('property')
                        increment_value = effect.get('increment_value', 1)
                        if property_name:
                            current_value = player_char.get_property(property_name, 0)
                            new_value = current_value + increment_value
                            player_char.set_property(property_name, new_value)
                            feedback_messages.append(f"You learned valuable information! {property_name.replace('_', ' ').title()}: {new_value}")
                    elif effect.get('type') == 'generate_event':
                        message_template = effect.get('message', '')
                        if message_template:
                            # Replace template variables
                            message = message_template.replace('{{player_name}}', player_char.get_display_name())
                            message = message.replace('{{target}}', target_character.get('name', target_name))
                            # Replace player property templates
                            import re
                            property_pattern = r'\{\{player_property:(\w+)\}\}'
                            def replace_property(match):
                                prop_name = match.group(1)
                                # Get the updated value after increment
                                return str(player_char.get_property(prop_name, 0))
                            message = re.sub(property_pattern, replace_property, message)
                            observers = effect.get('observers', ['room_characters'])
                            events_generated.append(Event(
                                message=message,
                                event_type="action_event",
                                source_room_id=player_char.current_room_id,
                                timestamp=datetime.now().isoformat(),
                                related_player_id=player_char.id,
                                observers=observers
                            ))
        
        # Generate the basic talk event
        event_message = f"{player_char.get_display_name()} talks to {target_character.get('name', target_name)}."
        events_generated.append(Event(
            message=event_message,
            event_type="action_event",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["room_characters"]
        ))
    else:
        feedback_messages.append(f"You don't see '{target_name}' here to talk to.")
        events_generated.append(Event(
            message=f"{player_char.get_display_name()} tried to talk to non-existent character '{target_name}'.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
    
    return events_generated, feedback_messages

def handle_expose_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles exposing cult members or other targets."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    target_name = params.get("target")
    
    if not target_name:
        feedback_messages.append("Expose action requires a target.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to expose without specifying a target.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages
    
    # Find the target character in the current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    target_character = None
    
    if current_room:
        # Check if the room has characters
        if hasattr(current_room, 'characters') and current_room.characters:
            for char_id, char_data in current_room.characters.items():
                if char_data.get('name', '').lower() == target_name.lower():
                    target_character = char_data
                    break
    
    if target_character:
        # Check for expose interactions on the target character
        if 'interactions' in target_character:
            expose_interaction = target_character['interactions'].get('expose')
            if expose_interaction and 'effects' in expose_interaction:
                # Process the interaction effects
                for effect in expose_interaction['effects']:
                    if effect.get('type') == 'set_property':
                        property_name = effect.get('property')
                        property_value = effect.get('value')
                        if property_name:
                            player_char.set_property(property_name, property_value)
                            feedback_messages.append(f"You expose {target_character.get('name', target_name)}! {property_name.replace('_', ' ').title()}: {property_value}")
                    elif effect.get('type') == 'generate_event':
                        message_template = effect.get('message', '')
                        if message_template:
                            # Replace template variables
                            message = message_template.replace('{{player_name}}', player_char.get_display_name())
                            message = message.replace('{{target}}', target_character.get('name', target_name))
                            # Replace player property templates
                            import re
                            property_pattern = r'\{\{player_property:(\w+)\}\}'
                            def replace_property(match):
                                prop_name = match.group(1)
                                return str(player_char.get_property(prop_name, 0))
                            message = re.sub(property_pattern, replace_property, message)
                            observers = effect.get('observers', ['room_characters'])
                            events_generated.append(Event(
                                message=message,
                                event_type="action_event",
                                source_room_id=player_char.current_room_id,
                                timestamp=datetime.now().isoformat(),
                                related_player_id=player_char.id,
                                observers=observers
                            ))
        
        # Generate the basic expose event
        event_message = f"{player_char.get_display_name()} exposes {target_character.get('name', target_name)}."
        events_generated.append(Event(
            message=event_message,
            event_type="action_event",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["room_characters"]
        ))
    else:
        feedback_messages.append(f"You don't see '{target_name}' here to expose.")
        events_generated.append(Event(
            message=f"{player_char.get_display_name()} tried to expose non-existent character '{target_name}'.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
    
    return events_generated, feedback_messages

def handle_arrest_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handles arresting cult members or other targets."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    target_name = params.get("target")
    
    if not target_name:
        feedback_messages.append("Arrest action requires a target.")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to arrest without specifying a target.",
            event_type="player_action_failed",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "game_master"]
        ))
        return events_generated, feedback_messages
    
    # Find the target character in the current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    target_character = None
    
    if current_room:
        # Check if the room has characters
        if hasattr(current_room, 'characters') and current_room.characters:
            for char_id, char_data in current_room.characters.items():
                if char_data.get('name', '').lower() == target_name.lower():
                    target_character = char_data
                    break
    
    if target_character:
        # Check for arrest interactions on the target character
        if 'interactions' in target_character:
            arrest_interaction = target_character['interactions'].get('arrest')
            if arrest_interaction and 'effects' in arrest_interaction:
                # Process the interaction effects
                for effect in arrest_interaction['effects']:
                    if effect.get('type') == 'set_property':
                        property_name = effect.get('property')
                        property_value = effect.get('value')
                        if property_name:
                            player_char.set_property(property_name, property_value)
                            feedback_messages.append(f"You arrest {target_character.get('name', target_name)}! {property_name.replace('_', ' ').title()}: {property_value}")
                    elif effect.get('type') == 'generate_event':
                        message_template = effect.get('message', '')
                        if message_template:
                            # Replace template variables
                            message = message_template.replace('{{player_name}}', player_char.get_display_name())
                            message = message.replace('{{target}}', target_character.get('name', target_name))
                            # Replace player property templates
                            import re
                            property_pattern = r'\{\{player_property:(\w+)\}\}'
                            def replace_property(match):
                                prop_name = match.group(1)
                                return str(player_char.get_property(prop_name, 0))
                            message = re.sub(property_pattern, replace_property, message)
                            observers = effect.get('observers', ['room_characters'])
                            events_generated.append(Event(
                                message=message,
                                event_type="action_event",
                                source_room_id=player_char.current_room_id,
                                timestamp=datetime.now().isoformat(),
                                related_player_id=player_char.id,
                                observers=observers
                            ))
        
        # Generate the basic arrest event
        event_message = f"{player_char.get_display_name()} arrests {target_character.get('name', target_name)}."
        events_generated.append(Event(
            message=event_message,
            event_type="action_event",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["room_characters"]
        ))
    else:
        feedback_messages.append(f"You don't see '{target_name}' here to arrest.")
        events_generated.append(Event(
            message=f"{player_char.get_display_name()} tried to arrest non-existent character '{target_name}'.",
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

    # Evaluate visibility and travel requirements on the exit, if present
    def _eval_reqs(reqs: Any) -> Tuple[bool, str]:
        if not reqs:
            return True, ""
        from motive.requirements_evaluator import evaluate_requirement
        # Normalize to list
        checks = reqs if isinstance(reqs, list) else [reqs]
        for req in checks:
            handled, passed, err = evaluate_requirement(player_char, game_master, req, params)
            # If requirement type is unknown (handled=False), treat as failure to be conservative
            if not handled or not passed:
                return False, (err or "Requirement not met.")
        return True, ""

    # Do not block movement based on visibility requirements; those affect discovery/description.
    # Movement is gated by travel_requirements only.

    travel_ok, trav_err = _eval_reqs(exit_data.get('travel_requirements'))
    if not travel_ok:
        feedback_messages.append(f"You cannot travel {direction}: {trav_err or 'travel requirements not met.'}")
        events_generated.append(Event(
            message=f"Player {player_char.name} attempted to move '{direction}' but travel requirements failed. {trav_err}",
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
        observers=["room_characters"]  # Only characters in the source room see the exit
    ))
    
    # Generate enter event for players in the destination room
    events_generated.append(Event(
        message=f"{player_char.name} entered the room from {direction}.",
        event_type="player_enter",
        source_room_id=destination_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_characters"]  # Only characters in the destination room see the enter
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
        message=f"{player_char.get_display_name()} says: \"{phrase}\".",
        event_type="player_communication",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_characters"]  # Characters in the room hear the speech
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
    object_name = params.get("object")  # Changed from "object_name" to "object" to match H&S config

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

    # DEBUG: Log read action attempt
    room_name = current_room.name if current_room else "UNKNOWN_ROOM"
    game_master.game_logger.debug(f"🔍 READ ACTION DEBUG: {player_char.name} in {room_name} (ID: {player_char.current_room_id}) attempting to read '{object_name}'")

    # First check player's inventory for the object
    obj_to_read = None
    if hasattr(player_char, 'inventory') and player_char.inventory:
        inventory_objects = list(player_char.inventory.keys())
        game_master.game_logger.debug(f"🔍 READ ACTION DEBUG: {player_char.name} inventory contains: {inventory_objects}")
        
        # Look for object in inventory by name (case-insensitive)
        for obj_id, obj in player_char.inventory.items():
            if obj.name.lower() == object_name.lower():
                obj_to_read = obj
                game_master.game_logger.debug(f"🔍 READ ACTION DEBUG: Found '{object_name}' in {player_char.name}'s inventory")
                break
    
    # If not found in inventory, check the current room
    if not obj_to_read:
        room_objects = list(current_room.objects.keys()) if hasattr(current_room, 'objects') else []
        game_master.game_logger.debug(f"🔍 READ ACTION DEBUG: Room '{room_name}' contains objects: {room_objects}")
        
        obj_to_read = current_room.get_object(object_name)
        if obj_to_read:
            game_master.game_logger.debug(f"🔍 READ ACTION DEBUG: Found '{object_name}' in room '{room_name}'")
    
    if not obj_to_read:
        game_master.game_logger.debug(f"🔍 READ ACTION DEBUG: '{object_name}' not found in inventory or room '{room_name}'")
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

    # Check if the object has a read action alias that redirects to look
    if hasattr(obj_to_read, 'action_aliases') and obj_to_read.action_aliases and 'read' in obj_to_read.action_aliases:
        read_alias = obj_to_read.action_aliases['read']
        if read_alias == 'look':
            # Redirect to look action
            return look_at_target(game_master, player_char, action_config, {"target": object_name})
    
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
        observers=["room_characters"]
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

    # Find the target player in the current room by player display name, character name, or character aliases
    target_player = None
    for candidate in game_master.players:
        candidate_char = getattr(candidate, 'character', None)
        if not candidate_char:
            continue
        if candidate_char.current_room_id != current_room.id:
            continue
        # Match by player display name
        if candidate.name.lower() == target_player_name.lower():
            target_player = candidate
            break
        # Match by character name
        if getattr(candidate_char, 'name', '').lower() == target_player_name.lower():
            target_player = candidate
            break
        # Match by character aliases (if any)
        character_aliases = getattr(candidate_char, 'aliases', [])
        if any(alias.lower() == target_player_name.lower() for alias in character_aliases):
            target_player = candidate
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

    # Don't whisper to yourself (compare character ids)
    if getattr(target_player, 'character', None) and target_player.character.id == player_char.id:
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
    
    # Event for the target player (as observation, not direct feedback)
    events_generated.append(Event(
        message=f"{player_char.get_display_name()} whispers to you: \"{phrase}\"",
        event_type="player_communication",
        source_room_id=current_room.id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,  # The speaker is the related player
        observers=["room_characters"]  # Target sees this as an observation
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
        observers=["player", "room_characters", "adjacent_rooms_characters"]  # Heard in current and adjacent rooms
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
    
    # DEBUG: Log pickup action attempt
    room_name = current_room.name if current_room else "UNKNOWN_ROOM"
    game_master.game_logger.debug(f"🔍 PICKUP ACTION DEBUG: {player_char.name} in {room_name} (ID: {player_char.current_room_id}) attempting to pickup '{object_name}'")
    
    # Find the object in the room
    # Strip quotes from object_name for comparison
    clean_object_name = object_name.strip('"\'')
    
    room_objects = list(current_room.objects.keys()) if hasattr(current_room, 'objects') else []
    game_master.game_logger.debug(f"🔍 PICKUP ACTION DEBUG: Room '{room_name}' contains objects: {room_objects}")
    
    target_object = None
    for obj_id, obj in current_room.objects.items():
        if obj.name.lower() == clean_object_name.lower():
            target_object = obj
            game_master.game_logger.debug(f"🔍 PICKUP ACTION DEBUG: Found '{object_name}' in room '{room_name}'")
            break
    
    if not target_object:
        game_master.game_logger.debug(f"🔍 PICKUP ACTION DEBUG: '{object_name}' not found in room '{room_name}'")
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
    
    # DEBUG: Log successful pickup
    game_master.game_logger.debug(f"🔍 PICKUP ACTION DEBUG: Successfully moved '{target_object.name}' from room '{room_name}' to {player_char.name}'s inventory")
    
    # Generate timestamp
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    
    # Generate events
    events = []
    feedback_messages = []
    
    # Process object pickup interaction if it exists
    if hasattr(target_object, 'interactions') and target_object.interactions and 'pickup' in target_object.interactions:
        pickup_interaction = target_object.interactions['pickup']
        if 'effects' in pickup_interaction:
            for effect in pickup_interaction['effects']:
                if effect.get('type') == 'increment_property':
                    property_name = effect.get('property')
                    increment_value = effect.get('increment_value', 1)
                    if property_name:
                        current_value = player_char.properties.get(property_name, 0)
                        player_char.set_property(property_name, current_value + increment_value)
                        feedback_messages.append(f"You discovered crucial information! {property_name.replace('_', ' ').title()}: {current_value + increment_value}")
                elif effect.get('type') == 'set_property':
                    property_name = effect.get('property')
                    property_value = effect.get('value')
                    if property_name:
                        player_char.set_property(property_name, property_value)
                        feedback_messages.append(f"You discovered crucial information! {property_name.replace('_', ' ').title()}: {property_value}")
    
    # Automatically trigger pickup_action interaction when picking up an object
    # Default to 'look' if no pickup_action is specified
    pickup_action = 'look'  # Default behavior
    if hasattr(target_object, 'properties') and target_object.properties:
        pickup_action = target_object.properties.get('pickup_action', 'look')
    
    # Process the pickup_action interaction
    if hasattr(target_object, 'interactions') and target_object.interactions and pickup_action in target_object.interactions:
        action_interaction = target_object.interactions[pickup_action]
        if 'effects' in action_interaction:
            for effect in action_interaction['effects']:
                if effect.get('type') == 'increment_property':
                    property_name = effect.get('property')
                    increment_value = effect.get('increment_value', 1)
                    if property_name:
                        current_value = player_char.properties.get(property_name, 0)
                        player_char.set_property(property_name, current_value + increment_value)
                        feedback_messages.append(f"You discovered crucial information! {property_name.replace('_', ' ').title()}: {current_value + increment_value}")
                elif effect.get('type') == 'set_property':
                    property_name = effect.get('property')
                    property_value = effect.get('value')
                    if property_name:
                        player_char.set_property(property_name, property_value)
                        feedback_messages.append(f"You discovered crucial information! {property_name.replace('_', ' ').title()}: {property_value}")
                elif effect.get('type') == 'generate_event':
                    # Generate the event from the pickup_action interaction
                    message = effect.get('message', '').replace('{{player_name}}', player_char.get_display_name())
                    # Replace player property placeholders
                    if '{{player_property:' in message:
                        import re
                        def replace_property(match):
                            prop_name = match.group(1)
                            prop_value = player_char.properties.get(prop_name, 0)
                            return str(prop_value)
                        message = re.sub(r'\{\{player_property:([^}]+)\}\}', replace_property, message)
                    
                    observers = effect.get('observers', ['room_characters'])
                    action_event = Event(
                        message=message,
                        event_type="action_event",
                        source_room_id=player_char.current_room_id,
                        timestamp=timestamp,
                        related_object_id=target_object.id,
                        related_player_id=player_char.id,
                        observers=observers
                    )
                    events.append(action_event)
    
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
        message=f"{player_char.get_display_name()} picks up the {target_object.name}.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["room_characters"]
    )
    events.append(room_pickup_event)
    
    # Event for adjacent rooms (optional - they might hear the pickup)
    adjacent_pickup_event = Event(
        message=f"{player_char.get_display_name()} picks up something.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=timestamp,
        related_object_id=target_object.id,
        related_player_id=player_char.id,
        observers=["adjacent_rooms_characters"]
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
            observers=["room_characters"]
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
            observers=["room_characters"]
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
        observers=["room_characters"]
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
        observers=["adjacent_rooms_characters"]
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
        observers=["player", "room_characters"]
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
    
    # Resolve exit by name or aliases (case-insensitive), mirroring move logic
    exit_info = None
    for _, ex in current_room.exits.items():
        if ex.get('is_hidden', False):
            continue
        if ex.get('name', '').lower() == exit_direction.lower():
            exit_info = ex
            break
        aliases = ex.get('aliases', [])
        if any(alias.lower() == exit_direction.lower() for alias in aliases):
            exit_info = ex
            break
    if not exit_info:
        feedback_messages.append(f"There is no exit '{exit_direction}' from this room.")
        return events_generated, feedback_messages

    # Get target room
    target_room_id = exit_info.get("destination_room_id")
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
        observers=["player", "room_characters"]
    )
    events_generated.append(current_room_event)
    
    # Generate event for target room observers
    target_room_event = Event(
        message=f"A {object_name} is thrown into the {target_room.name} from the {current_room.name}.",
        event_type="item_transfer",
        source_room_id=target_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_characters"]
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


def handle_investigate_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handle investigate action - thorough examination of objects."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    target = params.get("target", "").strip()
    if not target:
        feedback_messages.append("You need to specify what to investigate.")
        return events_generated, feedback_messages
    
    # Find the object in the current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append("You are not in a valid room.")
        return events_generated, feedback_messages
    
    # Look for the object in the room first
    target_object = None
    for obj_id, obj in current_room.objects.items():
        if obj.name.lower() == target.lower():
            target_object = obj
            break
    
    # If not found in room, check player's inventory
    if not target_object:
        for obj_id, obj in player_char.inventory.items():
            if obj.name.lower() == target.lower():
                target_object = obj
                break
    
    if not target_object:
        feedback_messages.append(f"You don't see '{target}' anywhere nearby.")
        return events_generated, feedback_messages

    # Check if the object has an investigate action alias that redirects to look
    if hasattr(target_object, 'action_aliases') and target_object.action_aliases and 'investigate' in target_object.action_aliases:
        investigate_alias = target_object.action_aliases['investigate']
        if investigate_alias == 'look':
            # Redirect to look action
            return look_at_target(game_master, player_char, action_config, {"target": target})

    # Generate investigation description
    investigation_desc = f"You carefully investigate the {target_object.name}."
    
    # Add object-specific investigation details if available
    if hasattr(target_object, 'investigation_description') and target_object.investigation_description:
        investigation_desc += f" {target_object.investigation_description}"
    elif hasattr(target_object, 'description') and target_object.description:
        investigation_desc += f" {target_object.description}"
    else:
        investigation_desc += " You examine it thoroughly but don't find anything unusual."
    
    feedback_messages.append(investigation_desc)
    
    # Create investigation event (v2 schema)
    events_generated.append(Event(
        message=f"{player_char.get_display_name()} investigates the {target_object.name}.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        related_object_id=target_object.id,
        observers=["room_characters"]
    ))
    
    return events_generated, feedback_messages


def handle_use_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handle use action - use an object from inventory on another object."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    object_name = params.get("object_name", "").strip()
    target = (params.get("target", "") or "").strip()

    if not object_name:
        feedback_messages.append("You need to specify an object to use.")
        return events_generated, feedback_messages

    # DEBUG: Log use action attempt
    current_room = game_master.rooms.get(player_char.current_room_id)
    room_name = current_room.name if current_room else "UNKNOWN_ROOM"
    game_master.game_logger.debug(f"🔍 USE ACTION DEBUG: {player_char.name} in {room_name} (ID: {player_char.current_room_id}) attempting to use '{object_name}' on '{target}'")

    # Check if player has the object in inventory first (prioritize inventory)
    inv_object = None
    inventory_objects = list(player_char.inventory.keys()) if hasattr(player_char, 'inventory') else []
    game_master.game_logger.debug(f"🔍 USE ACTION DEBUG: {player_char.name} inventory contains: {inventory_objects}")
    
    for obj in player_char.inventory.values():
        if obj.name.lower() == object_name.lower():
            inv_object = obj
            game_master.game_logger.debug(f"🔍 USE ACTION DEBUG: Found '{object_name}' in {player_char.name}'s inventory")
            break
    
    # If not found in inventory, check room objects
    room_object = None
    if not inv_object:
        if current_room:
            room_objects = list(current_room.objects.keys()) if hasattr(current_room, 'objects') else []
            game_master.game_logger.debug(f"🔍 USE ACTION DEBUG: Room '{room_name}' contains objects: {room_objects}")
            
            for obj in current_room.objects.values():
                if obj.name.lower() == object_name.lower():
                    room_object = obj
                    game_master.game_logger.debug(f"🔍 USE ACTION DEBUG: Found '{object_name}' in room '{room_name}'")
                    break
        else:
            game_master.game_logger.debug(f"🔍 USE ACTION DEBUG: No current room found for {player_char.name}")
    
    # If neither inventory nor room object found, return error
    if not inv_object and not room_object:
        game_master.game_logger.debug(f"🔍 USE ACTION DEBUG: '{object_name}' not found in inventory or room '{room_name}'")
        feedback_messages.append(f"You don't see '{object_name}' anywhere nearby.")
        return events_generated, feedback_messages
    
    # Use inventory object if available, otherwise use room object
    use_object = inv_object if inv_object else room_object

    # Helper: get entity interactions dict
    def _get_interactions(entity: Any) -> Dict[str, Any]:
        if entity is None:
            return {}
        try:
            ih = entity.get_property('interactions', None)  # Prefer via accessor
            if ih:
                return ih
        except Exception:
            pass
        return getattr(entity, 'properties', {}).get('interactions', {}) or {}

    # Helper: check simple when-conditions
    def _when_matches(when: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if not when:
            return True
        target_obj = context.get('target_object')
        room = context.get('room')
        # target_has_property: {property: 'is_locked', equals: True}
        thp = when.get('target_has_property')
        if thp:
            if not target_obj:
                return False
            prop = thp.get('property')
            expected = thp.get('equals', True)
            try:
                actual = target_obj.get_property(prop, None)
            except Exception:
                actual = getattr(getattr(target_obj, 'properties', {}), 'get', lambda *_: None)(prop)
            if actual != expected:
                return False
        # room_has_exit: {exit_name: 'bedroom door'} (matches name or alias)
        rhe = when.get('room_has_exit')
        if rhe:
            if not room:
                return False
            exit_name = (rhe.get('exit_name') or rhe.get('name') or '').lower()
            if not exit_name:
                return False
            found = False
            for ex in room.exits.values():
                if ex.get('name', '').lower() == exit_name:
                    found = True
                    break
                aliases = [a.lower() for a in ex.get('aliases', [])]
                if exit_name in aliases:
                    found = True
                    break
            if not found:
                return False
        return True

    # Helper: apply a single effect with a target selector
    def _apply_effect(eff: Dict[str, Any], context: Dict[str, Any]):
        nonlocal events_generated, feedback_messages
        eff_type = (eff or {}).get('type')
        if eff_type == 'set_property':
            prop = eff.get('property')
            if not prop:
                return
            target_ref = (eff.get('target') or 'self').lower()
            toggle = bool(eff.get('toggle', False))
            value = eff.get('value')
            target_entity = None
            if target_ref in ('self', 'object', 'inventory_object'):
                target_entity = context.get('inv_object') or context.get('use_object')
            elif target_ref in ('target', 'target_object'):
                target_entity = context.get('target_object')
            elif target_ref == 'room':
                target_entity = context.get('room')
            elif target_ref == 'player':
                target_entity = context.get('player_char')
            if not target_entity:
                return
            if toggle:
                try:
                    current_val = bool(target_entity.get_property(prop, False))
                except Exception:
                    current_val = bool(getattr(target_entity, 'properties', {}).get(prop, False))
                new_val = not current_val
                try:
                    target_entity.set_property(prop, new_val)
                except Exception:
                    if getattr(target_entity, 'properties', None) is None:
                        target_entity.properties = {}
                    target_entity.properties[prop] = new_val
            else:
                try:
                    target_entity.set_property(prop, value)
                except Exception:
                    if getattr(target_entity, 'properties', None) is None:
                        target_entity.properties = {}
                    target_entity.properties[prop] = value
        elif eff_type == 'add_tag':
            tag = eff.get('tag')
            if not tag:
                return
            target_ref = (eff.get('target') or 'self').lower()
            target_entity = context.get('inv_object') if target_ref in ('self','object','inventory_object') else (
                context.get('target_object') if target_ref in ('target','target_object') else (
                    context.get('room') if target_ref=='room' else context.get('player_char')
                )
            )
            if target_entity and hasattr(target_entity, 'add_tag'):
                target_entity.add_tag(tag)
        elif eff_type == 'remove_tag':
            tag = eff.get('tag')
            if not tag:
                return
            target_ref = (eff.get('target') or 'self').lower()
            target_entity = context.get('inv_object') if target_ref in ('self','object','inventory_object') else (
                context.get('target_object') if target_ref in ('target','target_object') else (
                    context.get('room') if target_ref=='room' else context.get('player_char')
                )
            )
            if target_entity and hasattr(target_entity, 'remove_tag'):
                target_entity.remove_tag(tag)
        elif eff_type == 'generate_event':
            msg_tmpl = eff.get('message', '')
            observers = eff.get('observers', [])
            inv_obj = context.get('inv_object')
            tgt = context.get('target_object')
            fmt_params = dict(params)
            fmt_params.update({
                'player_name': player_char.name,
                'object_name': inv_obj.name if inv_obj else '',
                'target_name': tgt.name if tgt else ''
            })
            try:
                msg = msg_tmpl.format(**fmt_params)
            except Exception:
                msg = msg_tmpl
            events_generated.append(Event(
                message=msg,
                event_type="player_action",
                source_room_id=player_char.current_room_id,
                timestamp=datetime.now().isoformat(),
                related_player_id=player_char.id,
                observers=observers
            ))

    # Helper: process interactions spec (list of effects or list of rules {when, effects})
    def _process_interactions(spec: Any, context: Dict[str, Any]) -> bool:
        if not spec:
            return False
        applied_any = False
        # Normalize to list
        entries = spec if isinstance(spec, list) else [spec]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            # Two shapes: direct effect (has 'type') or rule (has 'effects' and optional 'when')
            if 'type' in entry:
                _apply_effect(entry, context)
                applied_any = True
            else:
                when = entry.get('when', {})
                effects = entry.get('effects', [])
                if _when_matches(when, context):
                    for eff in effects:
                        _apply_effect(eff, context)
                    applied_any = applied_any or bool(effects)
        return applied_any

    # Resolve target object in room if provided
    current_room = game_master.rooms.get(player_char.current_room_id)
    target_object = None
    if target:
        if current_room:
            for obj in current_room.objects.values():
                if obj.name.lower() == target.lower():
                    target_object = obj
                    break

    # Compose common context for interactions
    context = {
        'player_char': player_char,
        'inv_object': inv_object,  # Keep for backward compatibility
        'use_object': use_object,  # The actual object being used
        'target_object': target_object,
        'room': current_room,
    }

    # Try interactions on use object, then target object, then room, then character (any entity can host interactions)
    applied = False
    for entity in (use_object, target_object, current_room, player_char):
        interactions = _get_interactions(entity)
        if isinstance(interactions, dict) and 'use' in interactions:
            applied = _process_interactions(interactions['use'], context) or applied

    if applied:
        # Provide generic feedback based on lit state if present (common UX)
        try:
            is_lit_val = use_object.get_property('is_lit', None)
        except Exception:
            is_lit_val = getattr(use_object, 'properties', {}).get('is_lit', None)
        if is_lit_val is True:
            feedback_messages.append(f"You light the {use_object.name}.")
        elif is_lit_val is False:
            # If explicitly false after a toggle, assume extinguished
            feedback_messages.append(f"You extinguish the {use_object.name}.")
        else:
            if target_object:
                feedback_messages.append(f"You use the {use_object.name} on the {target_object.name}.")
            else:
                feedback_messages.append(f"You use the {use_object.name}.")
        return events_generated, feedback_messages

    # If no interactions, and no explicit target provided and the item is a tool, perform default behavior
    tool_type = use_object.get_property('tool_type', None)
    if not target and tool_type == 'lighting':
        # Toggle is_lit property
        currently_lit = bool(use_object.get_property('is_lit', False))
        new_state = not currently_lit
        try:
            use_object.set_property('is_lit', new_state)
        except Exception:
            # Fallback: ensure properties dict exists
            if getattr(use_object, 'properties', None) is None:
                use_object.properties = {}
            use_object.properties['is_lit'] = new_state
        action_word = "light" if new_state else "extinguish"
        # Feedback and events
        feedback_messages.append(f"You {action_word} the {use_object.name}.")
        events_generated.append(Event(
            message=f"{player_char.name} {action_word}s the {use_object.name}.",
            event_type="player_action",
            source_room_id=player_char.current_room_id,
            timestamp=datetime.now().isoformat(),
            related_player_id=player_char.id,
            observers=["player", "room_characters"]
        ))
        return events_generated, feedback_messages

    # Generic use on target in room (legacy behavior)
    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append("You are not in a valid room.")
        return events_generated, feedback_messages

    target_object = None
    if target:
        for obj_id, obj in current_room.objects.items():
            if obj.name.lower() == target.lower():
                target_object = obj
                break

    use_desc = f"You use the {object_name}"
    if target_object:
        use_desc += f" on the {target_object.name}."
    else:
        use_desc += "."
    feedback_messages.append(use_desc)

    events_generated.append(Event(
        message=f"{player_char.get_display_name()} uses the {object_name}{' on the ' + target_object.name if target_object else ''}.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        observers=["room_characters"]
    ))
    return events_generated, feedback_messages


def handle_light_action(game_master: Any, player_char: Character, action_config: Any, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
    """Handle light action - light an object that can be lit."""
    feedback_messages: List[str] = []
    events_generated: List[Event] = []
    
    object_name = params.get("object_name", "").strip()
    if not object_name:
        feedback_messages.append("You need to specify what to light.")
        return events_generated, feedback_messages
    
    # Find the object in the current room
    current_room = game_master.rooms.get(player_char.current_room_id)
    if not current_room:
        feedback_messages.append("You are not in a valid room.")
        return events_generated, feedback_messages
    
    target_object = None
    for obj_id, obj in current_room.objects.items():
        if obj.name.lower() == object_name.lower():
            target_object = obj
            break
    
    if not target_object:
        feedback_messages.append(f"You don't see '{object_name}' in the current room.")
        return events_generated, feedback_messages
    
    # Check if object can be lit
    can_be_lit = False
    if hasattr(target_object, 'properties') and target_object.properties:
        can_be_lit = target_object.properties.get('can_be_lit', False)
    elif hasattr(target_object, 'can_be_lit'):
        can_be_lit = target_object.can_be_lit
    
    if not can_be_lit:
        feedback_messages.append(f"The {target_object.name} cannot be lit.")
        return events_generated, feedback_messages
    
    # Check if already lit
    is_lit = False
    if hasattr(target_object, 'properties') and target_object.properties:
        is_lit = target_object.properties.get('is_lit', False)
    elif hasattr(target_object, 'is_lit'):
        is_lit = target_object.is_lit
    
    if is_lit:
        feedback_messages.append(f"The {target_object.name} is already lit.")
        return events_generated, feedback_messages
    
    # Light the object
    if hasattr(target_object, 'properties'):
        if target_object.properties is None:
            target_object.properties = {}
        target_object.properties['is_lit'] = True
    else:
        target_object.is_lit = True
    
    feedback_messages.append(f"You light the {target_object.name}. It now provides warm, flickering light.")
    
    # Create light event (v2 schema)
    events_generated.append(Event(
        message=f"{player_char.name} lights the {target_object.name}.",
        event_type="player_action",
        source_room_id=player_char.current_room_id,
        timestamp=datetime.now().isoformat(),
        related_player_id=player_char.id,
        related_object_id=target_object.id,
        observers=["room_characters"]
    ))
    
    return events_generated, feedback_messages

