"""
Debug test for action parser quote handling.
"""
import pytest
from unittest.mock import Mock
from motive.action_parser import parse_player_response


class TestActionParserDebug:
    """Debug action parser quote handling."""
    
    def test_debug_quoted_parsing(self):
        """Debug the exact issue we're seeing in the logs."""
        # Create mock pickup action
        pickup_action = Mock()
        pickup_action.name = "pickup"
        object_name_param = Mock()
        object_name_param.type = "string"
        object_name_param.name = "object_name"
        object_name_param.required = True
        pickup_action.parameters = [object_name_param]
        available_actions = {"pickup": pickup_action}
        
        # Test the exact strings from the log
        test_cases = [
            '> pickup "warrior\'s armor"',
            '> pickup "legendary sword"',
            '> pickup "paladin\'s sword"',
            '> pickup "tiny gem"'
        ]
        
        for action_text in test_cases:
            print(f"\nTesting: {action_text}")
            parsed_actions, errors = parse_player_response(action_text, available_actions)
            
            if parsed_actions:
                action, params = parsed_actions[0]
                print(f"Parsed object_name: '{params['object_name']}'")
                # Check if quotes are properly stripped
                assert not params["object_name"].startswith('"'), f"Object name starts with quote: '{params['object_name']}'"
                assert not params["object_name"].endswith('"'), f"Object name ends with quote: '{params['object_name']}'"
                assert not params["object_name"].startswith("'"), f"Object name starts with single quote: '{params['object_name']}'"
                assert not params["object_name"].endswith("'"), f"Object name ends with single quote: '{params['object_name']}'"
            else:
                print(f"No actions parsed for: {action_text}")
                print(f"Errors: {errors}")
                assert False, f"Failed to parse action: {action_text}"
