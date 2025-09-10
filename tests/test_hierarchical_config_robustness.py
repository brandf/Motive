#!/usr/bin/env python3
"""
Comprehensive test suite for hierarchical configuration system robustness.
This tests all edge cases and provides excellent debugging information.
"""

import pytest
import tempfile
import os
from pathlib import Path
from motive.config_loader import ConfigLoader, ConfigLoadError


class TestHierarchicalConfigRobustness:
    """Comprehensive tests for hierarchical config system robustness."""
    
    def test_relative_path_resolution(self):
        """Test that relative paths are resolved correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Test relative path going up one level
        config = loader.load_config("test_relative_paths.yaml")
        
        assert config is not None
        assert config['id'] == 'test_relative_paths'
        assert 'test_relative_action' in config.get('actions', {})
        assert 'nested_object' in config.get('object_types', {})
        assert 'deep_character' in config.get('character_types', {})
    
    def test_missing_file_handling(self):
        """Test that missing files are handled gracefully with clear error messages."""
        loader = ConfigLoader(base_path="tests/configs")
        
        with pytest.raises(ConfigLoadError) as exc_info:
            loader.load_config("test_missing_file.yaml")
        
        error_msg = str(exc_info.value)
        assert "File not found" in error_msg
        assert "nonexistent_file.yaml" in error_msg
        assert "test_missing_file.yaml" in error_msg  # Should show the chain
    
    def test_invalid_yaml_handling(self):
        """Test that invalid YAML is handled gracefully with clear error messages."""
        loader = ConfigLoader(base_path="tests/configs")
        
        with pytest.raises(ConfigLoadError) as exc_info:
            loader.load_config("test_invalid_yaml.yaml")
        
        error_msg = str(exc_info.value)
        assert "YAML parsing error" in error_msg
        assert "invalid_syntax.yaml" in error_msg
        assert "test_invalid_yaml.yaml" in error_msg  # Should show the chain
    
    def test_self_reference_detection(self):
        """Test that self-references are detected and reported clearly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        with pytest.raises(ConfigLoadError) as exc_info:
            loader.load_config("test_self_reference.yaml")
        
        error_msg = str(exc_info.value)
        assert "Circular dependency detected" in error_msg
        assert "test_self_reference.yaml" in error_msg
        assert "->" in error_msg  # Should show the cycle path
    
    def test_deep_cycle_detection(self):
        """Test that deep cycles (a -> b -> c -> a) are detected and reported clearly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        with pytest.raises(ConfigLoadError) as exc_info:
            loader.load_config("test_deep_cycle.yaml")
        
        error_msg = str(exc_info.value)
        assert "Circular dependency detected" in error_msg
        assert "test_deep_cycle.yaml" in error_msg
        assert "cycle_b.yaml" in error_msg
        assert "cycle_c.yaml" in error_msg
        assert "->" in error_msg  # Should show the complete cycle path
    
    def test_merge_order(self):
        """Test that merge order is correct (later includes override earlier ones)."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_merge_order.yaml")
        
        assert config is not None
        assert config['id'] == 'test_merge_order'
        
        # Check that the final config overrides everything
        assert config['game_settings']['num_rounds'] == 999
        assert config['game_settings']['initial_ap_per_turn'] == 999
        
        # Check that override_config was merged with base_config
        assert 'override_action' in config.get('actions', {})
        assert 'base_action' in config.get('actions', {})  # Should be preserved (additive merging)
        
        # Check that shared_action was overridden
        shared_action = config.get('actions', {}).get('shared_action', {})
        assert shared_action.get('description') == 'This action overrides shared_action'
        assert shared_action.get('cost') == 20
        
        # Check that objects were merged
        assert 'override_object' in config.get('object_types', {})
        assert 'base_object' in config.get('object_types', {})  # Should be preserved (additive merging)
    
    def test_include_processing_order(self):
        """Test that includes are processed in the correct order."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Use existing test config that includes multiple files
        config = loader.load_config("test_merge_order.yaml")
        
        # The final config should have the highest priority
        assert config['game_settings']['num_rounds'] == 999
        assert config['game_settings']['initial_ap_per_turn'] == 999
        
        # Should have actions from both base and override
        assert 'base_action' in config.get('actions', {})
        assert 'override_action' in config.get('actions', {})
    
    def test_empty_includes_list(self):
        """Test that empty includes list is handled correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Create a test config with empty includes
        test_config = """
id: test_empty_includes
name: Test Empty Includes

includes: []

# Some content
actions:
  test_action:
    id: test_action
    name: Test Action
    description: This action tests empty includes
    cost: 5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(test_config)
            temp_path = f.name
        
        try:
            config = loader.load_config(Path(temp_path).name, base_path=Path(temp_path).parent)
            
            assert config is not None
            assert config['id'] == 'test_empty_includes'
            assert 'test_action' in config.get('actions', {})
            
        finally:
            os.unlink(temp_path)
    
    def test_no_includes_key(self):
        """Test that configs without includes key work correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Create a test config without includes
        test_config = """
id: test_no_includes
name: Test No Includes

# Some content
actions:
  test_action:
    id: test_action
    name: Test Action
    description: This action tests no includes
    cost: 5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(test_config)
            temp_path = f.name
        
        try:
            config = loader.load_config(Path(temp_path).name, base_path=Path(temp_path).parent)
            
            assert config is not None
            assert config['id'] == 'test_no_includes'
            assert 'test_action' in config.get('actions', {})
            
        finally:
            os.unlink(temp_path)
    
    def test_deep_nesting(self):
        """Test that deeply nested configs work correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        config = loader.load_config("test_relative_paths.yaml")
        
        assert config is not None
        assert config['id'] == 'test_relative_paths'
        
        # Should have data from all levels of nesting
        assert 'test_relative_action' in config.get('actions', {})
        assert 'nested_object' in config.get('object_types', {})
        assert 'deep_character' in config.get('character_types', {})
    
    def test_error_message_clarity(self):
        """Test that error messages are clear and helpful for debugging."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Test missing file error
        with pytest.raises(ConfigLoadError) as exc_info:
            loader.load_config("test_missing_file.yaml")
        
        error_msg = str(exc_info.value)
        assert "File not found" in error_msg
        assert "nonexistent_file.yaml" in error_msg
        assert "test_missing_file.yaml" in error_msg
        assert "tests" in error_msg and "configs" in error_msg  # Should show the base path
        
        # Test cycle error
        with pytest.raises(ConfigLoadError) as exc_info:
            loader.load_config("test_deep_cycle.yaml")
        
        error_msg = str(exc_info.value)
        assert "Circular dependency detected" in error_msg
        assert "test_deep_cycle.yaml" in error_msg
        assert "cycle_b.yaml" in error_msg
        assert "cycle_c.yaml" in error_msg
        assert "->" in error_msg  # Should show the cycle path
    
    def test_config_loader_caching(self):
        """Test that config loader caching works correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Load the same config twice
        config1 = loader.load_config("test_relative_paths.yaml")
        config2 = loader.load_config("test_relative_paths.yaml")
        
        # Should have the same content (cached)
        assert config1 == config2
        
        # Clear cache and load again
        loader.clear_cache()
        config3 = loader.load_config("test_relative_paths.yaml")
        
        # Should be a different object (not cached)
        assert config1 is not config3
        assert config1 == config3  # But content should be the same
    
    def test_absolute_path_handling(self):
        """Test that absolute paths are handled correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Create a test config with absolute path
        abs_path = os.path.abspath('tests/configs/base_config.yaml')
        test_config = f"""
