from typing import List, Dict, Any, Optional, Tuple
from motive.config import ActionConfig, ParameterConfig
import re

def _parse_single_action_line(action_line: str, available_actions: Dict[str, ActionConfig], room_objects: Optional[Dict[str, Any]] = None) -> Optional[Tuple[ActionConfig, Dict[str, Any]]]:
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
        # Check for object aliases if room_objects are provided
        if room_objects:
            # Extract the first word as potential action name
            words = action_line.strip().split()
            if words:
                potential_action = words[0].lower()
                # Check each object for aliases
                for obj_id, obj_data in room_objects.items():
                    # Handle both GameObject instances and dict data
                    if hasattr(obj_data, 'action_aliases'):
                        aliases = obj_data.action_aliases
                    elif isinstance(obj_data, dict) and 'action_aliases' in obj_data:
                        aliases = obj_data['action_aliases']
                    else:
                        continue
                    
                    if potential_action in aliases:
                        # Found an alias! Redirect to the actual action
                        actual_action = aliases[potential_action]
                        # Reconstruct the action line with the actual action
                        remaining_words = words[1:] if len(words) > 1 else []
                        new_action_line = f"{actual_action} {' '.join(remaining_words)}"
                        # Recursively parse with the redirected action
                        return _parse_single_action_line(new_action_line, available_actions, room_objects)
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
                # For single parameters, check if there are multiple quoted strings
                # If so, concatenate them into a single parameter
                import re
                quoted_pattern = r'"[^"]*"|\'[^\']*\''
                quoted_matches = re.findall(quoted_pattern, param_string)
                if len(quoted_matches) > 1:
                    # Multiple quoted strings - concatenate them
                    concatenated = ' '.join([match[1:-1] for match in quoted_matches])
                    params[param_name] = concatenated
                else:
                    # For single parameters, treat the entire remaining string as the parameter
                    # This allows multi-word arguments without quotes for the last parameter
                    params[param_name] = param_string
        else:
            # Handle multiple parameters - try to parse them intelligently
            if len(parameters) == 2 and all((p.get('type') if hasattr(p, 'get') else p.type) == "string" for p in parameters):
                # Special case for two string parameters (like whisper: player + phrase)
                # Use a more sophisticated parser for whisper actions
                import re
                
                # Check if this is a whisper action by looking at parameter names
                param_names = [p.get('name', '') if hasattr(p, 'get') else p.name for p in parameters]
                if 'player' in param_names and 'phrase' in param_names:
                    # Use specialized whisper parsing
                    try:
                        player_name, phrase = _parse_whisper_parameters(param_string)
                        params['player'] = player_name
                        params['phrase'] = phrase
                    except Exception as e:
                        # If whisper parsing fails, provide helpful error message
                        # This will be caught by the action validation and provide feedback
                        params['player'] = ""
                        params['phrase'] = ""
                        # Add a special error marker that can be detected later
                        params['_whisper_parse_error'] = f"Invalid whisper format. Expected: whisper \"player_name\" \"message\". Got: {param_string}. Error: {str(e)}"
                elif 'player' in param_names and 'object_name' in param_names:
                    # Specialized parsing for give action: give <player> <object>
                    try:
                        player_name, object_name = _parse_give_parameters(param_string)
                        params['player'] = player_name
                        params['object_name'] = object_name
                    except Exception as e:
                        # If give parsing fails, provide helpful error message
                        params['player'] = ""
                        params['object_name'] = ""
                        params['_give_parse_error'] = f"Invalid give format. Expected: give \"player_name\" \"object_name\". Got: {param_string}. Error: {str(e)}"
                elif 'object_name' in param_names and 'exit' in param_names:
                    # Specialized parsing for throw action: throw <object> <exit>
                    try:
                        object_name, exit_direction = _parse_throw_parameters(param_string)
                        params['object_name'] = object_name
                        params['exit'] = exit_direction
                    except Exception as e:
                        # If throw parsing fails, provide helpful error message
                        params['object_name'] = ""
                        params['exit'] = ""
                        params['_throw_parse_error'] = f"Invalid throw format. Expected: throw \"object_name\" \"exit\". Got: {param_string}. Error: {str(e)}"
                elif 'object_name' in param_names and 'target' in param_names:
                    # Specialized parsing for use action: use <object> [on/at <target>]
                    try:
                        object_name, target = _parse_use_parameters(param_string)
                        params['object_name'] = object_name
                        params['target'] = target
                    except Exception as e:
                        # If use parsing fails, provide helpful error message
                        params['object_name'] = ""
                        params['target'] = ""
                        params['_use_parse_error'] = f"Invalid use format. Expected: use \"object_name\" [on/at \"target\"]. Got: {param_string}. Error: {str(e)}"
                else:
                    # Fallback to original logic for other two-parameter actions
                    match = re.match(r'^(\S+)\s+(.+)$', param_string)
                    if match:
                        first_param_raw = match.group(1)
                        rest = match.group(2).strip()
                        # De-quote first param if quoted (e.g., "Key" -> Key)
                        first_param = _extract_quoted_content(first_param_raw)
                        
                        # Always normalize second param by de-quoting if quoted
                        second_param = _extract_quoted_content(rest)
                        # Assign to parameters in order
                        params[parameters[0].get('name', 'param1') if hasattr(parameters[0], 'get') else parameters[0].name] = first_param
                        params[parameters[1].get('name', 'param2') if hasattr(parameters[1], 'get') else parameters[1].name] = second_param
                    else:
                        # Fallback: assign raw (but de-quoted) string to first parameter
                        first_param_name = parameters[0].get('name', 'param1') if hasattr(parameters[0], 'get') else parameters[0].name
                        params[first_param_name] = _extract_quoted_content(param_string)
            elif "target" in [(p.get('name', '') if hasattr(p, 'get') else p.name) for p in parameters]:
                params["target"] = param_string
            elif parameters:
                # This case means we couldn't parse all expected parameters for a defined action.
                pass
    return action_config, params

