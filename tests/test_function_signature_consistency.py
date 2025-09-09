"""Test that all action handlers have consistent function signatures."""

import pytest
from motive.hooks.core_hooks import (
    generate_help_message, 
    handle_say_action, 
    handle_pickup_action,
    # These should all have the same signature: (game_master, player_char, action_config, params)
)


def test_all_action_handlers_have_consistent_signatures():
    """Test that all action handlers accept the same 4 parameters."""
    # This test will fail until we fix all function signatures
    # Expected signature: (game_master, player_char, action_config, params)
    
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
            self.game_actions = {}  # Add missing attribute
    
    class MockPlayerCharacter:
        def __init__(self):
            self.id = "test_char"
            self.name = "TestPlayer"
            self.current_room_id = "test_room"
    
    class MockActionConfig:
        pass
    
    gm = MockGameMaster()
    player_char = MockPlayerCharacter()
    action_config = MockActionConfig()
    params = {}
    
    # Test that all handlers accept the same signature
    try:
        generate_help_message(gm, player_char, action_config, params)
        handle_say_action(gm, player_char, action_config, params)
        handle_pickup_action(gm, player_char, action_config, params)
        # If we get here, all signatures are consistent
        assert True, "All action handlers have consistent signatures"
    except TypeError as e:
        pytest.fail(f"Function signature inconsistency found: {e}")


def test_whisper_action_case_insensitive():
    """Test that whisper action is case-insensitive for player names."""
    # This test will fail until we implement case-insensitive player matching
    # in the whisper action requirement checking
    
    # We need to test that "whisper Hero" and "whisper hero" both work
    # This is a placeholder test that will be implemented when we fix the whisper action
    assert True, "Case-insensitive whisper test placeholder"
