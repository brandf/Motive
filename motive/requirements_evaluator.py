from typing import Any, Dict, Optional, Tuple


def _resolve_target_instance(player_char, game_master, req) -> Optional[Any]:
    """Resolve target instance (player/room/object) based on requirement fields.

    Supports fields: target_type, target_id, target_id_param.
    """
    target_id_param = getattr(req, 'target_id_param', None) if hasattr(req, 'target_id_param') else req.get('target_id_param', None)
    target_id = getattr(req, 'target_id', None) if hasattr(req, 'target_id') else req.get('target_id', None)
    target_type = getattr(req, 'target_type', None) if hasattr(req, 'target_type') else req.get('target_type', 'player')

    # Allow params dict later if this is used from action path; for motives we pass empty
    # NOTE: We intentionally don't take params here; callers can pre-resolve and set on req if needed
    if target_type == "player":
        return player_char
    if target_type == "room":
        if target_id:
            return game_master.rooms.get(target_id)
        if player_char.current_room_id:
            return game_master.rooms.get(player_char.current_room_id)
        return None
    if target_type == "object":
        if target_id:
            inst = player_char.get_item_in_inventory(target_id)
            if inst:
                return inst
            current_room = game_master.rooms.get(player_char.current_room_id)
            if current_room:
                return current_room.get_object(target_id)
        return None
    return None


def evaluate_requirement(player_char, game_master, req: Any, params: Dict[str, Any]) -> Tuple[bool, bool, Optional[str]]:
    """Evaluate a single requirement.

    Returns (handled, passed, error_message). If handled is False, caller should fall back to legacy checks.

    Supported types:
    - entity_has_property: { target_type: player|room|object, target_id?: str, property: str, value: Any }
    - get_entity_attribute: { target_type, target_id?, attribute: str, value: Any }
    - character_has_property (alias of entity_has_property with target_type=player)
    - object_in_room
    - object_in_inventory
    - exit_exists
    """
    # Access type and dict-like view
    req_type = getattr(req, 'type', None) if hasattr(req, 'type') else req.get('type', '')

    # entity_has_property
    if req_type == "entity_has_property":
        target = _resolve_target_instance(player_char, game_master, req)
        property_name = getattr(req, 'property', None) if hasattr(req, 'property') else req.get('property', '')
        expected_value = getattr(req, 'value', None) if hasattr(req, 'value') else req.get('value', True)
        operator = getattr(req, 'operator', None) if hasattr(req, 'operator') else req.get('operator', '==')
        if not target or not property_name:
            return True, False, f"Missing target or property for entity_has_property."
        actual_value = target.get_property(property_name, None)
        
        # Handle different operators for numeric comparisons
        if operator == '>=' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value >= expected_value
            error_msg = None if passed else f"Property '{property_name}' is {actual_value}, expected >= {expected_value}."
        elif operator == '<=' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value <= expected_value
            error_msg = None if passed else f"Property '{property_name}' is {actual_value}, expected <= {expected_value}."
        elif operator == '>' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value > expected_value
            error_msg = None if passed else f"Property '{property_name}' is {actual_value}, expected > {expected_value}."
        elif operator == '<' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value < expected_value
            error_msg = None if passed else f"Property '{property_name}' is {actual_value}, expected < {expected_value}."
        else:
            # Default to equality comparison
            passed = actual_value == expected_value
            error_msg = None if passed else f"Property '{property_name}' is {actual_value}, expected {expected_value}."
        
        return True, passed, error_msg

    # get_entity_attribute (read-only attributes like name, description)
    if req_type == "get_entity_attribute":
        target = _resolve_target_instance(player_char, game_master, req)
        attribute = getattr(req, 'attribute', None) if hasattr(req, 'attribute') else req.get('attribute', '')
        expected_value = getattr(req, 'value', None) if hasattr(req, 'value') else req.get('value', None)
        if not target or not attribute:
            return True, False, f"Missing target or attribute for get_entity_attribute."
        actual_value = getattr(target, attribute, None)
        return True, (actual_value == expected_value), (None if actual_value == expected_value else f"Attribute '{attribute}' is {actual_value}, expected {expected_value}.")

    # character_has_property - alias through entity_has_property for player
    if req_type == "character_has_property":
        # Synthesize an entity_has_property check
        property_name = getattr(req, 'property', None) if hasattr(req, 'property') else req.get('property', '')
        expected_value = getattr(req, 'value', None) if hasattr(req, 'value') else req.get('value', True)
        operator = getattr(req, 'operator', None) if hasattr(req, 'operator') else req.get('operator', '==')
        actual_value = player_char.get_property(property_name, None)
        
        # Handle different operators for numeric comparisons
        if operator == '>=' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value >= expected_value
            error_msg = None if passed else f"Character property '{property_name}' is {actual_value}, expected >= {expected_value}."
        elif operator == '<=' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value <= expected_value
            error_msg = None if passed else f"Character property '{property_name}' is {actual_value}, expected <= {expected_value}."
        elif operator == '>' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value > expected_value
            error_msg = None if passed else f"Character property '{property_name}' is {actual_value}, expected > {expected_value}."
        elif operator == '<' and isinstance(actual_value, (int, float)) and isinstance(expected_value, (int, float)):
            passed = actual_value < expected_value
            error_msg = None if passed else f"Character property '{property_name}' is {actual_value}, expected < {expected_value}."
        else:
            # Default to equality comparison
            passed = actual_value == expected_value
            error_msg = None if passed else f"Character property '{property_name}' is {actual_value}, expected {expected_value}."
        
        return True, passed, error_msg

    # object_in_room by name parameter
    if req_type == "object_in_room":
        object_name_param = getattr(req, 'object_name_param', None) if hasattr(req, 'object_name_param') else req.get('object_name_param', 'object_name')
        object_name = params.get(object_name_param)
        if not object_name:
            return True, False, f"Missing parameter '{object_name_param}' for object_in_room requirement."
        current_room = game_master.rooms.get(player_char.current_room_id)
        found = False
        if current_room:
            for obj in current_room.objects.values():
                if obj.name.lower() == str(object_name).lower():
                    found = True
                    break
        return True, found, (None if found else f"Object '{object_name}' not in room.")

    # object_in_inventory by name parameter
    if req_type == "object_in_inventory":
        object_name_param = getattr(req, 'object_name_param', None) if hasattr(req, 'object_name_param') else req.get('object_name_param', 'object_name')
        object_name = params.get(object_name_param)
        if not object_name:
            return True, False, f"Missing parameter '{object_name_param}' for object_in_inventory requirement."
        in_inv = any(item.name.lower() == str(object_name).lower() for item in player_char.inventory.values())
        return True, in_inv, (None if in_inv else f"Object '{object_name}' not in inventory.")

    # exit_exists by direction in current room
    if req_type == "exit_exists":
        direction_param = getattr(req, 'direction_param', None) if hasattr(req, 'direction_param') else req.get('direction_param', 'direction')
        direction = params.get(direction_param)
        if not direction:
            return True, False, f"Missing parameter '{direction_param}' for exit_exists requirement."
        current_room = game_master.rooms.get(player_char.current_room_id)
        if not current_room or not current_room.exits:
            return True, False, f"No exits available."
        # check name or aliases
        for _, exit_info in current_room.exits.items():
            if exit_info.get('is_hidden', False):
                continue
            if exit_info.get('name', '').lower() == str(direction).lower():
                return True, True, None
            aliases = exit_info.get('aliases', [])
            if any(a.lower() == str(direction).lower() for a in aliases):
                return True, True, None
        return True, False, f"No exit found for direction '{direction}'."

    return False, False, None


