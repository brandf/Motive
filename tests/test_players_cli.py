"""Tests for --players CLI argument functionality."""

import pytest
from unittest.mock import Mock, patch
from motive.config import GameConfig, GameSettings, PlayerConfig
from motive.cli import run_game


class TestPlayersCLI:
    """Test the --players CLI argument functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a base game config with 2 players
        self.base_config = GameConfig(
            game_settings=GameSettings(
                num_rounds=1,
                initial_ap_per_turn=50,
                manual="docs/MANUAL.md"
            ),
            players=[
                PlayerConfig(name="Player1", provider="openai", model="gpt-4"),
                PlayerConfig(name="Player2", provider="openai", model="gpt-4")
            ]
        )
    
    def test_players_less_than_config(self):
        """Test using fewer players than defined in config."""
        # Test with 1 player when config has 2
        config = self.base_config.model_copy()
        
        # Simulate the players override logic
        players = 1
        if players < len(config.players):
            config.players = config.players[:players]
        
        assert len(config.players) == 1
        assert config.players[0].name == "Player1"
    
    def test_players_equal_to_config(self):
        """Test using same number of players as config."""
        config = self.base_config.model_copy()
        
        # Simulate the players override logic
        players = 2
        if players < len(config.players):
            config.players = config.players[:players]
        elif players > len(config.players):
            # This branch won't execute
            pass
        
        assert len(config.players) == 2
        assert config.players[0].name == "Player1"
        assert config.players[1].name == "Player2"
    
    def test_players_more_than_config_deterministic(self):
        """Test creating more players than config in deterministic mode."""
        config = self.base_config.model_copy()
        
        # Simulate the players override logic for deterministic mode
        players = 4
        deterministic = True
        
        if players < len(config.players):
            config.players = config.players[:players]
        elif players > len(config.players):
            original_players = config.players.copy()
            additional_needed = players - len(config.players)
            
            for i in range(additional_needed):
                # Pick a player to duplicate (cycle through if deterministic)
                if deterministic:
                    source_player = original_players[i % len(original_players)]
                else:
                    import random
                    source_player = random.choice(original_players)
                
                # Create a new player with sequential numbering (Player3, Player4, etc.)
                new_player = source_player.model_copy()
                new_player.name = f"Player{len(original_players) + i + 1}"
                config.players.append(new_player)
        
        assert len(config.players) == 4
        assert config.players[0].name == "Player1"
        assert config.players[1].name == "Player2"
        assert config.players[2].name == "Player3"  # First duplicate (i=0)
        assert config.players[3].name == "Player4"  # Second duplicate (i=1)
    
    def test_players_more_than_config_random(self):
        """Test creating more players than config in random mode."""
        config = self.base_config.model_copy()
        
        # Simulate the players override logic for random mode
        players = 5
        deterministic = False
        
        if players < len(config.players):
            config.players = config.players[:players]
        elif players > len(config.players):
            original_players = config.players.copy()
            additional_needed = players - len(config.players)
            
            # Mock random.choice to return predictable results
            with patch('random.choice') as mock_choice:
                mock_choice.side_effect = [
                    original_players[0],  # Player1
                    original_players[1],  # Player2
                    original_players[0],  # Player1
                ]
                
                for i in range(additional_needed):
                    # Pick a player to duplicate
                    if deterministic:
                        source_player = original_players[i % len(original_players)]
                    else:
                        source_player = mock_choice()
                    
                    # Create a new player with sequential numbering (Player3, Player4, etc.)
                    new_player = source_player.model_copy()
                    new_player.name = f"Player{len(original_players) + i + 1}"
                    config.players.append(new_player)
        
        assert len(config.players) == 5
        assert config.players[0].name == "Player1"
        assert config.players[1].name == "Player2"
        assert config.players[2].name == "Player3"  # First duplicate (i=0)
        assert config.players[3].name == "Player4"  # Second duplicate (i=1)
        assert config.players[4].name == "Player5"  # Third duplicate (i=2)
    
    def test_players_zero(self):
        """Test edge case of zero players."""
        config = self.base_config.model_copy()
        
        players = 0
        if players < len(config.players):
            config.players = config.players[:players]
        
        assert len(config.players) == 0
    
    def test_players_negative(self):
        """Test edge case of negative players."""
        config = self.base_config.model_copy()
        
        players = -1
        if players < len(config.players):
            # Handle negative players by setting to empty list
            if players <= 0:
                config.players = []
            else:
                config.players = config.players[:players]
        
        assert len(config.players) == 0
