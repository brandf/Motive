#!/usr/bin/env python3
"""Integration tests for parallel logging structure."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from motive.game_master import GameMaster


class TestParallelLoggingIntegration:
    """Integration tests for parallel logging structure."""
    
    def _create_mock_config(self):
        """Create a properly configured mock config."""
        mock_config = MagicMock()
        mock_config.theme_id = "fantasy"
        mock_config.edition_id = "hearth_and_shadow"
        mock_config.game_settings = MagicMock()
        mock_config.game_settings.num_rounds = 1
        mock_config.game_settings.manual = "manual.md"
        mock_config.game_settings.initial_ap_per_turn = 10
        return mock_config
    
    def test_single_game_log_structure(self):
        """Test that single games use the original log structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = self._create_mock_config()
            
            # Test single game with CLI arguments instead of env vars
            gm = GameMaster(mock_config, "single_game_2024_01_15", log_dir=temp_dir, no_file_logging=False)
            log_dir = gm.log_dir
            
            # Should use original structure: logs/<theme>/<edition>/<game_id>/
            expected_path = Path(temp_dir) / "fantasy" / "hearth_and_shadow" / "single_game_2024_01_15"
            assert log_dir == str(expected_path)
            assert expected_path.exists()
    
    def test_parallel_worker_log_structure(self):
        """Test that parallel workers use the new grouped log structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = self._create_mock_config()
            
            # Test parallel worker game with CLI arguments
            gm = GameMaster(mock_config, "my_parallel_run_worker_1", log_dir=temp_dir, no_file_logging=False)
            log_dir = gm.log_dir
            
            # Should use new structure: logs/<theme>/<edition>/<parallel_run_id>/<worker_game_id>/
            expected_path = Path(temp_dir) / "fantasy" / "hearth_and_shadow" / "my_parallel_run" / "my_parallel_run_worker_1"
            assert log_dir == str(expected_path)
            assert expected_path.exists()
            
            # Verify the parallel run directory exists
            parallel_run_dir = expected_path.parent
            assert parallel_run_dir.exists()
            assert parallel_run_dir.name == "my_parallel_run"
    
    def test_multiple_parallel_workers_grouped(self):
        """Test that multiple parallel workers are grouped under the same parallel run directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = self._create_mock_config()
            
            # Create multiple workers with CLI arguments
            workers = [
                "experiment_123_worker_1",
                "experiment_123_worker_2", 
                "experiment_123_worker_3"
            ]
            
            worker_dirs = []
            for worker_id in workers:
                gm = GameMaster(mock_config, worker_id, log_dir=temp_dir, no_file_logging=False)
                log_dir = gm.log_dir
                worker_dirs.append(log_dir)
            
            # All workers should be under the same parallel run directory
            parallel_run_dir = Path(temp_dir) / "fantasy" / "hearth_and_shadow" / "experiment_123"
            assert parallel_run_dir.exists()
            
            # Each worker should have its own subdirectory
            for i, worker_dir in enumerate(worker_dirs):
                expected_worker_dir = parallel_run_dir / workers[i]
                assert worker_dir == str(expected_worker_dir)
                assert expected_worker_dir.exists()
    
    def test_edge_case_worker_in_name(self):
        """Test edge case where game_id contains 'worker' but not '_worker_' pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = self._create_mock_config()
            
            # Test game_id with 'worker' but not the parallel pattern
            gm = GameMaster(mock_config, "game_with_worker_in_name", log_dir=temp_dir, no_file_logging=False)
            log_dir = gm.log_dir
            
            # Should use original structure since it doesn't match "_worker_" pattern
            expected_path = Path(temp_dir) / "fantasy" / "hearth_and_shadow" / "game_with_worker_in_name"
            assert log_dir == str(expected_path)
            assert expected_path.exists()
    
    def test_backward_compatibility_preserved(self):
        """Test that existing single game log structure is completely preserved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config = self._create_mock_config()
            
            # Test various single game ID formats with CLI arguments
            single_game_ids = [
                "game_2024_01_15",
                "experiment_abc123",
                "test_run",
                "parallel_efda735a",  # This looks like a parallel run ID but isn't a worker
            ]
            
            for game_id in single_game_ids:
                gm = GameMaster(mock_config, game_id, log_dir=temp_dir, no_file_logging=False)
                log_dir = gm.log_dir
                
                # Should use original structure: logs/<theme>/<edition>/<game_id>/
                expected_path = Path(temp_dir) / "fantasy" / "hearth_and_shadow" / game_id
                assert log_dir == str(expected_path)
                assert expected_path.exists()
                
                # Clean up for next iteration
                shutil.rmtree(expected_path)
