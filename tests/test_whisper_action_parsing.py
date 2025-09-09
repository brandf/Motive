"""Test whisper action parsing to identify the parameter extraction issue."""

import pytest
from motive.action_parser import _parse_single_action_line
from motive.config import ActionConfig, ParameterConfig


def test_whisper_action_parsing():
    """Test that whisper action parameters are parsed correctly."""
    # Create whisper action config
    whisper_action = ActionConfig(
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
    
    available_actions = {"whisper": whisper_action}
    
    # Test the problematic input
    action_line = 'whisper hero "do you have the key?"'
    result = _parse_single_action_line(action_line, available_actions)
    
    assert result is not None, "Action should be parsed"
    action_config, params = result
    
    assert action_config.name == "whisper"
    print(f"Parsed parameters: {params}")
    
    # The current parser will fail to extract both parameters
    # This test documents the issue
    if "player" in params and "phrase" in params:
        print("✅ Both parameters extracted correctly")
        assert params["player"] == "hero"
        assert params["phrase"] == "do you have the key?"
    else:
        print("❌ Parameter extraction failed - this is the bug we need to fix")
        print(f"Expected: {{'player': 'hero', 'phrase': 'do you have the key?'}}")
        print(f"Actual: {params}")


def test_single_parameter_action_parsing():
    """Test that single parameter actions still work correctly."""
    # Create a simple say action
    say_action = ActionConfig(
        id="say",
        name="say",
        cost=10,
        description="Say something to other players in the room.",
        category="communication",
        parameters=[
            ParameterConfig(
                name="phrase",
                type="string",
                description="The phrase to say.",
                required=True
            )
        ],
        requirements=[],
        effects=[]
    )
    
    available_actions = {"say": say_action}
    
    # Test single parameter parsing
    action_line = 'say "Hello everyone!"'
    result = _parse_single_action_line(action_line, available_actions)
    
    assert result is not None, "Action should be parsed"
    action_config, params = result
    
    assert action_config.name == "say"
    assert "phrase" in params
    assert params["phrase"] == "Hello everyone!"
    print("✅ Single parameter parsing works correctly")
