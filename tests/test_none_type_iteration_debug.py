#!/usr/bin/env python3
"""Debug test for NoneType iteration issue in v2→v1 conversion."""

import pytest
from unittest.mock import patch, Mock

from motive.cli import load_config


class TestNoneTypeIterationDebug:
    """Debug the NoneType iteration issue."""

    def test_identify_none_type_iteration_issue(self):
        """Identify what object is None when it should be iterable."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        # Check all the main collections that should be iterable
        print(f"Actions: {len(game_config.actions)}")
        print(f"Rooms: {len(game_config.rooms)}")
        print(f"Object types: {len(game_config.object_types)}")
        print(f"Character types: {len(game_config.character_types)}")
        print(f"Characters: {len(game_config.characters)}")
        print(f"Players: {len(game_config.players)}")
        
        # Check if any of these are None
        assert game_config.actions is not None, "actions is None"
        assert game_config.rooms is not None, "rooms is None"
        assert game_config.object_types is not None, "object_types is None"
        assert game_config.character_types is not None, "character_types is None"
        assert game_config.characters is not None, "characters is None"
        assert game_config.players is not None, "players is None"
        
        # Check individual objects for None values
        for action_id, action in game_config.actions.items():
            assert action.parameters is not None, f"Action {action_id} parameters is None"
            assert action.requirements is not None, f"Action {action_id} requirements is None"
            assert action.effects is not None, f"Action {action_id} effects is None"
            
            # Check if these are actually lists
            assert isinstance(action.parameters, list), f"Action {action_id} parameters is not a list: {type(action.parameters)}"
            assert isinstance(action.requirements, list), f"Action {action_id} requirements is not a list: {type(action.requirements)}"
            assert isinstance(action.effects, list), f"Action {action_id} effects is not a list: {type(action.effects)}"
        
        # Check room properties
        for room_id, room in game_config.rooms.items():
            assert room.exits is not None, f"Room {room_id} exits is None"
            assert room.objects is not None, f"Room {room_id} objects is None"
            assert room.tags is not None, f"Room {room_id} tags is None"
            assert room.properties is not None, f"Room {room_id} properties is None"
            
            # Check if these are actually the expected types
            assert isinstance(room.exits, dict), f"Room {room_id} exits is not a dict: {type(room.exits)}"
            assert isinstance(room.objects, dict), f"Room {room_id} objects is not a dict: {type(room.objects)}"
            assert isinstance(room.tags, list), f"Room {room_id} tags is not a list: {type(room.tags)}"
            assert isinstance(room.properties, dict), f"Room {room_id} properties is not a dict: {type(room.properties)}"
        
        # Check object properties
        for obj_id, obj_type in game_config.object_types.items():
            assert obj_type.properties is not None, f"Object {obj_id} properties is None"
            assert isinstance(obj_type.properties, dict), f"Object {obj_id} properties is not a dict: {type(obj_type.properties)}"
        
        # Check character properties
        for char_id, char_type in game_config.character_types.items():
            assert char_type.motives is not None or char_type.motives is None, f"Character {char_id} motives is invalid"
            assert char_type.aliases is not None, f"Character {char_id} aliases is None"
            assert char_type.initial_rooms is not None or char_type.initial_rooms is None, f"Character {char_id} initial_rooms is invalid"
            
            # Check if these are actually the expected types
            assert isinstance(char_type.aliases, list), f"Character {char_id} aliases is not a list: {type(char_type.aliases)}"
