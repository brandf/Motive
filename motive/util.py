#!/usr/bin/env python3
"""
Motive Utility Tool
Comprehensive utility for Motive game management including:
- Configuration analysis and validation
- Training data management
- Log processing and curation
- Game run utilities
"""

import argparse
import yaml
import warnings
import json
import sys
import shutil
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

try:
    from motive.cli import load_config as cli_load_config
    HIERARCHICAL_SUPPORT = True
except ImportError:
    HIERARCHICAL_SUPPORT = False


def load_config(config_path: str) -> Union[Dict[str, Any], 'GameConfig', 'V2GameConfig']:
    """Load and parse a YAML configuration file, supporting both traditional and hierarchical configs."""
    try:
        # Check if this is a hierarchical config (has includes)
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # If it has includes and we have hierarchical support, use the new loader
        if 'includes' in raw_config and HIERARCHICAL_SUPPORT:
            print(f"Detected hierarchical config with includes, using config loader...")
            # Use the new CLI loader that handles v2 configs
            game_config = cli_load_config(config_path)
            # Return the GameConfig/V2GameConfig object directly - the util functions will handle it
            return game_config
        else:
            # Traditional config loading
            return raw_config
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}", file=sys.stderr)
        sys.exit(1)


def show_raw_config(config: Union[Dict[str, Any], 'GameConfig', 'V2GameConfig'], format_type: str = 'yaml') -> None:
    """Output the raw merged configuration."""
    print(f"Merged Configuration ({format_type.upper()}):")
    print("=" * 50)
    
    # Convert config object to dict for output
    if hasattr(config, 'dict'):
        # Pydantic model (v2)
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Pydantic serializer warnings:",
                category=UserWarning,
            )
            config_dict = config.dict()
    elif hasattr(config, '__dict__'):
        # Object with __dict__ (v1 GameConfig)
        config_dict = config.__dict__
    else:
        # Already a dict
        config_dict = config
    
    if format_type == 'json':
        print(json.dumps(config_dict, indent=2, default=str))
    else:  # yaml
        print(yaml.dump(config_dict, default_flow_style=False, sort_keys=False))
    
    print()


def show_summary(config) -> None:
    """Display a summary of the configuration."""
    print("Configuration Summary:")
    print("=====================")
    
    # Handle v2 configs (V2GameConfig)
    if hasattr(config, 'action_definitions'):
        # V2GameConfig object
        action_count = len(config.action_definitions)
        entity_count = len(config.entity_definitions)
        
        # Count entities by type
        room_count = sum(1 for entity in config.entity_definitions.values() 
                        if hasattr(entity, 'types') and 'room' in entity.types)
        object_count = sum(1 for entity in config.entity_definitions.values() 
                         if hasattr(entity, 'types') and 'object' in entity.types)
        character_count = sum(1 for entity in config.entity_definitions.values() 
                             if hasattr(entity, 'types') and 'character' in entity.types)
        
        print(f"Actions: {action_count}")
        print(f"Entities: {entity_count}")
        print(f"  - Rooms: {room_count}")
        print(f"  - Objects: {object_count}")
        print(f"  - Characters: {character_count}")
    # Handle v1 configs (GameConfig or dict)
    elif hasattr(config, 'actions'):
        # GameConfig object (v1)
        action_count = len(config.actions)
        object_count = len(config.object_types)
        room_count = len(config.rooms)
        character_count = len(config.character_types)
        
        print(f"Actions: {action_count}")
        print(f"Objects: {object_count}")
        print(f"Rooms: {room_count}")
        print(f"Characters: {character_count}")
    else:
        # Dictionary config (v1)
        action_count = len(config.get('actions', {}))
        object_count = len(config.get('object_types', {}))
        room_count = len(config.get('rooms', {}))
        
        # Use characters if available, otherwise fall back to character_types
        characters = config.get('characters', {})
        if not characters:
            characters = config.get('character_types', {})
        character_count = len(characters)
        
        print(f"Actions: {action_count}")
        print(f"Objects: {object_count}")
        print(f"Rooms: {room_count}")
        print(f"Characters: {character_count}")
    
    print()


def show_actions(config) -> None:
    """Display available actions."""
    print("Available Actions:")
    print("=================")
    
    # Handle both v1 and v2 configs
    if hasattr(config, 'action_definitions'):
        # V2GameConfig object - use action_definitions
        actions = config.action_definitions
    elif hasattr(config, 'actions'):
        # GameConfig object (v1) - use actions
        actions = config.actions
    else:
        # Dictionary config - check for v2 first, then v1
        actions = config.get('action_definitions', config.get('actions', {}))
    
    if not actions:
        print("No actions found in this configuration.")
        return
    
    for action_name in sorted(actions.keys()):
        action = actions[action_name]
        
        # Handle both dict and Pydantic objects
        if hasattr(action, 'cost'):
            # Pydantic object (v2)
            cost = action.cost
            name = action.name
            description = action.description
            category = action.category
            parameters = action.parameters
            requirements = action.requirements
        else:
            # Dictionary object (v1)
            cost = action.get('cost', 0)
            name = action.get('name', action_name)
            description = action.get('description', 'No description')
            category = action.get('category')
            parameters = action.get('parameters', [])
            requirements = action.get('requirements', [])
        
        # Handle cost (can be int or dict with value)
        if isinstance(cost, dict):
            cost = cost.get('value', cost.get('cost', 0))
        
        category_str = f" ({category})" if category else ""
        
        print(f"- {name}: {description}")
        print(f"  Cost: {cost} AP{category_str}")
        
        # Show parameters
        if parameters:
            if hasattr(parameters[0], 'name'):
                # Pydantic objects
                param_list = [p.name for p in parameters]
            else:
                # Dictionary objects
                param_list = [p.get('name', 'unnamed') for p in parameters]
            print(f"  Parameters: {', '.join(param_list)}")
        
        # Show requirements
        if requirements:
            if hasattr(requirements[0], 'type'):
                # Pydantic objects
                req_list = [r.type for r in requirements]
            else:
                # Dictionary objects
                req_list = [r.get('type', 'unknown') for r in requirements]
            print(f"  Requirements: {', '.join(req_list)}")
        
        print()


