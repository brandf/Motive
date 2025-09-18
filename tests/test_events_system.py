"""
Tests for the events and observability system components.

These tests verify the core events system logic without complex GameMaster mocking.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from motive.config import Event
from motive.game_master import GameMaster


def test_event_creation():
    """Test that Event objects are created correctly."""
    event = Event(
        message="Player1 says: \"Hello!\".",
        event_type="player_communication",
        source_room_id="room1",
        timestamp=datetime.now().isoformat(),
        related_player_id="hero_instance_0",
        observers=["room_characters"]
    )
    
    assert event.message == "Player1 says: \"Hello!\"."
    assert event.event_type == "player_communication"
    assert event.source_room_id == "room1"
    assert event.related_player_id == "hero_instance_0"
    assert event.observers == ["room_characters"]


def test_distribute_events_room_characters_scope():
    """Test that events with room_characters scope are distributed correctly."""
    # Create a mock GameMaster with minimal setup
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.game_logger.warning = MagicMock()
    gm.event_queue = []
    gm.player_observations = {
        "player1": [],
        "player2": [],
        "player3": []
    }
    gm.rooms = {
        "room1": MagicMock(id="room1"),
        "room2": MagicMock(id="room2")
    }
    
    # Create mock players
    player1 = MagicMock()
    player1.name = "Player1"
    player1.character = MagicMock()
    player1.character.id = "player1"
    player1.character.current_room_id = "room1"
    
    player2 = MagicMock()
    player2.name = "Player2"
    player2.character = MagicMock()
    player2.character.id = "player2"
    player2.character.current_room_id = "room1"
    
    player3 = MagicMock()
    player3.name = "Player3"
    player3.character = MagicMock()
    player3.character.id = "player3"
    player3.character.current_room_id = "room2"
    
    gm.players = [player1, player2, player3]
    
    # Create a test event from room1
    test_event = Event(
        message="Player1 says: \"Hello!\".",
        event_type="player_communication",
        source_room_id="room1",
        timestamp=datetime.now().isoformat(),
        related_player_id="player1",
        observers=["room_characters"]
    )
    
    # Add event to queue
    gm.event_queue.append(test_event)
    
    # Distribute events
    gm._distribute_events()
    
    # Verify player2 (in same room) received the event
    assert len(gm.player_observations["player2"]) == 1
    assert gm.player_observations["player2"][0].message == "Player1 says: \"Hello!\"."
    
    # Verify player1 (event originator) did NOT receive their own event
    assert len(gm.player_observations["player1"]) == 0
    
    # Verify player3 (in different room) did NOT receive the event
    assert len(gm.player_observations["player3"]) == 0
    
    # Verify event queue was cleared
    assert len(gm.event_queue) == 0


def test_distribute_events_player_scope():
    """Test that events with player scope are distributed correctly."""
    # Create a mock GameMaster with minimal setup
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.game_logger.warning = MagicMock()
    gm.event_queue = []
    gm.player_observations = {
        "player1": [],
        "player2": []
    }
    gm.rooms = {
        "room1": MagicMock(id="room1")
    }
    
    # Create mock players
    player1 = MagicMock()
    player1.name = "Player1"
    player1.character = MagicMock()
    player1.character.id = "player1"
    player1.character.current_room_id = "room1"
    
    player2 = MagicMock()
    player2.name = "Player2"
    player2.character = MagicMock()
    player2.character.id = "player2"
    player2.character.current_room_id = "room1"
    
    gm.players = [player1, player2]
    
    # Create a test event for player1
    test_event = Event(
        message="Player1 requested help.",
        event_type="player_action",
        source_room_id="room1",
        timestamp=datetime.now().isoformat(),
        related_player_id="player1",
        observers=["player"]
    )
    
    # Add event to queue
    gm.event_queue.append(test_event)
    
    # Distribute events
    gm._distribute_events()
    
    # Verify player1 (targeted by player scope) received the event
    assert len(gm.player_observations["player1"]) == 1
    assert gm.player_observations["player1"][0].message == "Player1 requested help."
    
    # Verify player2 (not the target) did NOT receive the event
    assert len(gm.player_observations["player2"]) == 0
    
    # Verify event queue was cleared
    assert len(gm.event_queue) == 0


def test_distribute_events_all_players_scope():
    """Test that events with all_players scope are distributed correctly."""
    # Create a mock GameMaster with minimal setup
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.game_logger.warning = MagicMock()
    gm.event_queue = []
    gm.player_observations = {
        "player1": [],
        "player2": []
    }
    gm.rooms = {
        "room1": MagicMock(id="room1")
    }
    
    # Create mock players
    player1 = MagicMock()
    player1.name = "Player1"
    player1.character = MagicMock()
    player1.character.id = "player1"
    player1.character.current_room_id = "room1"
    
    player2 = MagicMock()
    player2.name = "Player2"
    player2.character = MagicMock()
    player2.character.id = "player2"
    player2.character.current_room_id = "room1"
    
    gm.players = [player1, player2]
    
    # Create a test event for all players
    test_event = Event(
        message="System announcement: Game starting!",
        event_type="system_message",
        source_room_id="room1",
        timestamp=datetime.now().isoformat(),
        related_player_id="system",
        observers=["all_players"]
    )
    
    # Add event to queue
    gm.event_queue.append(test_event)
    
    # Distribute events
    gm._distribute_events()
    
    # Verify both players received the event
    assert len(gm.player_observations["player1"]) == 1
    assert len(gm.player_observations["player2"]) == 1
    assert gm.player_observations["player1"][0].message == "System announcement: Game starting!"
    assert gm.player_observations["player2"][0].message == "System announcement: Game starting!"
    
    # Verify event queue was cleared
    assert len(gm.event_queue) == 0


def test_distribute_events_adjacent_rooms_characters_scope():
    """Test that events with adjacent_rooms_characters scope are distributed correctly."""
    # Create a mock GameMaster with minimal setup
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.game_logger.warning = MagicMock()
    gm.event_queue = []
    gm.player_observations = {
        "player1": [],
        "player2": [],
        "player3": []
    }
    
    # Create mock rooms with exits
    room1 = MagicMock()
    room1.id = "room1"
    room1.exits = {
        "north": {"destination_room_id": "room2"}
    }
    
    room2 = MagicMock()
    room2.id = "room2"
    room2.exits = {
        "south": {"destination_room_id": "room1"}
    }
    
    room3 = MagicMock()
    room3.id = "room3"
    room3.exits = {}
    
    gm.rooms = {"room1": room1, "room2": room2, "room3": room3}
    
    # Create mock players
    player1 = MagicMock()
    player1.name = "Player1"
    player1.character = MagicMock()
    player1.character.id = "player1"
    player1.character.current_room_id = "room1"
    
    player2 = MagicMock()
    player2.name = "Player2"
    player2.character = MagicMock()
    player2.character.id = "player2"
    player2.character.current_room_id = "room2"  # Adjacent to room1
    
    player3 = MagicMock()
    player3.name = "Player3"
    player3.character = MagicMock()
    player3.character.id = "player3"
    player3.character.current_room_id = "room3"  # Not adjacent to room1
    
    gm.players = [player1, player2, player3]
    
    # Create a test event from room1
    test_event = Event(
        message="Loud noise from room1!",
        event_type="environmental",
        source_room_id="room1",
        timestamp=datetime.now().isoformat(),
        related_player_id="system",
        observers=["adjacent_rooms_characters"]
    )
    
    # Add event to queue
    gm.event_queue.append(test_event)
    
    # Distribute events
    gm._distribute_events()
    
    # Verify player1 (in source room) did NOT receive the event
    assert len(gm.player_observations["player1"]) == 0
    
    # Verify player2 (in adjacent room) received the event
    assert len(gm.player_observations["player2"]) == 1
    assert gm.player_observations["player2"][0].message == "Loud noise from room1!"
    
    # Verify player3 (in non-adjacent room) did NOT receive the event
    assert len(gm.player_observations["player3"]) == 0
    
    # Verify event queue was cleared
    assert len(gm.event_queue) == 0


def test_distribute_events_unknown_room():
    """Test that events from unknown rooms are handled gracefully."""
    # Create a mock GameMaster with minimal setup
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.game_logger.warning = MagicMock()
    gm.event_queue = []
    gm.player_observations = {
        "player1": []
    }
    gm.rooms = {"room1": MagicMock(id="room1")}
    
    # Create mock player
    player1 = MagicMock()
    player1.name = "Player1"
    player1.character = MagicMock()
    player1.character.id = "player1"
    player1.character.current_room_id = "room1"
    
    gm.players = [player1]
    
    # Create a test event from unknown room
    test_event = Event(
        message="Event from unknown room",
        event_type="test",
        source_room_id="unknown_room",
        timestamp=datetime.now().isoformat(),
        related_player_id="system",
        observers=["room_characters"]
    )
    
    # Add event to queue
    gm.event_queue.append(test_event)
    
    # Distribute events
    gm._distribute_events()
    
    # Verify warning was logged
    gm.game_logger.warning.assert_called_with("Event originated from unknown room ID: unknown_room. Cannot distribute to room-based observers.")
    
    # Verify no players received the event
    assert len(gm.player_observations["player1"]) == 0
    
    # Verify event queue was cleared
    assert len(gm.event_queue) == 0


def test_distribute_events_empty_queue():
    """Test that distributing from empty queue works correctly."""
    # Create a mock GameMaster with minimal setup
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.event_queue = []
    gm.player_observations = {
        "player1": []
    }
    gm.rooms = {}
    gm.players = []
    
    # Distribute events from empty queue
    gm._distribute_events()
    
    # Should complete without error
    assert len(gm.event_queue) == 0


def test_self_observation_prevention():
    """Test that players cannot observe their own events."""
    # Create a mock GameMaster with minimal setup
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.game_logger.info = MagicMock()
    gm.event_queue = []
    gm.player_observations = {
        "player1": []
    }
    gm.rooms = {
        "room1": MagicMock(id="room1")
    }
    
    # Create mock player
    player1 = MagicMock()
    player1.name = "Player1"
    player1.character = MagicMock()
    player1.character.id = "player1"
    player1.character.current_room_id = "room1"
    
    gm.players = [player1]
    
    # Create a test event from player1
    test_event = Event(
        message="Player1 says: \"Hello!\".",
        event_type="player_communication",
        source_room_id="room1",
        timestamp=datetime.now().isoformat(),
        related_player_id="player1",  # Same as player1's character ID
        observers=["room_characters"]
    )
    
    # Add event to queue
    gm.event_queue.append(test_event)
    
    # Distribute events
    gm._distribute_events()
    
    # Verify player1 did NOT receive their own event
    assert len(gm.player_observations["player1"]) == 0
    
    # Verify event queue was cleared
    assert len(gm.event_queue) == 0
