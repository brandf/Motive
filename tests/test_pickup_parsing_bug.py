"""
Test pickup action parsing bug with quoted object names.
"""
import pytest
from unittest.mock import Mock, patch
from motive.game_master import GameMaster
from motive.character import Character
from motive.player import Player
from motive.room import Room
from motive.game_object import GameObject
from motive.config import ActionConfig, ParameterConfig


class TestPickupParsingBug:
    """Test that pickup action correctly parses quoted object names."""
    
    def test_pickup_quoted_object_name_parsing(self):
        """Test that pickup with quoted object name like 'legendary sword' works correctly."""
        # This test should FAIL initially, demonstrating the bug
        
        # Create mock available actions with proper parameter structure
        pickup_action = Mock()
        pickup_action.name = "pickup"
        
        # Create mock parameter for object_name
        object_name_param = Mock()
        object_name_param.type = "string"
        object_name_param.name = "object_name"
        object_name_param.required = True
        
        pickup_action.parameters = [object_name_param]
        available_actions = {"pickup": pickup_action}
        
        # Test the action parsing - this should work with quoted names
        action_text = '> pickup "legendary sword"'
        
        # The issue is likely in the action parser - let's test what it extracts
        from motive.action_parser import parse_player_response
        
        # This should extract the object name correctly without quotes
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        # Should find one pickup action
        assert len(parsed_actions) == 1
        action, params = parsed_actions[0]
        assert action.name == "pickup"
        assert params["object_name"] == "legendary sword"  # Should be without quotes
        
    def test_pickup_unquoted_object_name_parsing(self):
        """Test that pickup with unquoted object name also works."""
        # Create mock available actions with proper parameter structure
        pickup_action = Mock()
        pickup_action.name = "pickup"
        
        # Create mock parameter for object_name
        object_name_param = Mock()
        object_name_param.type = "string"
        object_name_param.name = "object_name"
        object_name_param.required = True
        
        pickup_action.parameters = [object_name_param]
        available_actions = {"pickup": pickup_action}
        
        action_text = '> pickup legendary sword'
        
        from motive.action_parser import parse_player_response
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        assert len(parsed_actions) == 1
        action, params = parsed_actions[0]
        assert action.name == "pickup"
        assert params["object_name"] == "legendary sword"
