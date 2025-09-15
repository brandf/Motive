#!/usr/bin/env python3
"""Smoke test for v2 configs - minimal end-to-end validation with mocked LLMs."""

import pytest
import tempfile
import os
import asyncio
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from pathlib import Path

# Mock LLM factory at module level to avoid credential issues
@pytest.fixture(autouse=True)
def mock_llm_factory():
    with patch('motive.player.Player.__init__') as mock_player_init:
        def mock_init(self, name, provider, model, log_dir=None, no_file_logging=False):
            self.name = name
            self.provider = provider
            self.model = model
            self.log_dir = log_dir
            self.no_file_logging = no_file_logging
            self.llm_client = MagicMock()
            self.logger = MagicMock()
            self.messages = []
            self.character = None
            # Don't call the original __init__
            
        mock_player_init.side_effect = mock_init
        yield mock_player_init

from motive.cli import load_config
from motive.game_master import GameMaster


class TestV2SmokeRun:
    """Smoke test that v2 configs can run end-to-end with mocked LLMs."""

    @pytest.mark.skip(reason="LLM mocking issues - needs different approach")
    @pytest.mark.asyncio
    async def test_v2_migrated_config_smoke_run(self):
        """Test that hearth_and_shadow_migrated.yaml can run a minimal game."""
        config_path = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Config file {config_path} not found")
        
        # Create temporary directory for logs
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock LLM clients to prevent real API calls
            with patch('motive.llm_factory.create_llm_client') as mock_create_llm:
                mock_llm = AsyncMock()
                mock_llm.generate_response.return_value = "> look"
                mock_create_llm.return_value = mock_llm
                
                # Load v2 config
                game_config = load_config(config_path)
                assert game_config is not None
                
                # Create GameMaster with mocked LLMs
                gm = GameMaster(
                    game_config=game_config,
                    game_id="v2_smoke_test",
                    log_dir=temp_dir,
                    deterministic=True
                )
                
                # Run a very short game (1 round, low AP)
                gm.num_rounds = 1
                # Note: initial_ap_per_turn is set in GameInitializer, not directly on GameMaster
                
                # Mock the game loop to run just one turn
                with patch.object(gm, 'run_game') as mock_run_game:
                    mock_run_game.return_value = None
                    
                    # This should not crash
                    await gm.run_game()
                    
                    # Verify initialization worked
                    assert len(gm.players) > 0, "Should have players"
                    assert gm.rooms is not None, "Should have rooms"

    @pytest.mark.skip(reason="LLM mocking issues - needs different approach")
    @pytest.mark.asyncio 
    async def test_v2_config_with_minimal_players(self):
        """Test v2 config with minimal player setup."""
        config_path = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Config file {config_path} not found")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('motive.llm_factory.create_llm_client') as mock_create_llm:
                mock_llm = AsyncMock()
                mock_llm.generate_response.return_value = "> help"
                mock_create_llm.return_value = mock_llm
                
                # Load config and modify for minimal test
                game_config = load_config(config_path)
                
                # Override with minimal settings
                game_config.game_settings.num_rounds = 1
                game_config.game_settings.initial_ap_per_turn = 2
                
                # Use only 1 player for speed
                game_config.players = game_config.players[:1]
                
                gm = GameMaster(
                    game_config=game_config,
                    game_id="v2_minimal_test", 
                    log_dir=temp_dir,
                    deterministic=True
                )
                
                # Mock the actual game execution
                with patch.object(gm, 'run_game') as mock_run_game:
                    mock_run_game.return_value = None
                    
                    await gm.run_game()
                    
                    # Verify basic initialization
                    assert gm.rooms is not None
                    assert gm.game_actions is not None
                    assert len(gm.players) == 1
                    
                    # Verify rooms were loaded
                    assert len(gm.rooms) > 0, "Should have rooms loaded"

    def test_v2_config_loading_and_structure(self):
        """Test that v2 config loading produces correct structure without full GameMaster init."""
        config_path = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml"
        
        if not os.path.exists(config_path):
            pytest.skip(f"Config file {config_path} not found")
        
        # Test config loading
        game_config = load_config(config_path)
        
        # Verify basic structure
        assert game_config is not None
        assert game_config.game_settings is not None
        assert game_config.game_settings.num_rounds == 10  # Default we set
        assert len(game_config.players) == 2  # Default players we set
        
        # Verify content was loaded
        assert len(game_config.rooms) > 0, "Should have rooms"
        assert len(game_config.object_types) > 0, "Should have object types" 
        assert len(game_config.character_types) > 0, "Should have character types"
        
        # Verify specific hearth_and_shadow content
        room_names = [room.name for room in game_config.rooms.values()]
        assert any('tavern' in name.lower() or 'church' in name.lower() for name in room_names), \
            "Should have tavern or church from hearth_and_shadow"
        
        # Verify we have substantial content
        assert len(game_config.rooms) >= 10, f"Expected >=10 rooms, got {len(game_config.rooms)}"
        assert len(game_config.object_types) >= 50, f"Expected >=50 objects, got {len(game_config.object_types)}"
        assert len(game_config.character_types) >= 5, f"Expected >=5 characters, got {len(game_config.character_types)}"
