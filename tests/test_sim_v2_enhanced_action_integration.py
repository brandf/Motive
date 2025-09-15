#!/usr/bin/env python3
"""Enhanced integration tests for portals and containers with unified core actions."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from motive.sim_v2.portals import PortalManager, PortalType
from motive.sim_v2.containers import ContainerManager, ContainerType
from motive.config import Event


class MockGameMaster:
    """Mock GameMaster for testing enhanced observability integration."""
    
    def __init__(self):
        self.rooms = {}
        self.players = []
        self.event_queue = []
        self.player_observations = {}
        self.portal_manager = PortalManager()
        self.container_manager = ContainerManager()
    
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
    
    def get_adjacent_rooms(self, room_id: str) -> List[str]:
        """Get rooms adjacent via exits AND portals."""
        adjacent = []
        room = self.rooms.get(room_id)
        if room:
            # Add normal exits
            for exit_dest in room.exits.values():
                if exit_dest not in adjacent:
                    adjacent.append(exit_dest)
            
            # Add portal destinations
            for portal_id, portal_dest in self.portal_manager._portals.items():
                if portal_dest.room_id not in adjacent:
                    adjacent.append(portal_dest.room_id)
        
        return adjacent
    
    def distribute_events(self):
        """Enhanced event distribution with portal-aware observability."""
        for event in self.event_queue:
            for player in self.players:
                observes = False
                
                if "all_players" in event.observers:
                    observes = True
                elif "player" in event.observers and event.related_player_id == player.id:
                    observes = True
                elif "room_players" in event.observers and player.current_room_id == event.source_room_id:
                    observes = True
                elif "adjacent_rooms" in event.observers:
                    # Check if player's current room is adjacent via exits OR portals
                    adjacent_rooms = self.get_adjacent_rooms(event.source_room_id)
                    if player.current_room_id in adjacent_rooms:
                        observes = True
                
                if observes and event.related_player_id != player.id:
                    self.player_observations[player.id].append(event)
        
        self.event_queue.clear()


def test_shout_through_portals():
    """Test that shouting propagates through portals to destination rooms."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "town_square")  # Adjacent via exit
    player3 = gm.add_player("player3", "Charlie", "forest")   # Adjacent via portal
    
    # Create portal in tavern
    gm.portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    
    # Player1 shouts in tavern
    shout_event = Event(
        message="Alice shouts: \"Help! I'm trapped!\"",
        event_type="player_communication",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["player", "room_players", "adjacent_rooms"]
    )
    gm.event_queue.append(shout_event)
    gm.distribute_events()
    
    # Check observability
    # Alice should not observe her own event
    assert len(gm.player_observations["player1"]) == 0
    
    # Bob should observe (adjacent via exit)
    assert len(gm.player_observations["player2"]) == 1
    assert "Help! I'm trapped!" in gm.player_observations["player2"][0].message
    
    # Charlie should ALSO observe (adjacent via portal)
    assert len(gm.player_observations["player3"]) == 1
    assert "Help! I'm trapped!" in gm.player_observations["player3"][0].message


def test_unified_move_action_with_portals():
    """Test that move action works with portals using natural syntax."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create portal in tavern
    gm.portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    
    # Test unified move action - through portal
    # This would be: "move mirror" or "move through mirror"
    destination = gm.portal_manager.traverse_portal("magic_mirror", "player1", "tavern")
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
        observers=["room_players"]
    )
    gm.event_queue.append(move_event)
    gm.distribute_events()
    
    # Bob should observe Alice's disappearance
    assert len(gm.player_observations["player2"]) == 1
    assert "disappears" in gm.player_observations["player2"][0].message


def test_unified_move_action_with_containers():
    """Test that move action works with containers using natural syntax."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create container
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    
    # Test unified move action - into container
    # This would be: "move into bag" or "enter bag"
    destination = gm.container_manager.enter_container("bag_of_holding", "player1", "tavern")
    assert destination == interior_room
    
    # Update player location
    player1.current_room_id = destination
    
    # Generate move event
    move_event = Event(
        message="Alice climbs into the bag of holding and disappears!",
        event_type="player_movement",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_players"]
    )
    gm.event_queue.append(move_event)
    gm.distribute_events()
    
    # Bob should observe Alice's disappearance
    assert len(gm.player_observations["player2"]) == 1
    assert "disappears" in gm.player_observations["player2"][0].message


