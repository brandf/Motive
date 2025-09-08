from typing import List, Dict, Any, Optional, Tuple
from motive.config import ActionConfig, ParameterConfig

def _parse_single_action_line(action_line: str, available_actions: Dict[str, ActionConfig]) -> Optional[Tuple[ActionConfig, Dict[str, Any]]]:
    """Parses a single action line into an ActionConfig and its parameters."""
    # Find the longest matching action name to handle multi-word actions
    found_action_name = None
    longest_match_len = 0

    for act_name in available_actions.keys():
        if action_line.lower().startswith(act_name.lower()):
            if len(act_name) > longest_match_len:
                longest_match_len = len(act_name)
                found_action_name = act_name
    
    if not found_action_name:
        return None

    action_name = found_action_name
    param_string = action_line[len(action_name):].strip()

    action_config = available_actions.get(action_name)
    if not action_config:
        return None # Should not happen if found_action_name is from available_actions

    params: Dict[str, Any] = {}
    if action_config.parameters:
        if len(action_config.parameters) == 1 and action_config.parameters[0].type == "string":
            param_name = action_config.parameters[0].name
            # Handle quoted parameters for multi-word arguments
            if (param_string.startswith('\'') and param_string.endswith('\'')) or \
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

def parse_player_response(player_response: str, available_actions: Dict[str, ActionConfig]) -> List[Tuple[ActionConfig, Dict[str, Any]]]:
    """Extracts and parses actions from a player's response.

    Looks for lines starting with '>' as indicators of actions.
    """
    parsed_actions: List[Tuple[ActionConfig, Dict[str, Any]]] = []
    lines = player_response.strip().splitlines()

    for line in lines:
        trimmed_line = line.strip()
        if trimmed_line.startswith(">"):
            action_line = trimmed_line[1:].strip()
            if action_line:
                parsed_action = _parse_single_action_line(action_line, available_actions)
                if parsed_action:
                    parsed_actions.append(parsed_action)
                # else: TODO: Handle invalid single action line more gracefully (e.g., log, add to feedback)

    return parsed_actions
