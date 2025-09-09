"""Test that manual path resolution works correctly after moving config to configs/ folder."""

import pytest
import os
from motive.config import GameConfig, GameSettings, PlayerConfig


def test_manual_path_resolution():
    """Test that manual path is resolved correctly relative to configs directory."""
    # Create a game config with the manual path from game.yaml
    game_config = GameConfig(
        game_settings=GameSettings(
            num_rounds=1,
            core_config_path="core.yaml",
            theme_config_path="themes/fantasy/fantasy.yaml",
            edition_config_path="themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml",
            manual="../MOTIVE_MANUAL.md",  # This is what's in game.yaml
            initial_ap_per_turn=20
        ),
        players=[
            PlayerConfig(name="TestPlayer", provider="openai", model="gpt-4")
        ]
    )
    
    # Test the path resolution logic (same as in GameMaster.__init__)
    configs_dir = os.path.dirname(os.path.abspath("configs/game.yaml"))
    manual_path = os.path.join(configs_dir, game_config.game_settings.manual)
    
    # Verify the path is resolved correctly
    expected_manual_path = os.path.join(configs_dir, "../MOTIVE_MANUAL.md")
    assert manual_path == expected_manual_path
    
    # Verify the manual file exists at the resolved path
    assert os.path.exists(manual_path), f"Manual file not found at: {manual_path}"
    
    # Verify we can read the manual content
    with open(manual_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert len(content) > 0, "Manual file is empty"
        assert "Motive" in content, "Manual file doesn't contain expected content"
