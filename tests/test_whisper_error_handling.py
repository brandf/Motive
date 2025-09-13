#!/usr/bin/env python3
"""Test whisper error handling for invalid formats."""

import pytest
from motive.action_parser import _parse_single_action_line
from motive.config import ActionConfig, ParameterConfig


@pytest.fixture
def whisper_action():
    """Create whisper action config for testing."""
    return ActionConfig(
        id="whisper",
        name="whisper",
        cost=10,
        description="Whisper privately to a specific player in the same room.",
        category="communication",
        parameters=[
            ParameterConfig(
                name="player",
                type="string",
                description="The name of the player to whisper to.",
                required=True
            ),
            ParameterConfig(
                name="phrase",
                type="string", 
                description="The phrase to whisper.",
                required=True
            )
        ],
        requirements=[],
        effects=[]
    )


@pytest.fixture
def available_actions(whisper_action):
    """Create available actions dict for testing."""
    return {"whisper": whisper_action}


class TestWhisperErrorHandling:
    """Test whisper error handling for invalid formats."""
    
    def test_natural_language_to_clause_fails_with_helpful_error(self, available_actions):
        """Test that natural language 'to X' format fails with helpful error message."""
        # This is the exact format that failed in the real game
        action_line = 'whisper \'father marcus, i need to speak with you privately about the confession and the crypt. it\'s urgent and concerns the town\'s safety, as well as yours.\' to father marcus'
        
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None, "Action should be parsed (but with error)"
        action_config, params = result
        assert action_config.name == "whisper"
        
        # Debug: print what we got
        print(f"Params: {params}")
        
        # Should have parse error marker
        assert '_whisper_parse_error' in params, f"Should have whisper parse error. Got: {params}"
        assert "Invalid whisper format" in params['_whisper_parse_error']
        assert "Expected: whisper \"player_name\" \"message\"" in params['_whisper_parse_error']
    
    def test_unquoted_format_works(self, available_actions):
        """Test that unquoted format works (this is valid CLI format)."""
        action_line = 'whisper John hello there'
        
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None, "Action should be parsed successfully"
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "John"
        assert params["phrase"] == "hello there"
        
        # Should NOT have parse error marker
        assert '_whisper_parse_error' not in params, "Should not have whisper parse error for valid unquoted format"
    
    def test_proper_cli_format_works(self, available_actions):
        """Test that proper CLI format works without errors."""
        action_line = 'whisper "Father Marcus" "I need to speak with you privately"'
        
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None, "Action should be parsed successfully"
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "Father Marcus"
        assert params["phrase"] == "I need to speak with you privately"
        
        # Should NOT have parse error marker
        assert '_whisper_parse_error' not in params, "Should not have whisper parse error"
