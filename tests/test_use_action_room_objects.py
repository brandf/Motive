"""Test that use action works on both inventory and room objects."""

import pytest
from unittest.mock import Mock, patch
from motive.hooks.core_hooks import handle_use_action
from motive.game_object import GameObject
from motive.character import Character
from motive.room import Room


def test_use_action_works_on_inventory_objects():
    """Test that use action works on objects in player inventory (current behavior)."""
    # Create mock game master
    game_master = Mock()
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    game_master.rooms = {"test_room": test_room}
    
    # Create test player with object in inventory
    player = Character(
        char_id="test_player",
        name="TestPlayer", 
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Create object in inventory
    inventory_object = GameObject(
        obj_id="torch",
        name="Torch",
        description="A burning torch",
        current_location_id="test_player",
        properties={"is_lit": True}
    )
    player.inventory = {"torch": inventory_object}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action on inventory object
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Torch"})
    
    # Should succeed
    assert len(feedback) > 0
    assert "You use the Torch" in feedback[0] or "You light the Torch" in feedback[0]


def test_use_action_now_works_on_room_objects():
    """Test that use action now works on room objects (after our fix)."""
    # Create mock game master
    game_master = Mock()
    
    # Create test room with object
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create object in room
    room_object = GameObject(
        obj_id="altar",
        name="Sacred Altar",
        description="A sacred altar",
        current_location_id="test_room",
        properties={"interactions": {"use": {"effects": [{"type": "generate_event", "message": "{{player_name}} uses the Sacred Altar", "observers": ["room_characters"]}]}}}
    )
    test_room.objects = {"altar": room_object}
    game_master.rooms = {"test_room": test_room}
    
    # Create test player
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character", 
        motive="Test motive",
        current_room_id="test_room"
    )
    player.inventory = {}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action on room object - should now work
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Sacred Altar"})
    
    # Should succeed after fix
    assert len(feedback) > 0
    assert "You use the Sacred Altar" in feedback[0]


def test_use_action_should_work_on_room_objects_after_fix():
    """Test that use action should work on room objects after our fix."""
    # This test will pass after we implement the fix
    # Create mock game master
    game_master = Mock()
    
    # Create test room with object
    test_room = Room(
        room_id="test_room",
        name="Test Room", 
        description="A test room",
        exits={}
    )
    
    # Create object in room with use interaction
    room_object = GameObject(
        obj_id="altar",
        name="Sacred Altar",
        description="A sacred altar",
        current_location_id="test_room",
        properties={"interactions": {"use": {"effects": [{"type": "generate_event", "message": "{{player_name}} uses the Sacred Altar", "observers": ["room_characters"]}]}}}
    )
    test_room.objects = {"altar": room_object}
    game_master.rooms = {"test_room": test_room}
    
    # Create test player
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive", 
        current_room_id="test_room"
    )
    player.inventory = {}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action on room object - should work after fix
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Sacred Altar"})
    
    # Should succeed after fix
    assert len(feedback) > 0
    assert "You use the Sacred Altar" in feedback[0]


def test_use_action_prioritizes_inventory_over_room():
    """Test that use action prioritizes inventory objects over room objects when both exist."""
    # Create mock game master
    game_master = Mock()
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room", 
        exits={}
    )
    
    # Create object in room
    room_object = GameObject(
        obj_id="torch_room",
        name="Torch",
        description="A torch on the wall",
        current_location_id="test_room",
        properties={"interactions": {"use": {"effects": [{"type": "generate_event", "message": "{{player_name}} uses the wall torch", "observers": ["room_characters"]}]}}}
    )
    test_room.objects = {"torch_room": room_object}
    game_master.rooms = {"test_room": test_room}
    
    # Create test player with same-named object in inventory
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Create object in inventory with same name
    inventory_object = GameObject(
        obj_id="torch_inv",
        name="Torch", 
        description="A torch in your hand",
        current_location_id="test_player",
        properties={"is_lit": True}
    )
    player.inventory = {"torch_inv": inventory_object}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action - should use inventory object, not room object
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Torch"})
    
    # Should use inventory object (prioritized)
    assert len(feedback) > 0
    assert "You use the Torch" in feedback[0] or "You light the Torch" in feedback[0]
    # Should NOT use room object
    assert "wall torch" not in feedback[0]
