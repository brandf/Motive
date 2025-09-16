"""
Test v2 room entity definition conversion.

This test ensures that v2 room entity definitions are properly converted to v1 room format.
"""

import pytest
from motive.game_initializer import GameInitializer
from unittest.mock import MagicMock
import tempfile


def test_v2_room_entity_conversion():
    """Test that v2 room entity definitions are loaded into game_rooms."""
    
    # Create a mock v2 config with room entity definitions
    v2_config_data = {
        'entity_definitions': {
            'town_square': {
                'behaviors': ['room'],
                'properties': {
                    'name': 'Town Square',
                    'description': 'The heart of the town, bustling with activity.',
                    'exits': '{"tavern": {"id": "tavern", "destination_room_id": "tavern"}}',
                    'objects': '{"notice_board": {"id": "notice_board", "object_type_id": "notice_board"}}'
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
        
        
        # Verify town_square was loaded into game_rooms
        assert 'town_square' in initializer.game_rooms
        room_data = initializer.game_rooms['town_square']
        
        # Verify room data structure
        assert room_data['name'] == 'Town Square'
        assert room_data['description'] == 'The heart of the town, bustling with activity.'
        assert 'exits' in room_data
        assert 'objects' in room_data
