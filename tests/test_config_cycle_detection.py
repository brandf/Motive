#!/usr/bin/env python3
"""
Test cycle detection in hierarchical configuration loading.
"""

import pytest
from pathlib import Path
from motive.config_loader import ConfigLoader, ConfigLoadError


class TestConfigCycleDetection:
    """Test cases for circular dependency detection in config loading."""
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected and reported correctly."""
        loader = ConfigLoader(base_path="tests/configs")
        
        with pytest.raises(ConfigLoadError, match="Circular dependency detected"):
            loader.load_config("circular_a.yaml")
    
    def test_circular_dependency_error_message(self):
        """Test that the error message shows the complete cycle path."""
        loader = ConfigLoader(base_path="tests/configs")
        
        try:
            loader.load_config("circular_a.yaml")
            pytest.fail("Expected ConfigLoadError for circular dependency")
        except ConfigLoadError as e:
            error_msg = str(e)
            assert "Circular dependency detected" in error_msg
            assert "circular_a.yaml" in error_msg
            assert "circular_b.yaml" in error_msg
            # Should show the complete cycle path
            assert "->" in error_msg
    
    def test_no_circular_dependency_valid_config(self):
        """Test that valid configs without cycles load successfully."""
        loader = ConfigLoader(base_path="configs")
        
        # This should work without errors
        config = loader.load_config("core.yaml")
        assert config is not None
        assert "action_definitions" in config
    
    def test_self_reference_detection(self):
        """Test that a config including itself is detected as a cycle."""
        # Create a self-referencing config
        self_ref_config = """
id: self_ref
name: Self Referencing Config

includes:
  - "self_ref.yaml"

actions:
  test_action:
    id: test_action
    name: Test Action
    description: This is a test action
    cost: 10
"""
        
        config_path = Path("tests/configs/self_ref.yaml")
        config_path.write_text(self_ref_config)
        
        try:
            loader = ConfigLoader(base_path="tests/configs")
            
            with pytest.raises(ConfigLoadError, match="Circular dependency detected"):
                loader.load_config("self_ref.yaml")
        finally:
            # Clean up
            if config_path.exists():
                config_path.unlink()
    
    def test_deep_circular_dependency(self):
        """Test detection of circular dependencies in longer chains."""
        # Create a chain: a -> b -> c -> a
        chain_a = """
id: chain_a
name: Chain A

includes:
  - "chain_b.yaml"

actions:
  action_a:
    id: action_a
    name: Action A
    cost: 10
"""
        
        chain_b = """
id: chain_b
name: Chain B

includes:
  - "chain_c.yaml"

actions:
  action_b:
    id: action_b
    name: Action B
    cost: 10
"""
        
        chain_c = """
id: chain_c
name: Chain C

includes:
  - "chain_a.yaml"

actions:
  action_c:
    id: action_c
    name: Action C
    cost: 10
"""
        
        try:
            # Write the chain configs
            (Path("tests/configs/chain_a.yaml")).write_text(chain_a)
            (Path("tests/configs/chain_b.yaml")).write_text(chain_b)
            (Path("tests/configs/chain_c.yaml")).write_text(chain_c)
            
            loader = ConfigLoader(base_path="tests/configs")
            
            with pytest.raises(ConfigLoadError, match="Circular dependency detected"):
                loader.load_config("chain_a.yaml")
                
        finally:
            # Clean up
            for filename in ["chain_a.yaml", "chain_b.yaml", "chain_c.yaml"]:
                config_path = Path(f"tests/configs/{filename}")
                if config_path.exists():
                    config_path.unlink()