def parse_player_response(player_response: str, available_actions: Dict[str, ActionConfig], room_objects: Optional[Dict[str, Any]] = None) -> Tuple[List[Tuple[ActionConfig, Dict[str, Any]]], List[str]]:
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
                parsed_action = _parse_single_action_line(action_line, available_actions, room_objects)
                if parsed_action:
                    action_config, params = parsed_action
                    # Check for parse errors in the parameters
                    if '_whisper_parse_error' in params or '_give_parse_error' in params or '_throw_parse_error' in params or '_use_parse_error' in params:
                        # Treat as invalid action with helpful error message
                        error_msg = params.get('_whisper_parse_error') or params.get('_give_parse_error') or params.get('_throw_parse_error') or params.get('_use_parse_error')
                        invalid_actions.append(f"{action_line} - {error_msg}")
                    else:
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


def _parse_whisper_parameters(param_string: str) -> Tuple[str, str]:
    """
    Parse whisper action parameters with strict CLI format validation.
    
    Only handles CLI-compatible formats:
    - whisper hero "hello there"
    - whisper "Captain Marcus" "any news?"
    - whisper "Hooded Figure" 'mutual "friends" are getting restless'
    - whisper "Guild Master" "Our mutual \"friends\" are getting restless"
    
    Does NOT handle natural language formats like:
    - whisper 'phrase' to Player (rejected)
    
    Returns:
        Tuple of (player_name, phrase)
    Raises:
        ValueError: If format doesn't match CLI pattern
    """
    param_string = param_string.strip()
    
    # First, check if this looks like natural language "to X" format
    # This is not CLI-compatible and should be rejected
    # Use regex to find " to " followed by words (player name)
    import re
    to_match = re.search(r'\s+to\s+(\w+(?:\s+\w+)*)\s*$', param_string)
    if to_match:
        # This looks like natural language format: 'phrase' to player
        # Split on the last " to " pattern
        parts = param_string.rsplit(' to ', 1)
        if len(parts) == 2:
            phrase_part = parts[0].strip()
            player_part = parts[1].strip()
            # Check if the phrase part is properly quoted (starts and ends with same quote type)
            if (phrase_part.startswith('"') and not phrase_part.endswith('"')) or (phrase_part.startswith("'") and not phrase_part.endswith("'")):
                raise ValueError(f"Malformed whisper format detected. Use CLI format: whisper \"player_name\" \"message\"")
            
            # If phrase is quoted but player is not, it's natural language format
            if ((phrase_part.startswith('"') and phrase_part.endswith('"')) or 
                (phrase_part.startswith("'") and phrase_part.endswith("'"))) and not ('"' in player_part or "'" in player_part):
                raise ValueError(f"Natural language 'to X' format not supported. Use CLI format: whisper \"player_name\" \"message\"")
    
    # Check for missing quotes only if it looks like it should be quoted
    # Don't reject simple unquoted formats like "hero hello there"
    if not ('"' in param_string or "'" in param_string) and ' ' in param_string:
        # Only reject if there are spaces but no quotes (indicating malformed quoted format)
        # Simple unquoted formats like "hero hello" are still valid
        pass  # Allow unquoted formats
    
    # Pattern 1: Handle mixed quote types - double quotes for player, single quotes for phrase
    # Use a more sophisticated approach to handle nested quotes
    if param_string.startswith('"') and "'" in param_string:
        # Find the end of the first quoted player name
        player_end = param_string.find('"', 1)
        if player_end != -1:
            player_name = param_string[1:player_end]
            # The rest should be the phrase in single quotes
            phrase_part = param_string[player_end + 1:].strip()
            if phrase_part.startswith("'") and phrase_part.endswith("'"):
                # Use _extract_quoted_content to properly handle escaped quotes
                phrase = _extract_quoted_content(phrase_part)
                return player_name, phrase
    
    # Pattern 1b: Handle double quotes for both player and phrase
    # Use a more sophisticated approach to handle nested quotes
    if param_string.startswith('"') and param_string.count('"') >= 4:  # At least 4 quotes for player + phrase
        # Find the end of the first quoted player name
        player_end = param_string.find('"', 1)
        if player_end != -1:
            player_name = param_string[1:player_end]
            # The rest should be the phrase in double quotes
            phrase_part = param_string[player_end + 1:].strip()
            if phrase_part.startswith('"') and phrase_part.endswith('"'):
                # Use _extract_quoted_content to properly handle escaped quotes
                phrase = _extract_quoted_content(phrase_part)
                return player_name, phrase
    
    # Pattern 1c: Handle mixed quote types - single quotes for player, double quotes for phrase  
    mixed_quotes_match2 = re.match(r'^\'([^\']+)\'\s+"([^"]+)"(?:\s+to\s+(\S+(?:\s+\S+)*))?$', param_string)
    if mixed_quotes_match2:
        player_name = mixed_quotes_match2.group(1)
        phrase = mixed_quotes_match2.group(2)
        return player_name, phrase
    
    # Pattern 1c: Look for quoted player name at the start, then phrase, then optional "to X"
    # Try to match: "Player Name" "phrase" to PlayerName or "Player Name" "phrase"
    quoted_player_with_to = re.match(r'^(["\'])([^"\']+)\1\s+(["\'])([^"\']+)\3(?:\s+to\s+(\S+(?:\s+\S+)*))?$', param_string)
    if quoted_player_with_to:
        player_name = quoted_player_with_to.group(2)
        phrase = quoted_player_with_to.group(4)
        return player_name, phrase
    
    # Pattern 2: Look for "to X" at the end (e.g., "phrase" to PlayerName)
    # This handles cases where the phrase comes first, then "to player"
    to_match = re.search(r'^(.+?)\s+to\s+(\S+(?:\s+\S+)*)$', param_string)
    if to_match:
        phrase_part = to_match.group(1).strip()
        player_part = to_match.group(2).strip()
        
        # Parse the phrase part (might be quoted)
        phrase = _extract_quoted_content(phrase_part)
        
        # Parse the player part (might be quoted)
        player_name = _extract_quoted_content(player_part)
        
        return player_name, phrase
    
    # Pattern 3: Look for single-word player followed by quoted phrase
    # Try to match: PlayerName "phrase" or PlayerName 'phrase'
    simple_match = re.match(r'^(\S+)\s+(.+)$', param_string)
    if simple_match:
        player_name = simple_match.group(1)
        phrase_part = simple_match.group(2).strip()
        phrase = _extract_quoted_content(phrase_part)
        return player_name, phrase
    
    # Pattern 4: Single word - treat as player name with empty phrase
    if not ' ' in param_string:
        return param_string, ""
    
    # Fallback: treat entire string as phrase, no player
    return "", param_string


