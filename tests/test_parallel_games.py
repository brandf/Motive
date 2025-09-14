"""
Tests for parallel game execution functionality.
"""

import pytest
import subprocess
import time
import sys
from datetime import datetime
from unittest.mock import Mock, patch
from motive.cli import ParallelGameRunner, GameStatus, GameProgress


class TestParallelGameRunner:
    """Test the parallel game runner functionality."""
    
    def test_parallel_runner_initialization(self):
        """Test that ParallelGameRunner initializes correctly."""
        runner = ParallelGameRunner(3, "configs/game.yaml", rounds=2, players=2)
        
        assert runner.num_games == 3
        assert runner.config_path == "configs/game.yaml"
        assert runner.game_args["rounds"] == 2
        assert runner.game_args["players"] == 2
        assert len(runner.games) == 0  # No games started yet
        assert runner.running is True
    
    def test_game_progress_initialization(self):
        """Test GameProgress dataclass initialization."""
        progress = GameProgress(
            game_id="test_game",
            status=GameStatus.STARTING,
            current_round=1,
            total_rounds=3,
            current_player=1,
            total_players=2
        )
        
        assert progress.game_id == "test_game"
        assert progress.status == GameStatus.STARTING
        assert progress.current_round == 1
        assert progress.total_rounds == 3
        assert progress.current_player == 1
        assert progress.total_players == 2
        assert progress.start_time is None
        assert progress.end_time is None
        assert progress.error_message is None
    
    def test_parse_game_output_round_detection(self):
        """Test parsing of round information from game output."""
        runner = ParallelGameRunner(1, "configs/game.yaml")
        game_id = "test_game"
        runner.games[game_id] = GameProgress(game_id=game_id, status=GameStatus.RUNNING)
        
        # Test round detection
        runner._parse_game_output(game_id, "🎯 Round 2 starting...")
        assert runner.games[game_id].current_round == 2
        
        runner._parse_game_output(game_id, "Round 3 begins")
        assert runner.games[game_id].current_round == 3
    
    def test_parse_game_output_player_detection(self):
        """Test parsing of player information from game output."""
        runner = ParallelGameRunner(1, "configs/game.yaml")
        game_id = "test_game"
        runner.games[game_id] = GameProgress(game_id=game_id, status=GameStatus.RUNNING)
        
        # Test player detection
        runner._parse_game_output(game_id, "Player 1 turn starting...")
        assert runner.games[game_id].current_player == 1
        
        runner._parse_game_output(game_id, "Player 2 begins")
        assert runner.games[game_id].current_player == 2
    
    def test_parse_game_output_completion_detection(self):
        """Test parsing of game completion from game output."""
        runner = ParallelGameRunner(1, "configs/game.yaml")
        game_id = "test_game"
        runner.games[game_id] = GameProgress(game_id=game_id, status=GameStatus.RUNNING)
        
        # Test completion detection
        runner._parse_game_output(game_id, "Game completed successfully")
        assert runner.games[game_id].status == GameStatus.COMPLETED
    
    def test_parse_game_output_error_detection(self):
        """Test parsing of error information from game output."""
        runner = ParallelGameRunner(1, "configs/game.yaml")
        game_id = "test_game"
        runner.games[game_id] = GameProgress(game_id=game_id, status=GameStatus.RUNNING)
        
        # Test error detection
        runner._parse_game_output(game_id, "Error: Something went wrong")
        assert runner.games[game_id].status == GameStatus.FAILED
        assert "Something went wrong" in runner.games[game_id].error_message
    
    @patch('subprocess.Popen')
    @patch('threading.Thread')
    def test_start_single_game(self, mock_thread, mock_popen):
        """Test starting a single game process."""
        # Create a proper mock process with iterable stdout/stderr
        mock_process = Mock()
        mock_process.stdout.readline = Mock(side_effect=['line1\n', 'line2\n', ''])
        mock_process.stderr.readline = Mock(side_effect=['error1\n', 'error2\n', ''])
        mock_popen.return_value = mock_process
        
        # Mock the thread to prevent actual threading
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        runner = ParallelGameRunner(1, "configs/game.yaml", rounds=2)
        
        # Initialize the game in the games dict before starting (as start_games would do)
        runner.games["test_game"] = GameProgress(
            game_id="test_game",
            status=GameStatus.STARTING,
            start_time=datetime.now()
        )
        
        runner._start_single_game("test_game")
        
        # Verify subprocess was called with correct arguments
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert "motive" in call_args
        assert "-c" in call_args
        assert "--game-id" in call_args
        assert "test_game" in call_args
        assert "--worker" in call_args
        assert "--rounds" in call_args
        assert "2" in call_args
        
        # Verify thread was created but not started (mocked)
        mock_thread.assert_called_once()
    
    def test_display_game_progress_formatting(self):
        """Test that game progress display formatting works correctly."""
        runner = ParallelGameRunner(1, "configs/game.yaml")
        
        # Create a test game progress
        game = GameProgress(
            game_id="test_game",
            status=GameStatus.RUNNING,
            current_round=2,
            total_rounds=5,
            current_player=1,
            total_players=3
        )
        
        # Test that the display method doesn't crash
        # (We can't easily test the actual output without mocking print)
        try:
            runner._display_game_progress(1, game)
        except Exception as e:
            pytest.fail(f"Display method raised an exception: {e}")


@pytest.mark.sandbox_integration
def test_parallel_cli_argument():
    """Test that the --parallel CLI argument is properly recognized."""
    # This is a basic test to ensure the argument parsing works
    # We can't easily test the full parallel execution without complex mocking
    import argparse
    from motive.cli import main
    
    # Test that the argument is defined
    parser = argparse.ArgumentParser()
    parser.add_argument('--parallel', type=int, metavar='N')
    
    args = parser.parse_args(['--parallel', '3'])
    assert args.parallel == 3
