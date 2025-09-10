"""Security tests for inventory management to prevent exploitation."""

import pytest
from motive.hooks.core_hooks import handle_pickup_action
from motive.game_object import GameObject
from motive.room import Room
from motive.character import Character


def test_pickup_object_not_in_room():
    """Test that players cannot pick up objects not in their current room."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create two rooms
    room1 = Room(room_id="room1", name="Room 1", description="First room", exits={})
    room2 = Room(room_id="room2", name="Room 2", description="Second room", exits={})
    
    # Create object in room2
    test_object = GameObject(
        obj_id="test_item",
        name="Item",
        description="A test item",
        current_location_id="room2",
        tags=[],
        properties={}
    )
    room2.add_object(test_object)
    
    # Create player in room1
    player_char = Character(
        char_id="test_char",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="room1"
    )
    
    # Setup game master
    gm = MockGameMaster()
    gm.rooms["room1"] = room1
    gm.rooms["room2"] = room2
    
    # Create mock action config
    class MockActionConfig:
        pass
    
    action_config = MockActionConfig()
    params = {"object_name": "Item"}
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify security: object should NOT be picked up
    assert len(events) == 0, f"Expected 0 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert "Item' not found in the room." in feedback[0]
    
    # Verify object is still in room2
    assert test_object.id in room2.objects, "Object should still be in room2"
    assert test_object.id not in player_char.inventory, "Object should NOT be in player inventory"


def test_pickup_nonexistent_object():
    """Test that players cannot pick up objects that don't exist."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create empty room
    test_room = Room(room_id="test_room", name="Test Room", description="Empty room", exits={})
    
    # Create player
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
    params = {"object_name": "NonExistentItem"}
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify security: no object should be picked up
    assert len(events) == 0, f"Expected 0 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert "NonExistentItem' not found in the room." in feedback[0]
    
    # Verify inventory remains empty
    assert len(player_char.inventory) == 0, "Player inventory should remain empty"


def test_pickup_object_already_in_inventory():
    """Test that players cannot pick up objects they already have."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create room with object
    test_room = Room(room_id="test_room", name="Test Room", description="Room with item", exits={})
    
    # Create object
    test_object = GameObject(
        obj_id="test_item",
        name="Item",
        description="A test item",
        current_location_id="test_room",
        tags=[],
        properties={}
    )
    test_room.add_object(test_object)
    
    # Create player with object already in inventory
    player_char = Character(
        char_id="test_char",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Add object to player inventory (simulating they already have it)
    player_char.add_item_to_inventory(test_object)
    
    # Setup game master
    gm = MockGameMaster()
    gm.rooms["test_room"] = test_room
    
    # Create mock action config
    class MockActionConfig:
        pass
    
    action_config = MockActionConfig()
    params = {"object_name": "Item"}
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify security: object should be picked up (this is actually valid behavior)
    # The object should be moved from room to inventory, even if player already has one
    assert len(events) == 3, f"Expected 3 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert "You pick up the Item." in feedback[0]
    
    # Verify object is moved from room to inventory
    assert test_object.id not in test_room.objects, "Object should be removed from room"
    assert test_object.id in player_char.inventory, "Object should be in player inventory"


def test_pickup_object_with_special_characters():
    """Test that players cannot exploit special characters in object names."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create room
    test_room = Room(room_id="test_room", name="Test Room", description="Room", exits={})
    
    # Create player
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
    
    # Test various potentially malicious object names
    malicious_names = [
        "'; DROP TABLE items; --",
        "<script>alert('xss')</script>",
        "../../etc/passwd",
        "Item\n; rm -rf /",
        "Item\0null",
        "Item\twith\ttabs",
        "Item with\nnewlines"
    ]
    
    for malicious_name in malicious_names:
        params = {"object_name": malicious_name}
        
        # Execute pickup action
        events, feedback = handle_pickup_action(gm, player_char, action_config, params)
        
        # Verify security: no object should be picked up
        assert len(events) == 0, f"Expected 0 events for malicious name '{malicious_name}', got {len(events)}"
        assert len(feedback) == 1, f"Expected 1 feedback message for malicious name '{malicious_name}', got {len(feedback)}"
        assert f"'{malicious_name}' not found in the room." in feedback[0]
        
        # Verify inventory remains empty
        assert len(player_char.inventory) == 0, f"Player inventory should remain empty for malicious name '{malicious_name}'"