def _extract_quoted_content(text: str) -> str:
    """
    Extract content from quoted string, handling nested quotes and escaping.
    
    Handles cases like:
    - "simple string" -> simple string
    - 'simple string' -> simple string
    - "string with \"nested\" quotes" -> string with "nested" quotes
    - 'string with \'nested\' quotes' -> string with 'nested' quotes
    - "string with 'mixed' quotes" -> string with 'mixed' quotes
    - unquoted string -> unquoted string
    - "quoted string" extra words -> quoted string (ignores extra words)
    """
    text = text.strip()
    
    # Check if it starts with a quote
    if text.startswith('"'):
        # Find the matching closing quote, handling escaped quotes
        end_quote_pos = -1
        i = 1
        while i < len(text):
            if text[i] == '"' and text[i-1] != '\\':
                end_quote_pos = i
                break
            i += 1
        
        if end_quote_pos != -1:
            # Extract content between quotes
            content = text[1:end_quote_pos]
            # Unescape \" within the content
            content = content.replace('\\"', '"')
            return content
    
    elif text.startswith("'"):
        # Find the matching closing quote, handling escaped quotes
        # We need to find the LAST single quote that's not escaped
        end_quote_pos = -1
        i = len(text) - 1
        while i > 0:
            if text[i] == "'" and text[i-1] != '\\':
                end_quote_pos = i
                break
            i -= 1
        
        if end_quote_pos != -1:
            # Extract content between quotes
            content = text[1:end_quote_pos]
            # Unescape \' within the content
            content = content.replace("\\'", "'")
            return content
    
    # Not quoted, return as-is
    return text


