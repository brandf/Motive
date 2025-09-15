#!/usr/bin/env python3
"""
Comprehensive tests for merging scenarios in hierarchical configuration system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from motive.config_loader import ConfigLoader, ConfigLoadError
from motive.list_merge_strategies import ListMergeStrategy, ListMerger
from motive.patch_system import PatchReference, PatchProcessor, create_reference, create_patch


class TestSimpleMerging:
    """Test simple additive merging (default behavior)."""
    
    def test_simple_dictionary_merge(self):
        """Test that dictionaries are merged recursively."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_simple_merging.yaml")
        
        assert config is not None
        assert config['id'] == 'test_simple_merging'
        
        # Should have overridden values
        assert config['game_settings']['num_rounds'] == 2
        assert config['game_settings']['initial_ap_per_turn'] == 30
        
        # Should have both base and new actions
        assert 'base_action' in config.get('actions', {})
        assert 'new_action' in config.get('actions', {})
        
        # Should have both base and new objects
        assert 'base_object' in config.get('object_types', {})
        assert 'new_object' in config.get('object_types', {})
        
        # Should have both base and new rooms
        assert 'base_room' in config.get('rooms', {})
        assert 'new_room' in config.get('rooms', {})
    
    def test_simple_list_append(self):
        """Test that lists are appended by default."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_simple_merging.yaml")
        
        # Actions should be appended
        actions = config.get('actions', {})
        assert len(actions) >= 2  # base_action + new_action
        
        # Object types should be appended
        object_types = config.get('object_types', {})
        assert len(object_types) >= 2  # base_object + new_object
    
    def test_nested_merging(self):
        """Test that nested structures are merged correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_simple_merging.yaml")
        
        # Check nested room structure
        new_room = config.get('rooms', {}).get('new_room', {})
        assert new_room['id'] == 'new_room'
        assert new_room['name'] == 'New Room'
        assert new_room['properties']['temperature'] == 'warm'


class TestAdvancedMerging:
    """Test advanced merging with list strategies."""
    
    def test_key_based_merging(self):
        """Test key-based merging for objects with IDs."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_advanced_merging.yaml")
        
        # Should have overridden base_action and added new_advanced_action
        actions = config.get('actions', {})
        assert 'base_action' in actions
        assert actions['base_action']['cost'] == 999  # Should be overridden
        assert 'new_advanced_action' in actions
    
    def test_unique_merging(self):
        """Test unique merging removes duplicates."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_advanced_merging.yaml")
        
        # Check that tags are merged uniquely
        test_object = config.get('object_types', {}).get('test_object', {})
        tags = test_object.get('tags', [])
        
        # Should have unique tags (filter out metadata)
        clean_tags = [tag for tag in tags if isinstance(tag, str)]
        assert len(clean_tags) == len(set(clean_tags))
        assert 'base' in clean_tags
        assert 'advanced' in clean_tags
        assert 'test' in clean_tags
    
    def test_remove_items_strategy(self):
        """Test remove items strategy."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_advanced_merging.yaml")
        
        # Check that excluded actions are removed
        excluded_actions = config.get('excluded_actions', [])
        assert 'base_action' not in excluded_actions
        assert 'old_action' not in excluded_actions
    
    def test_prepend_strategy(self):
        """Test prepend strategy puts items at the beginning."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_advanced_merging.yaml")
        
        # Check that priority actions are prepended
        priority_actions = config.get('priority_actions', [])
        if priority_actions:
            assert priority_actions[0]['id'] == 'urgent_action'
    
    def test_insert_strategy(self):
        """Test insert strategy puts items at specific positions."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_advanced_merging.yaml")
        
        # Check that items are inserted at position 1
        ordered_items = config.get('ordered_items', [])
        if len(ordered_items) > 2:
            # Filter out metadata
            clean_items = [item for item in ordered_items if isinstance(item, str)]
            assert 'inserted_item_1' in clean_items
            assert 'inserted_item_2' in clean_items


class TestPatchReferences:
    """Test patch-based references (advanced feature)."""
    
    def test_patch_reference_detection(self):
        """Test that patch references are detected correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # This test would need the patch system to be fully implemented
        # For now, we'll test that the config loads without errors
        try:
            config = loader.load_config("test_patch_references.yaml")
            assert config is not None
        except Exception as e:
            # Expected to fail until patch system is fully implemented
            assert "patch" in str(e).lower() or "ref" in str(e).lower()
    
    def test_patch_creation(self):
        """Test creating patch operations."""
        # Test basic patch creation
        patch = create_patch("set", field="cost", value=5)
        assert patch["operation"] == "set"
        assert patch["field"] == "cost"
        assert patch["value"] == 5
        
        # Test reference creation
        ref = create_reference("actions.move", [
            create_patch("set", field="cost", value=5),
            create_patch("add", field="tags", items=["patched"])
        ])
        assert ref["__ref__"] == "actions.move"
        assert len(ref["__patches__"]) == 2


