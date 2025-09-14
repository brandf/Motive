"""
Critical path tests for motive/cli.py

These tests focus on the most important CLI functionality that could break user experience:
- Argument parsing and validation
- Config loading and validation
- Parallel game execution
- Error handling and edge cases
- Game progress monitoring
"""

import pytest
import tempfile
import os
import sys
import asyncio
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from datetime import datetime

from motive.cli import (
    ParallelGameRunner, GameProgress, GameStatus,
    setup_logging, load_config, run_game, main
)


class TestParallelGameRunner:
    """Test the ParallelGameRunner class - critical for parallel execution."""
    
    def test_init_with_valid_config(self):
        """Test ParallelGameRunner initialization with valid config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
  - name: Player_2
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            runner = ParallelGameRunner(2, config_path, rounds=3)
            assert runner.num_games == 2
            assert runner.config_path == config_path
            assert runner.game_args['rounds'] == 3
            assert len(runner.games) == 0  # Games not started yet
            assert len(runner.processes) == 0
            assert runner.running is True
        finally:
            os.unlink(config_path)
    
    def test_init_with_invalid_config(self):
        """Test ParallelGameRunner initialization with invalid config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with patch('motive.cli.load_config', side_effect=Exception("Config error")):
                runner = ParallelGameRunner(1, config_path)
                assert runner.num_games == 1
                assert runner.config_path == config_path
                assert runner._config_cache is None  # Should handle invalid config gracefully
        finally:
            os.unlink(config_path)
    
    @patch('motive.cli.subprocess.Popen')
    @patch('motive.cli.threading.Thread')
    def test_start_games_single_game(self, mock_thread, mock_popen):
        """Test starting a single game."""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            runner = ParallelGameRunner(1, config_path, game_id="test_game")
            runner.start_games()
            
            assert len(runner.games) == 1
            assert "test_game" in runner.games
            game = runner.games["test_game"]
            assert game.status == GameStatus.STARTING
            assert game.game_id == "test_game"
            assert game.start_time is not None
            
            # Verify subprocess was called correctly
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert "motive" in call_args[0][0]
            assert "--worker" in call_args[0][0]
            assert "--game-id" in call_args[0][0]
            assert "test_game" in call_args[0][0]
            
            # Verify monitoring thread was started
            mock_thread.assert_called_once()
        finally:
            os.unlink(config_path)
    
    @patch('motive.cli.subprocess.Popen')
    @patch('motive.cli.threading.Thread')
    def test_start_games_multiple_games(self, mock_thread, mock_popen):
        """Test starting multiple parallel games."""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            runner = ParallelGameRunner(3, config_path, rounds=2)
            runner.start_games()
            
            assert len(runner.games) == 3
            assert len(runner.processes) == 3
            assert len(runner.monitor_threads) == 3
            
            # Check that game IDs are unique
            game_ids = list(runner.games.keys())
            assert len(set(game_ids)) == 3  # All unique
            
            # Check that subprocess was called 3 times
            assert mock_popen.call_count == 3
            assert mock_thread.call_count == 3
        finally:
            os.unlink(config_path)
    
    def test_start_single_game_exception_handling(self):
        """Test exception handling in _start_single_game."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            runner = ParallelGameRunner(1, config_path)
            runner.games["test_game"] = GameProgress(
                game_id="test_game",
                status=GameStatus.STARTING
            )
            
            with patch('motive.cli.subprocess.Popen', side_effect=OSError("Permission denied")):
                runner._start_single_game("test_game")
                
                # Should handle exception gracefully
                assert runner.games["test_game"].status == GameStatus.FAILED
                assert "Permission denied" in runner.games["test_game"].error_message
        finally:
            os.unlink(config_path)
    
    def test_parse_game_output_worker_messages(self):
        """Test parsing of structured worker messages."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            runner = ParallelGameRunner(1, config_path)
            runner.games["test_game"] = GameProgress(
                game_id="test_game",
                status=GameStatus.STARTING
            )
            
            # Test various worker messages
            runner._parse_game_output("test_game", "WORKER_START:")
            assert runner.games["test_game"].status == GameStatus.RUNNING
            
            runner._parse_game_output("test_game", "WORKER_ROUNDS: 10")
            assert runner.games["test_game"].total_rounds == 10
            
            runner._parse_game_output("test_game", "WORKER_PLAYERS: 3")
            assert runner.games["test_game"].total_players == 3
            
            runner._parse_game_output("test_game", "WORKER_ROUND_START: 2")
            assert runner.games["test_game"].current_round == 2
            assert runner.games["test_game"].current_turn_in_round == 0
            
            runner._parse_game_output("test_game", "WORKER_PLAYER_TURN: Player_2")
            assert runner.games["test_game"].current_player == 2
            assert runner.games["test_game"].current_turn_in_round == 1
            
            runner._parse_game_output("test_game", "WORKER_TURN_COMPLETE:")
            assert runner.games["test_game"].completed_turns == 1
            
            runner._parse_game_output("test_game", "WORKER_ROUND_END:")
            assert runner.games["test_game"].current_turn_in_round == 0
            
            runner._parse_game_output("test_game", "WORKER_GAME_END:")
            assert runner.games["test_game"].status == GameStatus.COMPLETED
            assert runner.games["test_game"].current_round == 0
        finally:
            os.unlink(config_path)
    
    def test_parse_game_output_player_name_edge_cases(self):
        """Test parsing player names with edge cases."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            runner = ParallelGameRunner(1, config_path)
            runner.games["test_game"] = GameProgress(
                game_id="test_game",
                status=GameStatus.STARTING
            )
            
            # Test invalid player name format
            runner._parse_game_output("test_game", "WORKER_PLAYER_TURN: InvalidPlayer")
            assert runner.games["test_game"].current_player == 1  # Default fallback
            
            # Test empty player name
            runner._parse_game_output("test_game", "WORKER_PLAYER_TURN: ")
            assert runner.games["test_game"].current_player == 1  # Default fallback
        finally:
            os.unlink(config_path)


class TestConfigLoading:
    """Test config loading functionality."""
    
    def test_load_config_valid_file(self):
        """Test loading a valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 10
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
  - name: Player_2
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            config = load_config(config_path, validate=True)
            assert config.game_settings.num_rounds == 10
            assert config.game_settings.initial_ap_per_turn == 3
            assert len(config.players) == 2
            assert config.players[0].name == "Player_1"
        finally:
            os.unlink(config_path)
    
    def test_load_config_invalid_file(self):
        """Test loading an invalid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with patch('sys.exit') as mock_exit:
                load_config(config_path, validate=True)
                mock_exit.assert_called_once_with(1)
        finally:
            os.unlink(config_path)
    
    def test_load_config_nonexistent_file(self):
        """Test loading a nonexistent config file."""
        with patch('sys.exit') as mock_exit:
            load_config("nonexistent_config.yaml", validate=True)
            mock_exit.assert_called_once_with(1)


class TestArgumentParsing:
    """Test CLI argument parsing and validation."""
    
    def test_main_with_valid_args(self):
        """Test main function with valid arguments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            # Test with valid config file
            test_args = ['motive', '-c', config_path, '--rounds', '3']
            
            with patch('sys.argv', test_args):
                with patch('motive.cli.run_game') as mock_run_game:
                    with patch('motive.cli.asyncio.run') as mock_asyncio_run:
                        main()
                        
                        # Verify run_game was called with correct arguments
                        mock_asyncio_run.assert_called_once()
                        call_args = mock_asyncio_run.call_args[0][0]
                        # The call_args is the coroutine, we can't easily inspect it
                        # but we can verify the function was called
        finally:
            os.unlink(config_path)
    
    def test_main_with_nonexistent_config(self):
        """Test main function with nonexistent config file."""
        test_args = ['motive', '-c', 'nonexistent.yaml']
        
        with patch('sys.argv', test_args):
            with patch('sys.exit') as mock_exit:
                main()
                # Should call sys.exit(1) at least once for config file not found
                assert mock_exit.call_count >= 1
                # Check that at least one call was with exit code 1
                exit_calls = [call for call in mock_exit.call_args_list if call[0][0] == 1]
                assert len(exit_calls) >= 1
    
    def test_main_parallel_mode_invalid_count(self):
        """Test main function with invalid parallel count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 5
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            test_args = ['motive', '-c', config_path, '--parallel', '0']
            
            with patch('sys.argv', test_args):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_once_with(1)
        finally:
            os.unlink(config_path)


class TestGameProgress:
    """Test GameProgress dataclass functionality."""
    
    def test_game_progress_initialization(self):
        """Test GameProgress initialization."""
        progress = GameProgress(
            game_id="test_game",
            status=GameStatus.STARTING
        )
        
        assert progress.game_id == "test_game"
        assert progress.status == GameStatus.STARTING
        assert progress.current_round == 0
        assert progress.total_rounds == 0
        assert progress.current_player == 0
        assert progress.total_players == 0
        assert progress.start_time is None
        assert progress.end_time is None
        assert progress.error_message is None
        assert progress.log_file is None
        assert progress.last_output_time is None
        assert progress.completed_turns == 0
        assert progress.current_turn_in_round == 0
    
    def test_game_progress_with_all_fields(self):
        """Test GameProgress with all fields set."""
        start_time = datetime.now()
        end_time = datetime.now()
        
        progress = GameProgress(
            game_id="test_game",
            status=GameStatus.COMPLETED,
            current_round=5,
            total_rounds=10,
            current_player=2,
            total_players=3,
            start_time=start_time,
            end_time=end_time,
            error_message="Test error",
            log_file="test.log",
            last_output_time=start_time,
            completed_turns=15,
            current_turn_in_round=2
        )
        
        assert progress.game_id == "test_game"
        assert progress.status == GameStatus.COMPLETED
        assert progress.current_round == 5
        assert progress.total_rounds == 10
        assert progress.current_player == 2
        assert progress.total_players == 3
        assert progress.start_time == start_time
        assert progress.end_time == end_time
        assert progress.error_message == "Test error"
        assert progress.log_file == "test.log"
        assert progress.last_output_time == start_time
        assert progress.completed_turns == 15
        assert progress.current_turn_in_round == 2


class TestSetupLogging:
    """Test logging setup functionality."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        # This is a simple function that sets up logging
        # We just need to ensure it doesn't crash
        setup_logging()
        # If we get here without exception, the test passes


