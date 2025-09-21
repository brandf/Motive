#!/usr/bin/env python3
"""
Integration test for config loading and game initialization.

This test verifies that the config loading pipeline works end-to-end
without mocking, catching issues like the one where config loads correctly
but GameMaster initialization fails.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from motive.cli import load_config
from motive.game_master import GameMaster


class TestConfigLoadingIntegration:
    """Test that config loading works end-to-end with game initialization."""
    
    def test_real_config_loads_correctly(self):
        """Test that the real game.yaml config loads with expected content."""
        config = load_config("configs/game.yaml", validate=True)
        
        # Verify v2 config structure
        assert hasattr(config, 'game_settings')
        assert hasattr(config, 'players')
        assert hasattr(config, 'entity_definitions')
        assert hasattr(config, 'action_definitions')
        
        # Verify we have reasonable content (not exact counts since content changes frequently)
        assert len(config.entity_definitions) > 50, f"Expected substantial number of entities, got {len(config.entity_definitions)}"
        assert len(config.action_definitions) >= 10, f"Expected at least 10 actions (core + fantasy + H&S), got {len(config.action_definitions)}"

        # Verify entity type distribution - check for reasonable ranges
        type_counts = {}
        for entity_id, entity_def in config.entity_definitions.items():
            for entity_type in entity_def.types:
                type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        assert type_counts.get('object', 0) > 30, f"Expected substantial number of objects, got {type_counts.get('object', 0)}"
        assert type_counts.get('room', 0) > 5, f"Expected reasonable number of rooms, got {type_counts.get('room', 0)}"
        assert type_counts.get('character', 0) > 3, f"Expected reasonable number of characters, got {type_counts.get('character', 0)}"
        
        # Verify all characters have motives (this is the important validation)
        characters_with_motives = 0
        total_characters = 0
        for entity_id, entity_def in config.entity_definitions.items():
            if 'character' in entity_def.types:
                total_characters += 1
                if hasattr(entity_def, 'attributes') and entity_def.attributes and 'motives' in entity_def.attributes:
                    characters_with_motives += 1
        
        assert characters_with_motives == total_characters, f"Expected all {total_characters} characters to have motives, but only {characters_with_motives} do"
    
    def test_gamemaster_initialization_with_real_config(self):
        """Test that GameMaster can initialize with the real config."""
        config = load_config("configs/game.yaml", validate=True)
        
        # Mock both manual loading and LLM client creation
        with (
            patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual"),
            patch("motive.player.create_llm_client", return_value=MagicMock())
        ):
            game_master = GameMaster(
                game_config=config,
                game_id="test_config_integration",
                deterministic=True,
                log_dir="test_logs",
                no_file_logging=True
            )
            
            # Verify GameMaster initialized correctly
            assert game_master is not None
            assert game_master.game_config is config
            
            # Verify rooms were created
            assert len(game_master.rooms) > 0, f"Expected rooms to be created, got {len(game_master.rooms)}"
            
            # Verify characters were assigned
            assert len(game_master.players) > 0, f"Expected players to be created, got {len(game_master.players)}"
            
            # Verify each player has a character
            for player in game_master.players:
                assert player.character is not None, f"Player {player.name} has no character assigned"
    
    def test_config_loading_vs_gamemaster_counts_match(self):
        """Test that config loading counts match GameMaster initialization counts."""
        config = load_config("configs/game.yaml", validate=True)
        
        # Count entities from config
        config_room_count = sum(1 for entity_def in config.entity_definitions.values()
                               if 'room' in entity_def.types)
        config_player_count = len(config.players)  # Number of players, not character types
        
        # Initialize GameMaster
        with (
            patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual"),
            patch("motive.player.create_llm_client", return_value=MagicMock())
        ):
            game_master = GameMaster(
                game_config=config,
                game_id="test_count_match",
                deterministic=True,
                log_dir="test_logs",
                no_file_logging=True
            )
            
            # Count entities from GameMaster
            gamemaster_room_count = len(game_master.rooms)
            gamemaster_player_count = len(game_master.players)
            
            # Verify counts match
            assert gamemaster_room_count == config_room_count, \
                f"Room count mismatch: config={config_room_count}, gamemaster={gamemaster_room_count}"
            
            assert gamemaster_player_count == config_player_count, \
                f"Player count mismatch: config={config_player_count}, gamemaster={gamemaster_player_count}"
    
    def test_config_loading_failure_scenarios(self):
        """Test config loading failure scenarios."""
        # Test nonexistent file
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.yaml", validate=True)
        
        # Test invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with pytest.raises(Exception):  # Should raise YAML parsing error
                load_config(config_path, validate=True)
        finally:
            os.unlink(config_path)
    
    def test_hierarchical_config_includes_work(self):
        """Test that hierarchical config includes are processed correctly."""
        config = load_config("configs/game.yaml", validate=True)
        
        # Verify that includes were processed by checking for content from included files
        # The game.yaml includes hearth_and_shadow.yaml which should have specific content
        
        # Check for specific rooms that should be in the included config
        room_names = []
        for entity_id, entity_def in config.entity_definitions.items():
            if 'room' in entity_def.types:
                if hasattr(entity_def, 'attributes') and entity_def.attributes:
                    room_name = entity_def.attributes.get('name', '')
                    if room_name:
                        room_names.append(room_name)
        
        # Should have rooms from the included config
        assert len(room_names) > 0, "No room names found in merged config"
        
        # Check for specific characters that should be in the included config
        character_names = []
        for entity_id, entity_def in config.entity_definitions.items():
            if 'character' in entity_def.types:
                if hasattr(entity_def, 'attributes') and entity_def.attributes:
                    char_name = entity_def.attributes.get('name', '')
                    if char_name:
                        character_names.append(char_name)
        
        # Should have characters from the included config
        assert len(character_names) > 0, "No character names found in merged config"


if __name__ == "__main__":
    pytest.main([__file__])
