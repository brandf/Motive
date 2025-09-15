#!/usr/bin/env python3
"""Test that migrated integration test configs work correctly with v2 systems."""

import pytest
import os
from motive.sim_v2.config_loader import V2ConfigLoader


class TestV2MigratedIntegrationConfigs:
    """Test that migrated integration test configs work with v2 systems."""
    
    def test_simple_merging_migrated_config(self):
        """Test the migrated simple merging config."""
        config_path = "tests/configs/test_simple_merging_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Migrated config not found: {config_path}")
        
        loader = V2ConfigLoader()
        config_data = loader.load_config_from_file(config_path)
        loader.load_v2_config(config_data)
        
        # Verify the config loaded correctly
        assert config_data is not None
        assert "entity_definitions" in config_data
        
        # Verify we have the expected entities
        registry = loader.definitions
        assert "new_room" in registry._defs
        assert "base_room" in registry._defs
        assert "new_object" in registry._defs
        # Note: base_object is in the base config, not directly in this config
        
        # Verify entity properties
        new_room = registry.get("new_room")
        assert "room" in new_room.types
        assert new_room.properties["name"].default == "New Room"
        assert new_room.properties["temperature"].default == "warm"
        assert new_room.properties["new"].default is True
        
        base_room = registry.get("base_room")
        assert "room" in base_room.types
        assert base_room.properties["name"].default == "Base Room"
        
        new_object = registry.get("new_object")
        assert "object" in new_object.types
        assert new_object.properties["name"].default == "New Object"
        assert new_object.properties["new"].default is True
        
        # Note: base_object is in the base config, not in this migrated config
    
    def test_hierarchical_migrated_config(self):
        """Test the migrated hierarchical config."""
        config_path = "tests/configs/test_hierarchical_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Migrated config not found: {config_path}")
        
        loader = V2ConfigLoader()
        config_data = loader.load_config_from_file(config_path)
        loader.load_v2_config(config_data)
        
        # Verify the config loaded correctly
        assert config_data is not None
        # This config has action_definitions, not entity_definitions
        assert "action_definitions" in config_data
        
        # Verify we have the expected actions
        assert len(loader.actions) > 0
        assert "hierarchical_test_action" in loader.actions
    
    def test_action_validation_migrated_config(self):
        """Test the migrated action validation config."""
        config_path = "tests/configs/test_action_validation_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Migrated config not found: {config_path}")
        
        loader = V2ConfigLoader()
        config_data = loader.load_config_from_file(config_path)
        loader.load_v2_config(config_data)
        
        # Verify the config loaded correctly
        assert config_data is not None
        assert "entity_definitions" in config_data
        
        # Verify we have the expected entities
        registry = loader.definitions
        assert "test_room" in registry._defs
        assert "test_object" in registry._defs
        
        # Verify we have actions
        assert len(loader.actions) > 0
    
    def test_standalone_migrated_config(self):
        """Test the migrated standalone config."""
        config_path = "tests/configs/test_standalone_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Migrated config not found: {config_path}")
        
        loader = V2ConfigLoader()
        config_data = loader.load_config_from_file(config_path)
        loader.load_v2_config(config_data)
        
        # Verify the config loaded correctly
        assert config_data is not None
        assert "entity_definitions" in config_data
        
        # Verify we have the expected entities
        registry = loader.definitions
        assert "test_room" in registry._defs
        assert "test_object" in registry._defs
        assert "test_character" in registry._defs
    
    def test_migrated_config_with_v2_systems(self):
        """Test that migrated configs work with v2 systems."""
        config_path = "tests/configs/test_simple_merging_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Migrated config not found: {config_path}")
        
        loader = V2ConfigLoader()
        config_data = loader.load_config_from_file(config_path)
        loader.load_v2_config(config_data)
        
        # Test with v2 systems
        registry = loader.definitions
        relations = loader.relations
        effect_engine = loader.effect_engine
        
        # Create entities from definitions
        new_room = registry.create_entity("new_room", "new_room_instance")
        new_object = registry.create_entity("new_object", "new_object_instance")
        
        # Test relations
        relations.place_entity("new_object_instance", "new_room_instance")
        
        # Verify relations work
        assert relations.get_contents_of("new_room_instance") == ["new_object_instance"]
        assert relations.get_container_of("new_object_instance") == "new_room_instance"
        
        # Test properties
        assert new_object.get_property("new") is True
        assert new_room.get_property("temperature") == "warm"
        
        # Test effects
        from motive.sim_v2.effects import SetPropertyEffect
        effect = SetPropertyEffect(
            target_entity="new_object_instance",
            property_name="new",
            value=False
        )
        
        entities = {"new_object_instance": new_object}
        effect_engine.execute_effect(effect, entities)
        
        assert new_object.get_property("new") is False
    
    def test_migration_preserves_content(self):
        """Test that migration preserved all original content."""
        config_path = "tests/configs/test_simple_merging_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Migrated config not found: {config_path}")
        
        loader = V2ConfigLoader()
        config_data = loader.load_config_from_file(config_path)
        loader.load_v2_config(config_data)
        
        # Verify migration statistics
        summary = loader.get_migration_summary()
        assert summary['definitions_loaded'] > 0
        
        # Verify specific content was preserved
        registry = loader.definitions
        
        # Check that the "new" boolean property was created from tags
        new_room = registry.get("new_room")
        assert "new" in new_room.properties
        assert new_room.properties["new"].default is True
        
        new_object = registry.get("new_object")
        assert "new" in new_object.properties
        assert new_object.properties["new"].default is True
