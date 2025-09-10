"""Test pickup action implementation."""

import pytest
from motive.hooks.core_hooks import handle_pickup_action
from motive.game_object import GameObject
from motive.room import Room
from motive.character import Character


def test_pickup_action_success():
    """Test successful pickup action."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room with an object
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create test object
    test_object = GameObject(
        obj_id="test_torch",
        name="Torch",
        description="A wooden torch",
        current_location_id="test_room",
        tags=["light_source"],
        properties={"is_lit": False}
    )
    
    # Add object to room
    test_room.add_object(test_object)
    
    # Create test player character
    player_char = Character(
        char_id="test_char",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Setup game master
    gm = MockGameMaster()
    gm.rooms["test_room"] = test_room
    
    # Create mock action config
    class MockActionConfig:
        pass
    
    action_config = MockActionConfig()
    params = {"object_name": "Torch"}
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify results
    assert len(events) == 3, f"Expected 3 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert feedback[0] == "You pick up the Torch."
    
    # Verify object was moved from room to inventory
    assert test_object.id not in test_room.objects, "Object should be removed from room"
    assert test_object.id in player_char.inventory, "Object should be added to player inventory"
    
    # Verify events
    player_event = events[0]
    assert player_event.observers == ["player"]
    assert "You pick up the Torch." in player_event.message
    
    room_event = events[1]
    assert room_event.observers == ["room_players"]
    assert "TestPlayer picks up the Torch." in room_event.message
    
    adjacent_event = events[2]
    assert adjacent_event.observers == ["adjacent_rooms"]
    assert "TestPlayer picks up something." in adjacent_event.message


def test_pickup_action_object_not_found():
    """Test pickup action when object is not in room."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create empty test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create test player character
    player_char = Character(
        char_id="test_char",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Setup game master
    gm = MockGameMaster()
    gm.rooms["test_room"] = test_room
    
    # Create mock action config
    class MockActionConfig:
        pass
    
    action_config = MockActionConfig()
    params = {"object_name": "NonExistentObject"}
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify results
    assert len(events) == 0, f"Expected 0 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert "NonExistentObject' not found in the room." in feedback[0]


def test_pickup_action_no_object_name():
    """Test pickup action when no object name is provided."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test player character
    player_char = Character(
        char_id="test_char",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Setup game master
    gm = MockGameMaster()
    
    # Create mock action config
    class MockActionConfig:
        pass
    
    action_config = MockActionConfig()
    params = {}  # No object_name parameter
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify results
    assert len(events) == 0, f"Expected 0 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert "No object specified to pick up." in feedback[0]


def test_pickup_action_case_insensitive():
    """Test pickup action with case-insensitive object name matching."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room with an object
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create test object with capital name
    test_object = GameObject(
        obj_id="test_torch",
        name="Torch",
        description="A wooden torch",
        current_location_id="test_room",
        tags=["light_source"],
        properties={"is_lit": False}
    )
    
    # Add object to room
    test_room.add_object(test_object)
    
    # Create test player character
    player_char = Character(
        char_id="test_char",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Setup game master
    gm = MockGameMaster()
    gm.rooms["test_room"] = test_room
    
    # Create mock action config
    class MockActionConfig:
        pass
    
    action_config = MockActionConfig()
    params = {"object_name": "torch"}  # lowercase
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify results
    assert len(events) == 3, f"Expected 3 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert feedback[0] == "You pick up the Torch."
    
    # Verify object was moved from room to inventory
    assert test_object.id not in test_room.objects, "Object should be removed from room"
    assert test_object.id in player_char.inventory, "Object should be added to player inventory"
