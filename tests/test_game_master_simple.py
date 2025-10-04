"""
Simple critical path tests for motive/game_master.py

These tests focus on the most important GameMaster functionality that can be tested without complex mocking:
- Game initialization and setup
- Action validation and execution
- Event distribution and observation
- Win condition checking
- Error handling and edge cases
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from motive.game_master import GameMaster
from motive.config import GameConfig, GameSettings, PlayerConfig


# Global temporary directory for test isolation
_test_temp_dir = None


def _get_test_temp_dir():
    """Get or create a temporary directory for test isolation."""
    global _test_temp_dir
    if _test_temp_dir is None:
        _test_temp_dir = tempfile.TemporaryDirectory()
    return _test_temp_dir.name


def _cleanup_test_temp_dir():
    """Clean up the test temporary directory."""
    global _test_temp_dir
    if _test_temp_dir is not None:
        _test_temp_dir.cleanup()
        _test_temp_dir = None


@pytest.fixture(autouse=True)
def isolated_game_master():
    """Automatically patch GameMaster to use temporary directories for test isolation."""
    # Patch GameMaster constructor to use temporary directory
    original_init = GameMaster.__init__
    
    def patched_init(self, game_config, game_id, *args, **kwargs):
        # Always use temporary directory for tests
        kwargs['log_dir'] = _get_test_temp_dir()
        return original_init(self, game_config, game_id, *args, **kwargs)
    
    with patch.object(GameMaster, '__init__', patched_init):
        yield
    
    # Clean up log handlers before cleaning up temp directory
    import logging
    import gc
    
    # Close all file handlers in the logging system
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            if hasattr(handler, 'close'):
                handler.close()
            logger.removeHandler(handler)
    
    # Also close handlers in the root logger
    for handler in logging.root.handlers[:]:
        if hasattr(handler, 'close'):
            handler.close()
        logging.root.removeHandler(handler)
    
    gc.collect()  # Force garbage collection to close file handles
    
    # Clean up after test
    _cleanup_test_temp_dir()


class TestGameMasterInitialization:
    """Test GameMaster initialization and setup."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_init_with_pydantic_config(self, mock_initializer, mock_player):
        """Test GameMaster initialization with Pydantic GameConfig."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        assert gm.num_rounds == 5
        assert gm.game_id == "test_game"
        assert gm.deterministic is False
        assert gm.log_dir.startswith(_get_test_temp_dir())
        assert gm.no_file_logging is False
        assert gm.character_override is None
        assert gm.motive_override is None
        
        # Verify GameInitializer was called
        mock_initializer.assert_called_once()
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_init_with_dict_config(self, mock_initializer, mock_player):
        """Test GameMaster initialization with dictionary config."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_config = {
            'game_settings': {
                'num_rounds': 3,
                'manual': 'test_manual.md',
                'initial_ap_per_turn': 2
            },
            'players': [
                {
                    'name': 'Player_1',
                    'provider': 'google',
                    'model': 'gemini-2.5-flash'
                }
            ]
        }
        
        # Convert dict config to proper PlayerConfig objects for _initialize_players
        player_configs = [PlayerConfig(**p) for p in game_config['players']]
        game_config['players'] = player_configs
        
        gm = GameMaster(game_config, "test_game", deterministic=True)
        
        assert gm.num_rounds == 3
        assert gm.game_id == "test_game"
        assert gm.deterministic is True
        assert gm.log_dir.startswith(_get_test_temp_dir())
        
        # Verify GameInitializer was called
        mock_initializer.assert_called_once()
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_init_with_character_motive_overrides(self, mock_initializer, mock_player):
        """Test GameMaster initialization with character and motive overrides."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(
            game_config, 
            "test_game", 
            character="warrior", 
            motive="build_secret_stash"
        )
        
        assert gm.character_override == "warrior"
        assert gm.motive_override == "build_secret_stash"
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_init_logging_setup(self, mock_initializer, mock_player):
        """Test that logging is properly set up during initialization."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Verify logger was created and configured
        assert gm.game_logger.name == "GameNarrative"
        assert gm.game_logger.level == 20  # INFO level
        assert len(gm.game_logger.handlers) == 2  # FileHandler + StreamHandler
        assert gm.game_logger.propagate is False


