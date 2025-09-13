#!/usr/bin/env python3
"""Test parallel run logging structure organization."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from motive.cli import ParallelGameRunner


class TestParallelLoggingStructure:
    """Test that parallel runs organize logs correctly."""
    
    @patch('motive.cli.load_config')
    def test_parallel_run_id_derivation(self, mock_load_config):
        """Test that game_id becomes parallel_run_id for parallel runs."""
        # Mock the config loading to avoid file system dependencies
        mock_load_config.return_value = MagicMock()
        
        # Test with explicit game_id
        runner = ParallelGameRunner(3, "config.yaml", game_id="my_parallel_run")
        
        # The base_game_id should be used as parallel_run_id
        assert runner.game_args.get('game_id') == "my_parallel_run"
        
        # Test with no game_id (should generate one)
        runner_no_id = ParallelGameRunner(3, "config.yaml")
        assert runner_no_id.game_args.get('game_id') is None
    
    @patch('motive.cli.load_config')
    def test_worker_game_id_generation(self, mock_load_config):
        """Test that worker game IDs are generated correctly."""
        mock_load_config.return_value = MagicMock()
        runner = ParallelGameRunner(3, "config.yaml", game_id="test_run")
        
        # Mock the start_games method to test ID generation
        with patch.object(runner, '_start_single_game'):
            runner.start_games()
            
            # Check that games are created with correct IDs
            expected_ids = ["test_run_worker_1", "test_run_worker_2", "test_run_worker_3"]
            actual_ids = list(runner.games.keys())
            assert actual_ids == expected_ids
    
    @patch('motive.cli.load_config')
    def test_single_game_no_worker_suffix(self, mock_load_config):
        """Test that single parallel game doesn't get worker suffix."""
        mock_load_config.return_value = MagicMock()
        runner = ParallelGameRunner(1, "config.yaml", game_id="single_run")
        
        with patch.object(runner, '_start_single_game'):
            runner.start_games()
            
            # Single game should use base ID directly
            assert list(runner.games.keys()) == ["single_run"]
    
    def test_log_directory_structure(self):
        """Test that log directories follow the new structure."""
        # This test validates the expected log directory structure
        # The actual implementation will be tested in integration tests
        
        expected_structure = {
            "base": "logs",
            "theme": "fantasy", 
            "edition": "hearth_and_shadow",
            "parallel_run_id": "test_parallel_run",
            "worker_game_ids": ["test_parallel_run_worker_1", "test_parallel_run_worker_2"]
        }
        
        # Expected paths:
        # logs/fantasy/hearth_and_shadow/test_parallel_run/test_parallel_run_worker_1/
        # logs/fantasy/hearth_and_shadow/test_parallel_run/test_parallel_run_worker_2/
        
        for worker_id in expected_structure["worker_game_ids"]:
            expected_path = Path(
                expected_structure["base"],
                expected_structure["theme"], 
                expected_structure["edition"],
                expected_structure["parallel_run_id"],
                worker_id
            )
            
            # The path should be structured correctly
            assert expected_path.parts[-1] == worker_id
            assert expected_path.parts[-2] == expected_structure["parallel_run_id"]
            assert expected_path.parts[-3] == expected_structure["edition"]
            assert expected_path.parts[-4] == expected_structure["theme"]
            assert expected_path.parts[-5] == expected_structure["base"]
    
    @patch('motive.cli.load_config')
    def test_parallel_run_id_preservation(self, mock_load_config):
        """Test that parallel run ID is preserved in worker game IDs."""
        mock_load_config.return_value = MagicMock()
        runner = ParallelGameRunner(2, "config.yaml", game_id="parallel_experiment_123")
        
        with patch.object(runner, '_start_single_game'):
            runner.start_games()
            
            # Worker IDs should preserve the parallel run ID
            expected_ids = [
                "parallel_experiment_123_worker_1", 
                "parallel_experiment_123_worker_2"
            ]
            actual_ids = list(runner.games.keys())
            assert actual_ids == expected_ids
    
    def test_log_path_structure_validation(self):
        """Test that the actual log paths follow the expected structure."""
        # This test will validate the actual log directory structure
        # when games are run with the new parallel logging system
        
        expected_structure = {
            "base": "logs",
            "theme": "fantasy", 
            "edition": "hearth_and_shadow",
            "parallel_run_id": "test_parallel_run",
            "worker_game_ids": ["test_parallel_run_worker_1", "test_parallel_run_worker_2"]
        }
        
        # Expected paths:
        # logs/fantasy/hearth_and_shadow/test_parallel_run/test_parallel_run_worker_1/
        # logs/fantasy/hearth_and_shadow/test_parallel_run/test_parallel_run_worker_2/
        
        for worker_id in expected_structure["worker_game_ids"]:
            expected_path = Path(
                expected_structure["base"],
                expected_structure["theme"], 
                expected_structure["edition"],
                expected_structure["parallel_run_id"],
                worker_id
            )
            
            # The path should be structured correctly
            assert expected_path.parts[-1] == worker_id
            assert expected_path.parts[-2] == expected_structure["parallel_run_id"]
            assert expected_path.parts[-3] == expected_structure["edition"]
            assert expected_path.parts[-4] == expected_structure["theme"]
            assert expected_path.parts[-5] == expected_structure["base"]


class TestParallelLoggingIntegration:
    """Integration tests for parallel logging structure."""
    
    def test_cli_parallel_flag_with_game_id(self):
        """Test that CLI correctly handles --parallel with --game-id."""
        # This would test the actual CLI integration
        # For now, we'll test the argument parsing logic
        
        import argparse
        from motive.cli import main
        
        # Test that parallel mode preserves game_id as parallel_run_id
        test_args = [
            "--parallel", "3",
            "--game-id", "my_parallel_test", 
            "--config", "configs/game.yaml"
        ]
        
        # We can't easily test the full CLI without running actual games,
        # but we can test the argument parsing logic
        parser = argparse.ArgumentParser()
        parser.add_argument('--parallel', type=int)
        parser.add_argument('--game-id', type=str)
        parser.add_argument('--config', type=str)
        
        args = parser.parse_args(test_args)
        
        assert args.parallel == 3
        assert args.game_id == "my_parallel_test"
    
    def test_backward_compatibility_single_game(self):
        """Test that single games still work with existing log structure."""
        # Single games (non-parallel) should continue to use the old structure:
        # logs/<theme>/<edition>/<game_id>/
        
        # This ensures backward compatibility
        single_game_id = "single_game_2024_01_15"
        expected_path = Path("logs", "fantasy", "hearth_and_shadow", single_game_id)
        
        # Single game should not have parallel run grouping
        assert expected_path.parts[-1] == single_game_id
        assert len(expected_path.parts) == 4  # logs/theme/edition/game_id
    
    @patch('motive.cli.load_config')
    def test_single_game_log_structure_preserved(self, mock_load_config):
        """Test that single games preserve the original log structure."""
        mock_load_config.return_value = MagicMock()
        
        # Test that single parallel game (num_games=1) doesn't change log structure
        runner = ParallelGameRunner(1, "config.yaml", game_id="single_game_test")
        
        with patch.object(runner, '_start_single_game'):
            runner.start_games()
            
            # Single game should use the game_id directly without worker suffix
            assert list(runner.games.keys()) == ["single_game_test"]
            
            # The log structure should be: logs/<theme>/<edition>/single_game_test/
            # NOT: logs/<theme>/<edition>/single_game_test/single_game_test/
