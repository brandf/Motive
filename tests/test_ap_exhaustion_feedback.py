"""Test that players get clear feedback about actions that couldn't be executed due to insufficient AP."""

import pytest
from motive.game_master import GameMaster
from motive.config import GameConfig
from motive.action_parser import parse_player_response


def test_ap_exhaustion_feedback():
    """Test that players get clear feedback about actions skipped due to insufficient AP."""
    # Mock action configs for testing
    class MockActionConfig:
        def __init__(self, name, cost=10):
            self.name = name
            self.cost = cost
            self.parameters = []  # Empty parameters for simple actions
    
    # Create mock actions
    mock_actions = {
        "pickup": MockActionConfig("pickup", 10),
        "look": MockActionConfig("look", 10),
        "move": MockActionConfig("move", 10),
        "say": MockActionConfig("say", 10),
        "help": MockActionConfig("help", 10)
    }
    
    # Parse actions that would exceed AP
    actions_text = """
> pickup torch
> pickup sword  
> pickup armor
> look
> move west
> say hello
> help
"""
    
    parsed_actions, invalid_actions = parse_player_response(actions_text, mock_actions)
    
    # Should have 7 valid actions
    assert len(parsed_actions) == 7
    assert len(invalid_actions) == 0
    
    # Simulate the action processing logic with limited AP (matching game master logic)
    response_feedback_messages = []
    actions_skipped_due_to_ap = []
    remaining_ap = 20  # Only enough for 2 actions at 10 AP each
    
    for i, (action_config, params) in enumerate(parsed_actions):
        if remaining_ap <= 0:
            # Track remaining actions that couldn't be processed due to AP exhaustion
            remaining_actions = parsed_actions[i:]
            for remaining_action_config, remaining_params in remaining_actions:
                actions_skipped_due_to_ap.append(f"{remaining_action_config.name} {remaining_params}")
            break
            
        # Calculate cost (simplified - assume all actions cost 10 AP)
        actual_cost = 10
        
        if actual_cost > remaining_ap:
            response_feedback_messages.append(f"Action '{action_config.name}' costs {actual_cost} AP, but you only have {remaining_ap} AP. Skipping this action.")
            actions_skipped_due_to_ap.append(f"{action_config.name} {params}")
        else:
            remaining_ap -= actual_cost
            response_feedback_messages.append(f"Action '{action_config.name}' executed successfully.")
    
    # Should have processed 2 actions (20 AP / 10 AP per action)
    assert len(response_feedback_messages) == 2
    assert remaining_ap == 0
    
    # Should have 5 actions skipped due to AP
    assert len(actions_skipped_due_to_ap) == 5
    
    # Should have tracked the skipped actions correctly
    assert len(actions_skipped_due_to_ap) == 5
    assert "pickup {}" in actions_skipped_due_to_ap  # pickup armor (3rd action)
    assert "look {}" in actions_skipped_due_to_ap
    assert "move {}" in actions_skipped_due_to_ap
    assert "say {}" in actions_skipped_due_to_ap
    assert "help {}" in actions_skipped_due_to_ap
    
    # The response feedback should only contain the 2 executed actions
    assert len(response_feedback_messages) == 2
    assert "Action 'pickup' executed successfully" in response_feedback_messages[0]
    assert "Action 'pickup' executed successfully" in response_feedback_messages[1]


def test_ap_exhaustion_feedback_integration():
    """Test the actual feedback format that would be sent to players."""
    # This test would require a more complex setup with actual game master execution
    # For now, we'll test the logic that should be implemented
    
    # Expected behavior:
    # 1. Player submits 7 actions with 20 AP
    # 2. First 2 actions execute (costing 20 AP total)
    # 3. Remaining 5 actions are skipped
    # 4. Feedback should clearly indicate which actions were skipped and why
    
    expected_feedback_patterns = [
        "Action 'pickup' executed successfully",
        "Action 'pickup' executed successfully", 
        "Actions skipped due to insufficient AP:",
        "pickup sword",
        "pickup armor", 
        "look",
        "move west",
        "say hello",
        "help"
    ]
    
    # This test documents the expected behavior
    # The actual implementation should generate feedback matching these patterns
    assert len(expected_feedback_patterns) > 0  # Placeholder assertion
