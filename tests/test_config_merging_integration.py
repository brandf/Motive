"""
Integration tests for configuration merging with real game configs.

These tests load actual game configurations and verify that merging
happens in the expected ways without being too specific about exact values.
"""

import pytest
from pathlib import Path
from motive.sim_v2.v2_config_preprocessor import V2ConfigPreprocessor
from motive.config_loader import ConfigLoader


class TestConfigMergingIntegration:
    """Integration tests for config merging with real game configs."""

    def test_game_yaml_inheritance_structure(self):
        """Test that game.yaml properly inherits from H&S config."""
        preprocessor = V2ConfigPreprocessor("configs")
        config = preprocessor.load_config("game.yaml")
        
        # Should have inherited game settings
        assert "game_settings" in config
        assert "num_rounds" in config["game_settings"]
        assert "initial_ap_per_turn" in config["game_settings"]
        
        # Should have inherited players
        assert "players" in config
        assert len(config["players"]) >= 2  # At least the base players
        
        # Should have inherited entities (v2 structure is different)
        assert "entity_definitions" in config
        # In v2, entities are stored as individual items, not grouped by type
        assert len(config["entity_definitions"]) > 0
        
        # Should have inherited actions (v2 uses action_definitions)
        assert "action_definitions" in config
        assert len(config["action_definitions"]) > 0

    def test_hs_config_inherits_fantasy_and_core(self):
        """Test that H&S config properly inherits from fantasy and core."""
        preprocessor = V2ConfigPreprocessor("configs")
        config = preprocessor.load_config("themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml")
        
        # Should have core actions (look, say, whisper, etc.)
        assert "action_definitions" in config
        core_actions = list(config["action_definitions"].keys())
        assert "look" in core_actions
        assert "say" in core_actions
        assert "whisper" in core_actions
        
        # Should have fantasy theme elements
        assert "entity_definitions" in config
        assert len(config["entity_definitions"]) > 0
        
        # Should have H&S specific content
        entity_names = list(config["entity_definitions"].keys())
        assert any("hearth" in name.lower() or "shadow" in name.lower() for name in entity_names)

    def test_players_list_merging_behavior(self):
        """Test that players lists merge correctly (not duplicate)."""
        preprocessor = V2ConfigPreprocessor("configs")
        config = preprocessor.load_config("game.yaml")
        
        # Should have exactly 3 players (not duplicated from inheritance)
        assert len(config["players"]) == 3
        
        # Should have proper player structure
        for player in config["players"]:
            assert "name" in player
            assert "provider" in player
            assert "model" in player
            assert player["name"].startswith("Player_")

    def test_entity_definitions_merge_correctly(self):
        """Test that entity definitions merge without duplication."""
        preprocessor = V2ConfigPreprocessor("configs")
        config = preprocessor.load_config("game.yaml")
        
        # Should have merged entities from all levels
        entities = config["entity_definitions"]
        
        # Should have entities from core, fantasy, and H&S
        assert len(entities) > 0
        entity_ids = list(entities.keys())
        
        # Should have core entities
        assert any("tavern" in entity_id.lower() for entity_id in entity_ids)
        
        # Should have H&S specific entities
        assert any("hearth" in entity_id.lower() or "shadow" in entity_id.lower() for entity_id in entity_ids)
        
        # Should have H&S specific characters
        assert any("detective" in entity_id.lower() or "thorn" in entity_id.lower() for entity_id in entity_ids)
        
        # Should have H&S specific objects
        assert any("evidence" in entity_id.lower() or "cult" in entity_id.lower() for entity_id in entity_ids)

    def test_actions_merge_without_duplication(self):
        """Test that actions merge correctly without duplicates."""
        preprocessor = V2ConfigPreprocessor("configs")
        config = preprocessor.load_config("game.yaml")
        
        # Should have actions from core, fantasy, and H&S
        assert len(config["action_definitions"]) > 0
        
        # Should not have duplicate action IDs
        action_ids = list(config["action_definitions"].keys())
        assert len(action_ids) == len(set(action_ids)), f"Duplicate action IDs found: {action_ids}"
        
        # Should have core actions
        assert "look" in action_ids
        assert "say" in action_ids
        assert "whisper" in action_ids
        
        # Should have H&S specific actions
        assert any("investigate" in action_id.lower() for action_id in action_ids)

    def test_game_settings_override_behavior(self):
        """Test that game settings override correctly."""
        preprocessor = V2ConfigPreprocessor("configs")
        config = preprocessor.load_config("game.yaml")
        
        # Should have game settings
        assert "game_settings" in config
        game_settings = config["game_settings"]
        
        # Should have overridden values
        assert "num_rounds" in game_settings
        assert "initial_ap_per_turn" in game_settings
        assert "log_path" in game_settings
        
        # Log path should be H&S specific
        assert "hearth_and_shadow" in game_settings["log_path"]

    def test_v2_config_structure_consistency(self):
        """Test that V2 configs have consistent structure."""
        # Load with V2 preprocessor
        v2_preprocessor = V2ConfigPreprocessor("configs")
        v2_config = v2_preprocessor.load_config("game.yaml")
        
        # Should have the expected v2 structure
        assert "players" in v2_config
        assert "entity_definitions" in v2_config
        assert "action_definitions" in v2_config
        assert "game_settings" in v2_config
        
        # Should have reasonable counts
        assert len(v2_config["players"]) >= 2
        assert len(v2_config["entity_definitions"]) > 0
        assert len(v2_config["action_definitions"]) > 0

    def test_merge_strategy_override_works_in_practice(self):
        """Test that __merge_strategy__: override works with real configs."""
        # Create a test config that uses override strategy
        test_config_content = """
game_settings:
  num_rounds: 1
  initial_ap_per_turn: 10

players:
  - __merge_strategy__: "override"
  - name: "TestPlayer1"
    provider: "test"
    model: "test-model"
  - name: "TestPlayer2"
    provider: "test"
    model: "test-model"
"""
        
        # Write test config
        test_config_path = Path("configs/test_override.yaml")
        test_config_path.write_text(test_config_content)
        
        try:
            preprocessor = V2ConfigPreprocessor("configs")
            config = preprocessor.load_config("test_override.yaml")
            
            # Should have exactly 2 players (override worked)
            assert len(config["players"]) == 2
            assert config["players"][0]["name"] == "TestPlayer1"
            assert config["players"][1]["name"] == "TestPlayer2"
            
            # Should still have other config elements
            assert "game_settings" in config
            assert config["game_settings"]["num_rounds"] == 1
            
        finally:
            # Clean up test config
            if test_config_path.exists():
                test_config_path.unlink()

    def test_merge_strategy_append_works_in_practice(self):
        """Test that __merge_strategy__: append works with real configs."""
        # Create a test config that uses append strategy
        test_config_content = """
game_settings:
  num_rounds: 1
  initial_ap_per_turn: 10

players:
  - __merge_strategy__: "append"
  - name: "BasePlayer"
    provider: "test"
    model: "test-model"
  - name: "AdditionalPlayer"
    provider: "test"
    model: "test-model"
"""
        
        # Write test config
        test_config_path = Path("configs/test_append.yaml")
        test_config_path.write_text(test_config_content)
        
        try:
            preprocessor = V2ConfigPreprocessor("configs")
            config = preprocessor.load_config("test_append.yaml")
            
            # Should have exactly 2 players (append worked - appended to empty list)
            assert len(config["players"]) == 2
            
            # Should have the expected players
            player_names = [p["name"] for p in config["players"]]
            assert "BasePlayer" in player_names
            assert "AdditionalPlayer" in player_names
            
        finally:
            # Clean up test config
            if test_config_path.exists():
                test_config_path.unlink()

    def test_complex_inheritance_chain(self):
        """Test complex inheritance chain: core -> fantasy -> H&S -> game."""
        preprocessor = V2ConfigPreprocessor("configs")
        config = preprocessor.load_config("game.yaml")
        
        # Should have elements from all levels
        assert "action_definitions" in config
        assert "entity_definitions" in config
        assert "players" in config
        assert "game_settings" in config
        
        # Should have core actions
        action_ids = list(config["action_definitions"].keys())
        assert "look" in action_ids
        assert "say" in action_ids
        
        # Should have fantasy theme elements
        entity_names = list(config["entity_definitions"].keys())
        assert any("fantasy" in name.lower() or "tavern" in name.lower() for name in entity_names)
        
        # Should have H&S specific elements
        assert any("detective" in name.lower() or "thorn" in name.lower() for name in entity_names)
        
        # Should have game-specific overrides
        assert config["game_settings"]["num_rounds"] == 10
        assert config["game_settings"]["initial_ap_per_turn"] == 40

    def test_config_loading_performance(self):
        """Test that config loading is reasonably fast."""
        import time
        
        preprocessor = V2ConfigPreprocessor("configs")
        
        start_time = time.time()
        config = preprocessor.load_config("game.yaml")
        end_time = time.time()
        
        load_time = end_time - start_time
        
        # Should load in reasonable time (less than 1 second)
        assert load_time < 1.0, f"Config loading took {load_time:.2f} seconds, which is too slow"
        
        # Should have loaded successfully
        assert config is not None
        assert len(config) > 0

    def test_missing_includes_handled_gracefully(self):
        """Test that missing include files are handled gracefully."""
        # Create a test config with missing include
        test_config_content = """
includes:
  - "nonexistent/file.yaml"

players:
  - name: "TestPlayer"
    provider: "test"
    model: "test-model"
"""
        
        # Write test config
        test_config_path = Path("configs/test_missing_include.yaml")
        test_config_path.write_text(test_config_content)
        
        try:
            preprocessor = V2ConfigPreprocessor("configs")
            
            # Should raise an appropriate error
            with pytest.raises(Exception):  # Should be V2ConfigLoadError
                preprocessor.load_config("test_missing_include.yaml")
                
        finally:
            # Clean up test config
            if test_config_path.exists():
                test_config_path.unlink()

    def test_circular_includes_prevented(self):
        """Test that circular includes are prevented."""
        # Create config A that includes B
        config_a_content = """
includes:
  - "config_b.yaml"

name: "ConfigA"
"""
        
        # Create config B that includes A
        config_b_content = """
includes:
  - "config_a.yaml"

name: "ConfigB"
"""
        
        # Write test configs
        config_a_path = Path("configs/config_a.yaml")
        config_b_path = Path("configs/config_b.yaml")
        
        config_a_path.write_text(config_a_content)
        config_b_path.write_text(config_b_content)
        
        try:
            preprocessor = V2ConfigPreprocessor("configs")
            
            # Should raise an appropriate error for circular dependency
            with pytest.raises(Exception):  # Should be V2ConfigLoadError
                preprocessor.load_config("config_a.yaml")
                
        finally:
            # Clean up test configs
            if config_a_path.exists():
                config_a_path.unlink()
            if config_b_path.exists():
                config_b_path.unlink()