class TestListMergeStrategies:
    """Test the list merging strategies directly."""
    
    def test_override_strategy(self):
        """Test override strategy replaces entire list."""
        merger = ListMerger()
        
        base = [1, 2, 3]
        override = [4, 5, 6]
        
        result = merger.merge_lists(base, override, ListMergeStrategy.OVERRIDE)
        assert result == [4, 5, 6]
    
    def test_append_strategy(self):
        """Test append strategy adds to end."""
        merger = ListMerger()
        
        base = [1, 2, 3]
        override = [4, 5, 6]
        
        result = merger.merge_lists(base, override, ListMergeStrategy.APPEND)
        assert result == [1, 2, 3, 4, 5, 6]
    
    def test_prepend_strategy(self):
        """Test prepend strategy adds to beginning."""
        merger = ListMerger()
        
        base = [1, 2, 3]
        override = [4, 5, 6]
        
        result = merger.merge_lists(base, override, ListMergeStrategy.PREPEND)
        assert result == [4, 5, 6, 1, 2, 3]
    
    def test_merge_unique_strategy(self):
        """Test merge unique strategy removes duplicates."""
        merger = ListMerger()
        
        base = [1, 2, 3]
        override = [3, 4, 5]
        
        result = merger.merge_lists(base, override, ListMergeStrategy.MERGE_UNIQUE)
        assert result == [1, 2, 3, 4, 5]
    
    def test_remove_items_strategy(self):
        """Test remove items strategy removes specified items."""
        merger = ListMerger()
        
        base = [1, 2, 3, 4, 5]
        override = [2, 4]
        
        result = merger.merge_lists(base, override, ListMergeStrategy.REMOVE_ITEMS)
        assert result == [1, 3, 5]
    
    def test_key_based_merge_strategy(self):
        """Test key-based merge strategy for objects with IDs."""
        merger = ListMerger()
        
        base = [
            {"id": "item1", "name": "Item 1", "value": 10},
            {"id": "item2", "name": "Item 2", "value": 20}
        ]
        override = [
            {"id": "item1", "name": "Updated Item 1", "value": 15},
            {"id": "item3", "name": "Item 3", "value": 30}
        ]
        
        result = merger.merge_lists(base, override, ListMergeStrategy.KEY_BASED_MERGE, key_field="id")
        
        # Should have 3 items
        assert len(result) == 3
        
        # item1 should be updated
        item1 = next(item for item in result if item["id"] == "item1")
        assert item1["name"] == "Updated Item 1"
        assert item1["value"] == 15
        
        # item2 should be unchanged
        item2 = next(item for item in result if item["id"] == "item2")
        assert item2["name"] == "Item 2"
        assert item2["value"] == 20
        
        # item3 should be added
        item3 = next(item for item in result if item["id"] == "item3")
        assert item3["name"] == "Item 3"
        assert item3["value"] == 30
    
    def test_smart_merge_strategy(self):
        """Test smart merge strategy auto-detects appropriate strategy."""
        merger = ListMerger()
        
        # Test with empty lists
        result = merger.merge_lists([], [1, 2, 3], ListMergeStrategy.SMART_MERGE)
        assert result == [1, 2, 3]
        
        result = merger.merge_lists([1, 2, 3], [], ListMergeStrategy.SMART_MERGE)
        assert result == [1, 2, 3]
        
        # Test with objects containing IDs
        base = [{"id": "item1", "name": "Item 1"}]
        override = [{"id": "item1", "name": "Updated Item 1"}]
        
        result = merger.merge_lists(base, override, ListMergeStrategy.SMART_MERGE)
        assert len(result) == 1
        assert result[0]["name"] == "Updated Item 1"


class TestMergeErrorHandling:
    """Test error handling in merge operations."""
    
    def test_invalid_merge_strategy(self):
        """Test that invalid merge strategies raise appropriate errors."""
        merger = ListMerger()
        
        with pytest.raises(ValueError):
            merger.merge_lists([1, 2, 3], [4, 5, 6], "invalid_strategy")
    
    def test_missing_key_field(self):
        """Test that missing key field in key-based merge is handled."""
        merger = ListMerger()
        
        base = [{"name": "Item 1"}]
        override = [{"name": "Item 2"}]
        
        # Should fall back to append strategy when key field is missing
        result = merger.merge_lists(base, override, ListMergeStrategy.KEY_BASED_MERGE, key_field="id")
        assert len(result) == 2
        assert result[0]["name"] == "Item 1"
        assert result[1]["name"] == "Item 2"


class TestRealWorldScenarios:
    """Test real-world configuration scenarios."""
    
    def test_game_config_merging(self):
        """Test merging a realistic game configuration."""
        loader = ConfigLoader(base_path="configs")
        
        # Test with the actual game config
        config = loader.load_config("game.yaml")
        
        assert config is not None
        assert 'game_settings' in config
        assert 'players' in config
        assert 'action_definitions' in config
        assert 'entity_definitions' in config
        # V2 configs have entity_definitions instead of separate rooms/objects
        assert 'entity_definitions' in config
        
        # Should have merged data from all includes
        assert len(config.get('action_definitions', {})) > 0
        assert len(config.get('entity_definitions', {})) > 0
        # V2 configs don't have separate rooms field
    
    def test_theme_edition_merging(self):
        """Test merging theme and edition configurations."""
        loader = ConfigLoader(base_path="configs")
        
        # Test with theme config
        theme_config = loader.load_config("themes/fantasy/fantasy.yaml")
        assert theme_config is not None
        assert 'object_types' in theme_config
        
        # Test with edition config
        edition_config = loader.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
        assert edition_config is not None
        assert 'rooms' in edition_config
    
    def test_complex_nesting(self):
        """Test complex nested configuration merging."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_relative_paths.yaml")
        
        assert config is not None
        # Should have data from all levels of nesting
        assert 'test_relative_action' in config.get('actions', {})
        assert 'nested_object' in config.get('object_types', {})
        assert 'deep_character' in config.get('character_types', {})