def _parse_give_parameters(param_string: str) -> Tuple[str, str]:
    """
    Parse give action parameters: give <player> <object>
    
    Handles CLI-compatible formats:
    - give Player_2 torch
    - give "Player_2" "magic sword"
    - give Player_2 "magic sword"
    - give "Captain Marcus" torch
    
    Returns:
        Tuple of (player_name, object_name)
    Raises:
        ValueError: If format is invalid
    """
    param_string = param_string.strip()
    
    if not param_string:
        raise ValueError("Give action requires both player and object parameters")
    
    # Split into words, but be careful with quoted strings
    words = []
    current_word = ""
    in_quotes = False
    quote_char = None
    
    i = 0
    while i < len(param_string):
        char = param_string[i]
        
        if not in_quotes:
            if char in ['"', "'"]:
                in_quotes = True
                quote_char = char
                current_word += char
            elif char == ' ':
                if current_word:
                    words.append(current_word)
                    current_word = ""
            else:
                current_word += char
        else:
            current_word += char
            if char == quote_char and (i == 0 or param_string[i-1] != '\\'):
                in_quotes = False
                quote_char = None
        
        i += 1
    
    if current_word:
        words.append(current_word)
    
    # Validate we have exactly 2 parameters
    if len(words) != 2:
        raise ValueError(f"Give action requires exactly 2 parameters (player and object), got {len(words)}")
    
    player_name = _extract_quoted_content(words[0])
    object_name = _extract_quoted_content(words[1])
    
    # Validate parameters are not empty
    if not player_name.strip():
        raise ValueError("Player name cannot be empty")
    
    if not object_name.strip():
        raise ValueError("Object name cannot be empty")
    
    return player_name.strip(), object_name.strip()


