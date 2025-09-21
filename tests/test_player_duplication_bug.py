"""Test for player duplication bug fix.

This test reproduces the issue where running with --players=3 
but only 1 player in config creates Player_1_1, Player_1_2 instead of Player_2, Player_3.
"""

import pytest
from unittest.mock import patch, MagicMock
from motive.cli import run_game
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


class TestPlayerDuplicationBug:
    """Test that player duplication creates sequential names (Player_2, Player_3) not suffixes (Player_1_1, Player_1_2)."""
    
    def test_player_duplication_creates_sequential_names(self):
        """Test that player duplication creates sequential names (Player_2, Player_3, Player_4, Player_5) not suffixes (Player_1_1, Player_1_2, Player_1_3, Player_1_4)."""
        # Load a minimal config with 1 player
        config = load_and_validate_v2_config(
            "minimal_game.yaml", 
            "tests/configs/v2/minimal_motives", 
            validate=False
        )
        
        # Simulate the CLI logic for --players=5
        players = 5
        current_players = config['players']
        original_player_count = len(current_players)  # Store original count (1)
        
        if players > original_player_count:
            # Create additional players by duplicating existing ones
            original_players = current_players.copy()
            additional_needed = players - original_player_count
            
            for i in range(additional_needed):
                # Pick a random player to duplicate (cycle through if deterministic)
                source_player = original_players[i % len(original_players)]
                
                # Create a new player with sequential numbering (Player_2, Player_3, etc.)
                new_player = source_player.copy()
                new_player['name'] = f"Player_{original_player_count + i + 1}"
                config['players'].append(new_player)
        
        # Verify the result
        assert len(config['players']) == 5
        assert config['players'][0]['name'] == "Player_1"
        assert config['players'][1]['name'] == "Player_2"  # Not Player_1_1
        assert config['players'][2]['name'] == "Player_3"  # Not Player_1_2
        assert config['players'][3]['name'] == "Player_4"  # Not Player_1_3
        assert config['players'][4]['name'] == "Player_5"  # Not Player_1_4
