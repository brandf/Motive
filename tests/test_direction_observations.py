"""Test that movement events include direction information for observers."""

import pytest
from unittest.mock import MagicMock
from motive.hooks.core_hooks import handle_move_action
from motive.game_objects import GameObject
from motive.game_rooms import Room
from motive.player import PlayerCharacter


def test_move_action_includes_direction_in_events():
    """Test that move action generates events with direction information."""
    # Create test rooms
    room1 = Room(
        room_id="room1",
        name="Room 1", 
        description="A test room",
        objects={},
        exits={"north": {"destination_room_id": "room2", "name": "North Exit"}}
    )
    room2 = Room(
        room_id="room2",
        name="Room 2",
        description="Another room", 
        objects={},
        exits={}
    )
    
    # Create test player character
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="room1"
    )
    
    # Create mock game master
    game_master = MagicMock()
    game_master.rooms = {"room1": room1, "room2": room2}
    
    # Test move action
    events, feedback = handle_move_action(game_master, player_char, {"direction": "North Exit"})
    
    # Verify we get 2 events (exit and enter)
    assert len(events) == 2
    
    # Verify exit event includes direction
    exit_event = events[0]
    assert exit_event.event_type == "player_exit"
    assert "left the room via North Exit" in exit_event.message
    assert exit_event.observers == ["room_players"]
    
    # Verify enter event includes direction
    enter_event = events[1]
    assert enter_event.event_type == "player_enter"
    assert "entered the room from North Exit" in enter_event.message
    assert enter_event.observers == ["room_players"]


def test_move_action_with_multiple_exits():
    """Test that direction is specified even when multiple exits exist."""
    # Create room with multiple exits
    room = Room(
        room_id="multi_exit_room",
        name="Multi Exit Room",
        description="A room with multiple exits",
        objects={},
        exits={
            "north": {"destination_room_id": "north_room", "name": "North Exit"},
            "south": {"destination_room_id": "south_room", "name": "South Exit"},
            "east": {"destination_room_id": "east_room", "name": "East Exit"}
        }
    )
    
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer", 
        backstory="A test character",
        motive="Test motive",
        current_room_id="multi_exit_room"
    )
    
    game_master = MagicMock()
    game_master.rooms = {
        "multi_exit_room": room,
        "north_room": Room("north_room", "North Room", "North room", {}, {}),
        "south_room": Room("south_room", "South Room", "South room", {}, {}),
        "east_room": Room("east_room", "East Room", "East room", {}, {})
    }
    
    # Test moving north
    events, _ = handle_move_action(game_master, player_char, {"direction": "North Exit"})
    assert "left the room via North Exit" in events[0].message
    assert "entered the room from North Exit" in events[1].message
    
    # Test moving south
    player_char.current_room_id = "multi_exit_room"  # Reset position
    events, _ = handle_move_action(game_master, player_char, {"direction": "South Exit"})
    assert "left the room via South Exit" in events[0].message
    assert "entered the room from South Exit" in events[1].message
