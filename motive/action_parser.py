from typing import List, Dict, Any, Optional, Tuple
from motive.config import ActionConfig, ParameterConfig

def _parse_single_action_line(action_line: str, available_actions: Dict[str, ActionConfig]) -> Optional[Tuple[ActionConfig, Dict[str, Any]]]:
    """Parses a single action line into an ActionConfig and its parameters."""
    # Find the longest matching action name to handle multi-word actions
    found_action_name = None
    longest_match_len = 0

    # Normalize action_line for matching by making it lowercase and stripping all whitespace
    normalized_action_line = action_line.lower().strip()

    for act_name_key, action_cfg in available_actions.items():
        # Use action_cfg.name for matching against the player input
        normalized_act_name = action_cfg.name.lower().strip()
        if normalized_action_line.startswith(normalized_act_name):
            if len(normalized_act_name) > longest_match_len:
                longest_match_len = len(normalized_act_name)
                found_action_name = act_name_key # Store the original key from available_actions
    
    if not found_action_name:
        return None

    action_config = available_actions.get(found_action_name)
    if not action_config:
        return None # Should not happen if found_action_name is from available_actions

    # Extract parameter string from the original action_line based on the length of the *matched action name*
    # Use action_config.name for slicing, as it's the actual string that matched within the input
    param_string = action_line[len(action_config.name):].strip()
    
    # Special handling for 'look at' syntax
    if action_config.name.lower() == "look" and param_string.lower().startswith("at "):
        param_string = param_string[len("at "):].strip()

    params: Dict[str, Any] = {}
    if action_config.parameters:
        if len(action_config.parameters) == 1 and action_config.parameters[0].type == "string":
            param_name = action_config.parameters[0].name
            # If param_string is empty, treat as if parameter was not provided
            if not param_string:
                params[param_name] = None
            # Handle quoted parameters for multi-word arguments
            elif (param_string.startswith('\'') and param_string.endswith('\'')) or \
               (param_string.startswith("\"") and param_string.endswith("\"")):
                params[param_name] = param_string[1:-1]
            else:
                params[param_name] = param_string
        else:
            # For more complex parameter types (e.g., multiple params, integers), this would need expansion.
            # For now, if there are multiple parameters or non-string types, just assign the raw string to a 'target' if it exists.
            if "target" in [p.name for p in action_config.parameters]:
                params["target"] = param_string
            elif action_config.parameters:
                # This case means we couldn't parse all expected parameters for a defined action.
                pass
    return action_config, params

def parse_player_response(player_response: str, available_actions: Dict[str, ActionConfig]) -> Tuple[List[Tuple[ActionConfig, Dict[str, Any]]], List[str]]:
    """Extracts and parses actions from a player's response.

    Looks for lines starting with '>' as indicators of actions.
    
    Returns:
        Tuple of (parsed_actions, invalid_actions)
    """
    parsed_actions: List[Tuple[ActionConfig, Dict[str, Any]]] = []
    invalid_actions: List[str] = []
    lines = player_response.strip().splitlines()

    for line in lines:
        trimmed_line = line.strip()
        if trimmed_line.startswith(">"):
            action_line = trimmed_line[1:].strip()
            if action_line:
                parsed_action = _parse_single_action_line(action_line, available_actions)
                if parsed_action:
                    parsed_actions.append(parsed_action)
                else:
                    # Add suggestion for similar actions
                    suggestion = _suggest_similar_action(action_line, available_actions)
                    if suggestion:
                        invalid_actions.append(f"{action_line} (did you mean '{suggestion}'?)")
                    else:
                        invalid_actions.append(action_line)

    return parsed_actions, invalid_actions

def _suggest_similar_action(action_line: str, available_actions: Dict[str, ActionConfig]) -> Optional[str]:
    """Suggests a similar action if the input doesn't match any known actions."""
    action_line_lower = action_line.lower().strip()
    
    # Get all available action names
    available_names = [action_cfg.name for action_cfg in available_actions.values()]
    
    # Check for common typos or partial matches
    for name in available_names:
        name_lower = name.lower()
        
        # Check if the action line is a prefix of a known action
        if name_lower.startswith(action_line_lower) and len(action_line_lower) >= 2:
            return name
            
        # Check if a known action is a prefix of the action line
        if action_line_lower.startswith(name_lower) and len(name_lower) >= 2:
            return name
            
        # Check for simple character differences (typos)
        if len(action_line_lower) == len(name_lower):
            differences = sum(1 for a, b in zip(action_line_lower, name_lower) if a != b)
            if differences <= 1:  # Allow 1 character difference
                return name
    
    return None