class TestRunGameFunction:
    """Test the run_game async function."""
    
    @pytest.mark.asyncio
    async def test_run_game_with_valid_config(self):
        """Test run_game with valid config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 2
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            with patch('motive.cli.GameMaster') as mock_gm_class:
                mock_gm = Mock()
                # Create async mock for run_game
                async def mock_run_game():
                    pass
                mock_gm.run_game = mock_run_game
                mock_gm_class.return_value = mock_gm
                
                await run_game(config_path, "test_game", validate=True, rounds=1)
                
                # Verify GameMaster was instantiated correctly
                mock_gm_class.assert_called_once()
                call_kwargs = mock_gm_class.call_args[1]
                assert call_kwargs['game_id'] == "test_game"
                assert call_kwargs['deterministic'] is False
        finally:
            os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_run_game_worker_mode(self):
        """Test run_game in worker mode."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 2
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            with patch('motive.cli.GameMaster') as mock_gm_class:
                mock_gm = Mock()
                # Create async mock for run_game_worker
                async def mock_run_game_worker():
                    pass
                mock_gm.run_game_worker = mock_run_game_worker
                mock_gm_class.return_value = mock_gm
                
                await run_game(config_path, "test_game", worker=True)
                
                # Verify GameMaster was instantiated correctly
                mock_gm_class.assert_called_once()
        finally:
            os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_run_game_keyboard_interrupt(self):
        """Test run_game handling KeyboardInterrupt."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 2
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            with patch('motive.cli.GameMaster') as mock_gm_class:
                mock_gm = Mock()
                # Create async mock that raises KeyboardInterrupt
                async def mock_run_game():
                    raise KeyboardInterrupt()
                mock_gm.run_game = mock_run_game
                mock_gm_class.return_value = mock_gm
                
                with patch('sys.exit') as mock_exit:
                    await run_game(config_path, "test_game")
                    mock_exit.assert_called_once_with(0)
        finally:
            os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_run_game_general_exception(self):
        """Test run_game handling general exceptions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 2
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            with patch('motive.cli.GameMaster') as mock_gm_class:
                mock_gm = Mock()
                # Create async mock that raises RuntimeError
                async def mock_run_game():
                    raise RuntimeError("Test error")
                mock_gm.run_game = mock_run_game
                mock_gm_class.return_value = mock_gm
                
                with patch('sys.exit') as mock_exit:
                    await run_game(config_path, "test_game")
                    mock_exit.assert_called_once_with(1)
        finally:
            os.unlink(config_path)