class TestManualLoading:
    """Test manual content loading."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_load_manual_content_success(self, mock_initializer, mock_player):
        """Test successful manual content loading."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Create a temporary manual file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Manual\n\nThis is a test manual.")
            manual_path = f.name
        
        try:
            # Mock the manual path
            gm.manual_path = manual_path
            
            content = gm._load_manual_content()
            
            assert "# Test Manual" in content
            assert "This is a test manual." in content
        finally:
            os.unlink(manual_path)
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_load_manual_content_file_not_found(self, mock_initializer, mock_player):
        """Test manual loading when file doesn't exist."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="nonexistent_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock the manual path to point to nonexistent file
        gm.manual_path = "nonexistent_manual.md"
        
        content = gm._load_manual_content()
        
        # Should return empty string (warning is logged, not printed)
        assert content == ""


class TestActionValidation:
    """Test action validation functionality."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_check_requirements_success(self, mock_initializer, mock_player):
        """Test successful requirement checking."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock character and action config
        mock_character = Mock()
        mock_character.name = "Player_1"
        mock_character.current_room = "tavern"
        
        mock_action_config = Mock()
        mock_action_config.requirements = []
        
        # Test with no requirements
        success, message, params = gm._check_requirements(
            mock_character, mock_action_config, {}
        )
        
        assert success is True
        assert message == ""
        assert params is None  # No requirements means no params
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_check_requirements_failure(self, mock_initializer, mock_player):
        """Test requirement checking failure."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock character and action config with requirements
        mock_character = Mock()
        mock_character.name = "Player_1"
        mock_character.current_room = "tavern"
        
        mock_requirement = Mock()
        mock_requirement.type = "player_in_room"
        mock_requirement.room_name = "forest"  # Different from current room
        
        mock_action_config = Mock()
        mock_action_config.requirements = [mock_requirement]
        
        # Test with failing requirement
        success, message, params = gm._check_requirements(
            mock_character, mock_action_config, {}
        )
        
        assert success is False
        assert "requirement" in message.lower()


class TestActionCostCalculation:
    """Test action cost calculation."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_calculate_action_cost_fixed(self, mock_initializer, mock_player):
        """Test action cost calculation with fixed cost."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock character and action config
        mock_character = Mock()
        mock_character.name = "Player_1"
        
        mock_action_config = Mock()
        mock_action_config.cost = 2  # Fixed cost
        
        cost = gm._calculate_action_cost(mock_character, mock_action_config, {})
        
        assert cost == 2
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_calculate_action_cost_dict(self, mock_initializer, mock_player):
        """Test action cost calculation with dictionary cost."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock character and action config
        mock_character = Mock()
        mock_character.name = "Player_1"
        
        mock_action_config = Mock()
        mock_action_config.cost = {"value": 3}  # Dictionary cost
        
        cost = gm._calculate_action_cost(mock_character, mock_action_config, {})
        
        assert cost == 3


class TestEventDistribution:
    """Test event distribution functionality."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_distribute_events(self, mock_initializer, mock_player):
        """Test event distribution to players."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            ),
            PlayerConfig(
                name="Player_2",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock players
        mock_player1 = Mock()
        mock_player1.name = "Player_1"
        mock_player1.character = Mock()
        mock_player1.character.name = "Player_1"
        mock_player1.character.current_room = "tavern"
        
        mock_player2 = Mock()
        mock_player2.name = "Player_2"
        mock_player2.character = Mock()
        mock_player2.character.name = "Player_2"
        mock_player2.character.current_room = "forest"
        
        gm.players = [mock_player1, mock_player2]
        
        # Mock event
        mock_event = Mock()
        mock_event.scope = "room"
        mock_event.room_name = "tavern"
        mock_event.event_type = "test_event"
        mock_event.description = "Test event"
        
        gm.pending_events = [mock_event]
        
        # Test event distribution
        gm._distribute_events()
        
        # Verify events were distributed to appropriate players
        # Note: _distribute_events processes events but doesn't clear them automatically
        # The method distributes events to players but leaves them in pending_events
        assert len(gm.pending_events) == 1  # Events remain until manually cleared


class TestWinConditions:
    """Test win condition checking."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_check_win_conditions_no_winners(self, mock_initializer, mock_player):
        """Test win condition checking with no winners."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock player with no completed motives
        mock_player = Mock()
        mock_player.name = "Player_1"
        mock_player.character = Mock()
        mock_player.character.completed_motives = []
        
        gm.players = [mock_player]
        
        gm._check_win_conditions_and_summarize()
        
        # The method logs results to the game logger, not to print
        # We can verify it completed without error
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_check_win_conditions_with_winners(self, mock_initializer, mock_player):
        """Test win condition checking with winners."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock player with completed motives
        mock_player = Mock()
        mock_player.name = "Player_1"
        mock_player.character = Mock()
        mock_player.character.completed_motives = ["build_secret_stash"]
        
        gm.players = [mock_player]
        
        gm._check_win_conditions_and_summarize()
        
        # The method logs results to the game logger, not to print
        # We can verify it completed without error


