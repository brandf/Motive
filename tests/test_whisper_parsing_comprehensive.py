"""Comprehensive tests for whisper action parsing covering real-world failure cases."""

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


class TestWhisperParsingSuccessCases:
    """Test cases that should parse successfully."""
    
    def test_simple_quoted_phrase(self, available_actions):
        """Test simple whisper with quoted phrase."""
        action_line = 'whisper hero "do you have the key?"'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "hero"
        assert params["phrase"] == "do you have the key?"
    
    def test_simple_unquoted_phrase(self, available_actions):
        """Test simple whisper with unquoted phrase."""
        action_line = 'whisper hero hello there'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "hero"
        assert params["phrase"] == "hello there"
    
    def test_multi_word_player_name(self, available_actions):
        """Test whisper to player with multi-word name."""
        action_line = 'whisper "Captain Marcus" "any news?"'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "Captain Marcus"
        assert params["phrase"] == "any news?"


class TestWhisperParsingFailureCases:
    """Test cases that currently fail and need to be fixed."""
    
    def test_complex_quoted_phrase_with_apostrophes(self, available_actions):
        """Test whisper with complex phrase containing apostrophes - this currently fails."""
        # This is the type of input that was failing in the logs
        action_line = 'whisper "Hooded Figure" \'mutual "friends" are getting restless. Any new intel on the town\'s patrols that might "ease their minds"?\''
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None, "Action should be parsed"
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "Hooded Figure"
        assert params["phrase"] == 'mutual "friends" are getting restless. Any new intel on the town\'s patrols that might "ease their minds"?'
    
    def test_phrase_with_quotes_and_apostrophes(self, available_actions):
        """Test whisper with phrase containing both quotes and apostrophes."""
        action_line = 'whisper "Guild Master" "Our mutual \\"friends\\" are getting restless, you said? What precisely do they require regarding the town\'s patrols?"'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None, "Action should be parsed"
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "Guild Master"
        assert params["phrase"] == 'Our mutual "friends" are getting restless, you said? What precisely do they require regarding the town\'s patrols?'
    
    def test_phrase_with_to_clause(self, available_actions):
        """Test whisper with 'to X' clause that should fail with helpful error."""
        action_line = 'whisper "Hooded Figure" "Are you here regarding the disappearances?" to Hooded Figure'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None, "Action should be parsed (but with error)"
        action_config, params = result
        assert action_config.name == "whisper"
        # Should have parse error marker for natural language format
        assert '_whisper_parse_error' in params, "Should have whisper parse error for natural language format"
        assert "Natural language 'to X' format not supported" in params['_whisper_parse_error']
    
    def test_phrase_with_escaped_quotes(self, available_actions):
        """Test whisper with escaped quotes in phrase."""
        action_line = 'whisper "Captain Marcus" "The Guild Master is here, asking questions. Our mutual \\"friends\\" are getting restless, you said? What precisely do they require regarding the town\'s patrols? And what of my family\'s safety in all this?"'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None, "Action should be parsed"
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "Captain Marcus"
        assert params["phrase"] == 'The Guild Master is here, asking questions. Our mutual "friends" are getting restless, you said? What precisely do they require regarding the town\'s patrols? And what of my family\'s safety in all this?'


class TestWhisperParsingEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_phrase(self, available_actions):
        """Test whisper with empty phrase."""
        action_line = 'whisper hero ""'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "hero"
        assert params["phrase"] == ""
    
    def test_missing_phrase(self, available_actions):
        """Test whisper with missing phrase."""
        action_line = 'whisper hero'
        result = _parse_single_action_line(action_line, available_actions)
        
        # This should either parse with empty phrase or fail gracefully
        if result is not None:
            action_config, params = result
            assert action_config.name == "whisper"
            assert params["player"] == "hero"
            # phrase might be None or empty string
        else:
            # If parsing fails, that's also acceptable behavior
            pass
    
    def test_whisper_with_extra_words(self, available_actions):
        """Test whisper with extra words that should be ignored."""
        action_line = 'whisper hero "hello there" please'
        result = _parse_single_action_line(action_line, available_actions)
        
        assert result is not None
        action_config, params = result
        assert action_config.name == "whisper"
        assert params["player"] == "hero"
        assert params["phrase"] == "hello there"


def test_real_world_failure_cases(available_actions):
    """Test the exact failure cases from the game logs."""
    
    # These are the exact inputs that were failing in the logs
    failure_cases = [
        # Case 1: Complex phrase with quotes and apostrophes
        {
            'input': 'whisper \'Our mutual "friends" are getting restless. Any new intel on the town\'s patrols that might "ease their minds"?\' to Hooded Figure',
            'expected_player': 'Hooded Figure',
            'expected_phrase': 'Our mutual "friends" are getting restless. Any new intel on the town\'s patrols that might "ease their minds"?'
        },
        # Case 2: Phrase with 'to' clause
        {
            'input': 'whisper \'Are you here regarding the disappearances?\' to Hooded Figure',
            'expected_player': 'Hooded Figure', 
            'expected_phrase': 'Are you here regarding the disappearances?'
        },
        # Case 3: Complex phrase with escaped quotes
        {
            'input': 'whisper \'The Guild Master is here, asking questions. Our mutual "friends" are getting restless, you said? What precisely do they require regarding the town\\\'s patrols? And what of my family\\\'s safety in all this?\' to Hooded Figure',
            'expected_player': 'Hooded Figure',
            'expected_phrase': 'The Guild Master is here, asking questions. Our mutual "friends" are getting restless, you said? What precisely do they require regarding the town\'s patrols? And what of my family\'s safety in all this?'
        }
    ]
    
    for i, case in enumerate(failure_cases):
        result = _parse_single_action_line(case['input'], available_actions)
        
        assert result is not None, f"Case {i+1} should be parsed (but with error): {case['input']}"
        action_config, params = result
        assert action_config.name == "whisper", f"Case {i+1} should parse as whisper action"
        # These are natural language formats that should now fail with helpful error
        assert '_whisper_parse_error' in params, f"Case {i+1} should have whisper parse error for natural language format"
        assert "Natural language 'to X' format not supported" in params['_whisper_parse_error'] or "Malformed whisper format detected" in params['_whisper_parse_error']

