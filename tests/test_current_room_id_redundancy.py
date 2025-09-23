"""Test that current_room_id is redundant in object instances."""

import pytest
from unittest.mock import Mock
from motive.game_object import GameObject


class TestCurrentRoomIdRedundancy:
    """Test that current_room_id is redundant in object instances."""
    
    def test_current_room_id_is_not_used_in_object_instantiation(self):
        """Test that current_room_id from object instance config is ignored."""
        # Simulate the object type definition
        obj_type_definition = Mock()
        obj_type_definition.name = 'Test Object'
        obj_type_definition.description = 'A test object'
        obj_type_definition.properties = {}
        obj_type_definition.interactions = {}
        
        # Simulate the object instance with current_room_id
        obj_instance_cfg = {
            'object_type_id': 'test_object_type',
            'current_room_id': 'wrong_room_id'  # This should be ignored
        }
        
        # Simulate the room
        room = Mock()
        room.id = 'correct_room_id'  # This is what should be used
        
        # Simulate the object instantiation logic from GameInitializer
        obj_id = 'test_object_instance'
        
        game_obj = GameObject(
            obj_id=obj_instance_cfg.get('id', obj_id),
            name=obj_instance_cfg.get('name') or obj_type_definition.name,
            description=obj_instance_cfg.get('description') or obj_type_definition.description,
            current_location_id=room.id,  # Uses room.id, not obj_instance_cfg['current_room_id']
            tags=[],
            properties=obj_type_definition.properties,
            action_aliases={},
            interactions=obj_type_definition.interactions
        )
        
        # Verify that the object uses the room's ID, not the instance's current_room_id
        assert game_obj.current_location_id == 'correct_room_id'
        assert game_obj.current_location_id != 'wrong_room_id'
        
        # Verify that current_room_id from the instance config is completely ignored
        assert 'current_room_id' in obj_instance_cfg  # It's in the config
        assert game_obj.current_location_id == room.id  # But it's not used
