"""Test drop action security and edge cases."""

import pytest
from motive.hooks.core_hooks import handle_drop_action
from motive.game_object import GameObject
from motive.room import Room
from motive.character import Character


def test_drop_action_malicious_input():
    """Test drop action with malicious input."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create test player character
    player_char = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player_char.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test with various malicious inputs
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "../../etc/passwd",
        "'; DROP TABLE users; --",
        "null",
        "undefined",
        "true",
        "false",
        "0",
        "1",
        "",
        "   ",
        "\n",
        "\t",
        "\r\n",
        "a" * 1000,  # Very long string
    ]
    
    for malicious_input in malicious_inputs:
        events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": malicious_input})
        
        # Should not crash and should return appropriate error
        assert len(events) == 1
        assert len(feedback) == 1
        assert "Cannot perform 'drop'" in feedback[0]
        
        # Should not modify game state
        assert len(player_char.inventory) == 0
        assert len(test_room.objects) == 0


def test_drop_action_special_characters():
    """Test drop action with special characters in object names."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create test object with special characters
    test_object = GameObject(
        obj_id="special_obj",
        name="Object with Special Chars: !@#$%^&*()",
        description="An object with special characters",
        current_location_id="test_room",
        properties={}
    )
    
    # Create test player character with object in inventory
    player_char = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player_char.inventory = {"special_obj": test_object}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test drop action with special characters
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "Object with Special Chars: !@#$%^&*()"})
    
    # Verify we get 3 events (player, room_characters, adjacent_rooms_characters)
    assert len(events) == 3
    
    # Verify event details - check the room_characters event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "drops the Object with Special Chars" in event.message
    assert event.observers == ["room_characters"]
    
    # Verify object was moved from inventory to room
    assert "special_obj" not in player_char.inventory
    assert "special_obj" in test_room.objects


def test_drop_action_unicode_characters():
    """Test drop action with unicode characters."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create test object with unicode characters
    test_object = GameObject(
        obj_id="unicode_obj",
        name="魔法の杖",
        description="A magical staff",
        current_location_id="test_room",
        properties={}
    )
    
    # Create test player character with object in inventory
    player_char = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player_char.inventory = {"unicode_obj": test_object}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test drop action with unicode characters
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "魔法の杖"})
    
    # Verify we get 3 events (player, room_characters, adjacent_rooms_characters)
    assert len(events) == 3
    
    # Verify event details - check the room_characters event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "drops the 魔法の杖" in event.message
    assert event.observers == ["room_characters"]
    
    # Verify object was moved from inventory to room
    assert "unicode_obj" not in player_char.inventory
    assert "unicode_obj" in test_room.objects


def test_drop_action_cross_room_exploit():
    """Test that drop action cannot be used to exploit cross-room object placement."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create two test rooms
    room1 = Room(
        room_id="room1",
        name="Room 1",
        description="First room",
        exits={}
    )
    room2 = Room(
        room_id="room2",
        name="Room 2",
        description="Second room",
        exits={}
    )
    
    # Create test object
    test_object = GameObject(
        obj_id="test_obj",
        name="Test Object",
        description="A test object",
        current_location_id="room1",  # Object thinks it's in room1
        properties={}
    )
    
    # Create test player character in room2 with object in inventory
    player_char = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="room2"  # Player is in room2
    )
    player_char.inventory = {"test_obj": test_object}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"room1": room1, "room2": room2}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test drop action
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "Test Object"})
    
    # Verify we get 3 events (player, room_characters, adjacent_rooms_characters)
    assert len(events) == 3
    
    # Verify event details - check the room_characters event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "drops the Test Object" in event.message
    assert event.observers == ["room_characters"]
    assert event.source_room_id == "room2"  # Event should be from player's current room
    
    # Verify object was moved to player's current room, not object's original room
    assert "test_obj" not in player_char.inventory
    assert "test_obj" in room2.objects  # Should be in room2 (player's room)
    assert "test_obj" not in room1.objects  # Should not be in room1 (object's original room)
    
    # Verify object's location was updated
    assert test_object.current_location_id == "room2"


def test_drop_action_inventory_integrity():
    """Test that drop action maintains inventory integrity."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create multiple test objects
    obj1 = GameObject(
        obj_id="obj1",
        name="Object 1",
        description="First object",
        current_location_id="test_room",
        properties={}
    )
    obj2 = GameObject(
        obj_id="obj2",
        name="Object 2",
        description="Second object",
        current_location_id="test_room",
        properties={}
    )
    obj3 = GameObject(
        obj_id="obj3",
        name="Object 3",
        description="Third object",
        current_location_id="test_room",
        properties={}
    )
    
    # Create test player character with multiple objects in inventory
    player_char = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player_char.inventory = {"obj1": obj1, "obj2": obj2, "obj3": obj3}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test dropping middle object
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "Object 2"})
    
    # Verify we get 3 events (player, room_characters, adjacent_rooms_characters)
    assert len(events) == 3
    
    # Verify event details - check the room_characters event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "drops the Object 2" in event.message
    assert event.observers == ["room_characters"]
    
    # Verify only the specified object was moved
    assert len(player_char.inventory) == 2
    assert "obj1" in player_char.inventory
    assert "obj2" not in player_char.inventory
    assert "obj3" in player_char.inventory
    
    # Verify object was moved to room
    assert len(test_room.objects) == 1
    assert "obj2" in test_room.objects
    assert test_room.objects["obj2"] == obj2
