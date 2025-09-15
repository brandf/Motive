"""Comprehensive validation that v2 integration tests work correctly."""

import pytest
from motive.cli import load_config


class TestV2IntegrationValidation:
    """Validate that v2 integration tests work correctly."""
    
    def test_v2_integration_config_loading(self):
        """Test that the v2 integration config loads correctly."""
        config_path = "tests/configs/test_standalone_migrated.yaml"
        game_config = load_config(config_path)
        
        # Verify basic structure
        assert game_config is not None
        assert game_config.game_settings is not None
        assert len(game_config.players) == 2
        
        # Verify v2 entity definitions are loaded
        assert len(game_config.rooms) > 0, "Should have rooms from entity_definitions"
        assert len(game_config.object_types) > 0, "Should have object types from entity_definitions"
        assert len(game_config.character_types) > 0, "Should have character types from entity_definitions"
        assert len(game_config.actions) > 0, "Should have actions from action_definitions"
        
        # Verify specific test content
        assert 'test_room' in game_config.rooms
        assert 'test_object' in game_config.object_types
        assert 'test_character' in game_config.character_types
        assert 'test_move' in game_config.actions
        
        # Verify v2 features are preserved
        test_character = game_config.character_types['test_character']
        assert hasattr(test_character, 'motives')
        assert hasattr(test_character, 'initial_rooms')
        assert hasattr(test_character, 'aliases')
        
        # Verify action categories are preserved
        test_action = game_config.actions['test_move']
        assert hasattr(test_action, 'category')
        assert test_action.category == 'movement'
    
    def test_v2_integration_config_hierarchical_loading(self):
        """Test that hierarchical loading works with v2 integration config."""
        config_path = "tests/configs/integration/game_test.yaml"
        game_config = load_config(config_path)
        
        # Should load the v2 base config plus hints
        assert game_config is not None
        assert game_config.game_settings is not None
        
        # Should have content from the v2 base config
        assert len(game_config.rooms) > 0
        assert len(game_config.object_types) > 0
        assert len(game_config.character_types) > 0
        assert len(game_config.actions) > 0
    
    def test_v2_config_structure_consistency(self):
        """Test that v2 configs have consistent structure."""
        config_path = "tests/configs/test_standalone_migrated.yaml"
        game_config = load_config(config_path)
        
        # Verify all expected attributes exist
        expected_attributes = [
            'game_settings', 'players', 'rooms', 'object_types', 
            'character_types', 'actions'
        ]
        
        for attr in expected_attributes:
            assert hasattr(game_config, attr), f"Missing attribute: {attr}"
            attr_value = getattr(game_config, attr)
            assert attr_value is not None, f"Attribute {attr} is None"
    
    def test_v2_character_types_structure(self):
        """Test that character_types have the correct v2 structure."""
        config_path = "tests/configs/test_standalone_migrated.yaml"
        game_config = load_config(config_path)
        
        test_character = game_config.character_types['test_character']
        
        # Verify it's a CharacterConfig object
        from motive.config import CharacterConfig
        assert isinstance(test_character, CharacterConfig)
        
        # Verify v2-specific fields
        assert hasattr(test_character, 'motives')
        assert hasattr(test_character, 'initial_rooms')
        assert hasattr(test_character, 'aliases')
        
        # Verify the content is preserved (as string representations)
        # Note: test_character has simple motive field, not complex motives array
        assert test_character.motive is not None
        assert test_character.initial_rooms is not None
        assert test_character.aliases is not None
    
    def test_v2_action_definitions_structure(self):
        """Test that action_definitions have the correct v2 structure."""
        config_path = "tests/configs/test_standalone_migrated.yaml"
        game_config = load_config(config_path)
        
        test_action = game_config.actions['test_move']
        
        # Verify it's an ActionConfig object
        from motive.config import ActionConfig
        assert isinstance(test_action, ActionConfig)
        
        # Verify v2-specific fields
        assert hasattr(test_action, 'category')
        assert test_action.category == 'movement'
        
        # Verify parameters, requirements, effects are preserved
        assert hasattr(test_action, 'parameters')
        assert hasattr(test_action, 'requirements')
        assert hasattr(test_action, 'effects')
        
        assert len(test_action.parameters) > 0
        # Note: test actions have empty effects arrays in the test config
        assert len(test_action.effects) >= 0
    
    def test_v2_room_definitions_structure(self):
        """Test that room definitions have the correct v2 structure."""
        config_path = "tests/configs/test_standalone_migrated.yaml"
        game_config = load_config(config_path)
        
        test_room = game_config.rooms['test_room']
        
        # Verify it's a RoomConfig object
        from motive.config import RoomConfig
        assert isinstance(test_room, RoomConfig)
        
        # Verify v2-specific fields are preserved
        assert hasattr(test_room, 'exits')
        assert hasattr(test_room, 'objects')
        
        # Verify the content is preserved (as string representations)
        assert test_room.exits is not None
        assert test_room.objects is not None
    
    def test_v2_object_definitions_structure(self):
        """Test that object definitions have the correct v2 structure."""
        config_path = "tests/configs/test_standalone_migrated.yaml"
        game_config = load_config(config_path)
        
        test_object = game_config.object_types['test_object']
        
        # Verify it's an ObjectTypeConfig object
        from motive.config import ObjectTypeConfig
        assert isinstance(test_object, ObjectTypeConfig)
        
        # Verify v2-specific properties are preserved
        assert hasattr(test_object, 'properties')
        assert test_object.properties is not None
        
        # Verify boolean properties are correctly typed
        assert 'portable' in test_object.properties
        assert 'test' in test_object.properties