def show_objects(config) -> None:
    """Display available objects."""
    print("Available Objects:")
    print("=================")
    
    # Handle both dict configs (v1) and GameConfig objects (v2)
    if hasattr(config, 'object_types'):
        # GameConfig object (v2)
        objects = config.object_types
    else:
        # Dictionary config (v1)
        objects = config.get('object_types', {})
    
    if not objects:
        print("No objects found in this configuration.")
        return
    
    for object_name in sorted(objects.keys()):
        obj = objects[object_name]
        
        # Handle both dict and Pydantic objects
        if hasattr(obj, 'name'):
            # Pydantic object (v2)
            name = obj.name
            description = obj.description
            tags = getattr(obj, 'tags', [])
        else:
            # Dictionary object (v1)
            name = obj.get('name', object_name)
            description = obj.get('description', 'No description')
            tags = obj.get('tags', [])
        
        print(f"- {name}: {description}")
        
        # Show tags
        if tags:
            print(f"  Tags: {', '.join(tags)}")
        
        # Show properties
        if hasattr(obj, 'properties'):
            # Pydantic object (v2)
            properties = obj.properties
        else:
            # Dictionary object (v1)
            properties = obj.get('properties', {})
        
        if properties:
            prop_list = [f"{k}: {v}" for k, v in properties.items()]
            print(f"  Properties: {', '.join(prop_list)}")
        
        print()


def show_rooms(config) -> None:
    """Display available rooms."""
    print("Available Rooms:")
    print("===============")
    
    # Handle both dict configs (v1) and GameConfig objects (v2)
    if hasattr(config, 'rooms'):
        # GameConfig object (v2)
        rooms = config.rooms
    else:
        # Dictionary config (v1)
        rooms = config.get('rooms', {})
    
    if not rooms:
        print("No rooms found in this configuration.")
        return
    
    for room_name in sorted(rooms.keys()):
        room = rooms[room_name]
        
        # Handle both dict and Pydantic objects
        if hasattr(room, 'name'):
            # Pydantic object (v2)
            name = room.name
            description = room.description
        else:
            # Dictionary object (v1)
            name = room.get('name', room_name)
            description = room.get('description', 'No description')
        
        print(f"- {name}: {description}")
        
        # Show exits
        if hasattr(room, 'exits'):
            # Pydantic object (v2)
            exits = room.exits
        else:
            # Dictionary object (v1)
            exits = room.get('exits', {})
        
        if exits:
            exit_list = [f"{name} -> {exit_info.get('destination_room_id', 'unknown')}" 
                        for name, exit_info in exits.items()]
            print(f"  Exits: {', '.join(exit_list)}")
        
        # Show objects
        if hasattr(room, 'objects'):
            # Pydantic object (v2)
            objects = room.objects
        else:
            # Dictionary object (v1)
            objects = room.get('objects', {})
        
        if objects:
            obj_list = [obj.get('name', name) for name, obj in objects.items()]
            print(f"  Objects: {', '.join(obj_list)}")
        
        print()


