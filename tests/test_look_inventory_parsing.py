"""Test that the action parser correctly handles 'look inventory' commands."""

import pytest
from motive.action_parser import parse_player_response


def test_look_inventory_parsing():
    """Test that 'look inventory' is parsed correctly."""
    # Mock action configs
    class MockParameter:
        def __init__(self, name, type_name, description):
            self.name = name
            self.type = type_name
            self.description = description
    
    class MockActionConfig:
        def __init__(self, name, parameters=None):
            self.name = name
            self.parameters = parameters or []
    
    mock_actions = {
        "look": MockActionConfig("look", [
            MockParameter("target", "string", "The name of the object or character to look at.")
        ])
    }
    
    # Test various forms of look inventory commands
    test_cases = [
        "> look inventory",
        "> look at inventory", 
        "> look Inventory",
        "> LOOK INVENTORY"
    ]
    
    for command in test_cases:
        parsed_actions, invalid_actions = parse_player_response(command, mock_actions)
        
        # Should parse successfully
        assert len(parsed_actions) == 1, f"Failed to parse: {command}"
        assert len(invalid_actions) == 0, f"Invalid actions for: {command}"
        
        # Should be a look action with inventory target (case preserved by parser)
        action_config, params = parsed_actions[0]
        assert action_config.name == "look", f"Wrong action for: {command}"
        # Parser preserves original case, look function handles case-insensitive matching
        assert params["target"].lower() == "inventory", f"Wrong target for: {command}"


def test_look_inventory_vs_look_object():
    """Test that 'look inventory' is distinguished from 'look at object'."""
    # Mock action configs
    class MockParameter:
        def __init__(self, name, type_name, description):
            self.name = name
            self.type = type_name
            self.description = description
    
    class MockActionConfig:
        def __init__(self, name, parameters=None):
            self.name = name
            self.parameters = parameters or []
    
    mock_actions = {
        "look": MockActionConfig("look", [
            MockParameter("target", "string", "The name of the object or character to look at.")
        ])
    }
    
    # Test that these parse differently
    inventory_command = "> look inventory"
    object_command = "> look sword"
    
    inventory_parsed, _ = parse_player_response(inventory_command, mock_actions)
    object_parsed, _ = parse_player_response(object_command, mock_actions)
    
    # Both should parse successfully
    assert len(inventory_parsed) == 1
    assert len(object_parsed) == 1
    
    # But with different targets
    _, inventory_params = inventory_parsed[0]
    _, object_params = object_parsed[0]
    
    assert inventory_params["target"] == "inventory"
    assert object_params["target"] == "sword"


def test_look_inventory_case_insensitive():
    """Test that look inventory works with different cases."""
    # Mock action configs
    class MockParameter:
        def __init__(self, name, type_name, description):
            self.name = name
            self.type = type_name
            self.description = description
    
    class MockActionConfig:
        def __init__(self, name, parameters=None):
            self.name = name
            self.parameters = parameters or []
    
    mock_actions = {
        "look": MockActionConfig("look", [
            MockParameter("target", "string", "The name of the object or character to look at.")
        ])
    }
    
    test_cases = [
        "> look inventory",
        "> look Inventory", 
        "> look INVENTORY",
        "> look at inventory",
        "> look at Inventory",
        "> look at INVENTORY"
    ]
    
    for command in test_cases:
        parsed_actions, invalid_actions = parse_player_response(command, mock_actions)
        
        # Should parse successfully
        assert len(parsed_actions) == 1, f"Failed to parse: {command}"
        assert len(invalid_actions) == 0, f"Invalid actions for: {command}"
        
        # Parser preserves original case, look function handles case-insensitive matching
        action_config, params = parsed_actions[0]
        assert params["target"].lower() == "inventory", f"Wrong target for: {command}"
