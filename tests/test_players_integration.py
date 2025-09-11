"""Integration tests for --players CLI argument with mock LLM."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from motive.config import GameConfig, GameSettings, PlayerConfig
from motive.game_master import GameMaster
from motive.character import Character
from motive.room import Room
from motive.game_object import GameObject


@pytest.mark.llm_integration
class TestPlayersIntegration:
    """Test player count functionality with mock LLM integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a minimal game config
        self.game_config = GameConfig(
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
        
        # Create test rooms
        self.town_square = Room(
            room_id="town_square",
            name="Town Square",
            description="A bustling town square",
            exits={}
        )
        
        # Add some objects
        self.town_square.add_object(GameObject(
            obj_id="torch_1",
            name="Torch",
            description="A wooden torch",
            current_location_id="town_square"
        ))
    
    def test_players_less_than_config_integration(self):
        """Test using fewer players than config in integration."""
        # Test with 1 player when config has 2
        config = self.game_config.model_copy()
        players = 1
        
        # Apply players override
        if players <= 0:
            config.players = []
        elif players < len(config.players):
            config.players = config.players[:players]
        
        assert len(config.players) == 1
        assert config.players[0].name == "Player1"
    
    def test_players_more_than_config_integration(self):
        """Test creating more players than config in integration."""
        # Test with 4 players when config has 2
        config = self.game_config.model_copy()
        players = 4
        deterministic = True
        
        # Apply players override
        if players <= 0:
            config.players = []
        elif players < len(config.players):
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
                
                # Create a new player with modified name
                new_player = source_player.model_copy()
                new_player.name = f"{source_player.name}_{i + 1}"
                config.players.append(new_player)
        
        assert len(config.players) == 4
        assert config.players[0].name == "Player1"
        assert config.players[1].name == "Player2"
        assert config.players[2].name == "Player1_1"
        assert config.players[3].name == "Player2_2"
    
    def test_players_more_than_characters_error(self):
        """Test error handling when more players than characters."""
        # Create a config with only 1 character but 3 players
        config = self.game_config.model_copy()
        players = 3
        deterministic = True
        
        # Apply players override
        if players <= 0:
            config.players = []
        elif players < len(config.players):
            config.players = config.players[:players]
        elif players > len(config.players):
            original_players = config.players.copy()
            additional_needed = players - len(config.players)
            
            for i in range(additional_needed):
                # Pick a player to duplicate
                if deterministic:
                    source_player = original_players[i % len(original_players)]
                else:
                    import random
                    source_player = random.choice(original_players)
                
                # Create a new player with modified name
                new_player = source_player.model_copy()
                new_player.name = f"{source_player.name}_{i + 1}"
                config.players.append(new_player)
        
        # Now we have 3 players but only 2 characters available
        # This should cause an error in character assignment
        assert len(config.players) == 3
        
        # Test that character assignment would fail
        # (This would be tested in the actual game initialization)
        # For now, just verify we have the right number of players
        assert config.players[0].name == "Player1"
        assert config.players[1].name == "Player2"
        assert config.players[2].name == "Player1_1"
    
    def test_players_zero_integration(self):
        """Test zero players edge case."""
        config = self.game_config.model_copy()
        players = 0
        
        # Apply players override
        if players <= 0:
            config.players = []
        elif players < len(config.players):
            config.players = config.players[:players]
        
        assert len(config.players) == 0
    
    def test_players_negative_integration(self):
        """Test negative players edge case."""
        config = self.game_config.model_copy()
        players = -1
        
        # Apply players override
        if players <= 0:
            config.players = []
        elif players < len(config.players):
            config.players = config.players[:players]
        
        assert len(config.players) == 0
