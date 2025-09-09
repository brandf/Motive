"""Test pickup constraints for objects with special tags."""

import pytest
from motive.hooks.core_hooks import handle_pickup_action
from motive.game_objects import GameObject
from motive.game_rooms import Room
from motive.player import PlayerCharacter


def test_pickup_immovable_object():
    """Test that immovable objects cannot be picked up."""
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
    
    # Create immovable object (like a fountain)
    immovable_object = GameObject(
        obj_id="fountain",
        name="Fountain",
        description="A stone fountain",
        current_location_id="test_room",
        properties={},
        tags=["immovable"]
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
    test_room.objects = {"fountain": immovable_object}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test pickup action
    events, feedback = handle_pickup_action(game_master, player_char, action_config, {"object_name": "Fountain"})
    
    # Verify we get 1 event (error case)
    assert len(events) == 1
    
    # Verify event details
    event = events[0]
    assert event.event_type == "player_action"
    assert "attempts to add the Fountain to their inventory" in event.message
    assert "but it is immovable" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was not moved to inventory
    assert "fountain" not in player_char.inventory
    assert "fountain" in test_room.objects
    
    # Verify feedback
    assert len(feedback) == 1
    assert "Cannot perform 'pickup': Cannot add 'Fountain' to inventory - it is immovable" in feedback[0]


def test_pickup_too_heavy_object():
    """Test that objects tagged as too_heavy cannot be picked up."""
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
    
    # Create heavy object
    heavy_object = GameObject(
        obj_id="boulder",
        name="Boulder",
        description="A massive boulder",
        current_location_id="test_room",
        properties={},
        tags=["too_heavy"]
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
    test_room.objects = {"boulder": heavy_object}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test pickup action
    events, feedback = handle_pickup_action(game_master, player_char, action_config, {"object_name": "Boulder"})
    
    # Verify we get 1 event (error case)
    assert len(events) == 1
    
    # Verify event details
    event = events[0]
    assert event.event_type == "player_action"
    assert "attempts to add the Boulder to their inventory" in event.message
    assert "but it is too heavy" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was not moved to inventory
    assert "boulder" not in player_char.inventory
    assert "boulder" in test_room.objects
    
    # Verify feedback
    assert len(feedback) == 1
    assert "Cannot perform 'pickup': Cannot add 'Boulder' to inventory - it is too heavy" in feedback[0]


def test_pickup_magically_bound_object():
    """Test that objects tagged as magically_bound cannot be picked up."""
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
    
    # Create magically bound object
    bound_object = GameObject(
        obj_id="altar",
        name="Sacred Altar",
        description="A sacred altar bound to this location",
        current_location_id="test_room",
        properties={},
        tags=["magically_bound"]
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
    test_room.objects = {"altar": bound_object}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test pickup action
    events, feedback = handle_pickup_action(game_master, player_char, action_config, {"object_name": "Sacred Altar"})
    
    # Verify we get 1 event (error case)
    assert len(events) == 1
    
    # Verify event details
    event = events[0]
    assert event.event_type == "player_action"
    assert "attempts to add the Sacred Altar to their inventory" in event.message
    assert "but it is magically bound to this location" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was not moved to inventory
    assert "altar" not in player_char.inventory
    assert "altar" in test_room.objects
    
    # Verify feedback
    assert len(feedback) == 1
    assert "Cannot perform 'pickup': Cannot add 'Sacred Altar' to inventory - it is magically bound to its location" in feedback[0]


def test_pickup_object_with_multiple_constraints():
    """Test that objects with multiple pickup constraints are handled correctly."""
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
    
    # Create object with multiple constraints (immovable takes precedence)
    constrained_object = GameObject(
        obj_id="statue",
        name="Ancient Statue",
        description="An ancient statue",
        current_location_id="test_room",
        properties={},
        tags=["immovable", "too_heavy", "magically_bound"]
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
    test_room.objects = {"statue": constrained_object}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test pickup action
    events, feedback = handle_pickup_action(game_master, player_char, action_config, {"object_name": "Ancient Statue"})
    
    # Verify we get 1 event (error case)
    assert len(events) == 1
    
    # Verify event details - should report immovable (first constraint checked)
    event = events[0]
    assert event.event_type == "player_action"
    assert "attempts to add the Ancient Statue to their inventory" in event.message
    assert "but it is immovable" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was not moved to inventory
    assert "statue" not in player_char.inventory
    assert "statue" in test_room.objects
    
    # Verify feedback
    assert len(feedback) == 1
    assert "Cannot perform 'pickup': Cannot add 'Ancient Statue' to inventory - it is immovable" in feedback[0]


def test_pickup_normal_object_still_works():
    """Test that normal objects without constraints can still be picked up."""
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
    
    # Create normal object (no pickup constraints)
    normal_object = GameObject(
        obj_id="torch",
        name="Torch",
        description="A wooden torch",
        current_location_id="test_room",
        properties={},
        tags=["light_source"]  # Has tags but no pickup constraints
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
    test_room.objects = {"torch": normal_object}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test pickup action
    events, feedback = handle_pickup_action(game_master, player_char, action_config, {"object_name": "Torch"})
    
    # Verify we get 3 events (successful pickup)
    assert len(events) == 3
    
    # Verify event details - check the room_players event (index 1)
    event = events[1]
    assert event.event_type == "player_action"
    assert "picks up the Torch" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was moved to inventory
    assert "torch" in player_char.inventory
    assert "torch" not in test_room.objects
    
    # Verify feedback
    assert len(feedback) == 1
    assert "You pick up the Torch" in feedback[0]


def test_pickup_constraint_case_insensitive():
    """Test that pickup constraints work with case insensitive object names."""
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
    
    # Create immovable object
    immovable_object = GameObject(
        obj_id="fountain",
        name="Fountain",
        description="A stone fountain",
        current_location_id="test_room",
        properties={},
        tags=["immovable"]
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
    test_room.objects = {"fountain": immovable_object}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test pickup action with lowercase name
    events, feedback = handle_pickup_action(game_master, player_char, action_config, {"object_name": "fountain"})
    
    # Verify we get 1 event (error case)
    assert len(events) == 1
    
    # Verify event details
    event = events[0]
    assert event.event_type == "player_action"
    assert "attempts to add the Fountain to their inventory" in event.message  # Uses actual object name
    assert "but it is immovable" in event.message
    assert event.observers == ["room_players"]
    
    # Verify object was not moved to inventory
    assert "fountain" not in player_char.inventory
    assert "fountain" in test_room.objects
    
    # Verify feedback
    assert len(feedback) == 1
    assert "Cannot perform 'pickup': Cannot add 'Fountain' to inventory - it is immovable" in feedback[0]

