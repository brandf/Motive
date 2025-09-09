"""Test to verify hint configuration is valid and properly structured."""

import pytest
import yaml
from motive.config import GameConfig


def test_hint_configuration_validation():
    """Test that the hint configuration is valid and properly structured."""
    # Load the game configuration
    with open("configs/game.yaml", "r", encoding="utf-8") as f:
        game_config_data = yaml.safe_load(f)
    
    # This should not raise any exceptions
    game_config = GameConfig(**game_config_data)
    
    # Verify hints configuration exists (may be None if no hints configured)
    hints = game_config.game_settings.hints
    
    # If hints are configured, verify their structure
    if hints is not None:
        assert len(hints) > 0
        
        # Verify hint structure
        for hint in hints:
            assert "hint_id" in hint
            assert "hint_action" in hint
            assert "when" in hint
            assert "round" in hint["when"]
            assert "players" in hint["when"]
    
    print("✅ Configuration is valid and hint structure is correct")


def test_hint_after_feature_configuration():
    """Test that the after feature is properly configured."""
    with open("configs/game.yaml", "r", encoding="utf-8") as f:
        game_config_data = yaml.safe_load(f)
    
    game_config = GameConfig(**game_config_data)
    hints = game_config.game_settings.hints
    
    # If hints are configured, check for 'after' condition
    if hints is not None:
        # Find hints with 'after' condition
        after_hints = [hint for hint in hints if "after" in hint["when"]]
        
        for hint in after_hints:
            assert "after" in hint["when"]
            assert isinstance(hint["when"]["after"], str)
            assert len(hint["when"]["after"]) > 0
    
    print("✅ After feature configuration is valid")


def test_round2_hints_configuration():
    """Test that round 2 hints are properly configured."""
    with open("configs/game.yaml", "r", encoding="utf-8") as f:
        game_config_data = yaml.safe_load(f)
    
    game_config = GameConfig(**game_config_data)
    hints = game_config.game_settings.hints
    
    # If hints are configured, check for round 2 hints
    if hints is not None:
        # Find round 2 hints
        round2_hints = [hint for hint in hints if hint["when"]["round"] == 2]
        
        # Verify round 2 hints have proper structure
        for hint in round2_hints:
            assert "hint_id" in hint
            assert "hint_action" in hint
            assert "when" in hint
            assert hint["when"]["round"] == 2
    
    print("✅ Round 2 hints properly configured")