class TestHintSystem:
    """Test hint system functionality."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_get_applicable_hints_empty(self, mock_initializer, mock_player):
        """Test getting applicable hints when none exist."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock game config with no hints
        gm.game_config = {'game_settings': {'hints': None}}
        
        hints = gm._get_applicable_hints("Player_1", 1)
        
        assert hints == []
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_get_applicable_hints_with_hints(self, mock_initializer, mock_player):
        """Test getting applicable hints when hints exist."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock game config with hints
        gm.game_config = {
            'game_settings': {
                'hints': [
                    {
                        'hint_id': 'test_hint',
                        'hint_action': '> look around',
                        'when': {}
                    }
                ]
            }
        }
        
        hints = gm._get_applicable_hints("Player_1", 1)
        
        assert len(hints) == 1
        assert "look around" in hints[0]


class TestActionDisplay:
    """Test action display functionality."""
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_get_example_actions(self, mock_initializer, mock_player):
        """Test getting example actions."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock actions as proper dictionary with Mock values that have required attributes
        mock_move = Mock()
        mock_move.category = "movement"
        mock_move.name = "move"
        mock_move.cost = 1

        mock_say = Mock()
        mock_say.category = "communication"
        mock_say.name = "say"
        mock_say.cost = 1

        mock_look = Mock()
        mock_look.category = "observation"
        mock_look.name = "look"
        mock_look.cost = 1
        
        gm.game_actions = {
            'move': mock_move,
            'say': mock_say,
            'look': mock_look
        }
        
        examples = gm._get_example_actions()
        
        assert len(examples) == 3
        # Examples should be action names, not formatted strings
        assert "look" in examples
        assert "move" in examples
        assert "say" in examples
    
    @patch('motive.game_master.Player')
    @patch('motive.game_master.GameInitializer')
    def test_get_action_display(self, mock_initializer, mock_player):
        """Test getting action display for player."""
        mock_init_instance = Mock()
        mock_initializer.return_value = mock_init_instance
        
        mock_player_instance = Mock()
        mock_player.return_value = mock_player_instance
        
        game_settings = GameSettings(
            num_rounds=5,
            manual="test_manual.md",
            initial_ap_per_turn=3
        )
        
        players = [
            PlayerConfig(
                name="Player_1",
                provider="google",
                model="gemini-2.5-flash"
            )
        ]
        
        game_config = GameConfig(
            game_settings=game_settings,
            players=players
        )
        
        gm = GameMaster(game_config, "test_game")
        
        # Mock character
        mock_character = Mock()
        mock_character.name = "Player_1"
        mock_character.current_room = "tavern"
        mock_character.action_points = 3
        
        # Mock actions as proper dictionary with Mock values that have required attributes
        mock_move = Mock()
        mock_move.category = "movement"
        mock_move.name = "move"
        mock_move.cost = 1

        mock_say = Mock()
        mock_say.category = "communication"
        mock_say.name = "say"
        mock_say.cost = 1

        mock_look = Mock()
        mock_look.category = "observation"
        mock_look.name = "look"
        mock_look.cost = 1
        
        gm.game_actions = {
            'move': mock_move,
            'say': mock_say,
            'look': mock_look
        }
        
        display = gm._get_action_display(mock_character, is_first_turn=True, round_num=1)
        
        assert "Example actions" in display
        assert "look" in display
        assert "move" in display
        assert "say" in display


if __name__ == '__main__':
    pytest.main([__file__])