def _parse_throw_parameters(param_string: str) -> Tuple[str, str]:
    """
    Parse throw action parameters: throw <object> <exit>
    
    Handles CLI-compatible formats:
    - throw torch north
    - throw "magic sword" "Rusty Anchor Tavern"
    - throw torch "Rusty Anchor Tavern"
    - throw "magic sword" north
    
    Returns:
        Tuple of (object_name, exit_direction)
    Raises:
        ValueError: If format is invalid
    """
    param_string = param_string.strip()
    
    if not param_string:
        raise ValueError("Throw action requires both object and exit parameters")
    
    # Split into words, but be careful with quoted strings
    words = []
    current_word = ""
    in_quotes = False
    quote_char = None
    
    i = 0
    while i < len(param_string):
        char = param_string[i]
        
        if not in_quotes:
            if char in ['"', "'"]:
                in_quotes = True
                quote_char = char
                current_word += char
            elif char == ' ':
                if current_word:
                    words.append(current_word)
                    current_word = ""
            else:
                current_word += char
        else:
            current_word += char
            if char == quote_char and (i == 0 or param_string[i-1] != '\\'):
                in_quotes = False
                quote_char = None
        
        i += 1
    
    if current_word:
        words.append(current_word)
    
    # Validate we have exactly 2 parameters
    if len(words) != 2:
        raise ValueError(f"Throw action requires exactly 2 parameters (object and exit), got {len(words)}")
    
    object_name = _extract_quoted_content(words[0])
    exit_direction = _extract_quoted_content(words[1])
    
    # Validate parameters are not empty
    if not object_name.strip():
        raise ValueError("Object name cannot be empty")
    
    if not exit_direction.strip():
        raise ValueError("Exit direction cannot be empty")
    
    return object_name.strip(), exit_direction.strip()


def _parse_use_parameters(param_string: str) -> Tuple[str, str]:
    """
    Parse use action parameters: use <object> [on/at <target>]
    
    Handles CLI-compatible formats:
    - use torch
    - use "magic sword"
    - use torch on door
    - use "magic sword" on "locked chest"
    - use torch at wall
    
    Returns:
        Tuple of (object_name, target)
        target will be empty string if not provided
    Raises:
        ValueError: If format is invalid
    """
    param_string = param_string.strip()
    
    if not param_string:
        raise ValueError("Use action requires an object name")
    
    # Look for common prepositions that indicate a target
    prepositions = ['on', 'at', 'with', 'against']
    
    # Find the first preposition
    preposition_pos = -1
    preposition = None
    for prep in prepositions:
        # Look for the preposition as a whole word (not part of another word)
        pattern = r'\b' + re.escape(prep) + r'\b'
        match = re.search(pattern, param_string, re.IGNORECASE)
        if match and (preposition_pos == -1 or match.start() < preposition_pos):
            preposition_pos = match.start()
            preposition = prep
    
    if preposition_pos != -1:
        # Split on the preposition
        object_part = param_string[:preposition_pos].strip()
        target_part = param_string[preposition_pos + len(preposition):].strip()
        
        # Extract quoted content from both parts
        object_name = _extract_quoted_content(object_part)
        target = _extract_quoted_content(target_part)
        
        # Validate object name is not empty
        if not object_name.strip():
            raise ValueError("Object name cannot be empty")
        
        return object_name.strip(), target.strip()
    else:
        # No preposition found, treat entire string as object name
        object_name = _extract_quoted_content(param_string)
        
        # Validate object name is not empty
        if not object_name.strip():
            raise ValueError("Object name cannot be empty")
        
        return object_name.strip(), ""
