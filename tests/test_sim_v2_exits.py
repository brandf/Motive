import pytest
from unittest.mock import Mock

from motive.sim_v2.exits import ExitManager, ExitState
from motive.sim_v2.relations import RelationsGraph


def test_exit_manager_creates_exit():
    """Test creating an exit between rooms."""
    manager = ExitManager()
    relations = RelationsGraph()
    
    # Create exit from room_1 to room_2
    exit_id = manager.create_exit("room_1", "room_2", "north", relations)
    
    assert exit_id is not None
    # Verify exit relation exists
    assert "room_2" in relations.get_contents_of("room_1")  # room_1 contains the exit
    # Note: In a full implementation, we'd track exit-specific relations


def test_exit_state_properties():
    """Test exit state properties (visible, traversable, locked)."""
    manager = ExitManager()
    relations = RelationsGraph()
    
    # Create exit
    exit_id = manager.create_exit("room_1", "room_2", "north", relations)
    
    # Get exit state
    exit_state = manager.get_exit_state(exit_id)
    
    # Test default properties
    assert exit_state.visible is True
    assert exit_state.traversable is True
    assert exit_state.is_locked is False


def test_exit_state_modification():
    """Test modifying exit state properties."""
    manager = ExitManager()
    relations = RelationsGraph()
    
    # Create exit
    exit_id = manager.create_exit("room_1", "room_2", "north", relations)
    
    # Modify exit state
    manager.set_exit_visible(exit_id, False)
    manager.set_exit_traversable(exit_id, False)
    manager.set_exit_locked(exit_id, True)
    
    # Verify changes
    exit_state = manager.get_exit_state(exit_id)
    assert exit_state.visible is False
    assert exit_state.traversable is False
    assert exit_state.is_locked is True


def test_exit_traversal_check():
    """Test checking if an exit can be traversed."""
    manager = ExitManager()
    relations = RelationsGraph()
    
    # Create exit
    exit_id = manager.create_exit("room_1", "room_2", "north", relations)
    
    # Test default traversal
    assert manager.can_traverse_exit(exit_id) is True
    
    # Lock the exit
    manager.set_exit_locked(exit_id, True)
    assert manager.can_traverse_exit(exit_id) is False
    
    # Make invisible
    manager.set_exit_visible(exit_id, False)
    assert manager.can_traverse_exit(exit_id) is False


def test_exit_direction_mapping():
    """Test getting exit by direction from a room."""
    manager = ExitManager()
    relations = RelationsGraph()
    
    # Create multiple exits from room_1
    north_exit = manager.create_exit("room_1", "room_2", "north", relations)
    south_exit = manager.create_exit("room_1", "room_3", "south", relations)
    
    # Test getting exits by direction
    assert manager.get_exit_by_direction("room_1", "north") == north_exit
    assert manager.get_exit_by_direction("room_1", "south") == south_exit
    assert manager.get_exit_by_direction("room_1", "east") is None  # No east exit
