"""
Debug multiple actions parsing.
"""
import pytest
from unittest.mock import Mock
from motive.action_parser import parse_player_response


class TestMultipleActionsDebug:
    """Debug multiple actions parsing."""
    
    def test_multiple_pickup_actions(self):
        """Test parsing multiple pickup actions like in the game log."""
        # Create mock pickup action
        pickup_action = Mock()
        pickup_action.name = "pickup"
        object_name_param = Mock()
        object_name_param.type = "string"
        object_name_param.name = "object_name"
        object_name_param.required = True
        pickup_action.parameters = [object_name_param]
        available_actions = {"pickup": pickup_action}
        
        # Test the exact input from the game log
        action_text = '> pickup "warrior\'s armor"\n> pickup "legendary sword"\n> pickup "paladin\'s sword"\n> pickup "tiny gem"'
        
        print(f"Input: {repr(action_text)}")
        parsed_actions, errors = parse_player_response(action_text, available_actions)
        
        print(f"Parsed actions: {parsed_actions}")
        print(f"Errors: {errors}")
        
        # Check each parsed action
        for i, (action, params) in enumerate(parsed_actions):
            print(f"Action {i}: {action.name if hasattr(action, 'name') else action.get('name', 'unknown')}")
            print(f"  Object name: '{params.get('object_name', 'NOT_FOUND')}'")
            
            # Check if quotes are properly stripped
            object_name = params.get('object_name', '')
            assert not object_name.startswith('"'), f"Action {i} object name starts with quote: '{object_name}'"
            assert not object_name.endswith('"'), f"Action {i} object name ends with quote: '{object_name}'"
            assert not object_name.startswith("'"), f"Action {i} object name starts with single quote: '{object_name}'"
            assert not object_name.endswith("'"), f"Action {i} object name ends with single quote: '{object_name}'"
        
        assert len(parsed_actions) == 4, f"Expected 4 actions, got {len(parsed_actions)}"