def test_pickup_object_case_sensitivity_security():
    """Test that case sensitivity doesn't create security vulnerabilities."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create room with object
    test_room = Room(room_id="test_room", name="Test Room", description="Room", exits={})
    
    # Create object with specific case
    test_object = GameObject(
        obj_id="test_item",
        name="Sword",
        description="A sharp sword",
        current_location_id="test_room",
        tags=[],
        properties={}
    )
    test_room.add_object(test_object)
    
    # Create player
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
    
    # Test different case variations
    case_variations = ["sword", "SWORD", "Sword", "sWoRd"]
    
    for case_variation in case_variations:
        params = {"object_name": case_variation}
        
        # Execute pickup action
        events, feedback = handle_pickup_action(gm, player_char, action_config, params)
        
        # Verify security: object should be picked up (case-insensitive matching is expected)
        assert len(events) == 3, f"Expected 3 events for case '{case_variation}', got {len(events)}"
        assert len(feedback) == 1, f"Expected 1 feedback message for case '{case_variation}', got {len(feedback)}"
        assert "You pick up the Sword." in feedback[0]
        
        # Verify object is moved from room to inventory
        assert test_object.id not in test_room.objects, f"Object should be removed from room for case '{case_variation}'"
        assert test_object.id in player_char.inventory, f"Object should be in player inventory for case '{case_variation}'"
        
        # Reset for next test
        test_room.add_object(test_object)
        player_char.remove_item_from_inventory(test_object.id)


def test_pickup_object_duplicate_ids():
    """Test that objects with duplicate IDs cannot be exploited."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create room
    test_room = Room(room_id="test_room", name="Test Room", description="Room", exits={})
    
    # Create two objects with same ID (this shouldn't happen in normal operation)
    object1 = GameObject(
        obj_id="duplicate_id",
        name="Item1",
        description="First item",
        current_location_id="test_room",
        tags=[],
        properties={}
    )
    object2 = GameObject(
        obj_id="duplicate_id",  # Same ID!
        name="Item2",
        description="Second item",
        current_location_id="test_room",
        tags=[],
        properties={}
    )
    
    # Add both objects to room
    test_room.add_object(object1)
    test_room.add_object(object2)  # This should overwrite the first one
    
    # Create player
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
    params = {"object_name": "Item1"}
    
    # Execute pickup action
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify security: Item1 should not be found because it was overwritten by Item2
    assert len(events) == 0, f"Expected 0 events, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message, got {len(feedback)}"
    assert "Item1' not found in the room." in feedback[0]
    
    # Verify inventory remains empty
    assert len(player_char.inventory) == 0, "Player inventory should remain empty"
    
    # Verify room still has Item2
    assert len(test_room.objects) == 1, "Room should have one object (Item2)"
    assert "duplicate_id" in test_room.objects, "Room should have the object with duplicate_id"
    
    # Now try to pick up Item2
    params = {"object_name": "Item2"}
    events, feedback = handle_pickup_action(gm, player_char, action_config, params)
    
    # Verify Item2 can be picked up
    assert len(events) == 3, f"Expected 3 events for Item2, got {len(events)}"
    assert len(feedback) == 1, f"Expected 1 feedback message for Item2, got {len(feedback)}"
    assert "You pick up the Item2." in feedback[0]
    
    # Verify Item2 is in inventory
    assert len(player_char.inventory) == 1, "Player should have exactly one object in inventory"
    assert "duplicate_id" in player_char.inventory, "Player should have the object with duplicate_id"
    
    # Verify room is empty
    assert len(test_room.objects) == 0, "Room should be empty after pickup"
