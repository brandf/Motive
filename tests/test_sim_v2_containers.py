#!/usr/bin/env python3
"""Tests for sim_v2 containers system."""

import pytest
from motive.sim_v2.containers import (
    ContainerManager, 
    ContainerType, 
    ContainerInterior
)


def test_container_manager_create_bag_of_holding():
    """Test creating a bag of holding with interior space."""
    manager = ContainerManager()
    
    # Create bag of holding
    result = manager.create_container("bag_of_holding_1", ContainerType.BAG, capacity=1000)
    assert result is True
    
    # Check interior space was created
    interior_room = manager.get_container_interior("bag_of_holding_1")
    assert interior_room is not None
    assert interior_room.startswith("bag_of_holding_1_interior")
    
    # Check capacity
    capacity = manager.get_container_capacity("bag_of_holding_1")
    assert capacity == 1000
    
    # Check properties
    properties = manager.get_container_properties("bag_of_holding_1")
    assert properties["container_type"] == ContainerType.BAG
    assert properties["capacity"] == 1000


def test_container_manager_create_portable_hole():
    """Test creating a portable hole with interior space."""
    manager = ContainerManager()
    
    # Create portable hole
    result = manager.create_container("portable_hole_1", ContainerType.HOLE, capacity=500)
    assert result is True
    
    # Check interior space
    interior_room = manager.get_container_interior("portable_hole_1")
    assert interior_room is not None
    assert interior_room.startswith("portable_hole_1_interior")
    
    # Check capacity
    capacity = manager.get_container_capacity("portable_hole_1")
    assert capacity == 500


def test_container_manager_enter_exit_container():
    """Test entering and exiting containers."""
    manager = ContainerManager()
    
    # Create container
    manager.create_container("bag_of_holding_1", ContainerType.BAG, capacity=1000)
    
    # Test entering from room (should work)
    result = manager.can_enter_container("bag_of_holding_1", "player_1", "tavern")
    assert result is True
    
    # Test entering from inventory (should fail)
    result = manager.can_enter_container("bag_of_holding_1", "player_1", "player_1_inventory")
    assert result is False
    
    # Test actual entry
    interior_room = manager.enter_container("bag_of_holding_1", "player_1", "tavern")
    assert interior_room is not None
    assert interior_room.startswith("bag_of_holding_1_interior")
    
    # Test exit
    exterior_room = manager.exit_container("bag_of_holding_1", "player_1", interior_room)
    assert exterior_room == "tavern"  # Should return to original location


def test_container_manager_multiple_containers():
    """Test managing multiple containers."""
    manager = ContainerManager()
    
    # Create multiple containers
    manager.create_container("bag_1", ContainerType.BAG, capacity=1000)
    manager.create_container("bag_2", ContainerType.BAG, capacity=500)
    manager.create_container("hole_1", ContainerType.HOLE, capacity=2000)
    
    # Check all have unique interior spaces
    interior_1 = manager.get_container_interior("bag_1")
    interior_2 = manager.get_container_interior("bag_2")
    interior_3 = manager.get_container_interior("hole_1")
    
    assert interior_1 != interior_2
    assert interior_2 != interior_3
    assert interior_1 != interior_3
    
    # Check capacities
    assert manager.get_container_capacity("bag_1") == 1000
    assert manager.get_container_capacity("bag_2") == 500
    assert manager.get_container_capacity("hole_1") == 2000


def test_container_manager_destroy_container():
    """Test destroying containers and their interior spaces."""
    manager = ContainerManager()
    
    # Create container
    manager.create_container("bag_of_holding_1", ContainerType.BAG, capacity=1000)
    interior_room = manager.get_container_interior("bag_of_holding_1")
    assert interior_room is not None
    
    # Destroy container
    result = manager.destroy_container("bag_of_holding_1")
    assert result is True
    
    # Check container is gone
    interior_room = manager.get_container_interior("bag_of_holding_1")
    assert interior_room is None


def test_container_manager_error_handling():
    """Test error handling for invalid operations."""
    manager = ContainerManager()
    
    # Try to get interior for non-existent container
    interior = manager.get_container_interior("nonexistent")
    assert interior is None
    
    # Try to enter non-existent container
    result = manager.can_enter_container("nonexistent", "player_1", "room_1")
    assert result is False
    
    interior = manager.enter_container("nonexistent", "player_1", "room_1")
    assert interior is None
    
    # Try to exit non-existent container
    exterior = manager.exit_container("nonexistent", "player_1", "room_1")
    assert exterior is None
    
    # Try to destroy non-existent container
    result = manager.destroy_container("nonexistent")
    assert result is False


def test_container_manager_properties():
    """Test container property management."""
    manager = ContainerManager()
    
    # Create container
    manager.create_container("bag_of_holding_1", ContainerType.BAG, capacity=1000)
    
    # Set custom properties
    manager.set_container_properties("bag_of_holding_1", {
        "weight": 5,
        "description": "A magical bag that leads to a pocket dimension",
        "magical": True
    })
    
    # Get properties
    properties = manager.get_container_properties("bag_of_holding_1")
    assert properties["container_type"] == ContainerType.BAG
    assert properties["capacity"] == 1000
    assert properties["weight"] == 5
    assert properties["description"] == "A magical bag that leads to a pocket dimension"
    assert properties["magical"] is True


def test_container_manager_capacity_management():
    """Test container capacity management."""
    manager = ContainerManager()
    
    # Create container
    manager.create_container("bag_of_holding_1", ContainerType.BAG, capacity=1000)
    
    # Check initial capacity
    capacity = manager.get_container_capacity("bag_of_holding_1")
    assert capacity == 1000
    
    # Update capacity
    result = manager.set_container_capacity("bag_of_holding_1", 2000)
    assert result is True
    
    # Check updated capacity
    capacity = manager.get_container_capacity("bag_of_holding_1")
    assert capacity == 2000
    
    # Try to update non-existent container
    result = manager.set_container_capacity("nonexistent", 1000)
    assert result is False
