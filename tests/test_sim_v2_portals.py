#!/usr/bin/env python3
"""Tests for sim_v2 portals system."""

import pytest
from motive.sim_v2.portals import (
    PortalManager, 
    PortalType, 
    PortalDestination
)


def test_portal_manager_create_static_portal():
    """Test creating a static portal with fixed destination."""
    manager = PortalManager()
    
    # Create static portal
    result = manager.create_portal("magic_mirror_1", "town_square", PortalType.STATIC)
    assert result is True
    
    # Check destination
    destination = manager.get_portal_destination("magic_mirror_1")
    assert destination == "town_square"
    
    # Check portal properties
    properties = manager.get_portal_properties("magic_mirror_1")
    assert properties["portal_type"] == PortalType.STATIC
    assert properties["destination"] == "town_square"


def test_portal_manager_create_dynamic_portal():
    """Test creating a dynamic portal with changeable destination."""
    manager = PortalManager()
    
    # Create dynamic portal
    result = manager.create_portal("teleportation_circle", "town_square", PortalType.DYNAMIC)
    assert result is True
    
    # Check initial destination
    destination = manager.get_portal_destination("teleportation_circle")
    assert destination == "town_square"
    
    # Change destination
    result = manager.set_portal_destination("teleportation_circle", "forest_clearing")
    assert result is True
    
    # Check new destination
    destination = manager.get_portal_destination("teleportation_circle")
    assert destination == "forest_clearing"


def test_portal_manager_traversal_conditions():
    """Test portal traversal with conditions."""
    manager = PortalManager()
    
    # Create portal
    manager.create_portal("magic_mirror_1", "town_square", PortalType.STATIC)
    
    # Test traversal from room (should work)
    result = manager.can_traverse_portal("magic_mirror_1", "player_1", "tavern")
    assert result is True
    
    # Test traversal from inventory (should fail)
    result = manager.can_traverse_portal("magic_mirror_1", "player_1", "player_1_inventory")
    assert result is False
    
    # Test actual traversal
    destination = manager.traverse_portal("magic_mirror_1", "player_1", "tavern")
    assert destination == "town_square"


def test_portal_manager_multiple_portals():
    """Test managing multiple portals."""
    manager = PortalManager()
    
    # Create multiple portals
    manager.create_portal("mirror_1", "town_square", PortalType.STATIC)
    manager.create_portal("mirror_2", "forest_clearing", PortalType.STATIC)
    manager.create_portal("circle_1", "dungeon_entrance", PortalType.DYNAMIC)
    
    # Check all destinations
    assert manager.get_portal_destination("mirror_1") == "town_square"
    assert manager.get_portal_destination("mirror_2") == "forest_clearing"
    assert manager.get_portal_destination("circle_1") == "dungeon_entrance"
    
    # Change dynamic portal destination
    manager.set_portal_destination("circle_1", "treasure_room")
    assert manager.get_portal_destination("circle_1") == "treasure_room"


def test_portal_manager_destroy_portal():
    """Test destroying portals."""
    manager = PortalManager()
    
    # Create portal
    manager.create_portal("magic_mirror_1", "town_square", PortalType.STATIC)
    assert manager.get_portal_destination("magic_mirror_1") == "town_square"
    
    # Destroy portal
    result = manager.destroy_portal("magic_mirror_1")
    assert result is True
    
    # Check portal is gone
    destination = manager.get_portal_destination("magic_mirror_1")
    assert destination is None


def test_portal_manager_error_handling():
    """Test error handling for invalid operations."""
    manager = PortalManager()
    
    # Try to get destination for non-existent portal
    destination = manager.get_portal_destination("nonexistent")
    assert destination is None
    
    # Try to set destination for non-existent portal
    result = manager.set_portal_destination("nonexistent", "somewhere")
    assert result is False
    
    # Try to traverse non-existent portal
    result = manager.can_traverse_portal("nonexistent", "player_1", "room_1")
    assert result is False
    
    destination = manager.traverse_portal("nonexistent", "player_1", "room_1")
    assert destination is None
    
    # Try to destroy non-existent portal
    result = manager.destroy_portal("nonexistent")
    assert result is False


def test_portal_manager_properties():
    """Test portal property management."""
    manager = PortalManager()
    
    # Create portal
    manager.create_portal("magic_mirror_1", "town_square", PortalType.STATIC)
    
    # Set custom properties
    manager.set_portal_properties("magic_mirror_1", {
        "weight": 50,
        "description": "A mirror that shows different locations",
        "activation_cost": 10
    })
    
    # Get properties
    properties = manager.get_portal_properties("magic_mirror_1")
    assert properties["portal_type"] == PortalType.STATIC
    assert properties["destination"] == "town_square"
    assert properties["weight"] == 50
    assert properties["description"] == "A mirror that shows different locations"
    assert properties["activation_cost"] == 10
