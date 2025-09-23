"""Test that example actions are filtered by AP cost and show costs."""

import pytest
from unittest.mock import Mock
from motive.game_master import GameMaster
from motive.character import Character
from motive.config import ActionConfig, ParameterConfig


def test_example_actions_filtered_by_ap_cost():
    """Test that example actions are filtered by current AP."""
    # Create mock game master
    game_master = Mock(spec=GameMaster)
    game_master.game_actions = {}
    
    # Create test player with low AP
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player.action_points = 5  # Low AP
    
    # Create mock actions with different costs
    mock_actions = {
        "look": ActionConfig(
            id="look",
            name="look",
            cost=10,
            description="Look around",
            category="observation",
            parameters=[],
            requirements=[],
            effects=[]
        ),
        "move": ActionConfig(
            id="move", 
            name="move",
            cost=10,
            description="Move to another room",
            category="movement",
            parameters=[ParameterConfig(name="direction", type="string", description="Direction to move")],
            requirements=[],
            effects=[]
        ),
        "expose": ActionConfig(
            id="expose",
            name="expose", 
            cost=20,
            description="Expose someone",
            category="investigation",
            parameters=[ParameterConfig(name="target", type="string", description="Target to expose")],
            requirements=[],
            effects=[]
        ),
        "arrest": ActionConfig(
            id="arrest",
            name="arrest",
            cost=25,
            description="Arrest someone",
            category="investigation", 
            parameters=[ParameterConfig(name="target", type="string", description="Target to arrest")],
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
        )
    }
    
    game_master.game_actions = mock_actions
    
    # Mock the ranking method
    game_master._rank_actions_for_examples = lambda actions, player_char=None: actions
    
    # Test that expensive actions are filtered out
    example_actions = GameMaster._get_example_actions(game_master, player)
    
    # Should not include expensive actions that exceed AP
    assert "expose" not in example_actions  # 20 AP > 5 AP
    assert "arrest" not in example_actions  # 25 AP > 5 AP
    
    # Should include affordable actions
    assert "help" in example_actions  # 1 AP <= 5 AP
    # Note: look and move cost 10 AP which is > 5 AP, so they should also be filtered


def test_example_actions_show_ap_costs():
    """Test that example actions display shows AP costs."""
    # Create real game master instance
    from motive.config import GameConfig, GameSettings, PlayerConfig
    
    game_settings = GameSettings(
        num_rounds=5,
        manual="test_manual.md",
        initial_ap_per_turn=20
    )
    
    players = [
        PlayerConfig(
            name="Player_1",
            provider="dummy",
            model="test"
        )
    ]
    
    game_config = GameConfig(
        game_settings=game_settings,
        players=players
    )
    
    game_master = GameMaster(game_config, "test_game")
    
    # Create test player
    player = Character(
        char_id="test_player",
        name="TestPlayer", 
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player.action_points = 20  # Sufficient AP
    
    # Create mock actions
    mock_actions = {
        "look": ActionConfig(
            id="look",
            name="look",
            cost=10,
            description="Look around",
            category="observation",
            parameters=[],
            requirements=[],
            effects=[]
        ),
        "move": ActionConfig(
            id="move",
            name="move",
            cost=10,
            description="Move to another room",
            category="movement",
            parameters=[ParameterConfig(name="direction", type="string", description="Direction to move")],
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
        )
    }
    
    game_master.game_actions = mock_actions
    
    # Mock the ranking method
    game_master._rank_actions_for_examples = lambda actions, player_char=None: ["look", "move", "help"]
    
    # Test the action display formatting using the actual method
    action_display = game_master._get_action_display(player)
    
    # Should show AP costs in the display
    assert "> look (10 AP)" in action_display
    assert "> move (10 AP)" in action_display  
    assert "> help (1 AP)" in action_display


def test_example_actions_affordable_only():
    """Test that only affordable actions are shown when AP is very low."""
    # Create mock game master
    game_master = Mock(spec=GameMaster)
    game_master.game_actions = {}
    
    # Create test player with very low AP
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character", 
        motive="Test motive",
        current_room_id="test_room"
    )
    player.action_points = 1  # Very low AP
    
    # Create mock actions
    mock_actions = {
        "look": ActionConfig(
            id="look",
            name="look",
            cost=10,
            description="Look around",
            category="observation",
            parameters=[],
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
    
    # Mock the ranking method
    game_master._rank_actions_for_examples = lambda actions, player_char=None: actions
    
    # Test that only affordable actions are shown
    example_actions = GameMaster._get_example_actions(game_master, player)
    
    # Should only include actions that cost <= 1 AP
    assert "help" in example_actions  # 1 AP
    assert "pass" in example_actions  # 0 AP
    assert "look" not in example_actions  # 10 AP > 1 AP


def test_example_actions_no_affordable_actions():
    """Test behavior when no actions are affordable."""
    # Create mock game master
    game_master = Mock(spec=GameMaster)
    game_master.game_actions = {}
    
    # Create test player with no AP
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive", 
        current_room_id="test_room"
    )
    player.action_points = 0  # No AP
    
    # Create mock actions (all expensive except help)
    mock_actions = {
        "look": ActionConfig(
            id="look",
            name="look",
            cost=10,
            description="Look around",
            category="observation",
            parameters=[],
            requirements=[],
            effects=[]
        ),
        "move": ActionConfig(
            id="move",
            name="move",
            cost=10,
            description="Move to another room",
            category="movement",
            parameters=[ParameterConfig(name="direction", type="string", description="Direction to move")],
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
        )
    }
    
    game_master.game_actions = mock_actions
    
    # Mock the ranking method
    game_master._rank_actions_for_examples = lambda actions, player_char=None: actions
    
    # Test that we still show some actions (fallback behavior)
    example_actions = GameMaster._get_example_actions(game_master, player)
    
    # Should still show some actions even if not affordable (fallback)
    assert len(example_actions) > 0
    # But they should be marked as unaffordable in the display
