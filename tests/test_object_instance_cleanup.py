"""Test that object instances work correctly after cleanup of redundant fields."""

import pytest
import yaml
from unittest.mock import Mock
from motive.game_object import GameObject
from motive.room import Room


class TestObjectInstanceCleanup:
    """Test that object instances work correctly after cleanup of redundant fields."""
    
    def test_object_instantiation_logic_without_redundant_fields(self):
        """Test the core object instantiation logic with cleaned up object instances."""
        # Simulate the object type definition (from hearth_and_shadow_objects.yaml)
        obj_type_definition = Mock()
        obj_type_definition.name = 'Test Object'
        obj_type_definition.description = 'A test object for cleanup validation'
        obj_type_definition.properties = {'pickupable': True, 'size': 'small'}
        obj_type_definition.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'generate_event',
                        'message': '{{player_name}} examines the test object.',
                        'observers': ['room_characters']
                    }
                ]
            }
        }
        
        # Simulate the cleaned up object instance (from hearth_and_shadow_rooms.yaml)
        obj_instance_cfg = {
            # Only essential fields - no redundant name/description/id
            'object_type_id': 'test_object_type',
            'current_room_id': 'test_room'
        }
        
        # Simulate the room
        room = Mock()
        room.id = 'test_room'
        
        # Simulate the object instantiation logic from GameInitializer
        obj_id = 'test_object_instance'  # This would be the YAML key
        
        # This is the actual logic from GameInitializer._instantiate_rooms_and_objects
        game_obj = GameObject(
            obj_id=obj_instance_cfg.get('id', obj_id),  # Use instance id or fall back to key
            name=obj_instance_cfg.get('name') or obj_type_definition.name,  # Use instance name or fall back to type
            description=obj_instance_cfg.get('description') or obj_type_definition.description,  # Use instance description or fall back to type
            current_location_id=room.id,
            tags=[],
            properties=obj_type_definition.properties,
            action_aliases={},
            interactions=obj_type_definition.interactions
        )
        
        # Verify the object has the correct properties from the type definition
        assert game_obj.name == 'Test Object'  # Should come from object type
        assert game_obj.description == 'A test object for cleanup validation'  # Should come from object type
        assert game_obj.id == 'test_object_instance'  # Should use the YAML key since no explicit id
        assert game_obj.properties['pickupable'] == True
        assert game_obj.properties['size'] == 'small'
        
        # Verify interactions were inherited from object type
        assert 'look' in game_obj.interactions
        assert len(game_obj.interactions['look']['effects']) == 1
    
    def test_object_instance_with_overrides(self):
        """Test that object instances can still override type definitions when needed."""
        # Simulate the object type definition
        obj_type_definition = Mock()
        obj_type_definition.name = 'Generic Object'
        obj_type_definition.description = 'A generic object'
        obj_type_definition.properties = {'pickupable': True}
        obj_type_definition.interactions = {}
        
        # Simulate the object instance with overrides
        obj_instance_cfg = {
            'name': 'Special Object',  # Override name
            'description': 'This is a special instance with custom name and description',  # Override description
            'object_type_id': 'generic_object_type',
            'current_room_id': 'test_room',
            'properties': {
                'pickupable': False  # Override property
            }
        }
        
        # Simulate the room
        room = Mock()
        room.id = 'test_room'
        
        # Simulate the object instantiation logic
        obj_id = 'special_object'
        
        # Merge properties (instance overrides type)
        final_properties = {**obj_type_definition.properties, **obj_instance_cfg.get('properties', {})}
        
        game_obj = GameObject(
            obj_id=obj_instance_cfg.get('id', obj_id),
            name=obj_instance_cfg.get('name') or obj_type_definition.name,
            description=obj_instance_cfg.get('description') or obj_type_definition.description,
            current_location_id=room.id,
            tags=[],
            properties=final_properties,
            action_aliases={},
            interactions=obj_type_definition.interactions
        )
        
        # Verify overrides work correctly
        assert game_obj.name == 'Special Object'  # Should use instance override
        assert game_obj.description == 'This is a special instance with custom name and description'  # Should use instance override
        assert game_obj.properties['pickupable'] == False  # Should use instance override
    
    def test_object_instance_with_explicit_id(self):
        """Test that object instances can have explicit id fields when needed."""
        # Simulate the object type definition
        obj_type_definition = Mock()
        obj_type_definition.name = 'Test Object'
        obj_type_definition.description = 'A test object'
        obj_type_definition.properties = {}
        obj_type_definition.interactions = {}
        
        # Simulate the object instance with explicit id
        obj_instance_cfg = {
            'id': 'custom_object_id',  # Explicit id different from key
            'object_type_id': 'test_object_type',
            'current_room_id': 'test_room'
        }
        
        # Simulate the room
        room = Mock()
        room.id = 'test_room'
        
        # Simulate the object instantiation logic
        obj_id = 'object_with_explicit_id'  # This would be the YAML key
        
        game_obj = GameObject(
            obj_id=obj_instance_cfg.get('id', obj_id),  # Should use explicit id
            name=obj_instance_cfg.get('name') or obj_type_definition.name,
            description=obj_instance_cfg.get('description') or obj_type_definition.description,
            current_location_id=room.id,
            tags=[],
            properties=obj_type_definition.properties,
            action_aliases={},
            interactions=obj_type_definition.interactions
        )
        
        # Verify explicit id is used
        assert game_obj.id == 'custom_object_id'  # Should use explicit id
        assert game_obj.name == 'Test Object'  # Should come from object type
    
    def test_object_interactions_work_after_cleanup(self):
        """Test that object interactions still work after cleanup."""
        # Simulate the object type definition with interactions
        obj_type_definition = Mock()
        obj_type_definition.name = 'Interactive Object'
        obj_type_definition.description = 'An object with interactions'
        obj_type_definition.properties = {}
        obj_type_definition.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'test_property',
                        'value': True
                    },
                    {
                        'type': 'generate_event',
                        'message': '{{player_name}} examines the interactive object.',
                        'observers': ['room_characters']
                    }
                ]
            }
        }
        
        # Simulate the cleaned up object instance
        obj_instance_cfg = {
            # Clean instance with only essential fields
            'object_type_id': 'interactive_object_type',
            'current_room_id': 'test_room'
        }
        
        # Simulate the room
        room = Mock()
        room.id = 'test_room'
        
        # Simulate the object instantiation logic
        obj_id = 'clean_object'
        
        game_obj = GameObject(
            obj_id=obj_instance_cfg.get('id', obj_id),
            name=obj_instance_cfg.get('name') or obj_type_definition.name,
            description=obj_instance_cfg.get('description') or obj_type_definition.description,
            current_location_id=room.id,
            tags=[],
            properties=obj_type_definition.properties,
            action_aliases={},
            interactions=obj_type_definition.interactions
        )
        
        # Verify interactions were inherited correctly
        assert 'look' in game_obj.interactions
        look_effects = game_obj.interactions['look']['effects']
        
        # Find the set_property effect
        set_property_effect = None
        for effect in look_effects:
            if effect.get('type') == 'set_property' and effect.get('property') == 'test_property':
                set_property_effect = effect
                break
        
        assert set_property_effect is not None, "Should have set_property effect"
        assert set_property_effect['value'] == True, "Should set test_property to True"
        
        # Find the generate_event effect
        generate_event_effect = None
        for effect in look_effects:
            if effect.get('type') == 'generate_event':
                generate_event_effect = effect
                break
        
        assert generate_event_effect is not None, "Should have generate_event effect"
        assert '{{player_name}} examines the interactive object.' in generate_event_effect['message']
    
    def test_actual_hearth_and_shadow_config_validation(self):
        """Test that the actual Hearth and Shadow configs are valid YAML."""
        # Test that the cleaned up configs are still valid YAML
        import yaml
        
        # Load and validate the rooms config
        with open('configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml', 'r') as f:
            rooms_data = yaml.safe_load(f)
        
        # Load and validate the objects config
        with open('configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml', 'r') as f:
            objects_data = yaml.safe_load(f)
        
        # Verify both configs loaded successfully
        assert rooms_data is not None, "Rooms config should be valid YAML"
        assert objects_data is not None, "Objects config should be valid YAML"
        
        # Verify entity_definitions exist
        assert 'entity_definitions' in rooms_data, "Rooms config should have entity_definitions"
        assert 'entity_definitions' in objects_data, "Objects config should have entity_definitions"
        
        # Test a few specific cleaned up objects
        test_cases = [
            ('town_square', 'town_statue'),
            ('town_square', 'cult_symbols'),
            ('town_square', 'fresh_evidence')
        ]
        
        for room_id, obj_id in test_cases:
            if room_id in rooms_data['entity_definitions']:
                room_data = rooms_data['entity_definitions'][room_id]
                if 'properties' in room_data and 'objects' in room_data['properties']:
                    if obj_id in room_data['properties']['objects']:
                        obj_instance = room_data['properties']['objects'][obj_id]
                        
                        # Verify the object instance has the essential fields
                        assert 'object_type_id' in obj_instance, f"{obj_id} should have object_type_id"
                        # current_room_id is redundant and has been removed
                        
                        # Verify the object type exists in objects config
                        object_type_id = obj_instance['object_type_id']
                        assert object_type_id in objects_data['entity_definitions'], f"Object type {object_type_id} should exist"
                        
                        obj_type = objects_data['entity_definitions'][object_type_id]
                        assert 'attributes' in obj_type, f"Object type {object_type_id} should have attributes"
                        assert 'name' in obj_type['attributes'], f"Object type {object_type_id} should have name"
                        assert 'description' in obj_type['attributes'], f"Object type {object_type_id} should have description"
                        
                        print(f"✅ {obj_id} in {room_id}: type={object_type_id}, name='{obj_type['attributes']['name']}'")