def show_characters(config) -> None:
    """Display available characters."""
    print("Available Characters:")
    print("===================")
    
    # Handle both dict configs (v1) and GameConfig/V2GameConfig objects (v2)
    if hasattr(config, 'entity_definitions'):
        # V2GameConfig object (v2) - extract characters from entity_definitions
        characters = {}
        for entity_id, entity_def in config.entity_definitions.items():
            if hasattr(entity_def, 'types') and 'character' in entity_def.types:
                characters[entity_id] = entity_def
    elif hasattr(config, 'character_types'):
        # GameConfig object (v1) - use character_types
        characters = config.character_types
    elif hasattr(config, 'characters'):
        # GameConfig object (v1) - use characters
        characters = config.characters
    else:
        # Dictionary config (v1) - use characters if available, otherwise fall back to character_types
        characters = config.get('characters', {})
        if not characters:
            characters = config.get('character_types', {})
    
    if not characters:
        print("No characters found in this configuration.")
        return
    
    for char_name in sorted(characters.keys()):
        char = characters[char_name]
        
        # Handle v2 entity definitions, v1 Pydantic objects, and dictionaries
        if hasattr(char, 'config') and char.config:
            # V2 entity definition
            name = char.config.get('name', char_name)
            backstory = char.config.get('backstory', 'No backstory')
        elif hasattr(char, 'name'):
            # V1 Pydantic object
            name = char.name
            backstory = char.backstory
        else:
            # Dictionary object (v1)
            name = char.get('name', char_name)
            backstory = char.get('backstory', 'No backstory')
        
        print(f"- {name}: {backstory}")
        
        # Handle motives for different config types
        motives_found = False
        if hasattr(char, 'config') and char.config and 'motives' in char.config:
            # V2 entity definition - motives in config
            motives = char.config['motives']
            if isinstance(motives, list) and len(motives) > 0:
                print(f"  Motives: {len(motives)} available")
                for i, motive in enumerate(motives, 1):
                    if isinstance(motive, dict):
                        motive_desc = motive.get('description', 'No description')
                        print(f"    {i}. {motive_desc}")
                    else:
                        print(f"    {i}. {motive}")
                motives_found = True
        elif hasattr(char, 'motives') and char.motives:
            # V1 Pydantic object
            motives = char.motives
            if isinstance(motives, list) and len(motives) > 0:
                print(f"  Motives: {len(motives)} available")
                for i, motive in enumerate(motives, 1):
                    motive_desc = motive.get('description', 'No description') if isinstance(motive, dict) else str(motive)
                    print(f"    {i}. {motive_desc}")
                motives_found = True
        elif hasattr(char, 'motive') and char.motive:
            # Single motive
            print(f"  Motive: {char.motive}")
            motives_found = True
        elif 'motives' in char and char['motives']:
            # Dictionary with motives
            motives = char['motives']
            if isinstance(motives, list) and len(motives) > 0:
                print(f"  Motives: {len(motives)} available")
                for i, motive in enumerate(motives, 1):
                    motive_desc = motive.get('description', 'No description') if isinstance(motive, dict) else str(motive)
                    print(f"    {i}. {motive_desc}")
                motives_found = True
        elif 'motive' in char:
            # Dictionary with single motive
            print(f"  Motive: {char.get('motive', 'No motive')}")
            motives_found = True
        
        if not motives_found:
            print(f"  Motive: No motive")
        print()


def show_entities(config, entity_type: str = None) -> None:
    """Display v2 entity definitions with detailed information."""
    print("V2 Entity Definitions:")
    print("=====================")
    
    # Check if this is a v2 config with entity_definitions
    if not hasattr(config, 'entity_definitions'):
        print("This is not a v2 config with entity_definitions.")
        return
    
    entities = config.entity_definitions
    if not entities:
        print("No entity definitions found in this configuration.")
        return
    
    # Filter by entity type if specified
    filtered_entities = {}
    if entity_type:
        for entity_id, entity_def in entities.items():
            if hasattr(entity_def, 'types') and entity_type in entity_def.types:
                filtered_entities[entity_id] = entity_def
    else:
        filtered_entities = entities
    
    if not filtered_entities:
        print(f"No entities of type '{entity_type}' found.")
        return
    
    print(f"Found {len(filtered_entities)} entities" + (f" of type '{entity_type}'" if entity_type else ""))
    print()
    
    for entity_id, entity_def in sorted(filtered_entities.items()):
        print(f"Entity: {entity_id}")
        print(f"  Type: {type(entity_def)}")
        print(f"  Types/Behaviors: {entity_def.types}")
        
        # Show properties
        if hasattr(entity_def, 'properties') and entity_def.properties:
            print(f"  Properties:")
            for prop_name, prop_value in entity_def.properties.items():
                print(f"    {prop_name}: {prop_value}")
        
        # Show attributes (immutable) including motives if present
        if hasattr(entity_def, 'attributes') and entity_def.attributes:
            print(f"  Attributes:")
            for attr_key, attr_value in entity_def.attributes.items():
                if attr_key == 'motives' and isinstance(attr_value, list):
                    print(f"    {attr_key}: {len(attr_value)} motives")
                    for i, motive in enumerate(attr_value, 1):
                        if isinstance(motive, dict):
                            motive_id = motive.get('id', f'motive_{i}')
                            motive_desc = motive.get('description', 'No description')
                            print(f"      {i}. {motive_id}: {motive_desc}")
                        else:
                            print(f"      {i}. {motive}")
                else:
                    print(f"    {attr_key}: {attr_value}")
        
        print()

def debug_config_loading(config_path: str) -> None:
    """Debug config loading process with detailed information."""
    print("Config Loading Debug:")
    print("===================")
    print(f"Loading config from: {config_path}")
    
    try:
        config = load_config(config_path)
        print(f"✅ Config loaded successfully")
        print(f"Config type: {type(config)}")
        print(f"Config attributes: {[attr for attr in dir(config) if not attr.startswith('_')]}")
        
        # Check if it's a v2 config
        if hasattr(config, 'entity_definitions'):
            print(f"\nV2 Config detected:")
            print(f"  Entity definitions: {len(config.entity_definitions)}")
            print(f"  Action definitions: {len(config.action_definitions)}")
            
            # Count by type
            type_counts = {}
            for entity_id, entity_def in config.entity_definitions.items():
                for entity_type in entity_def.types:
                    type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
            
            print(f"  Entity types: {type_counts}")
            
            # Check character motives
            characters_with_motives = 0
            characters_without_motives = 0
            for entity_id, entity_def in config.entity_definitions.items():
                if 'character' in entity_def.types:
                    if hasattr(entity_def, 'attributes') and entity_def.attributes and 'motives' in entity_def.attributes:
                        characters_with_motives += 1
                    else:
                        characters_without_motives += 1
            
            print(f"  Characters with motives: {characters_with_motives}")
            print(f"  Characters without motives: {characters_without_motives}")
            
        else:
            print(f"\nV1 Config detected:")
            if hasattr(config, 'character_types'):
                print(f"  Character types: {len(config.character_types)}")
            if hasattr(config, 'object_types'):
                print(f"  Object types: {len(config.object_types)}")
            if hasattr(config, 'actions'):
                print(f"  Actions: {len(config.actions)}")
                
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        import traceback
        traceback.print_exc()

