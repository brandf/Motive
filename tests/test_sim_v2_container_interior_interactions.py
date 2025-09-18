#!/usr/bin/env python3
"""Tests for container interior interactions - objects and characters can interact normally inside containers."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from motive.sim_v2.containers import ContainerManager, ContainerType
from motive.config import Event


class MockGameMaster:
    """Mock GameMaster for testing container interior interactions."""
    
    def __init__(self):
        self.rooms = {}
        self.players = []
        self.event_queue = []
        self.player_observations = {}
        self.container_manager = ContainerManager()
        self.objects = {}  # object_id -> object data
        self.player_inventories = {}  # player_id -> [object_ids]
    
    def add_room(self, room_id: str, name: str, description: str):
        """Add a room to the game."""
        room = Mock()
        room.id = room_id
        room.name = name
        room.description = description
        room.objects = {}  # objects in this room
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
        self.player_inventories[player_id] = []
        return player
    
    def add_object(self, obj_id: str, name: str, location: str):
        """Add an object to the game."""
        obj = Mock()
        obj.id = obj_id
        obj.name = name
        obj.current_location_id = location
        self.objects[obj_id] = obj
        
        # Add to room's object list
        if location in self.rooms:
            self.rooms[location].objects[obj_id] = obj
        
        return obj
    
    def move_object_to_room(self, obj_id: str, room_id: str):
        """Move an object to a room."""
        if obj_id in self.objects:
            obj = self.objects[obj_id]
            old_location = obj.current_location_id
            
            # Remove from old location
            if old_location in self.rooms:
                if obj_id in self.rooms[old_location].objects:
                    del self.rooms[old_location].objects[obj_id]
            
            # Add to new location
            obj.current_location_id = room_id
            if room_id in self.rooms:
                self.rooms[room_id].objects[obj_id] = obj
    
    def distribute_events(self):
        """Distribute events to observers."""
        for event in self.event_queue:
            for player in self.players:
                observes = False
                
                if "all_players" in event.observers:
                    observes = True
                elif "player" in event.observers and event.related_player_id == player.id:
                    observes = True
                elif "room_characters" in event.observers and player.current_room_id == event.source_room_id:
                    observes = True
                
                if observes and event.related_player_id != player.id:
                    self.player_observations[player.id].append(event)
        
        self.event_queue.clear()


def test_container_interior_pickup_drop():
    """Test that players can pickup/drop objects inside container interiors."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern")
    
    # Create container and its interior
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding")
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    
    # Create object inside the container
    key = gm.add_object("key_1", "rusty key", interior_room)
    
    # Player1 picks up key from inside container
    pickup_event = Event(
        message="Alice picks up the rusty key.",
        event_type="item_pickup",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(pickup_event)
    gm.distribute_events()
    
    # Bob should observe the pickup
    assert len(gm.player_observations["player2"]) == 1
    assert "picks up the rusty key" in gm.player_observations["player2"][0].message
    
    # Clear observations
    gm.player_observations["player2"] = []
    
    # Player1 drops key back into container interior
    gm.move_object_to_room("key_1", interior_room)
    
    drop_event = Event(
        message="Alice drops the rusty key.",
        event_type="item_drop",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:01:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(drop_event)
    gm.distribute_events()
    
    # Bob should observe the drop
    assert len(gm.player_observations["player2"]) == 1
    assert "drops the rusty key" in gm.player_observations["player2"][0].message


def test_container_interior_give_action():
    """Test that players can give objects to each other inside container interiors."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern")
    
    # Create container and its interior
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding")
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    
    # Player1 gives object to Player2 inside container
    give_event = Event(
        message="Alice gives the rusty key to Bob.",
        event_type="item_transfer",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(give_event)
    gm.distribute_events()
    
    # Both players should observe the transfer
    assert len(gm.player_observations["player2"]) == 1
    assert "gives the rusty key to Bob" in gm.player_observations["player2"][0].message


def test_container_interior_communication():
    """Test that players can communicate normally inside container interiors."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern")
    
    # Create container and its interior
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding")
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    player3 = gm.add_player("player3", "Charlie", "tavern")  # Outside container
    
    # Player1 says something inside container
    say_event = Event(
        message="Alice says: \"It's cozy in here!\"",
        event_type="player_communication",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(say_event)
    gm.distribute_events()
    
    # Bob should observe (same interior room)
    assert len(gm.player_observations["player2"]) == 1
    assert "It's cozy in here!" in gm.player_observations["player2"][0].message
    
    # Charlie should NOT observe (outside container)
    assert len(gm.player_observations["player3"]) == 0


def test_container_interior_shout():
    """Test that shouting inside containers works normally."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern")
    
    # Create container and its interior
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding")
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    player3 = gm.add_player("player3", "Charlie", "tavern")  # Outside container
    
    # Player1 shouts inside container
    shout_event = Event(
        message="Alice shouts: \"Help! I'm stuck in here!\"",
        event_type="player_communication",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters", "adjacent_rooms_characters"]
    )
    gm.event_queue.append(shout_event)
    gm.distribute_events()
    
    # Bob should observe (same interior room)
    assert len(gm.player_observations["player2"]) == 1
    assert "Help! I'm stuck in here!" in gm.player_observations["player2"][0].message
    
    # Charlie should NOT observe (outside container, no adjacency)
    assert len(gm.player_observations["player3"]) == 0


def test_container_interior_object_interactions():
    """Test that players can interact with objects inside container interiors."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern")
    
    # Create container and its interior
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding")
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    
    # Create objects inside container
    book = gm.add_object("book_1", "ancient tome", interior_room)
    chest = gm.add_object("chest_1", "treasure chest", interior_room)
    
    # Player1 reads book inside container
    read_event = Event(
        message="Alice reads the ancient tome.",
        event_type="player_action",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(read_event)
    gm.distribute_events()
    
    # Bob should observe the reading
    assert len(gm.player_observations["player2"]) == 1
    assert "reads the ancient tome" in gm.player_observations["player2"][0].message
    
    # Clear observations
    gm.player_observations["player2"] = []
    
    # Player1 opens chest inside container
    open_event = Event(
        message="Alice opens the treasure chest.",
        event_type="player_action",
        source_room_id=interior_room,
        timestamp="2025-01-01T12:01:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(open_event)
    gm.distribute_events()
    
    # Bob should observe the opening
    assert len(gm.player_observations["player2"]) == 1
    assert "opens the treasure chest" in gm.player_observations["player2"][0].message


def test_container_interior_multiple_containers():
    """Test that multiple containers can have separate interior spaces."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern")
    
    # Create multiple containers
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    gm.container_manager.create_container("portable_hole", ContainerType.HOLE, capacity=2000)
    
    bag_interior = gm.container_manager.get_container_interior("bag_of_holding")
    hole_interior = gm.container_manager.get_container_interior("portable_hole")
    
    # Add interior rooms
    bag_room = gm.add_room(bag_interior, "Bag Interior", "Inside the bag of holding")
    hole_room = gm.add_room(hole_interior, "Hole Interior", "Inside the portable hole")
    
    # Create players in different containers
    player1 = gm.add_player("player1", "Alice", bag_interior)
    player2 = gm.add_player("player2", "Bob", hole_interior)
    
    # Player1 says something in bag
    say_event = Event(
        message="Alice says: \"I'm in the bag!\"",
        event_type="player_communication",
        source_room_id=bag_interior,
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(say_event)
    gm.distribute_events()
    
    # Bob should NOT observe (different container interior)
    assert len(gm.player_observations["player2"]) == 0
    
    # Clear and test reverse
    gm.player_observations["player2"] = []
    
    # Player2 says something in hole
    say_event2 = Event(
        message="Bob says: \"I'm in the hole!\"",
        event_type="player_communication",
        source_room_id=hole_interior,
        timestamp="2025-01-01T12:01:00",
        related_player_id="player2",
        observers=["room_characters"]
    )
    gm.event_queue.append(say_event2)
    gm.distribute_events()
    
    # Alice should NOT observe (different container interior)
    assert len(gm.player_observations["player1"]) == 0


def test_container_interior_exit_reentry():
    """Test that players can exit and re-enter containers, maintaining interior state."""
    gm = MockGameMaster()
    
    # Create rooms
    tavern = gm.add_room("tavern", "Tavern", "A cozy tavern")
    
    # Create container and its interior
    gm.container_manager.create_container("bag_of_holding", ContainerType.BAG, capacity=1000)
    interior_room = gm.container_manager.get_container_interior("bag_of_holding")
    interior = gm.add_room(interior_room, "Bag Interior", "Inside the bag of holding")
    
    # Create players
    player1 = gm.add_player("player1", "Alice", interior_room)
    player2 = gm.add_player("player2", "Bob", interior_room)
    
    # Create object inside container
    key = gm.add_object("key_1", "rusty key", interior_room)
    
    # Player1 exits container
    exit_event = Event(
        message="Alice climbs out of the bag of holding.",
        event_type="player_movement",
        source_room_id=interior_room,  # Event happens in interior room
        timestamp="2025-01-01T12:00:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(exit_event)
    gm.distribute_events()
    
    # Update player location
    player1.current_room_id = "tavern"
    
    # Bob should observe Alice's exit
    assert len(gm.player_observations["player2"]) == 1
    assert "climbs out" in gm.player_observations["player2"][0].message
    
    # Clear observations
    gm.player_observations["player2"] = []
    
    # Player1 re-enters container
    reenter_event = Event(
        message="Alice climbs back into the bag of holding.",
        event_type="player_movement",
        source_room_id=interior_room,  # Event happens in interior room
        timestamp="2025-01-01T12:01:00",
        related_player_id="player1",
        observers=["room_characters"]
    )
    gm.event_queue.append(reenter_event)
    gm.distribute_events()
    
    # Update player location
    player1.current_room_id = interior_room
    
    # Bob should observe Alice's re-entry
    assert len(gm.player_observations["player2"]) == 1
    assert "climbs back into" in gm.player_observations["player2"][0].message
    
    # The key should still be in the container interior
    assert key.current_location_id == interior_room
    assert "key_1" in interior.objects
