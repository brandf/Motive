"""
Test v2 entity definition conversion to v1 config objects.

This test ensures that v2 entity definitions are properly converted to v1
ObjectTypeConfig and CharacterConfig objects with correct field mapping.
"""

import pytest
from motive.config import ObjectTypeConfig, CharacterConfig
from motive.game_initializer import GameInitializer
from unittest.mock import MagicMock
import tempfile


def test_v2_object_entity_conversion():
    """Test that v2 object entity definitions convert to ObjectTypeConfig correctly."""
    
    # Create a mock v2 config with entity_definitions
    v2_config_data = {
        'entity_definitions': {
            'torch': {
                'behaviors': ['object'],
                'properties': {
                    'name': 'Torch',
                    'description': 'A burning torch that provides light',
                    'portable': True,
                    'size': 'medium',
                    'is_lit': True
                }
            }
        }
    }
    
    # Create GameInitializer with mock config
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_logger = MagicMock()
        initializer = GameInitializer(v2_config_data, "test_game", mock_logger)
        
        # Load configurations
        initializer._load_configurations()
        
        # Verify torch was converted to ObjectTypeConfig
        assert 'torch' in initializer.game_object_types
        torch_config = initializer.game_object_types['torch']
        
        # Verify required fields are present
        assert isinstance(torch_config, ObjectTypeConfig)
        assert torch_config.id == 'torch'
        assert torch_config.name == 'Torch'
        assert torch_config.description == 'A burning torch that provides light'


def test_v2_character_entity_conversion():
    """Test that v2 character entity definitions convert to CharacterConfig correctly."""
    
    # Create a mock v2 config with character entity definitions
    v2_config_data = {
        'entity_definitions': {
            'detective': {
                'behaviors': ['character'],
                'properties': {
                    'name': 'Detective James Thorne',
                    'backstory': 'A skilled investigator with a troubled past',
                    'investigative': True,
                    'reputation': 'respected'
                }
            }
        }
    }
    
    # Create GameInitializer with mock config
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_logger = MagicMock()
        initializer = GameInitializer(v2_config_data, "test_game", mock_logger)
        
        # Load configurations
        initializer._load_configurations()
        
        # Verify detective was converted to CharacterConfig
        assert 'detective' in initializer.game_character_types
        detective_config = initializer.game_character_types['detective']
        
        # Verify required fields are present
        assert isinstance(detective_config, CharacterConfig)
        assert detective_config.id == 'detective'
        assert detective_config.name == 'Detective James Thorne'
        assert detective_config.backstory == 'A skilled investigator with a troubled past'