def debug_character_motives(config_path: str, character_id: str = None) -> None:
    """Debug character motives specifically."""
    print("Character Motives Debug:")
    print("=======================")
    
    try:
        config = load_config(config_path)
        
        if hasattr(config, 'entity_definitions'):
            # V2 config
            characters = {}
            for entity_id, entity_def in config.entity_definitions.items():
                if 'character' in entity_def.types:
                    characters[entity_id] = entity_def
            
            if character_id:
                if character_id in characters:
                    char_def = characters[character_id]
                    print(f"Character: {character_id}")
                    print(f"  Type: {type(char_def)}")
                    print(f"  Types: {char_def.types}")
                    print(f"  Properties: {char_def.properties}")
                    print(f"  Attributes: {char_def.attributes}")
                    
                    if hasattr(char_def, 'attributes') and char_def.attributes and 'motives' in char_def.attributes:
                        motives = char_def.attributes['motives']
                        print(f"  Motives ({len(motives)}):")
                        for i, motive in enumerate(motives, 1):
                            print(f"    {i}. {motive}")
                    else:
                        print(f"  Motives: None found")
                else:
                    print(f"Character '{character_id}' not found")
                    print(f"Available characters: {list(characters.keys())}")
            else:
                print(f"All characters ({len(characters)}):")
                for char_id, char_def in characters.items():
                    has_motives = hasattr(char_def, 'attributes') and char_def.attributes and 'motives' in char_def.attributes
                    motive_count = len(char_def.attributes['motives']) if has_motives else 0
                    print(f"  {char_id}: {motive_count} motives")
        else:
            print("This is not a v2 config with entity_definitions")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

def debug_action_aliases(config_path: str, object_id: str = None) -> None:
    """Debug action aliases in object definitions."""
    print("Action Aliases Debug:")
    print("===================")
    
    try:
        config = load_config(config_path)
        
        if hasattr(config, 'entity_definitions'):
            # V2 config - check entity definitions
            objects_with_aliases = {}
            for entity_id, entity_def in config.entity_definitions.items():
                if 'object' in entity_def.types:
                    # Check both direct attribute and in attributes dict
                    aliases = None
                    if hasattr(entity_def, 'action_aliases') and entity_def.action_aliases:
                        aliases = entity_def.action_aliases
                    elif hasattr(entity_def, 'attributes') and entity_def.attributes and 'action_aliases' in entity_def.attributes:
                        aliases = entity_def.attributes['action_aliases']
                    
                    if aliases:
                        objects_with_aliases[entity_id] = aliases
            
            if object_id:
                if object_id in objects_with_aliases:
                    print(f"Object: {object_id}")
                    print(f"  Action aliases: {objects_with_aliases[object_id]}")
                else:
                    print(f"Object '{object_id}' not found or has no action aliases")
                    print(f"Available objects with aliases: {list(objects_with_aliases.keys())}")
            else:
                print(f"Objects with action aliases ({len(objects_with_aliases)}):")
                for obj_id, aliases in objects_with_aliases.items():
                    print(f"  {obj_id}: {aliases}")
                
                # Also check if any objects should have aliases but don't
                all_objects = {}
                for entity_id, entity_def in config.entity_definitions.items():
                    if 'object' in entity_def.types:
                        all_objects[entity_id] = entity_def
                
                objects_without_aliases = []
                for obj_id, obj_def in all_objects.items():
                    # Check both direct attribute and in attributes dict
                    has_aliases = False
                    if hasattr(obj_def, 'action_aliases') and obj_def.action_aliases:
                        has_aliases = True
                    elif hasattr(obj_def, 'attributes') and obj_def.attributes and 'action_aliases' in obj_def.attributes:
                        has_aliases = True
                    
                    if not has_aliases:
                        objects_without_aliases.append(obj_id)
                
                if objects_without_aliases:
                    print(f"\nObjects without action aliases ({len(objects_without_aliases)}):")
                    for obj_id in objects_without_aliases[:10]:  # Show first 10
                        print(f"  {obj_id}")
                    if len(objects_without_aliases) > 10:
                        print(f"  ... and {len(objects_without_aliases) - 10} more")
        else:
            print("This is not a v2 config with entity_definitions")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


def show_includes(config: Dict[str, Any], config_path: str) -> None:
    """Display include information for hierarchical configs."""
    print("Include Information:")
    print("==================")
    
    # Check if this is a hierarchical config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        if 'includes' in raw_config:
            includes = raw_config['includes']
            if not isinstance(includes, list):
                includes = [includes]
            
            print(f"Configuration includes {len(includes)} files:")
            for i, include in enumerate(includes, 1):
                print(f"  {i}. {include}")
            
            if HIERARCHICAL_SUPPORT:
                print("\nHierarchical config loader is available.")
                print("Includes are processed first, then this config merges on top.")
            else:
                print("\nHierarchical config loader not available.")
                print("Falling back to traditional config loading.")
        else:
            print("This is a traditional config (no includes).")
            
    except Exception as e:
        print(f"Error reading include information: {e}")
    
    print()


