"""
Test action parser quote handling for object names.
"""
import pytest
from unittest.mock import Mock
from motive.action_parser import parse_player_response


class TestActionParserQuoteHandling:
    """Test that action parser correctly handles quoted object names."""
    
    def test_pickup_quoted_object_name_parsing(self):
        """Test that pickup action correctly parses quoted object names."""
        # Create mock pickup action
        pickup_action = Mock()
        pickup_action.name = "pickup"
        object_name_param = Mock()
        object_name_param.type = "string"
        object_name_param.name = "object_name"
        object_name_param.required = True
        pickup_action.parameters = [object_name_param]
        available_actions = {"pickup": pickup_action}
        
        # Test with double quotes
        action_text = '> pickup "Large Sword"'
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        assert len(parsed_actions) == 1
        action, params = parsed_actions[0]
        assert action.name == "pickup"
        assert params["object_name"] == "Large Sword"  # Quotes should be stripped
        
        # Test with single quotes
        action_text = "> pickup 'Warrior's Armor'"
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        assert len(parsed_actions) == 1
        action, params = parsed_actions[0]
        assert action.name == "pickup"
        assert params["object_name"] == "Warrior's Armor"  # Quotes should be stripped
        
        # Test with unquoted name
        action_text = "> pickup Tiny Gem"
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        assert len(parsed_actions) == 1
        action, params = parsed_actions[0]
        assert action.name == "pickup"
        assert params["object_name"] == "Tiny Gem"  # No quotes to strip
    
    def test_pickup_malformed_quotes_parsing(self):
        """Test that pickup action handles malformed quotes correctly."""
        # Create mock pickup action
        pickup_action = Mock()
        pickup_action.name = "pickup"
        object_name_param = Mock()
        object_name_param.type = "string"
        object_name_param.name = "object_name"
        object_name_param.required = True
        pickup_action.parameters = [object_name_param]
        available_actions = {"pickup": pickup_action}
        
        # Test with mismatched quotes (what we're seeing in the logs)
        action_text = '> pickup "Large Sword"'
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        assert len(parsed_actions) == 1
        action, params = parsed_actions[0]
        assert action.name == "pickup"
        # This should work correctly
        assert params["object_name"] == "Large Sword"
        
        # Test with quotes that don't match properly
        action_text = '> pickup "Warrior\'s Armor"'
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        assert len(parsed_actions) == 1
        action, params = parsed_actions[0]
        assert action.name == "pickup"
        # This should handle the mixed quotes correctly
        assert params["object_name"] == "Warrior's Armor"
