#!/usr/bin/env python3
"""Integration test for v2→v1 config conversion - validates entire pipeline."""

import pytest
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path

from motive.cli import load_config
from motive.config import GameConfig, ActionConfig, RoomConfig, ObjectTypeConfig, CharacterConfig


class TestV2ToV1ConversionIntegration:
    """Test that v2 configs convert properly to v1 format with correct Pydantic objects."""

    def test_v2_config_conversion_creates_valid_pydantic_objects(self):
        """Test that v2 config conversion creates proper Pydantic objects."""
        config_path = "configs/game.yaml"
        
        # Load v2 config and convert to v1
        game_config = load_config(config_path)
        
        # Verify it's a proper GameConfig object
        assert isinstance(game_config, GameConfig)
        assert game_config.game_settings is not None
        assert len(game_config.players) == 2
        
        # Verify actions are proper ActionConfig objects
        assert len(game_config.actions) > 0
        for action_id, action in game_config.actions.items():
            assert isinstance(action, ActionConfig), f"Action {action_id} is not ActionConfig: {type(action)}"
            
            # Verify action has proper attributes
            assert hasattr(action, 'id')
            assert hasattr(action, 'name')
            assert hasattr(action, 'cost')
            assert hasattr(action, 'parameters')
            assert hasattr(action, 'requirements')
            assert hasattr(action, 'effects')
            
            # Test that cost can be accessed (this was the failing point)
            if hasattr(action.cost, 'type'):
                # Complex cost object
                assert action.cost.type in ['static', 'code_binding']
            else:
                # Simple numeric cost
                assert isinstance(action.cost, int)
            
            # Test that parameters have proper structure
            for param in action.parameters:
                assert hasattr(param, 'name')
                assert hasattr(param, 'type')
                assert hasattr(param, 'description')
        
        # Verify rooms are proper RoomConfig objects
        assert len(game_config.rooms) > 0
        for room_id, room in game_config.rooms.items():
            assert isinstance(room, RoomConfig), f"Room {room_id} is not RoomConfig: {type(room)}"
            assert hasattr(room, 'id')
            assert hasattr(room, 'name')
            assert hasattr(room, 'description')
        
        # Verify object types are proper ObjectTypeConfig objects
        assert len(game_config.object_types) > 0
        for obj_id, obj_type in game_config.object_types.items():
            assert isinstance(obj_type, ObjectTypeConfig), f"Object {obj_id} is not ObjectTypeConfig: {type(obj_type)}"
            assert hasattr(obj_type, 'id')
            assert hasattr(obj_type, 'name')
            assert hasattr(obj_type, 'description')
        
        # Verify character types are proper CharacterConfig objects
        assert len(game_config.character_types) > 0
        for char_id, char_type in game_config.character_types.items():
            assert isinstance(char_type, CharacterConfig), f"Character {char_id} is not CharacterConfig: {type(char_type)}"
            assert hasattr(char_type, 'id')
            assert hasattr(char_type, 'name')
            assert hasattr(char_type, 'backstory')

    def test_action_cost_processing_with_mocked_game_master(self):
        """Test that action cost processing works with mocked GameMaster."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        # Mock GameMaster components
        with patch('motive.game_master.GameMaster') as mock_gm_class:
            mock_gm = Mock()
            mock_gm_class.return_value = mock_gm
            
            # Test action cost calculation for different action types
            for action_id, action in game_config.actions.items():
                # This should not raise 'dict' object has no attribute 'type'
                try:
                    if hasattr(action.cost, 'type'):
                        if action.cost.type == 'code_binding':
                            # Test code_binding cost
                            assert action.cost.function_name is not None
                        elif action.cost.type == 'static':
                            # Test static cost
                            assert action.cost.value is not None
                    else:
                        # Test simple numeric cost (pass action has cost -1, which is valid)
                        assert isinstance(action.cost, int)
                        assert action.cost >= -1  # Allow -1 for pass action
                except AttributeError as e:
                    pytest.fail(f"Action {action_id} cost processing failed: {e}")

    def test_parameter_processing_with_mocked_game_master(self):
        """Test that action parameter processing works correctly."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        # Test parameter processing for each action
        for action_id, action in game_config.actions.items():
            for param in action.parameters:
                # This should not raise any attribute errors
                try:
                    assert param.name is not None
                    assert param.type is not None
                    assert param.description is not None
                except AttributeError as e:
                    pytest.fail(f"Action {action_id} parameter processing failed: {e}")

    def test_effects_processing_with_mocked_game_master(self):
        """Test that action effects processing works correctly."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        # Test effects processing for each action
        for action_id, action in game_config.actions.items():
            for effect in action.effects:
                # This should not raise any attribute errors
                try:
                    assert hasattr(effect, 'type')
                    assert effect.type is not None
                except AttributeError as e:
                    pytest.fail(f"Action {action_id} effect processing failed: {e}")

    def test_requirements_processing_with_mocked_game_master(self):
        """Test that action requirements processing works correctly."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        # Test requirements processing for each action
        for action_id, action in game_config.actions.items():
            for req in action.requirements:
                # This should not raise any attribute errors
                try:
                    assert hasattr(req, 'type')
                    assert req.type is not None
                except AttributeError as e:
                    pytest.fail(f"Action {action_id} requirement processing failed: {e}")

    @pytest.mark.skip(reason="LLM mocking issues - needs different approach")
    def test_full_game_initialization_with_mocked_llms(self):
        """Test that GameMaster can initialize with converted v2 configs."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('motive.llm_factory.create_llm_client') as mock_create_llm:
                mock_llm = Mock()
                mock_create_llm.return_value = mock_llm
                
                # This should not raise any conversion errors
                try:
                    from motive.game_master import GameMaster
                    gm = GameMaster(
                        game_config=game_config,
                        game_id="conversion_test",
                        log_dir=temp_dir,
                        deterministic=True
                    )
                    
                    # Verify initialization succeeded
                    assert gm.rooms is not None
                    assert len(gm.rooms) > 0
                    assert len(gm.game_object_types) > 0
                    assert len(gm.game_character_types) > 0
                    assert len(gm.game_actions) > 0
                    
                    # Clean up log handlers
                    for handler in gm.game_logger.handlers[:]:
                        handler.close()
                        gm.game_logger.removeHandler(handler)
                        
                except Exception as e:
                    pytest.fail(f"GameMaster initialization failed: {e}")

    def test_specific_actions_that_were_failing(self):
        """Test specific actions that were causing issues in CLI runs."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        # Test help action specifically (was causing the .type error)
        if 'help' in game_config.actions:
            help_action = game_config.actions['help']
            assert isinstance(help_action, ActionConfig)
            
            # Test cost processing
            if hasattr(help_action.cost, 'type'):
                assert help_action.cost.type == 'code_binding'
                assert help_action.cost.function_name == 'calculate_help_cost'
                assert help_action.cost.value == 1
            
            # Test parameters
            for param in help_action.parameters:
                assert hasattr(param, 'name')
                assert hasattr(param, 'type')
                assert hasattr(param, 'description')
        
        # Test look action specifically
        if 'look' in game_config.actions:
            look_action = game_config.actions['look']
            assert isinstance(look_action, ActionConfig)
            
            # Test cost processing
            if hasattr(look_action.cost, 'type'):
                assert look_action.cost.type == 'static'
            else:
                assert isinstance(look_action.cost, int)
                assert look_action.cost == 10