# ============================================================================
# Training Data Management Functions
# ============================================================================

def find_latest_log_directory() -> Optional[str]:
    """Find the most recent log directory"""
    logs_base = Path("logs")
    if not logs_base.exists():
        return None
    
    # Find all log directories recursively
    log_dirs = []
    for root, dirs, files in os.walk(logs_base):
        if "game.log" in files:
            log_dirs.append(root)
    
    if not log_dirs:
        return None
    
    # Sort by modification time (newest first)
    log_dirs.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
    return log_dirs[0]


def extract_game_config_from_log(game_log_path: Path) -> Dict[str, Any]:
    """Extract game configuration from game.log file"""
    config = {
        "game_settings": {},
        "players": [],
        "total_rounds": "unknown",
        "ap_per_turn": "unknown"
    }
    
    try:
        with open(game_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract player configurations and game settings
        for line in lines:
            if "Initialized player:" in line and "using" in line:
                # Format: "  - Initialized player: Player_1 using google/gemini-2.5-flash"
                parts = line.strip().split("using")
                if len(parts) == 2:
                    player_part = parts[0].split(":")[-1].strip()
                    model_part = parts[1].strip()
                    
                    # Parse provider/model
                    if "/" in model_part:
                        provider, model = model_part.split("/", 1)
                    else:
                        provider = "unknown"
                        model = model_part
                    
                    config["players"].append({
                        "name": player_part,
                        "provider": provider,
                        "model": model
                    })
            
            # Extract game settings
            elif "Game settings:" in line:
                # Skip the header line
                continue
            elif "  num_rounds:" in line:
                try:
                    rounds = int(line.split(":")[-1].strip())
                    config["total_rounds"] = rounds
                    config["game_settings"]["num_rounds"] = rounds
                except:
                    pass
            elif "  initial_ap_per_turn:" in line:
                try:
                    ap = int(line.split(":")[-1].strip())
                    config["ap_per_turn"] = ap
                    config["game_settings"]["initial_ap_per_turn"] = ap
                except:
                    pass
            elif "  manual:" in line:
                try:
                    manual = line.split(":")[-1].strip()
                    config["game_settings"]["manual"] = manual
                except:
                    pass
    
    except Exception as e:
        print(f"Warning: Could not extract full config from {game_log_path}: {e}")
    
    return config


def copy_good_run(log_dir: Optional[str] = None, dest_name: Optional[str] = None) -> bool:
    """Copy a good game run from logs/ to training_data/raw/"""
    
    # If no log_dir provided, find the latest one
    if log_dir is None:
        log_dir = find_latest_log_directory()
        if log_dir is None:
            print("Error: No log directories found in logs/")
            return False
        print(f"Using latest log directory: {log_dir}")
    
    # Validate input directory
    log_path = Path(log_dir)
    if not log_path.exists():
        print(f"Error: Directory {log_dir} does not exist")
        return False
        
    if not (log_path / "game.log").exists():
        print(f"Error: No game.log found in {log_dir}")
        return False
    
    # Create timestamped directory in training_data/raw/
    if dest_name:
        dest_dir = Path("training_data/raw") / dest_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_dir = Path("training_data/raw") / f"run_{timestamp}"
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all log files
    copied_files = []
    for log_file in log_path.glob("*.log"):
        dest_file = dest_dir / log_file.name
        shutil.copy2(log_file, dest_file)
        copied_files.append(log_file.name)
        print(f"Copied: {log_file.name}")
    
    # Extract game configuration from game.log
    game_config = extract_game_config_from_log(log_path / "game.log")
    
    # Create metadata file
    metadata = {
        "source_directory": str(log_path),
        "copied_at": datetime.now().isoformat(),
        "files_copied": copied_files,
        "description": "Good game run - manually curated",
        "edition": "hearth_and_shadow",
        "game_settings": game_config.get("game_settings", {}),
        "players": game_config.get("players", []),
        "total_rounds": game_config.get("total_rounds", "unknown"),
        "ap_per_turn": game_config.get("ap_per_turn", "unknown")
    }
    
    metadata_file = dest_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nCopied {len(copied_files)} files to {dest_dir}")
    print(f"Metadata saved to {metadata_file}")
    
    return True


def process_training_data(raw_dir: Optional[str] = None, name: Optional[str] = None) -> bool:
    """Process training data from raw logs into various formats"""
    
    if raw_dir:
        # Process specific directory
        return process_single_run(raw_dir, name)
    else:
        # Process all runs in training_data/raw/
        raw_base = Path("training_data/raw")
        if not raw_base.exists():
            print("No training_data/raw/ directory found")
            return False
        
        runs = [d for d in raw_base.iterdir() if d.is_dir()]
        if not runs:
            print("No training runs found in training_data/raw/")
            return False
        
        print(f"Processing {len(runs)} training runs...")
        success = True
        for run_dir in runs:
            if not process_single_run(str(run_dir), name):
                success = False
        
        return success


def process_single_run(raw_dir: str, name: Optional[str] = None) -> bool:
    """Process a single training run"""
    
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        print(f"Error: Directory {raw_dir} does not exist")
        return False
    
    # Load metadata
    metadata_file = raw_path / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
    else:
        metadata = {"description": "Unknown run"}
    
    # Create processed directory
    if name:
        processed_dir = Path("training_data/processed") / name
    else:
        processed_dir = Path("training_data/processed") / raw_path.name
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Process game.log (complete GM view of all conversations)
    game_log_file = raw_path / "game.log"
    if game_log_file.exists():
        with open(game_log_file, 'r', encoding='utf-8') as f:
            game_log_content = f.read()
        
        # Save complete game log as primary training data
        game_log_processed = processed_dir / "complete_game_log.txt"
        with open(game_log_processed, 'w', encoding='utf-8') as f:
            f.write(game_log_content)
    
    # Also process individual player logs (filtered player perspectives)
    player_logs = list(raw_path.glob("Player_*_chat.log"))
    if player_logs:
        # Combine all player conversations for comparison
        all_conversations = []
        for player_log in sorted(player_logs):
            player_name = player_log.stem.replace("_chat", "")
            with open(player_log, 'r', encoding='utf-8') as f:
                conversations = f.read().strip()
                all_conversations.append(f"=== {player_name} ===\n{conversations}")
        
        # Save combined player conversations
        combined_file = processed_dir / "player_perspectives.txt"
        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(all_conversations))
    
    # Create training data summary
    summary = {
        "processed_at": datetime.now().isoformat(),
        "source": str(raw_path),
        "files_processed": [f.name for f in player_logs] + (["game.log"] if game_log_file.exists() else []),
        "total_players": len(player_logs),
        "primary_training_data": "complete_game_log.txt",
        "player_perspectives": "player_perspectives.txt" if player_logs else None,
        "metadata": metadata
    }
    
    summary_file = processed_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Processed {raw_dir} -> {processed_dir}")
    print(f"  - {len(player_logs)} player logs processed")
    print(f"  - Combined conversations saved to {combined_file}")
    
    return True