def test_throw_through_portals():
    """Test that throw action works through portals."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "town_square")
    player3 = gm.add_player("player3", "Charlie", "forest")
    
    # Create portal
    gm.portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    
    # Player1 throws object through portal
    # This would be: "throw rock through mirror" or "throw rock mirror"
    throw_event = Event(
        message="Alice throws a rock through the magic mirror!",
        event_type="player_action",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_players", "adjacent_rooms"]
    )
    gm.event_queue.append(throw_event)
    gm.distribute_events()
    
    # Bob should observe (adjacent via exit)
    assert len(gm.player_observations["player2"]) == 1
    assert "throws a rock through the magic mirror" in gm.player_observations["player2"][0].message
    
    # Charlie should ALSO observe (adjacent via portal)
    assert len(gm.player_observations["player3"]) == 1
    assert "throws a rock through the magic mirror" in gm.player_observations["player3"][0].message


def test_throw_into_containers():
    """Test that throw action works into containers."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "tavern")
    
    # Create container
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    
    # Player1 throws object into container
    # This would be: "throw rock into bag" or "throw rock bag"
    throw_event = Event(
        message="Alice throws a rock into the bag of holding!",
        event_type="player_action",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_players"]
    )
    gm.event_queue.append(throw_event)
    gm.distribute_events()
    
    # Bob should observe
    assert len(gm.player_observations["player2"]) == 1
    assert "throws a rock into the bag of holding" in gm.player_observations["player2"][0].message


def test_throw_portals_and_containers():
    """Test that portals and containers themselves can be thrown."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    player2 = gm.add_player("player2", "Bob", "town_square")
    
    # Create portal and container
    gm.portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    
    # Player1 throws portal to adjacent room
    # This would be: "throw mirror north"
    throw_portal_event = Event(
        message="Alice throws the magic mirror north!",
        event_type="player_action",
        source_room_id="tavern",
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_players", "adjacent_rooms"]
    )
    gm.event_queue.append(throw_portal_event)
    gm.distribute_events()
    
    # Bob should observe (adjacent room)
    assert len(gm.player_observations["player2"]) == 1
    assert "throws the magic mirror north" in gm.player_observations["player2"][0].message
    
    # Clear observations
    gm.player_observations["player2"] = []
    
    # Player1 throws container to adjacent room
    # This would be: "throw bag north"
    throw_container_event = Event(
        message="Alice throws the bag of holding north!",
        event_type="player_action",
        source_room_id="tavern",
        timestamp="2025-01-01T12:01:00",
        related_player_id="player1",
        observers=["room_players", "adjacent_rooms"]
    )
    gm.event_queue.append(throw_container_event)
    gm.distribute_events()
    
    # Bob should observe
    assert len(gm.player_observations["player2"]) == 1
    assert "throws the bag of holding north" in gm.player_observations["player2"][0].message


def test_shout_into_containers():
    """Test that shouting works into container interiors."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {})
    
    # Create container and its interior
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    
    # Add interior room to game
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    player3 = gm.add_player("player3", "Charlie", "tavern")  # Outside container
    
    # Player1 shouts inside container
    shout_event = Event(
        message="Alice shouts: \"It's roomy in here!\"",
        event_type="player_communication",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_players", "adjacent_rooms"]  # Should include container interior
    )
    gm.event_queue.append(shout_event)
    gm.distribute_events()
    
    # Bob should observe (same interior room)
    assert len(gm.player_observations["player2"]) == 1
    assert "It's roomy in here!" in gm.player_observations["player2"][0].message
    
    # Charlie should NOT observe (outside container, no adjacency)
    assert len(gm.player_observations["player3"]) == 0


def test_mixed_exit_types_in_move():
    """Test that move action can handle mixed exit types (normal + portal + container)."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern", {"north": "town_square"})
    town_square = gm.add_room("town_square", "Town Square", "The heart of the town", {"south": "tavern"})
    forest = gm.add_room("forest", "Forest", "A dark forest", {})
    
    # Create players
    player1 = gm.add_player("player1", "Alice", "tavern")
    
    # Create portal and container in tavern
    gm.portal_manager.create_portal("magic_mirror", "forest", PortalType.STATIC)
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    
    # Test all three move types work from same room
    # Normal exit
    assert "town_square" in tavern.exits.values()
    
    # Portal destination
    portal_dest = gm.portal_manager.get_portal_destination("magic_mirror")
    assert portal_dest == "forest"
    
    # Container interior
    container_dest = gm.container_manager.get_container_interior("bag_of_holding")
    assert container_dest == interior_room
    
    # All three should be accessible via unified move action
    # "move north" -> town_square
    # "move mirror" -> forest  
    # "move bag" -> interior_room
