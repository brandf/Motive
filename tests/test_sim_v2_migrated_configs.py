#!/usr/bin/env python3
"""Tests for migrated v2 configs."""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any

from motive.sim_v2.config_loader import V2ConfigLoader


def load_config_file(file_path: str) -> Dict[str, Any]:
    """Load a config file from the project root."""
    config_path = Path(__file__).parent.parent / file_path
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_migrated_rooms_config():
    """Test that migrated rooms config loads correctly."""
    loader = V2ConfigLoader()
    
    # Load migrated config
    config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_migrated.yaml")
    
    # Load as v2 config
    loader.load_v2_config(config)
    
    # Verify migration
    summary = loader.get_migration_summary()
    assert summary['definitions_loaded'] == 11  # Should have 11 rooms
    
    # Verify specific rooms exist
    registry = loader.definitions
    expected_rooms = ["town_square", "tavern", "adventurer_guild", "thieves_den", "church", 
                     "cemetery", "bank", "market_district", "underground_tunnels", 
                     "secret_cult_chamber", "old_forest_path"]
    
    for room_id in expected_rooms:
        assert room_id in registry._defs, f"Room {room_id} not in migrated config"
        
        # Verify room properties
        room_def = registry.get(room_id)
        assert "room" in room_def.types
        assert room_def.properties["name"].default is not None
        assert room_def.properties["description"].default is not None


def test_migrated_objects_config():
    """Test that migrated objects config loads correctly."""
    loader = V2ConfigLoader()
    
    # Load migrated config
    config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_migrated.yaml")
    
    # Load as v2 config
    loader.load_v2_config(config)
    
    # Verify migration
    summary = loader.get_migration_summary()
    assert summary['definitions_loaded'] == 65  # Should have 65 objects
    
    # Verify specific objects exist
    registry = loader.definitions
    expected_objects = ["notice_board", "torch", "broken_fountain", "bar", "quest_board"]
    
    for obj_id in expected_objects:
        assert obj_id in registry._defs, f"Object {obj_id} not in migrated config"
        
        # Verify object properties
        obj_def = registry.get(obj_id)
        assert "object" in obj_def.types
        assert obj_def.properties["name"].default is not None
        assert obj_def.properties["description"].default is not None


def test_migrated_characters_config():
    """Test that migrated characters config loads correctly."""
    loader = V2ConfigLoader()
    
    # Load migrated config
    config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_migrated.yaml")
    
    # Load as v2 config
    loader.load_v2_config(config)
    
    # Verify migration
    summary = loader.get_migration_summary()
    assert summary['definitions_loaded'] == 8  # Should have 8 characters
    
    # Verify specific characters exist
    registry = loader.definitions
    expected_characters = ["detective_thorne", "mayor_victoria_blackwater", "father_marcus", 
                          "guild_master_elena", "dr_sarah_chen"]
    
    for char_id in expected_characters:
        assert char_id in registry._defs, f"Character {char_id} not in migrated config"
        
        # Verify character properties
        char_def = registry.get(char_id)
        assert "character" in char_def.types
        assert char_def.properties["name"].default is not None
        assert char_def.properties["backstory"].default is not None


def test_migrated_main_config():
    """Test that the main migrated config loads correctly."""
    loader = V2ConfigLoader()
    
    # Load main migrated config
    config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml")
    
    # Load as v2 config
    loader.load_v2_config(config)
    
    # Verify all content was loaded
    summary = loader.get_migration_summary()
    assert summary['definitions_loaded'] > 0  # Should have definitions from all configs


def test_migrated_config_preserves_content():
    """Test that migrated configs preserve all original content."""
    loader = V2ConfigLoader()
    
    # Load original v1 config
    v1_config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    loader.migrate_v1_to_v2(v1_config)
    v1_summary = loader.get_migration_summary()
    
    # Load migrated v2 config
    loader2 = V2ConfigLoader()
    v2_config = loader2.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml")
    loader2.load_v2_config(v2_config)
    v2_summary = loader2.get_migration_summary()
    
    # Both should have the same content
    assert v1_summary['definitions_loaded'] == v2_summary['definitions_loaded']
    assert v1_summary['actions_loaded'] == v2_summary['actions_loaded']


def test_migrated_config_with_v2_systems():
    """Test that migrated configs work with v2 systems."""
    loader = V2ConfigLoader()
    
    # Load migrated config
    config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml")
    loader.load_v2_config(config)
    
    # Test with v2 systems
    from motive.sim_v2.relations import RelationsGraph
    from motive.sim_v2.effects import EffectEngine, SetPropertyEffect
    
    registry = loader.definitions
    relations = RelationsGraph()
    effect_engine = EffectEngine()
    
    # Create entities from migrated definitions
    town_square = registry.create_entity("town_square", "town_square_instance")
    torch = registry.create_entity("torch", "torch_instance")
    
    # Test relations
    relations.place_entity("player1", "town_square_instance")
    assert relations.get_contents_of("town_square_instance") == ["player1"]
    
    # Test effects
    effect = SetPropertyEffect(
        target_entity="torch_instance",
        property_name="fuel",
        value=50
    )
    
    entities = {"torch_instance": torch}
    effect_engine.execute_effect(effect, entities)
    assert torch.get_property("fuel") == 50


def test_migrated_config_validation():
    """Test that migrated configs are valid YAML and load without errors."""
    config_files = [
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml",
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_migrated.yaml",
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_migrated.yaml",
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_migrated.yaml",
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_actions_migrated.yaml"
    ]
    
    for config_file in config_files:
        # Should load without errors
        config = load_config_file(config_file)
        assert config is not None
        
        # Should have expected structure
        if "entity_definitions" in config:
            assert isinstance(config["entity_definitions"], dict)
        if "action_definitions" in config:
            assert isinstance(config["action_definitions"], dict)
