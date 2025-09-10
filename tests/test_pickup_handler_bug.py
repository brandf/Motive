"""
Test pickup action handler bug with quoted object names.
"""
import pytest
from unittest.mock import Mock
from motive.character import Character
from motive.room import Room
from motive.game_object import GameObject


class TestPickupHandlerBug:
    """Test that pickup action handler correctly processes quoted object names."""
    
    def test_pickup_action_handler_with_quoted_name(self):
        """Test that the pickup action handler correctly processes quoted object names."""
        # This test should FAIL initially, demonstrating the bug
        
        # Create test objects
        legendary_sword = GameObject(
            obj_id="legendary_sword",
            name="Legendary Sword",
            description="A powerful magical sword",
            current_location_id="test_room"
        )
        
        test_room = Room(
            room_id="test_room",
            name="Test Room",
            description="A test room",
            objects={"legendary_sword": legendary_sword}
        )
        
        test_character = Character(
            char_id="test_char",
            name="Test Hero",
            backstory="A test character",
            motive="Test motive",
            current_room_id="test_room"
        )
        
        # Create a mock game master
        game_master = Mock()
        game_master.rooms = {"test_room": test_room}
        game_master.game_objects = {"legendary_sword": legendary_sword}
        game_master.game_logger = Mock()
        
        # Test the pickup action handler directly
        from motive.hooks.core_hooks import handle_pickup_action
        
        # Create mock action config
        pickup_action_config = Mock()
        pickup_action_config.name = "pickup"
        
        # Test with quoted object name - this should work
        params = {"object_name": "legendary sword"}  # Without quotes
        
        # Also test the problematic case from the log
        params_with_quotes = {"object_name": '"legendary sword"'}  # With quotes
        
        # The handler should find the object by name (case-insensitive)
        events, feedback = handle_pickup_action(game_master, test_character, pickup_action_config, params)
        
        # Debug: print the actual feedback
        print(f"Feedback: {feedback}")
        
        # Should succeed
        assert len(feedback) > 0
        assert any("pick up" in msg.lower() for msg in feedback)
        
        # Now test the problematic case with quotes
        # Create a fresh room and character for the second test since the first one consumed the object
        legendary_sword2 = GameObject(
            obj_id="legendary_sword2",
            name="Legendary Sword",
            description="A powerful magical sword",
            current_location_id="test_room2"
        )
        
        test_room2 = Room(
            room_id="test_room2",
            name="Test Room 2",
            description="A test room",
            objects={"legendary_sword2": legendary_sword2}
        )
        
        test_character2 = Character(
            char_id="test_char2",
            name="Test Hero 2",
            backstory="A test character",
            motive="Test motive",
            current_room_id="test_room2"
        )
        
        game_master.rooms["test_room2"] = test_room2
        
        print(f"Testing with params: {params_with_quotes}")
        events2, feedback2 = handle_pickup_action(game_master, test_character2, pickup_action_config, params_with_quotes)
        
        # Debug: print the actual feedback for quoted case
        print(f"Feedback with quotes: {feedback2}")
        
        # This should also succeed (quotes should be stripped)
        assert len(feedback2) > 0
        assert any("pick up" in msg.lower() for msg in feedback2)
