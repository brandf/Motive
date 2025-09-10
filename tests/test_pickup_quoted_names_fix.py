"""
Test pickup action with quoted names to ensure the fix works correctly.
"""
import pytest
from unittest.mock import Mock, patch
from motive.game_master import GameMaster
from motive.character import Character
from motive.room import Room
from motive.game_object import GameObject
from motive.hooks.core_hooks import handle_pickup_action


class TestPickupQuotedNamesFix:
    """Test that pickup action correctly handles quoted object names."""
    
    def test_pickup_action_with_quoted_name_should_work(self):
        """Test that pickup action works with quoted object names like 'large sword'."""
        # Create test objects
        large_sword = GameObject(
            obj_id="large_sword",
            name="Large Sword",
            description="A large, heavy sword",
            current_location_id="test_room"
        )
        
        test_room = Room(
            room_id="test_room",
            name="Test Room",
            description="A test room",
            objects={"large_sword": large_sword}
        )
        
        test_character = Character(
            char_id="test_char",
            name="TestHero",
            backstory="A test hero",
            motive="Test the pickup action",
            current_room_id="test_room"
        )
        
        game_master = Mock()
        game_master.rooms = {"test_room": test_room}
        
        pickup_action_config = Mock()
        pickup_action_config.name = "pickup"
        
        # Test with quoted name - this should work now
        params = {"object_name": '"large sword"'}
        events, feedback = handle_pickup_action(game_master, test_character, pickup_action_config, params)
        
        # Should successfully pick up the object
        assert any("pick up" in msg.lower() for msg in feedback)
        assert not any("not found" in msg.lower() for msg in feedback)
        assert not any("not in room" in msg.lower() for msg in feedback)
    
    def test_pickup_action_with_unquoted_name_should_work(self):
        """Test that pickup action still works with unquoted object names."""
        # Create test objects
        large_sword = GameObject(
            obj_id="large_sword",
            name="Large Sword",
            description="A large, heavy sword",
            current_location_id="test_room"
        )
        
        test_room = Room(
            room_id="test_room",
            name="Test Room",
            description="A test room",
            objects={"large_sword": large_sword}
        )
        
        test_character = Character(
            char_id="test_char",
            name="TestHero",
            backstory="A test hero",
            motive="Test the pickup action",
            current_room_id="test_room"
        )
        
        game_master = Mock()
        game_master.rooms = {"test_room": test_room}
        
        pickup_action_config = Mock()
        pickup_action_config.name = "pickup"
        
        # Test with unquoted name - this should still work
        params = {"object_name": "large sword"}
        events, feedback = handle_pickup_action(game_master, test_character, pickup_action_config, params)
        
        # Should successfully pick up the object
        assert any("pick up" in msg.lower() for msg in feedback)
        assert not any("not found" in msg.lower() for msg in feedback)
        assert not any("not in room" in msg.lower() for msg in feedback)
    
    def test_pickup_action_with_single_quotes_should_work(self):
        """Test that pickup action works with single-quoted object names."""
        # Create test objects
        large_sword = GameObject(
            obj_id="large_sword",
            name="Large Sword",
            description="A large, heavy sword",
            current_location_id="test_room"
        )
        
        test_room = Room(
            room_id="test_room",
            name="Test Room",
            description="A test room",
            objects={"large_sword": large_sword}
        )
        
        test_character = Character(
            char_id="test_char",
            name="TestHero",
            backstory="A test hero",
            motive="Test the pickup action",
            current_room_id="test_room"
        )
        
        game_master = Mock()
        game_master.rooms = {"test_room": test_room}
        
        pickup_action_config = Mock()
        pickup_action_config.name = "pickup"
        
        # Test with single-quoted name
        params = {"object_name": "'large sword'"}
        events, feedback = handle_pickup_action(game_master, test_character, pickup_action_config, params)
        
        # Should successfully pick up the object
        assert any("pick up" in msg.lower() for msg in feedback)
        assert not any("not found" in msg.lower() for msg in feedback)
        assert not any("not in room" in msg.lower() for msg in feedback)
    
    def test_pickup_action_with_mixed_quotes_should_work(self):
        """Test that pickup action works with mixed quote types."""
        # Create test objects
        large_sword = GameObject(
            obj_id="large_sword",
            name="Large Sword",
            description="A large, heavy sword",
            current_location_id="test_room"
        )
        
        test_room = Room(
            room_id="test_room",
            name="Test Room",
            description="A test room",
            objects={"large_sword": large_sword}
        )
        
        test_character = Character(
            char_id="test_char",
            name="TestHero",
            backstory="A test hero",
            motive="Test the pickup action",
            current_room_id="test_room"
        )
        
        game_master = Mock()
        game_master.rooms = {"test_room": test_room}
        
        pickup_action_config = Mock()
        pickup_action_config.name = "pickup"
        
        # Test with mixed quotes
        params = {"object_name": "'large sword\""}
        events, feedback = handle_pickup_action(game_master, test_character, pickup_action_config, params)
        
        # Should successfully pick up the object
        assert any("pick up" in msg.lower() for msg in feedback)
        assert not any("not found" in msg.lower() for msg in feedback)
        assert not any("not in room" in msg.lower() for msg in feedback)
