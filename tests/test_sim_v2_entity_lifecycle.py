#!/usr/bin/env python3
"""Tests for sim_v2 entity lifecycle system."""

import pytest
from motive.sim_v2.entity_lifecycle import (
    EntityLifecycleManager, 
    EntityState, 
    EntityLifecycleEvent
)


def test_entity_lifecycle_manager_spawn():
    """Test spawning new entities."""
    manager = EntityLifecycleManager()
    
    # Spawn a new entity
    entity_id = manager.spawn_entity("torch_def", "room_1", {"fuel": 100, "is_lit": False})
    
    assert entity_id is not None
    assert manager.is_entity_active(entity_id) is True
    assert manager.get_entity_state(entity_id) == EntityState.ACTIVE
    
    # Check entity data
    entity_data = manager.get_entity_data(entity_id)
    assert entity_data is not None
    assert entity_data["definition_id"] == "torch_def"
    assert entity_data["location"] == "room_1"
    assert entity_data["fuel"] == 100
    assert entity_data["is_lit"] is False
    
    # Check lifecycle events
    events = manager.get_lifecycle_events(entity_id)
    assert len(events) == 1
    assert events[0].event_type == "spawn"
    assert events[0].entity_id == entity_id


def test_entity_lifecycle_manager_destroy():
    """Test destroying entities."""
    manager = EntityLifecycleManager()
    
    # Spawn an entity
    entity_id = manager.spawn_entity("torch_def", "room_1", {"fuel": 100})
    assert manager.is_entity_active(entity_id) is True
    
    # Destroy the entity
    result = manager.destroy_entity(entity_id, "burned_out")
    assert result is True
    assert manager.is_entity_active(entity_id) is False
    assert manager.get_entity_state(entity_id) == EntityState.DESTROYED
    assert manager.get_entity_data(entity_id) is None
    
    # Check lifecycle events
    events = manager.get_lifecycle_events(entity_id)
    assert len(events) == 2
    assert events[0].event_type == "spawn"
    assert events[1].event_type == "destroy"
    assert events[1].metadata["reason"] == "burned_out"


def test_entity_lifecycle_manager_clone():
    """Test cloning entities."""
    manager = EntityLifecycleManager()
    
    # Spawn an entity
    entity_id = manager.spawn_entity("torch_def", "room_1", {"fuel": 100, "is_lit": True})
    
    # Clone the entity
    clone_id = manager.clone_entity(entity_id, "room_2")
    assert clone_id is not None
    assert clone_id != entity_id
    assert manager.is_entity_active(clone_id) is True
    assert manager.get_entity_state(clone_id) == EntityState.CLONED
    
    # Check clone data
    clone_data = manager.get_entity_data(clone_id)
    assert clone_data is not None
    assert clone_data["definition_id"] == "torch_def"
    assert clone_data["location"] == "room_2"
    assert clone_data["fuel"] == 100
    assert clone_data["is_lit"] is True
    
    # Check lifecycle events
    events = manager.get_lifecycle_events(clone_id)
    assert len(events) == 1
    assert events[0].event_type == "clone"
    assert events[0].metadata["source_entity"] == entity_id


def test_entity_lifecycle_manager_multiple_entities():
    """Test managing multiple entities."""
    manager = EntityLifecycleManager()
    
    # Spawn multiple entities
    torch_id = manager.spawn_entity("torch_def", "room_1", {"fuel": 100})
    sword_id = manager.spawn_entity("sword_def", "room_1", {"damage": 10})
    potion_id = manager.spawn_entity("potion_def", "room_2", {"healing": 50})
    
    # Check all are active
    active_entities = manager.get_active_entities()
    assert len(active_entities) == 3
    assert torch_id in active_entities
    assert sword_id in active_entities
    assert potion_id in active_entities
    
    # Destroy one entity
    manager.destroy_entity(potion_id, "consumed")
    
    # Check remaining active entities
    active_entities = manager.get_active_entities()
    assert len(active_entities) == 2
    assert torch_id in active_entities
    assert sword_id in active_entities
    assert potion_id not in active_entities


def test_entity_lifecycle_manager_error_handling():
    """Test error handling for invalid operations."""
    manager = EntityLifecycleManager()
    
    # Try to destroy non-existent entity
    result = manager.destroy_entity("nonexistent", "test")
    assert result is False
    
    # Try to clone non-existent entity
    clone_id = manager.clone_entity("nonexistent")
    assert clone_id is None
    
    # Try to get data for non-existent entity
    data = manager.get_entity_data("nonexistent")
    assert data is None
    
    # Try to get state for non-existent entity
    state = manager.get_entity_state("nonexistent")
    assert state is None


def test_entity_lifecycle_manager_unique_ids():
    """Test that spawned entities get unique IDs."""
    manager = EntityLifecycleManager()
    
    # Spawn multiple entities
    id1 = manager.spawn_entity("torch_def", "room_1")
    id2 = manager.spawn_entity("torch_def", "room_1")
    id3 = manager.spawn_entity("sword_def", "room_1")
    
    # All IDs should be unique
    assert id1 != id2
    assert id2 != id3
    assert id1 != id3
    
    # All should be active
    assert manager.is_entity_active(id1) is True
    assert manager.is_entity_active(id2) is True
    assert manager.is_entity_active(id3) is True


def test_entity_lifecycle_manager_clone_without_location():
    """Test cloning entities without specifying new location."""
    manager = EntityLifecycleManager()
    
    # Spawn an entity
    entity_id = manager.spawn_entity("torch_def", "room_1", {"fuel": 100})
    
    # Clone without specifying location (should use same location)
    clone_id = manager.clone_entity(entity_id)
    assert clone_id is not None
    
    clone_data = manager.get_entity_data(clone_id)
    assert clone_data["location"] == "room_1"  # Same location as original
