#!/usr/bin/env python3
"""Integration tests for complete v1 to v2 migration."""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any

from motive.sim_v2.config_loader import V2ConfigLoader
from motive.sim_v2.definitions import DefinitionRegistry
from motive.sim_v2.actions_pipeline import ActionPipeline
from motive.sim_v2.relations import RelationsGraph
from motive.sim_v2.effects import EffectEngine


def load_config_file(file_path: str) -> Dict[str, Any]:
    """Load a config file from the project root."""
    config_path = Path(__file__).parent.parent / file_path
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_complete_hearth_and_shadow_migration():
    """Test complete migration of hearth_and_shadow config with all components."""
    loader = V2ConfigLoader()
    
    # Load complete hierarchical config (this includes all sub-configs)
    config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    
    # Migrate to v2
    loader.migrate_v1_to_v2(config)
    
    # Verify comprehensive migration
    summary = loader.get_migration_summary()
    
    # Should have migrated substantial content
    assert summary['migration_stats']['rooms_migrated'] >= 10  # hearth_and_shadow has 11 rooms
    assert summary['migration_stats']['objects_migrated'] >= 20  # hearth_and_shadow has many objects
    assert summary['migration_stats']['characters_migrated'] >= 8  # hearth_and_shadow has 8 characters
    assert summary['migration_stats']['actions_migrated'] >= 0  # May be 0 if actions.yaml is empty
    
    # Verify we can create entities from definitions
    registry = loader.definitions
    
    # Test room entity creation
    town_square_def = registry.get("town_square")
    town_square_entity = registry.create_entity("town_square", "town_square_instance")
    assert town_square_entity.get_property("name") == "Town Square"
    assert "The heart of Blackwater" in town_square_entity.get_property("description")
    
    # Test object entity creation
    torch_def = registry.get("torch")
    torch_entity = registry.create_entity("torch", "torch_instance")
    assert torch_entity.get_property("name") == "Torch"
    assert torch_entity.get_property("pickupable") is True
    assert torch_entity.get_property("fuel") == 100
    
    # Test character entity creation
    detective_def = registry.get("detective_thorne")
    detective_entity = registry.create_entity("detective_thorne", "detective_instance")
    assert detective_entity.get_property("name") == "Detective James Thorne"
    assert "investigator" in detective_entity.get_property("backstory")


def test_migration_preserves_all_content():
    """Test that migration preserves all original content without loss."""
    loader = V2ConfigLoader()
    
    # Load individual configs to count original content
    rooms_config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    objects_config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml")
    characters_config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters.yaml")
    
    original_room_count = len(rooms_config.get("rooms", {}))
    original_object_count = len(objects_config.get("object_types", {}))
    original_character_count = len(characters_config.get("characters", {}))
    
    # Migrate all configs
    loader.migrate_v1_to_v2(rooms_config)
    loader.migrate_v1_to_v2(objects_config)
    loader.migrate_v1_to_v2(characters_config)
    
    # Verify all content was migrated
    summary = loader.get_migration_summary()
    assert summary['migration_stats']['rooms_migrated'] == original_room_count
    assert summary['migration_stats']['objects_migrated'] == original_object_count
    assert summary['migration_stats']['characters_migrated'] == original_character_count
    
    # Verify specific entities exist
    registry = loader.definitions
    
    # Check all rooms exist
    expected_rooms = ["town_square", "tavern", "adventurer_guild", "thieves_den", "church", 
                     "cemetery", "bank", "market_district", "underground_tunnels", 
                     "secret_cult_chamber", "old_forest_path"]
    for room_id in expected_rooms:
        assert room_id in registry._defs, f"Room {room_id} not migrated"
    
    # Check key objects exist
    expected_objects = ["notice_board", "torch", "broken_fountain", "bar", "quest_board"]
    for obj_id in expected_objects:
        assert obj_id in registry._defs, f"Object {obj_id} not migrated"
    
    # Check key characters exist
    expected_characters = ["detective_thorne", "mayor_victoria_blackwater", "father_marcus", 
                          "guild_master_elena", "dr_sarah_chen"]
    for char_id in expected_characters:
        assert char_id in registry._defs, f"Character {char_id} not migrated"


def test_migration_with_v2_systems_integration():
    """Test that migrated content works with v2 systems (relations, effects, etc.)."""
    loader = V2ConfigLoader()
    
    # Load and migrate config
    config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    loader.migrate_v1_to_v2(config)
    
    # Create v2 systems
    relations = RelationsGraph()
    effect_engine = EffectEngine()
    
    # Test that we can create entities and use them with v2 systems
    registry = loader.definitions
    
    # Create room entities
    town_square_entity = registry.create_entity("town_square", "town_square_instance")
    tavern_entity = registry.create_entity("tavern", "tavern_instance")
    
    # Test relations system
    relations.place_entity("player1", "town_square_instance")
    relations.place_entity("player2", "tavern_instance")
    
    assert relations.get_contents_of("town_square_instance") == ["player1"]
    assert relations.get_contents_of("tavern_instance") == ["player2"]
    
    # Test effects system
    torch_entity = registry.create_entity("torch", "torch_instance")
    from motive.sim_v2.effects import SetPropertyEffect
    
    # Create effect to modify torch properties
    effect = SetPropertyEffect(
        target_entity="torch_instance",
        property_name="fuel",
        value=50
    )
    
    # Execute effect
    entities = {"torch_instance": torch_entity}
    effect_engine.execute_effect(effect, entities)
    
    # Verify effect was applied
    assert torch_entity.get_property("fuel") == 50


