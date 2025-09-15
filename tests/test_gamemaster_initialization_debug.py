#!/usr/bin/env python3
"""Debug test for GameMaster initialization with v2→v1 converted configs."""

import pytest
import tempfile
from unittest.mock import patch, Mock, MagicMock

from motive.cli import load_config

# Mock LLM factory at module level to avoid credential issues
@pytest.fixture(autouse=True)
def mock_llm_factory():
    with patch('motive.player.Player.__init__', return_value=None) as mock_player_init:
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
            
        mock_player_init.side_effect = mock_init
        yield mock_player_init


class TestGameMasterInitializationDebug:
    """Debug GameMaster initialization step by step."""

    @pytest.mark.skip(reason="LLM mocking issues - needs different approach")
    def test_gamemaster_initialization_step_by_step(self):
        """Test GameMaster initialization step by step to find the NoneType iteration issue."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                from motive.game_master import GameMaster
                
                # Test just the GameMaster constructor
                print("Testing GameMaster constructor...")
                gm = GameMaster(
                    game_config=game_config,
                    game_id="debug_test",
                    log_dir=temp_dir,
                    deterministic=True
                )
                
                print("GameMaster constructor succeeded!")
                print(f"Rooms: {len(gm.rooms) if gm.rooms else 'No rooms'}")
                print(f"Actions: {len(gm.game_actions) if gm.game_actions else 'No actions'}")
                
                # Clean up log handlers
                for handler in gm.game_logger.handlers[:]:
                    handler.close()
                    gm.game_logger.removeHandler(handler)
                    
            except Exception as e:
                print(f"GameMaster initialization failed: {e}")
                print(f"Exception type: {type(e)}")
                import traceback
                traceback.print_exc()
                pytest.fail(f"GameMaster initialization failed: {e}")

    @pytest.mark.skip(reason="LLM mocking issues - needs different approach")
    def test_game_initializer_separately(self):
        """Test GameInitializer separately to isolate the issue."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        try:
            from motive.game_initializer import GameInitializer
            import logging
            import tempfile
            
            print("Testing GameInitializer...")
            # Create a mock logger
            mock_logger = logging.getLogger("test")
            
            initializer = GameInitializer(game_config, "debug_test", mock_logger)
            
            print("GameInitializer constructor succeeded!")
            
            # Test initialization
            print("Testing game state initialization...")
            # Create Player instances from PlayerConfig objects (like GameMaster does)
            from motive.player import Player
            players = []
            with tempfile.TemporaryDirectory() as temp_dir:
                for p_config in game_config.players:
                    player = Player(
                        name=p_config.name,
                        provider=p_config.provider,
                        model=p_config.model,
                        log_dir=temp_dir,
                        no_file_logging=True
                    )
                    players.append(player)
                
                game_state = initializer.initialize_game_world(players)
                
                print("Game state initialization succeeded!")
                print(f"Rooms: {len(game_state.rooms)}")
                print(f"Actions: {len(game_state.actions)}")
                print(f"Object types: {len(game_state.object_types)}")
                print(f"Character types: {len(game_state.character_types)}")
            
        except Exception as e:
            print(f"GameInitializer failed: {e}")
            print(f"Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"GameInitializer failed: {e}")

    def test_config_validation(self):
        """Test that the converted config is valid for GameInitializer."""
        config_path = "configs/game.yaml"
        game_config = load_config(config_path)
        
        # Check all required fields
        assert game_config.game_settings is not None
        assert game_config.players is not None
        assert game_config.rooms is not None
        assert game_config.object_types is not None
        assert game_config.character_types is not None
        assert game_config.actions is not None
        
        # Check that collections are not empty where expected
        assert len(game_config.rooms) > 0, "No rooms in config"
        assert len(game_config.object_types) > 0, "No object types in config"
        assert len(game_config.character_types) > 0, "No character types in config"
        assert len(game_config.actions) > 0, "No actions in config"
        
        print("Config validation passed!")
        print(f"Rooms: {len(game_config.rooms)}")
        print(f"Object types: {len(game_config.object_types)}")
        print(f"Character types: {len(game_config.character_types)}")
        print(f"Actions: {len(game_config.actions)}")
        print(f"Players: {len(game_config.players)}")
