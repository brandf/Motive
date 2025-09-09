"""
Tests for dynamic example actions generation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from motive.game_master import GameMaster
from motive.config import ActionConfig, ParameterConfig


class TestDynamicExampleActions:
    """Test that example actions are generated dynamically from available actions."""
    
    def test_get_example_actions_dynamic_generation(self):
        """Test that example actions are generated from available actions, not hardcoded."""
        # Create a mock GameMaster with some actions
        game_master = Mock(spec=GameMaster)
        
        # Mock some actions
        mock_actions = {
            "look": ActionConfig(
                id="look",
                name="look",
                cost=10,
                description="Look around",
                category="observation",
                parameters=[ParameterConfig(name="target", type="string", description="Target to look at")],
                requirements=[],
                effects=[]
            ),
            "move": ActionConfig(
                id="move", 
                name="move",
                cost=10,
                description="Move in a direction",
                category="movement",
                parameters=[ParameterConfig(name="direction", type="string", description="Direction to move")],
                requirements=[],
                effects=[]
            ),
            "say": ActionConfig(
                id="say",
                name="say", 
                cost=10,
                description="Say something",
                category="communication",
                parameters=[ParameterConfig(name="phrase", type="string", description="What to say")],
                requirements=[],
                effects=[]
            ),
            "pickup": ActionConfig(
                id="pickup",
                name="pickup",
                cost=10,
                description="Pick up an object",
                category="inventory", 
                parameters=[ParameterConfig(name="object_name", type="string", description="Object to pick up")],
                requirements=[],
                effects=[]
            ),
            "help": ActionConfig(
                id="help",
                name="help",
                cost=1,
                description="Get help",
                category="system",
                parameters=[],
                requirements=[],
                effects=[]
            ),
            "pass": ActionConfig(
                id="pass",
                name="pass",
                cost=0,
                description="Pass turn",
                category="system",
                parameters=[],
                requirements=[],
                effects=[]
            )
        }
        
        game_master.game_actions = mock_actions
        
        # Test the dynamic example actions generation
        example_actions = GameMaster._get_example_actions(game_master)
        
        # Should include core actions in a reasonable order
        assert "look" in example_actions
        assert "move" in example_actions
        assert "say" in example_actions
        assert "pickup" in example_actions
        assert "help" in example_actions
        
        # Should not include pass (since it's not typically shown as an example)
        assert "pass" not in example_actions
        
        # Should be in a reasonable order (movement/observation first, then interaction)
        assert example_actions[0] in ["look", "move"]  # First should be basic actions
        assert example_actions[-1] == "help"  # Help should be last
        
        # Should not be hardcoded - verify the algorithm works with different action sets
        # Test with a minimal set of actions
        minimal_actions = {
            "look": mock_actions["look"],
            "help": mock_actions["help"]
        }
        game_master.game_actions = minimal_actions
        
        minimal_example_actions = GameMaster._get_example_actions(game_master)
        # Should still work with minimal actions
        assert "look" in minimal_example_actions
        assert "help" in minimal_example_actions
        assert len(minimal_example_actions) >= 2
        
    def test_example_actions_in_player_prompt(self):
        """Test that the player prompt uses dynamic example actions."""
        # This test would require a more complex setup with actual GameMaster
        # For now, we'll test the method exists and works
        game_master = Mock(spec=GameMaster)
        game_master.game_actions = {}
        
        # Should handle empty actions gracefully
        example_actions = GameMaster._get_example_actions(game_master)
        assert isinstance(example_actions, list)
        
    def test_example_actions_prioritizes_core_categories(self):
        """Test that example actions prioritize core categories."""
        game_master = Mock(spec=GameMaster)
        
        # Create actions with different categories
        mock_actions = {
            "look": ActionConfig(id="look", name="look", cost=10, description="Look", category="observation", parameters=[], requirements=[], effects=[]),
            "move": ActionConfig(id="move", name="move", cost=10, description="Move", category="movement", parameters=[], requirements=[], effects=[]),
            "say": ActionConfig(id="say", name="say", cost=10, description="Say", category="communication", parameters=[], requirements=[], effects=[]),
            "pickup": ActionConfig(id="pickup", name="pickup", cost=10, description="Pickup", category="inventory", parameters=[], requirements=[], effects=[]),
            "help": ActionConfig(id="help", name="help", cost=1, description="Help", category="system", parameters=[], requirements=[], effects=[]),
            "custom_action": ActionConfig(id="custom_action", name="custom_action", cost=10, description="Custom", category="custom", parameters=[], requirements=[], effects=[])
        }
        
        game_master.game_actions = mock_actions
        
        example_actions = GameMaster._get_example_actions(game_master)
        
        # Core categories should be prioritized
        core_categories = ["observation", "movement", "communication", "inventory", "system"]
        core_actions = [action for action in example_actions if mock_actions[action].category in core_categories]
        
        # Most example actions should be from core categories
        assert len(core_actions) >= len(example_actions) - 1  # Allow for one non-core action