def list_training_runs() -> None:
    """List all available training runs"""
    
    raw_dir = Path("training_data/raw")
    if not raw_dir.exists():
        print("No training_data/raw/ directory found")
        return
    
    runs = [d for d in raw_dir.iterdir() if d.is_dir()]
    if not runs:
        print("No training runs found")
        return
    
    print("Available Training Runs:")
    print("=======================")
    
    for run_dir in sorted(runs):
        metadata_file = run_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
            description = metadata.get("description", "No description")
            files_count = len(metadata.get("files_copied", []))
            copied_at = metadata.get("copied_at", "Unknown date")
        else:
            description = "No metadata"
            files_count = len(list(run_dir.glob("*.log")))
            copied_at = "Unknown date"
        
        print(f"- {run_dir.name}")
        print(f"  Description: {description}")
        print(f"  Files: {files_count}")
        print(f"  Copied: {copied_at}")
        print()


def publish_to_sample(processed_dir: Optional[str] = None, name: Optional[str] = None, force: bool = False) -> bool:
    """Publish processed training data to sample folder"""
    
    # Find processed directory
    if processed_dir:
        source_dir = Path(processed_dir)
        if not source_dir.exists():
            print(f"Error: Processed directory {processed_dir} does not exist")
            return False
    else:
        # Find latest processed directory
        processed_base = Path("training_data/processed")
        if not processed_base.exists():
            print("No training_data/processed/ directory found")
            return False
        
        processed_dirs = [d for d in processed_base.iterdir() if d.is_dir()]
        if not processed_dirs:
            print("No processed training runs found")
            return False
        
        # Sort by modification time (newest first)
        processed_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        source_dir = processed_dirs[0]
        print(f"Using latest processed directory: {source_dir.name}")
    
    # Create published subdirectory
    if name:
        published_dir = Path("training_data/published") / name
    else:
        published_dir = Path("training_data/published") / source_dir.name
    
    if published_dir.exists() and not force:
        print(f"Published directory {published_dir.name} already exists. Use -f/--force to overwrite.")
        return False
    
    # Create published directory
    published_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy processed files to published
    copied_files = []
    
    # Copy complete_game_log.txt (primary training data)
    game_log_file = source_dir / "complete_game_log.txt"
    if game_log_file.exists():
        dest_file = published_dir / "complete_game_log.txt"
        shutil.copy2(game_log_file, dest_file)
        copied_files.append("complete_game_log.txt")
        print(f"Copied: complete_game_log.txt")
    
    # Copy player_perspectives.txt
    player_perspectives_file = source_dir / "player_perspectives.txt"
    if player_perspectives_file.exists():
        dest_file = published_dir / "player_perspectives.txt"
        shutil.copy2(player_perspectives_file, dest_file)
        copied_files.append("player_perspectives.txt")
        print(f"Copied: player_perspectives.txt")
    
    # Copy any other processed files
    for file in source_dir.glob("*.txt"):
        if file.name not in ["complete_game_log.txt", "player_perspectives.txt"]:
            dest_file = published_dir / file.name
            shutil.copy2(file, dest_file)
            copied_files.append(file.name)
            print(f"Copied: {file.name}")
    
    # Copy and update metadata
    source_metadata = source_dir / "summary.json"
    if source_metadata.exists():
        with open(source_metadata, 'r') as f:
            summary = json.load(f)
        
        # Extract metadata from summary
        metadata = summary.get("metadata", {})
        
        # Update description to indicate this is published
        metadata["description"] = f"PUBLISHED: {metadata.get('description', 'High-quality training data')}"
        
        # Add published-specific notes
        metadata["published_notes"] = [
            "This is a curated subset of high-quality training data",
            "Use this as a reference for expected data quality and format",
            f"Published from: {source_dir.name}",
            f"Published at: {datetime.now().isoformat()}"
        ]
        
        # Save updated metadata
        metadata_file = published_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        copied_files.append("metadata.json")
        print(f"Updated: metadata.json")
    
    print(f"\nPublished {len(copied_files)} files to training_data/published/{published_dir.name}/")
    print("Published data updated successfully!")
    
    return True


