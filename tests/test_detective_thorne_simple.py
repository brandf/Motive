"""
Simple, focused tests for Detective Thorne's motive completion.

These tests verify that the core interaction mechanisms work correctly
without complex mocking.
"""

import pytest
from motive.hooks.core_hooks import handle_pickup_action, look_at_target
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


class TestDetectiveThorneSimple:
    """Simple tests for Detective Thorne's motive interactions."""
    
    def test_pickup_action_supports_set_property(self):
        """Test that pickup action supports set_property effects."""
        # This test verifies that the fix I made to handle_pickup_action works
        # by checking that it can process both increment_property and set_property effects
        
        # Create a simple mock setup
        from unittest.mock import Mock
        
        game_master = Mock()
        player = Mock()
        player.properties = {}
        player.current_room_id = "test_room"
        player.id = "test_player"  # Add string ID
        player.add_item_to_inventory = Mock()
        
        def set_property(name, value):
            player.properties[name] = value
        
        player.set_property = set_property
        
        room = Mock()
        room.remove_object = Mock()
        
        # Create object with set_property effect
        test_object = Mock()
        test_object.id = "test_object"
        test_object.name = "Test Object"
        test_object.interactions = {
            'pickup': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'test_property',
                        'value': True
                    }
                ]
            }
        }
        
        room.objects = {"test_object": test_object}
        game_master.rooms = {"test_room": room}
        
        # Mock inventory validation
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            # Execute pickup action
            events, feedback = handle_pickup_action(
                game_master, 
                player, 
                Mock(), 
                {"object_name": "Test Object"}
            )
        
        # Verify the property was set
        assert player.properties.get('test_property') is True
        assert "Test Property: True" in feedback[0]
    
    def test_pickup_action_supports_increment_property(self):
        """Test that pickup action supports increment_property effects."""
        # Create a simple mock setup
        from unittest.mock import Mock
        
        game_master = Mock()
        player = Mock()
        player.properties = {}
        player.current_room_id = "test_room"
        player.id = "test_player"  # Add string ID
        player.add_item_to_inventory = Mock()
        
        def set_property(name, value):
            player.properties[name] = value
        
        player.set_property = set_property
        
        room = Mock()
        room.remove_object = Mock()
        
        # Create object with increment_property effect
        test_object = Mock()
        test_object.id = "test_object"
        test_object.name = "Test Object"
        test_object.interactions = {
            'pickup': {
                'effects': [
                    {
                        'type': 'increment_property',
                        'target': 'player',
                        'property': 'test_counter',
                        'increment_value': 1
                    }
                ]
            }
        }
        
        room.objects = {"test_object": test_object}
        game_master.rooms = {"test_room": room}
        
        # Mock inventory validation
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            # Execute pickup action
            events, feedback = handle_pickup_action(
                game_master, 
                player, 
                Mock(), 
                {"object_name": "Test Object"}
            )
        
        # Verify the property was incremented
        assert player.properties.get('test_counter') == 1
        assert "Test Counter: 1" in feedback[0]
    
    def test_look_at_target_supports_set_property(self):
        """Test that look_at_target supports set_property effects."""
        # Create a simple mock setup
        from unittest.mock import Mock
        
        game_master = Mock()
        player = Mock()
        player.properties = {}
        player.current_room_id = "test_room"
        player.id = "test_player"  # Add string ID
        player.get_item_in_inventory = Mock(return_value=None)
        player.get_display_name = Mock(return_value="Test Player")
        
        def set_property(name, value):
            player.properties[name] = value
        
        def get_property(name, default=None):
            return player.properties.get(name, default)
        
        player.set_property = set_property
        player.get_property = get_property
        
        room = Mock()
        
        # Create object with set_property effect
        test_object = Mock()
        test_object.id = "test_object"
        test_object.name = "Test Object"
        test_object.description = "A test object"
        test_object.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'test_property',
                        'value': True
                    }
                ]
            }
        }
        
        room.get_object = Mock(return_value=test_object)
        game_master.rooms = {"test_room": room}
        
        # Execute look action
        events, feedback = look_at_target(
            game_master, 
            player, 
            Mock(), 
            {"target": "Test Object"}
        )
        
        # Verify the property was set
        assert player.properties.get('test_property') is True
    
    def test_look_at_target_supports_increment_property(self):
        """Test that look_at_target supports increment_property effects."""
        # Create a simple mock setup
        from unittest.mock import Mock
        
        game_master = Mock()
        player = Mock()
        player.properties = {}
        player.current_room_id = "test_room"
        player.id = "test_player"  # Add string ID
        player.get_item_in_inventory = Mock(return_value=None)
        player.get_display_name = Mock(return_value="Test Player")
        
        def set_property(name, value):
            player.properties[name] = value
        
        def get_property(name, default=None):
            return player.properties.get(name, default)
        
        player.set_property = set_property
        player.get_property = get_property
        
        room = Mock()
        
        # Create object with increment_property effect
        test_object = Mock()
        test_object.id = "test_object"
        test_object.name = "Test Object"
        test_object.description = "A test object"
        test_object.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'increment_property',
                        'target': 'player',
                        'property': 'test_counter',
                        'increment_value': 1
                    }
                ]
            }
        }
        
        room.get_object = Mock(return_value=test_object)
        game_master.rooms = {"test_room": room}
        
        # Execute look action
        events, feedback = look_at_target(
            game_master, 
            player, 
            Mock(), 
            {"target": "Test Object"}
        )
        
        # Verify the property was incremented
        assert player.properties.get('test_counter') == 1