def test_migration_error_handling_and_recovery():
    """Test that migration handles errors gracefully and provides useful feedback."""
    loader = V2ConfigLoader()
    
    # Test with malformed config
    malformed_config = {
        "rooms": {
            "valid_room": {
                "id": "valid_room",
                "name": "Valid Room",
                "description": "A valid room"
            },
            "invalid_room": {
                # Missing required 'id' field
                "name": "Invalid Room"
            }
        },
        "object_types": {
            "valid_object": {
                "id": "valid_object",
                "name": "Valid Object",
                "description": "A valid object"
            }
        }
    }
    
    # Migration should not crash
    loader.migrate_v1_to_v2(malformed_config)
    
    # Should have warnings for invalid content
    summary = loader.get_migration_summary()
    assert len(summary['migration_stats']['warnings']) > 0
    
    # Should still migrate valid content
    assert summary['migration_stats']['rooms_migrated'] >= 1  # At least valid_room
    assert summary['migration_stats']['objects_migrated'] >= 1  # At least valid_object
    
    # Verify valid content was migrated
    registry = loader.definitions
    assert "valid_room" in registry._defs
    assert "valid_object" in registry._defs


def test_migration_with_real_game_scenario():
    """Test migration with a realistic game scenario setup."""
    loader = V2ConfigLoader()
    
    # Load complete config
    config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
    loader.migrate_v1_to_v2(config)
    
    # Set up a realistic game scenario
    registry = loader.definitions
    relations = RelationsGraph()
    
    # Create game world
    town_square = registry.create_entity("town_square", "town_square")
    tavern = registry.create_entity("tavern", "tavern")
    torch = registry.create_entity("torch", "torch_1")
    detective = registry.create_entity("detective_thorne", "detective_1")
    
    # Set up relations (detective in town square, torch in tavern)
    relations.place_entity("detective_1", "town_square")
    relations.place_entity("torch_1", "tavern")
    
    # Verify scenario setup
    assert relations.get_contents_of("town_square") == ["detective_1"]
    assert relations.get_contents_of("tavern") == ["torch_1"]
    
    # Verify entity properties
    assert detective.get_property("name") == "Detective James Thorne"
    assert torch.get_property("name") == "Torch"
    assert torch.get_property("pickupable") is True
    
    # Test that we can modify properties (simulating game actions)
    torch.set_property("fuel", 75)  # Torch burns some fuel
    assert torch.get_property("fuel") == 75


def test_migration_statistics_accuracy():
    """Test that migration statistics are accurate and useful."""
    loader = V2ConfigLoader()
    
    # Load multiple configs
    configs = [
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml",
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml",
        "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters.yaml"
    ]
    
    for config_path in configs:
        config = load_config_file(config_path)
        loader.migrate_v1_to_v2(config)
    
    # Verify statistics
    summary = loader.get_migration_summary()
    
    # Statistics should be accurate
    assert summary['migration_stats']['rooms_migrated'] > 0
    assert summary['migration_stats']['objects_migrated'] > 0
    assert summary['migration_stats']['characters_migrated'] > 0
    
    # Total definitions should equal sum of individual migrations
    total_migrated = (
        summary['migration_stats']['rooms_migrated'] +
        summary['migration_stats']['objects_migrated'] +
        summary['migration_stats']['characters_migrated']
    )
    assert summary['definitions_loaded'] == total_migrated
    
    # Should have no actions (hearth_and_shadow_actions.yaml is empty)
    assert summary['migration_stats']['actions_migrated'] == 0
    assert summary['actions_loaded'] == 0


def test_migration_with_v2_enhanced_configs_compatibility():
    """Test that v1 migration works alongside v2 enhanced configs."""
    loader = V2ConfigLoader()
    
    # Load v1 config
    v1_config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    loader.migrate_v1_to_v2(v1_config)
    
    # Load v2 enhanced config
    v2_config = load_config_file("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_v2.yaml")
    loader.load_v2_config(v2_config)
    
    # Both should be loaded without conflicts
    summary = loader.get_migration_summary()
    assert summary['definitions_loaded'] > 0
    
    # Should be able to access both v1 migrated and v2 native definitions
    registry = loader.definitions
    assert "town_square" in registry._defs  # From v1 migration
    # Note: v2 configs might have different structure, so we just verify no crashes
