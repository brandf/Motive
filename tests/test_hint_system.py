"""Test the hint system for guiding LLM players toward specific actions."""

import pytest
from motive.config import GameConfig, GameSettings, PlayerConfig


def test_hint_system_configuration():
    """Test that hint configuration is properly loaded and parsed."""
    # Create a game config with hints
    game_config = GameConfig(
        game_settings=GameSettings(
            num_rounds=2,
            core_config_path="core.yaml",
            theme_config_path="themes/fantasy/fantasy.yaml",
            edition_config_path="themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow.yaml",
            manual="../MANUAL.md",
            initial_ap_per_turn=20,
            hints=[
                {
                    "hint_action": "> whisper Hero \"do you have the key?\"",
                    "when": {
                        "round": 1,
                        "players": ["Lyra"]
                    }
                },
                {
                    "hint_action": "> shout \"I'm looking for the amulet!\"",
                    "when": {
                        "round": 1,
                        "players": ["Arion"]
                    }
                }
            ]
        ),
        players=[
            PlayerConfig(name="Arion", provider="google", model="gemini-2.5-flash"),
            PlayerConfig(name="Lyra", provider="google", model="gemini-2.5-flash")
        ]
    )
    
    # Verify hints are loaded
    assert game_config.game_settings.hints is not None
    assert len(game_config.game_settings.hints) == 2
    
    # Verify hint structure
    whisper_hint = game_config.game_settings.hints[0]
    assert whisper_hint["hint_action"] == "> whisper Hero \"do you have the key?\""
    assert whisper_hint["when"]["round"] == 1
    assert whisper_hint["when"]["players"] == ["Lyra"]
    
    shout_hint = game_config.game_settings.hints[1]
    assert shout_hint["hint_action"] == "> shout \"I'm looking for the amulet!\""
    assert shout_hint["when"]["round"] == 1
    assert shout_hint["when"]["players"] == ["Arion"]


def test_hint_evaluation_logic():
    """Test the hint evaluation logic for different players and rounds."""
    # Mock hint data
    hints = [
        {
            "hint_action": "> whisper Hero \"do you have the key?\"",
            "when": {
                "round": 1,
                "players": ["Lyra"]
            }
        },
        {
            "hint_action": "> shout \"I'm looking for the amulet!\"",
            "when": {
                "round": 2,
                "players": ["Arion"]
            }
        }
    ]
    
    # Test hint evaluation logic (same as in GameMaster._get_applicable_hints)
    def evaluate_hints(player_name: str, round_num: int):
        applicable_hints = []
        for hint in hints:
            # Check if hint applies to this player and round using structured when clause
            when_condition = hint.get("when", {})
            if not evaluate_when_condition(when_condition, player_name, round_num):
                continue
            
            hint_action = hint.get("hint_action", "")
            if hint_action:
                applicable_hints.append(hint_action)
        
        return applicable_hints
    
    def evaluate_when_condition(when_condition: dict, player_name: str, round_num: int) -> bool:
        """Evaluate a structured when condition to determine if a hint should be shown."""
        if not when_condition:
            return True  # No condition means always show
        
        # Check round condition
        if "round" in when_condition:
            required_round = when_condition["round"]
            if isinstance(required_round, int):
                if round_num < required_round:
                    return False
        
        # Check player condition
        if "players" in when_condition:
            target_players = when_condition["players"]
            if isinstance(target_players, list):
                if player_name not in target_players:
                    return False
            elif isinstance(target_players, str):
                if player_name != target_players:
                    return False
        
        return True
    
    # Test cases
    assert evaluate_hints("Lyra", 1) == ["> whisper Hero \"do you have the key?\""]
    assert evaluate_hints("Lyra", 2) == ["> whisper Hero \"do you have the key?\""]
    assert evaluate_hints("Arion", 1) == []  # Round 1, but hint requires round >= 2
    assert evaluate_hints("Arion", 2) == ["> shout \"I'm looking for the amulet!\""]
    assert evaluate_hints("UnknownPlayer", 1) == []  # Player not in any hints
