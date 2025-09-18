#!/usr/bin/env python3
"""Integration tests for portals and containers with core actions and observability."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from motive.sim_v2.portals import PortalManager, PortalType
from motive.sim_v2.containers import ContainerManager, ContainerType
from motive.config import Event


class MockGameMaster:
    """Mock GameMaster for testing observability integration."""
    
    def __init__(self):
        self.rooms = {}
        self.players = []
        self.event_queue = []
        self.player_observations = {}
    
    def add_room(self, room_id: str, name: str, description: str, exits: Dict[str, str] = None):
        """Add a room to the game."""
        room = Mock()
        room.id = room_id
        room.name = name
        room.description = description
        room.exits = exits or {}
        self.rooms[room_id] = room
        return room
    
    def add_player(self, player_id: str, name: str, current_room_id: str):
        """Add a player to the game."""
        player = Mock()
        player.id = player_id
        player.name = name
        player.current_room_id = current_room_id
        self.players.append(player)
        self.player_observations[player_id] = []
        return player
    
    def distribute_events(self):
        """Mock event distribution logic."""
        for event in self.event_queue:
            for player in self.players:
                observes = False
                
                if "all_players" in event.observers:
                    observes = True
                elif "player" in event.observers and event.related_player_id == player.id:
                    observes = True
                elif "room_characters" in event.observers and player.current_room_id == event.source_room_id:
                    observes = True
                elif "adjacent_rooms_characters" in event.observers:
                    # Check if player's current room is adjacent to event_room
                    event_room = self.rooms.get(event.source_room_id)
                    if event_room:
                        for exit_data in event_room.exits.values():
                            if exit_data == player.current_room_id:
                                observes = True
                                break
                
                if observes and event.related_player_id != player.id:
                    self.player_observations[player.id].append(event)
        
        self.event_queue.clear()


def test_portal_shout_observability():
    """Test that shouting works correctly when portals are present in rooms."""
    gm = MockGameMaster()
    portal_manager = PortalManager()
    
    # Create rooms with exits
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "town_square")
    player3 = gm.add_player("player3", "Charlie", "forest")
    
    # Create portal in tavern
    portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    
    # Player1 shouts in tavern
    shout_event = Event(
        message="Alice shouts: \"Help! I'm trapped!\"",
        event_type="player_communication",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["player", "room_characters", "adjacent_rooms_characters"]
    )
    gm.event_queue.append(shout_event)
    gm.distribute_events()
    
    # Check observability
    # Alice should not observe her own event (she gets feedback instead)
    assert len(gm.player_observations["player1"]) == 0
    
    # Bob should observe (adjacent room via exit)
    assert len(gm.player_observations["player2"]) == 1
    assert "Help! I'm trapped!" in gm.player_observations["player2"][0].message
    
    # Charlie should NOT observe (not adjacent via exits, even though portal exists)
    assert len(gm.player_observations["player3"]) == 0


def test_container_shout_observability():
    """Test that shouting works correctly when containers are present in rooms."""
    gm = MockGameMaster()
    container_manager = ContainerManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "town_square")
    
    # Create container in tavern
    container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = container_manager.get_container_interior("bag_of_holding")
    
    # Player1 shouts in tavern
    shout_event = Event(
        message="Alice shouts: \"I found a bag of holding!\"",
        event_type="player_communication",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["player", "room_characters", "adjacent_rooms_characters"]
    )
    gm.event_queue.append(shout_event)
    gm.distribute_events()
    
    # Check observability
    # Alice should not observe her own event
    assert len(gm.player_observations["player1"]) == 0
    
    # Bob should observe (adjacent room via exit)
    assert len(gm.player_observations["player2"]) == 1
    assert "bag of holding" in gm.player_observations["player2"][0].message


def test_portal_move_action():
    """Test that move action works correctly with portals."""
    gm = MockGameMaster()
    portal_manager = PortalManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create portal in tavern
    portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    
    # Player1 moves through portal (not through normal exit)
    # This would be a custom action that uses portal traversal
    destination = portal_manager.traverse_portal("magic_mirror", "player1", "tavern")
    assert destination == "forest"
    
    # Update player location
    player1.current_room_id = destination
    
    # Generate move event
    move_event = Event(
        message="Alice steps through the magic mirror and disappears!",
        event_type="player_movement",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(move_event)
    gm.distribute_events()
    
    # Bob should observe Alice's disappearance
    assert len(gm.player_observations["player2"]) == 1
    assert "disappears" in gm.player_observations["player2"][0].message


def test_container_enter_exit_observability():
    """Test observability when players enter/exit containers."""
    gm = MockGameMaster()
    container_manager = ContainerManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create container
    container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = container_manager.get_container_interior("bag_of_holding")
    
    # Player1 enters container
    destination = container_manager.enter_container("bag_of_holding", "player1", "tavern")
    assert destination == interior_room
    
    # Generate enter event
    enter_event = Event(
        message="Alice climbs into the bag of holding and disappears!",
        event_type="player_movement",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(enter_event)
    gm.distribute_events()
    
    # Bob should observe Alice's disappearance
    assert len(gm.player_observations["player2"]) == 1
    assert "disappears" in gm.player_observations["player2"][0].message
    
    # Clear observations for next test
    gm.player_observations["player2"] = []
    
    # Player1 exits container
    exterior = container_manager.exit_container("bag_of_holding", "player1", interior_room)
    assert exterior == "tavern"
    
    # Generate exit event
    exit_event = Event(
        message="Alice climbs out of the bag of holding!",
        event_type="player_movement",
        source_room_id="tavern",
        timestamp="2025-01-01T12:01:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(exit_event)
    gm.distribute_events()
    
    # Bob should observe Alice's reappearance
    assert len(gm.player_observations["player2"]) == 1
    assert "climbs out" in gm.player_observations["player2"][0].message


def test_portal_pickup_drop_actions():
    """Test that pickup/drop actions work correctly with portals."""
    gm = MockGameMaster()
    portal_manager = PortalManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create portal
    portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    
    # Player1 picks up portal (if it's an object)
    pickup_event = Event(
        message="Alice picks up the magic mirror.",
        event_type="item_pickup",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(pickup_event)
    gm.distribute_events()
    
    # Bob should observe the pickup
    assert len(gm.player_observations["player2"]) == 1
    assert "picks up the magic mirror" in gm.player_observations["player2"][0].message
    
    # Clear observations
    gm.player_observations["player2"] = []
    
    # Player1 drops portal
    drop_event = Event(
        message="Alice drops the magic mirror.",
        event_type="item_drop",
        source_room_id="tavern",
        timestamp="2025-01-01T12:01:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(drop_event)
    gm.distribute_events()
    
    # Bob should observe the drop
    assert len(gm.player_observations["player2"]) == 1
    assert "drops the magic mirror" in gm.player_observations["player2"][0].message


def test_container_pickup_drop_actions():
    """Test that pickup/drop actions work correctly with containers."""
    gm = MockGameMaster()
    container_manager = ContainerManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create container
    container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    
    # Player1 picks up container
    pickup_event = Event(
        message="Alice picks up the bag of holding.",
        event_type="item_pickup",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(pickup_event)
    gm.distribute_events()
    
    # Bob should observe the pickup
    assert len(gm.player_observations["player2"]) == 1
    assert "picks up the bag of holding" in gm.player_observations["player2"][0].message


def test_portal_throw_action():
    """Test that throw action works correctly with portals."""
    gm = MockGameMaster()
    portal_manager = PortalManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "town_square")
    
    # Create portal
    portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    
    # Player1 throws object through portal (custom action)
    throw_event = Event(
        message="Alice throws a rock through the magic mirror!",
        event_type="player_action",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters", "adjacent_rooms_characters"]
    )
    gm.event_queue.append(throw_event)
    gm.distribute_events()
    
    # Bob should observe (adjacent room)
    assert len(gm.player_observations["player2"]) == 1
    assert "throws a rock through the magic mirror" in gm.player_observations["player2"][0].message


def test_container_interior_observability():
    """Test observability within container interiors."""
    gm = MockGameMaster()
    container_manager = ContainerManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    
    # Create container and its interior
    container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = container_manager.get_container_interior("bag_of_holding")
    
    # Add interior room to game
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    
    # Player1 shouts inside container
    shout_event = Event(
        message="Alice shouts: \"It's roomy in here!\"",
        event_type="player_communication",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(shout_event)
    gm.distribute_events()
    
    # Bob should observe (same interior room)
    assert len(gm.player_observations["player2"]) == 1
    assert "It's roomy in here!" in gm.player_observations["player2"][0].message


def test_portal_dynamic_destination_changes():
    """Test observability when portal destinations change dynamically."""
    gm = MockGameMaster()
    portal_manager = PortalManager()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    dungeon = gm.add_room("dungeon", "Dungeon", "A dark dungeon", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create dynamic portal
    portal_manager.create_portal("teleportation_circle", "forest", PortalType.DYNAMIC)
    
    # Player1 changes portal destination
    portal_manager.set_portal_destination("teleportation_circle", "dungeon")
    
    # Generate portal change event
    change_event = Event(
        message="The teleportation circle's destination changes to the dungeon!",
        event_type="environment_change",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(change_event)
    gm.distribute_events()
    
    # Bob should observe the change
    assert len(gm.player_observations["player2"]) == 1
    assert "destination changes" in gm.player_observations["player2"][0].message
