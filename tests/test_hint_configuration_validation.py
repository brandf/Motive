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
    
    # Verify we have hints
    assert game_config.game_settings.hints is not None
    assert len(game_config.game_settings.hints) > 0
    
    # Verify specific hints exist
    hint_ids = [hint["hint_id"] for hint in game_config.game_settings.hints]
    assert "whisper_test" in hint_ids
    assert "shout_test" in hint_ids
    assert "help_communication_test" in hint_ids
    assert "follow_up_whisper" in hint_ids
    assert "round2_test" in hint_ids
    
    print("✅ Configuration is valid and all expected hints are present")


def test_hint_after_feature_configuration():
    """Test that the after feature is properly configured."""
    with open("configs/game.yaml", "r", encoding="utf-8") as f:
        game_config_data = yaml.safe_load(f)
    
    game_config = GameConfig(**game_config_data)
    hints = game_config.game_settings.hints
    
    # Find the follow_up_whisper hint
    follow_up_hint = None
    for hint in hints:
        if hint["hint_id"] == "follow_up_whisper":
            follow_up_hint = hint
            break
    
    assert follow_up_hint is not None, "follow_up_whisper hint not found"
    
    # Verify it has the after condition
    assert "after" in follow_up_hint["when"], "follow_up_whisper missing 'after' condition"
    assert follow_up_hint["when"]["after"] == "whisper_test", "follow_up_whisper should depend on whisper_test"
    
    # Verify it's configured for round 2 (to fix timing issue)
    assert follow_up_hint["when"]["round"] == 2, "follow_up_whisper should be in round 2"
    
    print("✅ follow_up_whisper hint properly configured with after condition for round 2")


def test_round2_hints_configuration():
    """Test that round 2 hints are properly configured."""
    with open("configs/game.yaml", "r", encoding="utf-8") as f:
        game_config_data = yaml.safe_load(f)
    
    game_config = GameConfig(**game_config_data)
    hints = game_config.game_settings.hints
    
    # Find round 2 hints
    round2_hints = [hint for hint in hints if hint["when"]["round"] == 2]
    
    assert len(round2_hints) >= 2, "Should have at least 2 round 2 hints"
    
    round2_hint_ids = [hint["hint_id"] for hint in round2_hints]
    assert "follow_up_whisper" in round2_hint_ids
    assert "round2_test" in round2_hint_ids
    
    print(f"✅ Found {len(round2_hints)} round 2 hints: {round2_hint_ids}")
