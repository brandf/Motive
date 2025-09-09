"""Test drop action implementation."""

import pytest
from motive.hooks.core_hooks import handle_drop_action
from motive.game_objects import GameObject
from motive.game_rooms import Room
from motive.player import PlayerCharacter


def test_drop_action_success():
    """Test successful drop action."""
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
    
    # Create test object
    test_object = GameObject(
        obj_id="test_torch",
        name="Torch",
        description="A wooden torch",
        current_location_id="test_room",
        properties={}
    )
    
    # Create test player character with object in inventory
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player_char.inventory = {"test_torch": test_object}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test drop action
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "Torch"})
    
    # Verify we get 3 events (player, room_players, adjacent_rooms)
    assert len(events) == 3
    
    # Verify event details - check the room_players event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "drops the Torch" in event.message
    assert event.observers == ["room_players"]
    assert event.source_room_id == "test_room"
    assert event.related_object_id == "test_torch"
    assert event.related_player_id == "test_player"
    
    # Verify object was moved from inventory to room
    assert "test_torch" not in player_char.inventory
    assert "test_torch" in test_room.objects
    assert test_room.objects["test_torch"] == test_object
    
    # Verify feedback
    assert len(feedback) == 1
    assert "You drop the Torch" in feedback[0]


def test_drop_action_object_not_in_inventory():
    """Test drop action when object is not in inventory."""
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
    
    # Create test player character with empty inventory
    player_char = PlayerCharacter(
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
    
    # Test drop action
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "Torch"})
    
    # Verify we get 1 event (error case only generates room_players event)
    assert len(events) == 1
    
    # Verify event details
    event = events[0]
    assert event.event_type == "player_action"
    assert "attempts to drop the Torch" in event.message
    assert "but it is not in their inventory" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was not moved
    assert "test_torch" not in player_char.inventory
    assert "test_torch" not in test_room.objects
    
    # Verify feedback
    assert len(feedback) == 1
    assert "Cannot perform 'drop': Object 'Torch' not in inventory" in feedback[0]


def test_drop_action_case_insensitive():
    """Test drop action with case insensitive object name."""
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
    
    # Create test object
    test_object = GameObject(
        obj_id="test_torch",
        name="Torch",
        description="A wooden torch",
        current_location_id="test_room",
        properties={}
    )
    
    # Create test player character with object in inventory
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player_char.inventory = {"test_torch": test_object}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test drop action with lowercase name
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "torch"})
    
    # Verify we get 3 events (player, room_players, adjacent_rooms)
    assert len(events) == 3
    
    # Verify event details - check the room_players event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "drops the Torch" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was moved from inventory to room
    assert "test_torch" not in player_char.inventory
    assert "test_torch" in test_room.objects


def test_drop_action_no_object_name():
    """Test drop action with no object name provided."""
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
    player_char = PlayerCharacter(
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
    
    # Test drop action with no object name
    events, feedback = handle_drop_action(game_master, player_char, action_config, {})
    
    # Verify we get 1 event
    assert len(events) == 1
    
    # Verify event details
    event = events[0]
    assert event.event_type == "player_action"
    assert "attempts to drop" in event.message
    assert "but no object was specified" in event.message
    assert event.observers == ["room_players"]
    
    # Verify feedback
    assert len(feedback) == 1
    assert "Cannot perform 'drop': No object name provided" in feedback[0]


def test_drop_action_multiple_objects_same_name():
    """Test drop action when multiple objects have the same name."""
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
    
    # Create two objects with same name but different IDs
    torch1 = GameObject(
        obj_id="torch_1",
        name="Torch",
        description="A wooden torch",
        current_location_id="test_room",
        properties={}
    )
    torch2 = GameObject(
        obj_id="torch_2",
        name="Torch",
        description="Another wooden torch",
        current_location_id="test_room",
        properties={}
    )
    
    # Create test player character with both objects in inventory
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player_char.inventory = {"torch_1": torch1, "torch_2": torch2}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test drop action - should drop the first one found
    events, feedback = handle_drop_action(game_master, player_char, action_config, {"object_name": "Torch"})
    
    # Verify we get 3 events (player, room_players, adjacent_rooms)
    assert len(events) == 3
    
    # Verify event details - check the room_players event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "drops the Torch" in event.message
    assert event.observers == ["room_players"]
    
    # Verify one object was moved from inventory to room
    assert len(player_char.inventory) == 1
    assert "torch_1" not in player_char.inventory or "torch_2" not in player_char.inventory
    assert len(test_room.objects) == 1
