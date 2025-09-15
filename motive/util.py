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
import json
import sys
import shutil
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from motive.cli import load_config as cli_load_config
    HIERARCHICAL_SUPPORT = True
except ImportError:
    HIERARCHICAL_SUPPORT = False


def load_config(config_path: str) -> Dict[str, Any]:
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
            # Return the GameConfig object directly - the util functions will handle it
            return game_config
        else:
            # Traditional config loading
            return raw_config
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}", file=sys.stderr)
        sys.exit(1)


def show_raw_config(config: Dict[str, Any], format_type: str = 'yaml') -> None:
    """Output the raw merged configuration."""
    print(f"Merged Configuration ({format_type.upper()}):")
    print("=" * 50)
    
    if format_type == 'json':
        print(json.dumps(config, indent=2, default=str))
    else:  # yaml
        print(yaml.dump(config, default_flow_style=False, sort_keys=False))
    
    print()


def show_summary(config) -> None:
    """Display a summary of the configuration."""
    print("Configuration Summary:")
    print("=====================")
    
    # Handle both dict configs (v1) and GameConfig objects (v2)
    if hasattr(config, 'actions'):
        # GameConfig object (v2)
        action_count = len(config.actions)
        object_count = len(config.object_types)
        room_count = len(config.rooms)
        character_count = len(config.character_types)
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
    
    # Handle both dict configs (v1) and GameConfig objects (v2)
    if hasattr(config, 'actions'):
        # GameConfig object (v2)
        actions = config.actions
    else:
        # Dictionary config (v1)
        actions = config.get('actions', {})
    
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
    
    # Handle both dict configs (v1) and GameConfig objects (v2)
    if hasattr(config, 'characters'):
        # GameConfig object (v2) - use character_types
        characters = config.character_types
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
        
        # Handle both dict and Pydantic objects
        if hasattr(char, 'name'):
            # Pydantic object (v2)
            name = char.name
            backstory = char.backstory
        else:
            # Dictionary object (v1)
            name = char.get('name', char_name)
            backstory = char.get('backstory', 'No backstory')
        
        print(f"- {name}: {backstory}")
        
        # Handle both legacy single motive and new multiple motives
        if hasattr(char, 'motives') and char.motives:
            motives = char.motives
            if isinstance(motives, list) and len(motives) > 0:
                print(f"  Motives: {len(motives)} available")
                for i, motive in enumerate(motives, 1):
                    motive_desc = motive.get('description', 'No description') if isinstance(motive, dict) else str(motive)
                    print(f"    {i}. {motive_desc}")
            else:
                print(f"  Motive: No motive")
        elif hasattr(char, 'motive') and char.motive:
            print(f"  Motive: {char.motive}")
        elif 'motives' in char and char['motives']:
            motives = char['motives']
            if isinstance(motives, list) and len(motives) > 0:
                print(f"  Motives: {len(motives)} available")
                for i, motive in enumerate(motives, 1):
                    motive_desc = motive.get('description', 'No description') if isinstance(motive, dict) else str(motive)
                    print(f"    {i}. {motive_desc}")
            else:
                print(f"  Motive: No motive")
        elif 'motive' in char:
            print(f"  Motive: {char.get('motive', 'No motive')}")
        else:
            print(f"  Motive: No motive")
        print()


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
            from motive.config_validator import validate_merged_config
            validated_config = validate_merged_config(config)
            print("Configuration validation successful!")
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
    
    if args.all or args.includes:
        show_includes(config, args.config)
    
    # If no specific options were provided, show actions by default
    if not any([args.all, args.actions, args.objects, args.rooms, args.characters, args.includes]):
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