def show_training_stats() -> None:
    """Show statistics about training data"""
    
    raw_dir = Path("training_data/raw")
    processed_dir = Path("training_data/processed")
    
    print("Training Data Statistics:")
    print("=======================")
    
    # Raw data stats
    if raw_dir.exists():
        raw_runs = [d for d in raw_dir.iterdir() if d.is_dir()]
        print(f"Raw runs: {len(raw_runs)}")
        
        total_files = 0
        total_players = 0
        llm_models = set()
        game_rounds = set()
        
        for run_dir in raw_runs:
            log_files = list(run_dir.glob("*.log"))
            total_files += len(log_files)
            player_logs = list(run_dir.glob("Player_*_chat.log"))
            total_players += len(player_logs)
            
            # Check metadata for LLM info
            metadata_file = run_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Collect LLM models
                    for player in metadata.get("players", []):
                        model = f"{player.get('provider', 'unknown')}/{player.get('model', 'unknown')}"
                        llm_models.add(model)
                    
                    # Collect game rounds
                    rounds = metadata.get("total_rounds", "unknown")
                    if rounds != "unknown":
                        game_rounds.add(rounds)
                        
                except Exception:
                    pass
        
        print(f"Total log files: {total_files}")
        print(f"Total player logs: {total_players}")
        
        if llm_models:
            print(f"LLM models used: {', '.join(sorted(llm_models))}")
        if game_rounds:
            print(f"Game rounds: {', '.join(map(str, sorted(game_rounds)))}")
    else:
        print("Raw runs: 0")
    
    # Processed data stats
    if processed_dir.exists():
        processed_runs = [d for d in processed_dir.iterdir() if d.is_dir()]
        print(f"Processed runs: {len(processed_runs)}")
    else:
        print("Processed runs: 0")
    
    print()


# ============================================================================
# Main CLI Functions
# ============================================================================

def util_main(args=None):
    """Main utility function that can be called with arguments for testing."""
    parser = argparse.ArgumentParser(
        description="Motive Utility Tool - Configuration analysis, training data management, and more",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration Analysis Examples:
  motive-util config                           # Analyze default config
  motive-util config -c configs/game.yaml -A  # Show actions from core config
  motive-util config -c configs/game_new.yaml -I  # Show include info
  motive-util config -c tests/configs/integration/game_test.yaml -a  # Show all information
  motive-util config --raw-config              # Output merged config as YAML
  motive-util config --raw-config-json         # Output merged config as JSON
  motive-util config --validate                # Validate config through Pydantic

Training Data Examples:
  motive-util training copy                   # Copy latest log run
  motive-util training copy -n "excellent_run" # Copy with custom name
  motive-util training process                 # Process all raw runs
  motive-util training process -n "processed_excellent" # Process with custom name
  motive-util training publish                 # Publish latest processed data to published
  motive-util training publish -n "final_dataset" # Publish with custom name
  motive-util training publish -f              # Force overwrite existing published data
  motive-util training list                   # List available runs
  motive-util training stats                  # Show statistics
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Configuration analysis subcommand
    config_parser = subparsers.add_parser('config', help='Analyze game configurations')
    config_parser.add_argument(
        '-c', '--config',
        default='configs/game.yaml',
        help='Path to configuration file (default: configs/game.yaml)'
    )
    config_parser.add_argument(
        '-A', '--actions',
        action='store_true',
        help='Show available actions'
    )
    config_parser.add_argument(
        '-O', '--objects',
        action='store_true',
        help='Show available objects'
    )
    config_parser.add_argument(
        '-R', '--rooms',
        action='store_true',
        help='Show available rooms'
    )
    config_parser.add_argument(
        '-C', '--characters',
        action='store_true',
        help='Show available characters'
    )
    config_parser.add_argument(
        '-E', '--entities',
        nargs='?',
        const='all',
        metavar='TYPE',
        help='Show v2 entity definitions (optionally filtered by type: character, object, room)'
    )
    config_parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Show all available information'
    )
    config_parser.add_argument(
        '-I', '--includes',
        action='store_true',
        help='Show include information for hierarchical configs'
    )
    config_parser.add_argument(
        '--raw-config',
        action='store_true',
        help='Output the merged configuration as YAML (useful for debugging config merging)'
    )
    config_parser.add_argument(
        '--raw-config-json',
        action='store_true',
        help='Output the merged configuration as JSON (useful for debugging config merging)'
    )
    config_parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate the merged configuration through Pydantic models before output'
    )
    config_parser.add_argument(
        '--debug-loading',
        action='store_true',
        help='Debug config loading process with detailed information'
    )
    config_parser.add_argument(
        '--debug-motives',
        nargs='?',
        const='all',
        metavar='CHARACTER_ID',
        help='Debug character motives (optionally for specific character)'
    )
    config_parser.add_argument(
        '--debug-aliases',
        nargs='?',
        const='all',
        metavar='OBJECT_ID',
        help='Debug action aliases (optionally for specific object)'
    )
    
    # Training data subcommand
    training_parser = subparsers.add_parser('training', help='Manage training data')
    training_subparsers = training_parser.add_subparsers(dest='training_command', help='Training data commands')
    
    # Copy training data
    copy_parser = training_subparsers.add_parser('copy', help='Copy a good game run to training data')
    copy_parser.add_argument('log_dir', nargs='?', help='Path to log directory to copy (optional - uses latest if not provided)')
    copy_parser.add_argument('-n', '--name', help='Custom name for the training run')
    
    # Process training data
    process_parser = training_subparsers.add_parser('process', help='Process training data')
    process_parser.add_argument('raw_dir', nargs='?', help='Specific raw directory to process (optional)')
    process_parser.add_argument('-n', '--name', help='Custom name for the processed run')
    
    # List training runs
    training_subparsers.add_parser('list', help='List available training runs')
    
    # Show training stats
    training_subparsers.add_parser('stats', help='Show training data statistics')
    
    # Publish to published
    publish_parser = training_subparsers.add_parser('publish', help='Publish processed data to published folder')
    publish_parser.add_argument('processed_dir', nargs='?', help='Specific processed directory to publish (optional - uses latest if not provided)')
    publish_parser.add_argument('-n', '--name', help='Custom name for the published run')
    publish_parser.add_argument('-f', '--force', action='store_true', help='Force overwrite existing published data')
    
    # Legacy support - if no subcommand, assume config analysis
    # Note: Arguments are already defined above for the config subcommand
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.0.1'
    )
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)
    
    # Handle different commands
    if args.command == 'training':
        handle_training_command(args)
    else:
        # Default to config analysis (legacy support)
        handle_config_command(args)


