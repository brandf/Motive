"""Integration tests for CostConfig objects with real configuration loading."""

import pytest
import yaml
from motive.config import GameConfig, CostConfig
from motive.hooks.core_hooks import calculate_help_cost


def test_help_action_cost_calculation_real_config():
    """Test help action cost calculation with real CostConfig objects from config."""
    # Load merged configuration to get actions
    from motive.cli import load_config
    config = load_config("configs/game.yaml")
    
    # Find the help action
    help_action = config.actions.get("help")
    
    assert help_action is not None, "Help action not found in configuration"
    assert hasattr(help_action.cost, 'type'), "Help action cost should be CostConfig object"
    cost = help_action.cost
    assert cost.type == "code_binding", "Help action should use code_binding cost type"
    assert cost.function_name == "calculate_help_cost", "Should use calculate_help_cost function"
    assert cost.value == 1, "Base cost should be 1 (matches manual)"
    
    # Test cost calculation with mock objects
    class MockGameMaster:
        pass
    
    class MockCharacter:
        def __init__(self):
            self.name = "TestPlayer"
    
    class MockActionConfig:
        def __init__(self, cost):
            self.cost = cost
    
    # Test general help (no category)
    general_help_config = MockActionConfig(help_action.cost)
    general_cost = calculate_help_cost(MockGameMaster(), MockCharacter(), general_help_config, {})
    assert general_cost == 1, f"General help should cost 1, got {general_cost}"
    
    # Test category-specific help
    category_cost = calculate_help_cost(MockGameMaster(), MockCharacter(), general_help_config, {"category": "communication"})
    assert category_cost == 0, f"Category help should cost 0 (1//2), got {category_cost}"
    
    # Test empty category
    empty_category_cost = calculate_help_cost(MockGameMaster(), MockCharacter(), general_help_config, {"category": ""})
    assert empty_category_cost == 1, f"Empty category should cost 1, got {empty_category_cost}"
    
    # Test whitespace category
    whitespace_category_cost = calculate_help_cost(MockGameMaster(), MockCharacter(), general_help_config, {"category": "   "})
    assert whitespace_category_cost == 1, f"Whitespace category should cost 1, got {whitespace_category_cost}"


def test_all_actions_have_valid_cost_configs():
    """Test that all actions in the real configuration have valid cost configurations."""
    from motive.config import CoreConfig
    with open("configs/core.yaml", "r", encoding="utf-8") as f:
        core_config_data = yaml.safe_load(f)
    core_config = CoreConfig(**core_config_data)
    
    for action_id, action in core_config.actions.items():
        if isinstance(action.cost, int):
            # Static cost - should be non-negative (0 is valid for pass action)
            assert action.cost >= 0, f"Action {action_id} has invalid static cost: {action.cost}"
        elif isinstance(action.cost, CostConfig):
            # Dynamic cost - should have valid type and function
            assert action.cost.type in ["static", "code_binding"], f"Action {action_id} has invalid cost type: {action.cost.type}"
            if action.cost.type == "code_binding":
                assert action.cost.function_name is not None, f"Action {action_id} missing function_name for code_binding cost"
                assert action.cost.value is not None, f"Action {action_id} missing value for code_binding cost"
            elif action.cost.type == "static":
                assert action.cost.value is not None, f"Action {action_id} missing value for static cost"
                assert action.cost.value > 0, f"Action {action_id} has invalid static cost value: {action.cost.value}"
        else:
            pytest.fail(f"Action {action_id} has invalid cost type: {type(action.cost)}")


def test_cost_config_serialization():
    """Test that CostConfig objects can be properly serialized and deserialized."""
    # Test code_binding cost
    code_binding_cost = CostConfig(type="code_binding", function_name="calculate_help_cost", value=10)
    assert code_binding_cost.type == "code_binding"
    assert code_binding_cost.function_name == "calculate_help_cost"
    assert code_binding_cost.value == 10
    
    # Test static cost
    static_cost = CostConfig(type="static", value=5)
    assert static_cost.type == "static"
    assert static_cost.value == 5
    assert static_cost.function_name is None


def test_help_action_integration_with_real_objects():
    """Test help action integration using real GameMaster and Character objects."""
    from motive.game_master import GameMaster
    from motive.character import Character

    # Load merged configuration to get actions
    from motive.cli import load_config
    config = load_config("configs/game.yaml")
    
    # Create a minimal GameMaster for testing
    class MockGameMaster:
        def __init__(self):
            self.game_config = config
    
    # Create a real Character
    player_char = Character(
        char_id="test_char",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Find help action
    help_action = config.actions.get("help")
    
    assert help_action is not None
    
    # Test cost calculation with real objects
    gm = MockGameMaster()
    
    # Test general help
    general_cost = calculate_help_cost(gm, player_char, help_action, {})
    assert general_cost == 1
    
    # Test category help
    category_cost = calculate_help_cost(gm, player_char, help_action, {"category": "communication"})
    assert category_cost == 0  # 1 // 2 = 0