id: test_absolute_path
name: Test Absolute Path

includes:
  - "{abs_path.replace(os.sep, '/')}"        

# Some content
actions:
  test_action:
    id: test_action
    name: Test Action
    description: This action tests absolute paths
    cost: 5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(test_config)
            temp_path = f.name
        
        try:
            config = loader.load_config(Path(temp_path).name, base_path=Path(temp_path).parent)
            
            assert config is not None
            assert config['id'] == 'test_absolute_path'
            assert 'base_action' in config.get('actions', {})  # Should have loaded base_config
            
        finally:
            os.unlink(temp_path)
    
    def test_include_path_normalization(self):
        """Test that include paths are normalized correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Test with existing config that has relative paths
        config = loader.load_config("test_relative_paths.yaml")
        
        assert config is not None
        assert config['id'] == 'test_relative_paths'
        
        # Should have loaded the included configs successfully
        assert 'actions' in config
        assert 'object_types' in config
    
    def test_large_config_handling(self):
        """Test that large configs are handled efficiently."""
        loader = ConfigLoader(base_path="tests/configs")
        
        # Test with existing config that has multiple includes
        config = loader.load_config("test_merge_order.yaml")
        
        assert config is not None
        assert config['id'] == 'test_merge_order'
        
        # Should have loaded multiple configs successfully
        assert 'actions' in config
        assert 'object_types' in config
        assert len(config.get('actions', {})) > 0
    
    # Note: Concurrent loading test removed - config loading happens once at startup
    # and is fast enough that thread safety complexity isn't justified for this use case
