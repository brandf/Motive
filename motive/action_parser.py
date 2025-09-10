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
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(action_cfg, 'name'):
            action_name = action_cfg.name
        else:
            action_name = action_cfg.get('name', act_name_key)
        # Use action_cfg.name for matching against the player input                                                                   
        normalized_act_name = action_name.lower().strip()
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
    # Handle both Pydantic objects and dictionaries from merged config
    if hasattr(action_config, 'name'):
        action_name = action_config.name
    else:
        action_name = action_config.get('name', found_action_name)
    # Use action_config.name for slicing, as it's the actual string that matched within the input                                     
    param_string = action_line[len(action_name):].strip()
    
    # Special handling for 'look at' syntax
    if action_name.lower() == "look" and param_string.lower().startswith("at "):
        param_string = param_string[len("at "):].strip()

    params: Dict[str, Any] = {}
    # Handle both Pydantic objects and dictionaries from merged config
    if hasattr(action_config, 'parameters'):
        parameters = action_config.parameters
    else:
        parameters = action_config.get('parameters', [])
    
    if parameters:
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(parameters[0], 'type'):
            param_type = parameters[0].type
            param_name = parameters[0].name
        else:
            param_type = parameters[0].get('type', 'string')
            param_name = parameters[0].get('name', 'target')
            
        if len(parameters) == 1 and param_type == "string":
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
            # Handle multiple parameters - try to parse them intelligently
            if len(parameters) == 2 and all((p.get('type') if hasattr(p, 'get') else p.type) == "string" for p in parameters):
                # Special case for two string parameters (like whisper: player + phrase)
                # Look for quoted phrase at the end
                import re
                # Pattern to match: word(s) followed by quoted string
                match = re.match(r'^(\S+)\s+(.+)$', param_string)
                if match:
                    first_param = match.group(1)
                    rest = match.group(2).strip()
                    
                    # Check if rest is a quoted string
                    if ((rest.startswith('\'') and rest.endswith('\'')) or 
                        (rest.startswith('"') and rest.endswith('"'))):
                        quoted_content = rest[1:-1]
                        # Assign to parameters in order
                        params[parameters[0].get('name', 'param1') if hasattr(parameters[0], 'get') else parameters[0].name] = first_param
                        params[parameters[1].get('name', 'param2') if hasattr(parameters[1], 'get') else parameters[1].name] = quoted_content
                    else:
                        # Fallback: assign first word to first param, rest to second
                        params[parameters[0].get('name', 'param1') if hasattr(parameters[0], 'get') else parameters[0].name] = first_param
                        params[parameters[1].get('name', 'param2') if hasattr(parameters[1], 'get') else parameters[1].name] = rest
                else:
                    # Fallback: assign raw string to first parameter
                    params[parameters[0].get('name', 'param1') if hasattr(parameters[0], 'get') else parameters[0].name] = param_string
            elif "target" in [(p.get('name', '') if hasattr(p, 'get') else p.name) for p in parameters]:
                params["target"] = param_string
            elif parameters:
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
    available_names = []
    for action_cfg in available_actions.values():
        if hasattr(action_cfg, 'name'):
            available_names.append(action_cfg.name)
        else:
            available_names.append(action_cfg.get('name', 'unknown'))
    
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
