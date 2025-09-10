"""
Tests for the hierarchical configuration loader with include support.
"""

import pytest
import tempfile
import os
import yaml
from pathlib import Path
from motive.config_loader import ConfigLoader, load_game_config, ConfigLoadError


class TestConfigLoader:
    """Test the ConfigLoader class."""
    
    def test_load_simple_config(self):
        """Test loading a simple config without includes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple config
            config_data = {
                "game_settings": {
                    "num_rounds": 2,
                    "manual": "MANUAL.md"
                },
                "players": [
                    {"name": "TestPlayer", "provider": "openai", "model": "gpt-4"}
                ]
            }
            
            config_path = Path(temp_dir) / "test.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(temp_dir)
            result = loader.load_config("test.yaml")
            
            assert result["game_settings"]["num_rounds"] == 2
            assert result["game_settings"]["manual"] == "MANUAL.md"
            assert len(result["players"]) == 1
            assert result["players"][0]["name"] == "TestPlayer"
    
    def test_load_config_with_includes(self):
        """Test loading a config with includes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config
            base_config = {
                "game_settings": {
                    "num_rounds": 2,
                    "manual": "MANUAL.md"
                },
                "actions": {
                    "look": {
                        "id": "look",
                        "name": "look",
                        "cost": 10,
                        "description": "Look around"
                    }
                }
            }
            
            # Create included config
            included_config = {
                "actions": {
                    "move": {
                        "id": "move",
                        "name": "move", 
                        "cost": 10,
                        "description": "Move in a direction"
                    }
                },
                "objects": {
                    "sword": {
                        "id": "sword",
                        "name": "Sword",
                        "description": "A sharp blade"
                    }
                }
            }
            
            # Create main config with include
            main_config = {
                "includes": ["base.yaml", "included.yaml"],
                "actions": {
                    "say": {
                        "id": "say",
                        "name": "say",
                        "cost": 10,
                        "description": "Say something"
                    }
                },
                "players": [
                    {"name": "TestPlayer", "provider": "openai", "model": "gpt-4"}
                ]
            }
            
            # Write config files
            with open(Path(temp_dir) / "base.yaml", 'w') as f:
                yaml.dump(base_config, f)
            
            with open(Path(temp_dir) / "included.yaml", 'w') as f:
                yaml.dump(included_config, f)
            
            with open(Path(temp_dir) / "main.yaml", 'w') as f:
                yaml.dump(main_config, f)
            
            # Load main config
            loader = ConfigLoader(temp_dir)
            result = loader.load_config("main.yaml")
            
            # Should have all actions from base, included, and main
            assert "look" in result["actions"]
            assert "say" in result["actions"]
            assert "move" in result["actions"]  # From included.yaml
            
            # Should have objects from included
            assert "sword" in result["objects"]
            
            # Should have players from main
            assert len(result["players"]) == 1
            assert result["players"][0]["name"] == "TestPlayer"
            
            # Should not have includes in final result
            assert "includes" not in result
    
    def test_load_config_with_multiple_includes(self):
        """Test loading a config with multiple includes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create configs
            config1 = {
                "actions": {
                    "look": {"id": "look", "name": "look", "cost": 10, "description": "Look"}
                },
                "objects": {
                    "sword": {"id": "sword", "name": "Sword", "description": "A blade"}
                }
            }
            
            config2 = {
                "actions": {
                    "move": {"id": "move", "name": "move", "cost": 10, "description": "Move"},
                    "look": {"id": "look", "name": "look", "cost": 5, "description": "Look (overridden)"}
                },
                "objects": {
                    "bow": {"id": "bow", "name": "Bow", "description": "A ranged weapon"}
                }
            }
            
            config3 = {
                "actions": {
                    "say": {"id": "say", "name": "say", "cost": 10, "description": "Say"}
                }
            }
            
            main_config = {
                "includes": ["config1.yaml", "config2.yaml", "config3.yaml"],
                "players": [{"name": "TestPlayer", "provider": "openai", "model": "gpt-4"}]
            }
            
            # Write config files
            for i, config in enumerate([config1, config2, config3], 1):
                with open(Path(temp_dir) / f"config{i}.yaml", 'w') as f:
                    yaml.dump(config, f)
            
            with open(Path(temp_dir) / "main.yaml", 'w') as f:
                yaml.dump(main_config, f)
            
            # Load main config
            loader = ConfigLoader(temp_dir)
            result = loader.load_config("main.yaml")
            
            # Should have all actions
            assert "look" in result["actions"]
            assert "move" in result["actions"]
            assert "say" in result["actions"]
            
            # Look should be overridden by config2 (cost 5, not 10)
            assert result["actions"]["look"]["cost"] == 5
            assert result["actions"]["look"]["description"] == "Look (overridden)"
            
            # Should have all objects
            assert "sword" in result["objects"]
            assert "bow" in result["objects"]
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create configs with circular dependency
            config1 = {
                "includes": ["config2.yaml"],
                "name": "config1"
            }
            
            config2 = {
                "includes": ["config1.yaml"],
                "name": "config2"
            }
            
            # Write config files
            with open(Path(temp_dir) / "config1.yaml", 'w') as f:
                yaml.dump(config1, f)
            
            with open(Path(temp_dir) / "config2.yaml", 'w') as f:
                yaml.dump(config2, f)
            
            # Load should fail with circular dependency error
            loader = ConfigLoader(temp_dir)
            with pytest.raises(ConfigLoadError, match="Circular dependency detected"):
                loader.load_config("config1.yaml")
    
    def test_file_not_found_error(self):
        """Test that missing files raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "includes": ["nonexistent.yaml"],
                "name": "test"
            }
            
            with open(Path(temp_dir) / "main.yaml", 'w') as f:
                yaml.dump(config, f)
            
            loader = ConfigLoader(temp_dir)
            with pytest.raises(ConfigLoadError):
                loader.load_config("main.yaml")
    
    def test_relative_path_resolution(self):
        """Test that relative paths in includes are resolved correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory structure
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            
            # Create config in subdirectory
            sub_config = {
                "actions": {
                    "jump": {"id": "jump", "name": "jump", "cost": 5, "description": "Jump"}
                }
            }
            
            main_config = {
                "includes": ["subdir/config.yaml"],
                "players": [{"name": "TestPlayer", "provider": "openai", "model": "gpt-4"}]
            }
            
            # Write config files
            with open(subdir / "config.yaml", 'w') as f:
                yaml.dump(sub_config, f)
            
            with open(Path(temp_dir) / "main.yaml", 'w') as f:
                yaml.dump(main_config, f)
            
            # Load main config
            loader = ConfigLoader(temp_dir)
            result = loader.load_config("main.yaml")
            
            # Should have action from subdirectory
            assert "jump" in result["actions"]
            assert result["actions"]["jump"]["cost"] == 5
    
    def test_convenience_function(self):
        """Test the load_game_config convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                "game_settings": {
                    "num_rounds": 3,
                    "manual": "MANUAL.md"
                }
            }
            
            with open(Path(temp_dir) / "game.yaml", 'w') as f:
                yaml.dump(config_data, f)
            
            result = load_game_config("game.yaml", temp_dir)
            
            assert result["game_settings"]["num_rounds"] == 3
            assert result["game_settings"]["manual"] == "MANUAL.md"
    
    def test_cache_behavior(self):
        """Test that configs are cached and not reloaded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                "name": "test_config",
                "value": 42
            }
            
            with open(Path(temp_dir) / "test.yaml", 'w') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(temp_dir)
            
            # Load first time
            result1 = loader.load_config("test.yaml")
            
            # Load second time - should use cache
            result2 = loader.load_config("test.yaml")
            
            assert result1 == result2
            assert len(loader.get_loaded_configs()) == 1
    
    def test_clear_cache(self):
        """Test that cache can be cleared."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {"name": "test"}
            
            with open(Path(temp_dir) / "test.yaml", 'w') as f:
                yaml.dump(config_data, f)
            
            loader = ConfigLoader(temp_dir)
            loader.load_config("test.yaml")
            
            assert len(loader.get_loaded_configs()) == 1
            
            loader.clear_cache()
            assert len(loader.get_loaded_configs()) == 0