def handle_config_command(args):
    """Handle configuration analysis commands"""
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file '{args.config}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration
    print(f"Loading configuration from: {args.config}")
    print()
    
    config = load_config(args.config)
    
    # Handle validation if requested
    if args.validate:
        print("Validating configuration through Pydantic models...")
        try:
            # Check if this is a v2 config
            if isinstance(config, dict):
                is_v2_config = ('entity_definitions' in config and config['entity_definitions']) or \
                              ('action_definitions' in config and config['action_definitions'])
            else:
                # Check if it's a V2GameConfig object
                is_v2_config = hasattr(config, 'entity_definitions') or hasattr(config, 'action_definitions')
            
            if is_v2_config:
                # Use v2 validation
                from motive.sim_v2.v2_config_validator import validate_v2_config
                if isinstance(config, dict):
                    validated_config = validate_v2_config(config)
                else:
                    # Already a V2GameConfig object, no need to re-validate
                    validated_config = config
                print("V2 configuration validation successful!")
            else:
                # Use v1 validation
                from motive.config_validator import validate_merged_config
                if isinstance(config, dict):
                    validated_config = validate_merged_config(config)
                else:
                    # Already a GameConfig object, no need to re-validate
                    validated_config = config
                print("V1 configuration validation successful!")
            print()
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            if hasattr(e, 'validation_errors') and e.validation_errors:
                print("Validation errors:")
                for error in e.validation_errors:
                    print(f"  - {error}")
            sys.exit(1)
    
    # Handle raw config output
    if args.raw_config:
        show_raw_config(config, 'yaml')
        return  # Don't show other information when outputting raw config
    
    if args.raw_config_json:
        show_raw_config(config, 'json')
        return  # Don't show other information when outputting raw config
    
    # Show summary by default
    show_summary(config)
    
    # Show specific sections based on arguments
    if args.all or args.actions:
        show_actions(config)
    
    if args.all or args.objects:
        show_objects(config)
    
    if args.all or args.rooms:
        show_rooms(config)
    
    if args.all or args.characters:
        show_characters(config)
    
    if args.entities:
        entity_type = None if args.entities == 'all' else args.entities
        show_entities(config, entity_type)
    
    if args.debug_loading:
        debug_config_loading(args.config)
    
    if args.debug_motives:
        character_id = None if args.debug_motives == 'all' else args.debug_motives
        debug_character_motives(args.config, character_id)
    
    if args.debug_aliases:
        object_id = None if args.debug_aliases == 'all' else args.debug_aliases
        debug_action_aliases(args.config, object_id)
    
    if args.all or args.includes:
        show_includes(config, args.config)
    
    # If no specific options were provided, show actions by default
    if not any([args.all, args.actions, args.objects, args.rooms, args.characters, args.entities, args.debug_loading, args.debug_motives, args.includes]):
        show_actions(config)


def handle_training_command(args):
    """Handle training data management commands"""
    if args.training_command == 'copy':
        success = copy_good_run(args.log_dir, args.name)
        sys.exit(0 if success else 1)
    elif args.training_command == 'process':
        success = process_training_data(args.raw_dir, args.name)
        sys.exit(0 if success else 1)
    elif args.training_command == 'list':
        list_training_runs()
    elif args.training_command == 'stats':
        show_training_stats()
    elif args.training_command == 'publish':
        success = publish_to_sample(args.processed_dir, args.name, args.force)
        sys.exit(0 if success else 1)
    else:
        print("Error: No training command specified. Use 'motive-util training --help' for options.")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    util_main()


if __name__ == '__main__':
    main()
