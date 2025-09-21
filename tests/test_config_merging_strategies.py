"""
Test config merging strategies to ensure v2 configs support flexible merging.

This test verifies that v2 configs can use __merge_strategy__ markers to control
how lists are merged (override, append, prepend, etc.) just like v1 configs.
"""

import pytest
import tempfile
import os
from pathlib import Path
from motive.sim_v2.v2_config_preprocessor import V2ConfigPreprocessor


class TestConfigMergingStrategies:
    """Test that v2 config merging supports flexible strategies."""
    
    def test_override_strategy_works(self):
        """Test that __merge_strategy__: override replaces the entire list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config with players
            base_config = """
players:
  - name: "Player_1"
    provider: "google"
    model: "gemini-2.5-flash"
  - name: "Player_2"
    provider: "google"
    model: "gemini-2.5-flash"
"""
            base_path = Path(temp_dir) / "base.yaml"
            base_path.write_text(base_config)
            
            # Create override config that should replace players entirely
            override_config = """
includes:
  - "base.yaml"

players:
  - __merge_strategy__: "override"
  - name: "Player_A"
    provider: "openai"
    model: "gpt-4"
  - name: "Player_B"
    provider: "anthropic"
    model: "claude-3"
"""
            override_path = Path(temp_dir) / "override.yaml"
            override_path.write_text(override_config)
            
            # Load config using v2 preprocessor
            preprocessor = V2ConfigPreprocessor(temp_dir)
            result = preprocessor.load_config("override.yaml")
            
            # Should have only the override players, not the base players
            assert len(result['players']) == 2
            assert result['players'][0]['name'] == "Player_A"
            assert result['players'][1]['name'] == "Player_B"
            # Should NOT have the original players
            player_names = [p['name'] for p in result['players']]
            assert "Player_1" not in player_names
            assert "Player_2" not in player_names
    
    def test_append_strategy_works(self):
        """Test that __merge_strategy__: append adds to the existing list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config with players
            base_config = """
players:
  - name: "Player_1"
    provider: "google"
    model: "gemini-2.5-flash"
"""
            base_path = Path(temp_dir) / "base.yaml"
            base_path.write_text(base_config)
            
            # Create override config that should append to players
            override_config = """
includes:
  - "base.yaml"

players:
  - __merge_strategy__: "append"
  - name: "Player_2"
    provider: "openai"
    model: "gpt-4"
"""
            override_path = Path(temp_dir) / "override.yaml"
            override_path.write_text(override_config)
            
            # Load config using v2 preprocessor
            preprocessor = V2ConfigPreprocessor(temp_dir)
            result = preprocessor.load_config("override.yaml")
            
            # Should have both base and override players
            assert len(result['players']) == 2
            assert result['players'][0]['name'] == "Player_1"
            assert result['players'][1]['name'] == "Player_2"
    
    def test_prepend_strategy_works(self):
        """Test that __merge_strategy__: prepend adds to the beginning of the list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config with players
            base_config = """
players:
  - name: "Player_2"
    provider: "google"
    model: "gemini-2.5-flash"
"""
            base_path = Path(temp_dir) / "base.yaml"
            base_path.write_text(base_config)
            
            # Create override config that should prepend to players
            override_config = """
includes:
  - "base.yaml"

players:
  - __merge_strategy__: "prepend"
  - name: "Player_1"
    provider: "openai"
    model: "gpt-4"
"""
            override_path = Path(temp_dir) / "override.yaml"
            override_path.write_text(override_config)
            
            # Load config using v2 preprocessor
            preprocessor = V2ConfigPreprocessor(temp_dir)
            result = preprocessor.load_config("override.yaml")
            
            # Should have prepended player first, then base player
            assert len(result['players']) == 2
            assert result['players'][0]['name'] == "Player_1"
            assert result['players'][1]['name'] == "Player_2"
    
    def test_default_behavior_is_append(self):
        """Test that without __merge_strategy__, lists are appended (current behavior)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config with players
            base_config = """
players:
  - name: "Player_1"
    provider: "google"
    model: "gemini-2.5-flash"
"""
            base_path = Path(temp_dir) / "base.yaml"
            base_path.write_text(base_config)
            
            # Create override config without merge strategy (should default to append)
            override_config = """
includes:
  - "base.yaml"

players:
  - name: "Player_2"
    provider: "openai"
    model: "gpt-4"
"""
            override_path = Path(temp_dir) / "override.yaml"
            override_path.write_text(override_config)
            
            # Load config using v2 preprocessor
            preprocessor = V2ConfigPreprocessor(temp_dir)
            result = preprocessor.load_config("override.yaml")
            
            # Should have both players (append behavior)
            assert len(result['players']) == 2
            assert result['players'][0]['name'] == "Player_1"
            assert result['players'][1]['name'] == "Player_2"
