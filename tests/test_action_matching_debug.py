"""
Debug action matching logic.
"""
import pytest
from unittest.mock import Mock
from motive.action_parser import _parse_single_action_line


class TestActionMatchingDebug:
    """Debug action matching logic."""
    
    def test_action_matching_with_conflicting_names(self):
        """Test action matching when there are conflicting action names."""
        # Create actions that might conflict
        pickup_action = Mock()
        pickup_action.name = "pickup"
        pickup_action.parameters = []
        
        pass_action = Mock()
        pass_action.name = "pass"
        pass_action.parameters = []
        
        # Test with actions that might cause conflicts
        available_actions = {
            "pickup": pickup_action,
            "pass": pass_action
        }
        
        # Test pickup action
        action_line = 'pickup "Large Sword"'
        result = _parse_single_action_line(action_line, available_actions)
        
        if result:
            action, params = result
            print(f"Matched action: {action.name}")
            print(f"Parameters: {params}")
            assert action.name == "pickup", f"Expected 'pickup', got '{action.name}'"
        else:
            assert False, "Failed to match pickup action"
    
    def test_action_matching_with_pickup_only(self):
        """Test action matching with only pickup action."""
        # Create only pickup action
        pickup_action = Mock()
        pickup_action.name = "pickup"
        object_name_param = Mock()
        object_name_param.type = "string"
        object_name_param.name = "object_name"
        pickup_action.parameters = [object_name_param]
        
        available_actions = {
            "pickup": pickup_action
        }
        
        # Test pickup action
        action_line = 'pickup "Large Sword"'
        result = _parse_single_action_line(action_line, available_actions)
        
        if result:
            action, params = result
            print(f"Matched action: {action.name}")
            print(f"Object name: '{params.get('object_name', 'NOT_FOUND')}'")
            assert action.name == "pickup"
            assert params.get('object_name') == "Large Sword"
        else:
            assert False, "Failed to match pickup action"
