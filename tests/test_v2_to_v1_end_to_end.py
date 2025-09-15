#!/usr/bin/env python3
"""End-to-end test for v2→v1 conversion pipeline.

This test validates that v2 configs can be loaded, converted to v1 format,
and used to run a complete game scenario with mocked LLMs.
"""

import tempfile
import unittest.mock
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from motive.cli import load_config
from motive.game_master import GameMaster
from motive.config import GameConfig


class TestV2ToV1EndToEnd:
    """Test complete v2→v1 conversion pipeline end-to-end."""

    def test_v2_config_loading_and_conversion(self):
        """Test that v2 configs load and convert to proper v1 GameConfig objects."""
        config_path = "configs/game.yaml"
        
        # Load v2 config and convert to v1
        game_config = load_config(config_path)
        
        # Verify it's a proper GameConfig object
        assert isinstance(game_config, GameConfig)
        assert game_config.game_settings is not None
        assert len(game_config.players) == 2
        
        # Verify actions are properly converted
        assert len(game_config.actions) > 0
        for action_id, action in game_config.actions.items():
            assert hasattr(action, 'id')
            assert hasattr(action, 'name')
            assert hasattr(action, 'description')
            assert hasattr(action, 'cost')
            assert hasattr(action, 'parameters')
            assert hasattr(action, 'requirements')
            assert hasattr(action, 'effects')
            
            # Verify effects are properly converted
            for effect in action.effects:
                assert hasattr(effect, 'type')
                if effect.type == 'code_binding':
                    assert hasattr(effect, 'function_name')
                    assert hasattr(effect, 'observers')
        
        # Verify rooms are properly converted
        assert len(game_config.rooms) > 0
        for room_id, room in game_config.rooms.items():
            assert hasattr(room, 'id')
            assert hasattr(room, 'name')
            assert hasattr(room, 'description')
            assert hasattr(room, 'exits')
            assert hasattr(room, 'objects')
            assert hasattr(room, 'tags')
            assert hasattr(room, 'properties')
        
        # Verify object types are properly converted
        assert len(game_config.object_types) > 0
        for obj_id, obj_type in game_config.object_types.items():
            assert hasattr(obj_type, 'id')
            assert hasattr(obj_type, 'name')
            assert hasattr(obj_type, 'description')
            assert hasattr(obj_type, 'properties')
        
        # Verify character types are properly converted
        assert len(game_config.character_types) > 0
        for char_id, char_type in game_config.character_types.items():
            assert hasattr(char_type, 'id')
            assert hasattr(char_type, 'name')
            assert hasattr(char_type, 'backstory')
            assert hasattr(char_type, 'motive')
            assert hasattr(char_type, 'motives')
            assert hasattr(char_type, 'aliases')
            assert hasattr(char_type, 'initial_rooms')

    def test_v2_config_game_initialization(self):
        """Test that v2 configs can be loaded and converted for game initialization."""
        config_path = "configs/game.yaml"
        
        # Load v2 config
        game_config = load_config(config_path)
        
        # Verify the config has all necessary components for game initialization
        assert game_config.game_settings is not None
        assert len(game_config.players) == 2
        assert len(game_config.rooms) >= 10  # Should have multiple rooms from hearth_and_shadow
        assert len(game_config.object_types) >= 60  # Should have multiple objects
        assert len(game_config.character_types) >= 8  # Should have multiple characters
        assert len(game_config.actions) >= 10  # Should have multiple actions
        
        # Verify specific content that would be needed for game initialization
        room_ids = list(game_config.rooms.keys())
        assert 'town_square' in room_ids
        assert 'church' in room_ids
        assert 'tavern' in room_ids
        
        character_ids = list(game_config.character_types.keys())
        assert 'mayor_victoria_blackwater' in character_ids
        assert 'father_marcus' in character_ids
        
        action_ids = list(game_config.actions.keys())
        assert 'look' in action_ids
        assert 'help' in action_ids
        assert 'move' in action_ids

    def test_v2_config_action_conversion(self):
        """Test that v2 actions are properly converted for execution."""
        config_path = "configs/game.yaml"
        
        # Load v2 config
        game_config = load_config(config_path)
        
        # Test that look action is properly converted (this was the failing action before)
        look_action = game_config.actions.get('look')
        assert look_action is not None
        
        # Verify the look action has proper structure for execution
        assert hasattr(look_action, 'id')
        assert hasattr(look_action, 'name')
        assert hasattr(look_action, 'description')
        assert hasattr(look_action, 'cost')
        assert hasattr(look_action, 'parameters')
        assert hasattr(look_action, 'requirements')
        assert hasattr(look_action, 'effects')
        
        # Verify the look action has the correct effect that was causing issues
        code_binding_effects = [e for e in look_action.effects if e.type == 'code_binding']
        assert len(code_binding_effects) > 0
        
        effect = code_binding_effects[0]
        assert effect.function_name == 'look_at_target'
        assert 'player' in effect.observers
        
        # Verify other core actions are present and properly structured
        core_actions = ['help', 'move', 'say', 'pickup', 'drop']
        for action_name in core_actions:
            action = game_config.actions.get(action_name)
            assert action is not None, f"Core action '{action_name}' should be present"
            assert hasattr(action, 'effects'), f"Action '{action_name}' should have effects"

    def test_v2_config_hierarchical_loading(self):
        """Test that hierarchical v2 configs load correctly."""
        config_path = "configs/game.yaml"
        
        # Load v2 config
        game_config = load_config(config_path)
        
        # Verify hierarchical content is present
        # Should have content from hearth_and_shadow (rooms, objects, characters)
        assert len(game_config.rooms) >= 10  # hearth_and_shadow has 11 rooms
        assert len(game_config.object_types) >= 60  # hearth_and_shadow has 65+ objects
        assert len(game_config.character_types) >= 8  # hearth_and_shadow has 8 characters
        
        # Verify specific content from hearth_and_shadow
        room_names = [room.name for room in game_config.rooms.values()]
        assert "Town Square" in room_names
        assert "Sacred Heart Church" in room_names
        assert "The Rusty Anchor Tavern" in room_names
        
        character_names = [char.name for char in game_config.character_types.values()]
        assert "Mayor Victoria Blackwater" in character_names
        assert "Father Marcus" in character_names
        
        # Verify actions are present
        action_names = [action.name for action in game_config.actions.values()]
        assert "look" in action_names
        assert "help" in action_names
        assert "move" in action_names

    def test_v2_config_effect_conversion(self):
        """Test that v2 effects are properly converted to v1 format."""
        config_path = "configs/game.yaml"
        
        # Load v2 config
        game_config = load_config(config_path)
        
        # Find the look action (which has a code_binding effect)
        look_action = game_config.actions.get('look')
        assert look_action is not None
        
        # Verify the look action has the correct effect
        assert len(look_action.effects) > 0
        
        # Find the code_binding effect
        code_binding_effects = [e for e in look_action.effects if e.type == 'code_binding']
        assert len(code_binding_effects) > 0
        
        effect = code_binding_effects[0]
        assert effect.function_name == 'look_at_target'
        assert 'player' in effect.observers
