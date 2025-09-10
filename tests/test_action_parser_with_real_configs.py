"""
Test action parser with real action configurations.
"""
import pytest
from unittest.mock import Mock, patch
from motive.action_parser import parse_player_response
from motive.config_loader import load_and_validate_game_config


class TestActionParserWithRealConfigs:
    """Test action parser with real action configurations."""
    
    def test_pickup_with_real_configs(self):
        """Test pickup action parsing with real action configurations."""
        # Load real config to get actual action definitions
        config = load_and_validate_game_config("game.yaml", base_path="configs", validate=False)
        
        # Get the actions from the config
        actions = config.get('actions', {})
        print(f"Available actions: {list(actions.keys())}")
        
        # Test pickup action parsing
        action_text = '> pickup "Large Sword"'
        parsed_actions, errors = parse_player_response(action_text, actions)
        
        print(f"Input: {action_text}")
        print(f"Parsed actions: {parsed_actions}")
        print(f"Errors: {errors}")
        
        if parsed_actions:
            action, params = parsed_actions[0]
            print(f"Action name: {action.name if hasattr(action, 'name') else action.get('name', 'unknown')}")
            print(f"Object name: '{params.get('object_name', 'NOT_FOUND')}'")
            
            # Check if quotes are properly stripped
            object_name = params.get('object_name', '')
            assert not object_name.startswith('"'), f"Object name starts with quote: '{object_name}'"
            assert not object_name.endswith('"'), f"Object name ends with quote: '{object_name}'"
            assert not object_name.startswith("'"), f"Object name starts with single quote: '{object_name}'"
            assert not object_name.endswith("'"), f"Object name ends with single quote: '{object_name}'"
        else:
            assert False, f"Failed to parse action: {action_text}, errors: {errors}"
