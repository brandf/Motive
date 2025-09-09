#!/usr/bin/env python3
"""
Motive Configuration Analysis Tool
Analyzes game configurations and provides summaries of available actions, objects, etc.
"""

import argparse
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and parse a YAML configuration file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}", file=sys.stderr)
        sys.exit(1)


def show_summary(config: Dict[str, Any]) -> None:
    """Display a summary of the configuration."""
    print("Configuration Summary:")
    print("=====================")
    
    action_count = len(config.get('actions', {}))
    object_count = len(config.get('object_types', {}))
    room_count = len(config.get('rooms', {}))
    character_count = len(config.get('character_types', {}))
    
    print(f"Actions: {action_count}")
    print(f"Objects: {object_count}")
    print(f"Rooms: {room_count}")
    print(f"Characters: {character_count}")
    print()


def show_actions(config: Dict[str, Any]) -> None:
    """Display available actions."""
    print("Available Actions:")
    print("=================")
    
    actions = config.get('actions', {})
    if not actions:
        print("No actions found in this configuration.")
        return
    
    for action_name in sorted(actions.keys()):
        action = actions[action_name]
        
        # Handle cost (can be int or dict with value)
        cost = action.get('cost', 0)
        if isinstance(cost, dict):
            cost = cost.get('value', cost.get('cost', 0))
        
        category = f" ({action.get('category', 'uncategorized')})" if action.get('category') else ""
        
        print(f"- {action.get('name', action_name)}: {action.get('description', 'No description')}")
        print(f"  Cost: {cost} AP{category}")
        
        # Show parameters
        params = action.get('parameters', [])
        if params:
            param_list = [p.get('name', 'unnamed') for p in params]
            print(f"  Parameters: {', '.join(param_list)}")
        
        # Show requirements
        requirements = action.get('requirements', [])
        if requirements:
            req_list = [r.get('type', 'unknown') for r in requirements]
            print(f"  Requirements: {', '.join(req_list)}")
        
        print()


def show_objects(config: Dict[str, Any]) -> None:
    """Display available objects."""
    print("Available Objects:")
    print("=================")
    
    objects = config.get('object_types', {})
    if not objects:
        print("No objects found in this configuration.")
        return
    
    for object_name in sorted(objects.keys()):
        obj = objects[object_name]
        print(f"- {obj.get('name', object_name)}: {obj.get('description', 'No description')}")
        
        # Show tags
        tags = obj.get('tags', [])
        if tags:
            print(f"  Tags: {', '.join(tags)}")
        
        # Show properties
        properties = obj.get('properties', {})
        if properties:
            prop_list = [f"{k}: {v}" for k, v in properties.items()]
            print(f"  Properties: {', '.join(prop_list)}")
        
        print()


def show_rooms(config: Dict[str, Any]) -> None:
    """Display available rooms."""
    print("Available Rooms:")
    print("===============")
    
    rooms = config.get('rooms', {})
    if not rooms:
        print("No rooms found in this configuration.")
        return
    
    for room_name in sorted(rooms.keys()):
        room = rooms[room_name]
        print(f"- {room.get('name', room_name)}: {room.get('description', 'No description')}")
        
        # Show exits
        exits = room.get('exits', {})
        if exits:
            exit_list = [f"{name} -> {exit_info.get('destination_room_id', 'unknown')}" 
                        for name, exit_info in exits.items()]
            print(f"  Exits: {', '.join(exit_list)}")
        
        # Show objects
        objects = room.get('objects', {})
        if objects:
            obj_list = [obj.get('name', name) for name, obj in objects.items()]
            print(f"  Objects: {', '.join(obj_list)}")
        
        print()


def show_characters(config: Dict[str, Any]) -> None:
    """Display available characters."""
    print("Available Characters:")
    print("===================")
    
    characters = config.get('character_types', {})
    if not characters:
        print("No characters found in this configuration.")
        return
    
    for char_name in sorted(characters.keys()):
        char = characters[char_name]
        print(f"- {char.get('name', char_name)}: {char.get('backstory', 'No backstory')}")
        print(f"  Motive: {char.get('motive', 'No motive')}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Motive game configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze-configs.py -a                    # Show all information
  python analyze-configs.py -c configs/core.yaml -A # Show actions from core config
  python analyze-configs.py -c configs/themes/fantasy/fantasy.yaml -O # Show objects from fantasy theme
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='configs/core.yaml',
        help='Path to configuration file (default: configs/core.yaml)'
    )
    
    parser.add_argument(
        '-A', '--actions',
        action='store_true',
        help='Show available actions'
    )
    
    parser.add_argument(
        '-O', '--objects',
        action='store_true',
        help='Show available objects'
    )
    
    parser.add_argument(
        '-R', '--rooms',
        action='store_true',
        help='Show available rooms'
    )
    
    parser.add_argument(
        '-C', '--characters',
        action='store_true',
        help='Show available characters'
    )
    
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Show all available information'
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file '{args.config}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration
    print(f"Loading configuration from: {args.config}")
    print()
    
    config = load_config(args.config)
    
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
    
    # If no specific options were provided, show actions by default
    if not any([args.all, args.actions, args.objects, args.rooms, args.characters]):
        show_actions(config)


if __name__ == '__main__':
    main()
