#!/usr/bin/env python3
"""Tests for entity lifecycle integration with enhanced configs."""

import pytest
import yaml
from motive.sim_v2.entity_lifecycle import (
    EntityLifecycleManager, 
    EntityState, 
    EntityLifecycleEvent
)


def load_enhanced_yaml_config(file_path):
    """Load enhanced YAML config file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def test_entity_lifecycle_in_enhanced_config():
    """Test that enhanced config includes entity lifecycle definitions."""
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_v2.yaml")
    
    # Check that detective_thorne has entity_lifecycle
    detective = config["characters"]["detective_thorne"]
    assert "entity_lifecycle" in detective
    
    lifecycle_config = detective["entity_lifecycle"]
    
    # Check spawn definitions
    assert "spawn_definitions" in lifecycle_config
    spawn_defs = lifecycle_config["spawn_definitions"]
    assert len(spawn_defs) == 2
    
    # Check evidence_bag spawn definition
    evidence_bag = next(defn for defn in spawn_defs if defn["definition_id"] == "evidence_bag")
    assert evidence_bag["spawn_location"] == "current"
    assert evidence_bag["custom_properties"]["evidence_type"] == "physical"
    assert evidence_bag["custom_properties"]["integrity"] == 100
    
    # Check investigation_note spawn definition
    investigation_note = next(defn for defn in spawn_defs if defn["definition_id"] == "investigation_note")
    assert investigation_note["spawn_location"] == "current"
    assert investigation_note["custom_properties"]["confidentiality"] == "high"
    
    # Check clone capabilities
    assert "clone_capabilities" in lifecycle_config
    clone_caps = lifecycle_config["clone_capabilities"]
    assert len(clone_caps) == 1
    assert "evidence_bag" in clone_caps[0]["source_entity_types"]
    assert "investigation_note" in clone_caps[0]["source_entity_types"]
    
    # Check destroy capabilities
    assert "destroy_capabilities" in lifecycle_config
    destroy_caps = lifecycle_config["destroy_capabilities"]
    assert len(destroy_caps) == 1
    assert "evidence_bag" in destroy_caps[0]["entity_types"]
    assert "investigation_note" in destroy_caps[0]["entity_types"]


def test_entity_lifecycle_manager_with_config_data():
    """Test EntityLifecycleManager with data from enhanced config."""
    manager = EntityLifecycleManager()
    
    # Spawn entities based on config data
    evidence_bag_id = manager.spawn_entity(
        "evidence_bag", 
        "room_1", 
        {"evidence_type": "physical", "integrity": 100, "description": "A sturdy bag for collecting evidence"}
    )
    
    investigation_note_id = manager.spawn_entity(
        "investigation_note", 
        "room_1", 
        {"content": "Investigation findings", "confidentiality": "high", "description": "Detailed notes from your investigation"}
    )
    
    # Test that entities are spawned correctly
    assert manager.is_entity_active(evidence_bag_id) is True
    assert manager.is_entity_active(investigation_note_id) is True
    
    # Test entity data
    evidence_data = manager.get_entity_data(evidence_bag_id)
    assert evidence_data["definition_id"] == "evidence_bag"
    assert evidence_data["location"] == "room_1"
    assert evidence_data["evidence_type"] == "physical"
    assert evidence_data["integrity"] == 100
    
    note_data = manager.get_entity_data(investigation_note_id)
    assert note_data["definition_id"] == "investigation_note"
    assert note_data["confidentiality"] == "high"
    
    # Test cloning based on config capabilities
    clone_id = manager.clone_entity(evidence_bag_id, "room_2")
    assert clone_id is not None
    assert manager.is_entity_active(clone_id) is True
    
    clone_data = manager.get_entity_data(clone_id)
    assert clone_data["definition_id"] == "evidence_bag"
    assert clone_data["location"] == "room_2"
    assert clone_data["evidence_type"] == "physical"
    assert clone_data["integrity"] == 100  # Original integrity preserved
    
    # Test destroying based on config capabilities
    result = manager.destroy_entity(investigation_note_id, "compromised")
    assert result is True
    assert manager.is_entity_active(investigation_note_id) is False


def test_entity_lifecycle_manager_spawn_multiple_from_config():
    """Test spawning multiple entities from config definitions."""
    manager = EntityLifecycleManager()
    
    # Spawn multiple evidence bags
    bag1_id = manager.spawn_entity("evidence_bag", "room_1", {"evidence_type": "physical", "integrity": 100})
    bag2_id = manager.spawn_entity("evidence_bag", "room_2", {"evidence_type": "digital", "integrity": 80})
    bag3_id = manager.spawn_entity("evidence_bag", "room_1", {"evidence_type": "witness", "integrity": 90})
    
    # All should be active and unique
    assert manager.is_entity_active(bag1_id) is True
    assert manager.is_entity_active(bag2_id) is True
    assert manager.is_entity_active(bag3_id) is True
    
    assert bag1_id != bag2_id
    assert bag2_id != bag3_id
    assert bag1_id != bag3_id
    
    # Check active entities
    active_entities = manager.get_active_entities()
    assert len(active_entities) == 3
    assert bag1_id in active_entities
    assert bag2_id in active_entities
    assert bag3_id in active_entities


def test_entity_lifecycle_manager_clone_with_modifications():
    """Test cloning entities with modifications as specified in config."""
    manager = EntityLifecycleManager()
    
    # Spawn original entity
    original_id = manager.spawn_entity(
        "evidence_bag", 
        "room_1", 
        {"evidence_type": "physical", "integrity": 100, "description": "Original evidence bag"}
    )
    
    # Clone with modifications (as per config clone_modifications)
    clone_id = manager.clone_entity(original_id, "room_2")
    assert clone_id is not None
    
    # Get clone data and apply modifications manually (simulating config-based modifications)
    clone_data = manager.get_entity_data(clone_id)
    
    # Simulate the clone_modifications from config
    clone_data["evidence_type"] = "copy"  # Modified as per config
    clone_data["integrity"] = 50  # Modified as per config
    
    # Update the clone data (this would be done by the system applying config modifications)
    manager._entities[clone_id].update(clone_data)
    
    # Verify modifications
    modified_clone_data = manager.get_entity_data(clone_id)
    assert modified_clone_data["evidence_type"] == "copy"
    assert modified_clone_data["integrity"] == 50
    assert modified_clone_data["description"] == "Original evidence bag"  # Unmodified


def test_entity_lifecycle_manager_destroy_with_reasons():
    """Test destroying entities with different reasons as specified in config."""
    manager = EntityLifecycleManager()
    
    # Spawn entities
    bag_id = manager.spawn_entity("evidence_bag", "room_1", {"integrity": 100})
    note_id = manager.spawn_entity("investigation_note", "room_1", {"confidentiality": "high"})
    
    # Destroy with different reasons from config
    result1 = manager.destroy_entity(bag_id, "compromised")
    result2 = manager.destroy_entity(note_id, "outdated")
    
    assert result1 is True
    assert result2 is True
    
    # Check lifecycle events
    bag_events = manager.get_lifecycle_events(bag_id)
    note_events = manager.get_lifecycle_events(note_id)
    
    assert len(bag_events) == 2  # spawn + destroy
    assert bag_events[1].event_type == "destroy"
    assert bag_events[1].metadata["reason"] == "compromised"
    
    assert len(note_events) == 2  # spawn + destroy
    assert note_events[1].event_type == "destroy"
    assert note_events[1].metadata["reason"] == "outdated"
