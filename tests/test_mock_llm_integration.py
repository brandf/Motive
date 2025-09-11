"""Mock LLM integration tests with canned responses."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from motive.game_master import GameMaster
from motive.config import GameConfig, GameSettings, PlayerConfig, CharacterConfig
from motive.character import Character
from motive.room import Room
from motive.game_object import GameObject
from motive.player import Player


@pytest.mark.llm_integration
class TestMockLLMIntegration:
    """Test full game flow with mocked LLM responses."""

    def setup_method(self):
        """Set up test environment with mock LLM."""
        # Create game config
        self.game_config = GameConfig(
            game_settings=GameSettings(
                num_rounds=2,
                initial_ap_per_turn=50,
                manual="docs/MANUAL.md"
            ),
            players=[
                PlayerConfig(
                    name="TestPlayer1",
                    provider="openai",
                    model="gpt-4"
                ),
                PlayerConfig(
                    name="TestPlayer2", 
                    provider="openai",
                    model="gpt-4"
                )
            ]
        )
        
        # Create test rooms
        self.town_square = Room(
            room_id="town_square",
            name="Town Square",
            description="A bustling town square with a fountain in the center.",
            exits={"north": {"id": "north_exit", "name": "North", "destination_room_id": "church"}}
        )
        
        self.church = Room(
            room_id="church",
            name="Sacred Heart Church",
            description="A peaceful church with stained glass windows.",
            exits={"south": {"id": "south_exit", "name": "South", "destination_room_id": "town_square"}}
        )
        
        # Create test objects
        self.torch = GameObject(
            obj_id="torch_1",
            name="Torch",
            description="A wooden torch",
            current_location_id="town_square",
            properties={"readable": False}
        )
        
        self.holy_water = GameObject(
            obj_id="holy_water_1", 
            name="Holy Water",
            description="A vial of blessed holy water",
            current_location_id="church",
            properties={"readable": False}
        )
        
        # Add objects to rooms
        self.town_square.objects = {"torch_1": self.torch}
        self.church.objects = {"holy_water_1": self.holy_water}

    def create_mock_llm_client(self, responses):
        """Create a mock LLM client that returns canned responses."""
        mock_client = AsyncMock()
        
        # Create a response queue
        response_queue = responses.copy()
        
        async def mock_invoke(messages):
            """Mock invoke that returns the next canned response."""
            if response_queue:
                response_content = response_queue.pop(0)
                return Mock(content=response_content)
            else:
                return Mock(content="No more responses available")
        
        mock_client.ainvoke = mock_invoke
        return mock_client

    def test_deterministic_character_assignment(self):
        """Test that deterministic mode produces consistent character assignments."""
        from motive.config import MotiveConfig
        
        # Create a simple test with multiple characters and motives
        motives1 = [
            MotiveConfig(id="motive1", description="Save the village"),
            MotiveConfig(id="motive2", description="Find the treasure")
        ]
        motives2 = [
            MotiveConfig(id="motive3", description="Defeat the dragon"),
            MotiveConfig(id="motive4", description="Protect the innocent")
        ]
        
        # Test deterministic character creation
        char1_det = Character(
            char_id="char1",
            name="Arion",
            backstory="A brave hero",
            motives=motives1,
            deterministic=True
        )
        
        char2_det = Character(
            char_id="char2",
            name="Luna", 
            backstory="A wise mage",
            motives=motives2,
            deterministic=True
        )
        
        # Test non-deterministic character creation
        char1_rand = Character(
            char_id="char1",
            name="Arion",
            backstory="A brave hero",
            motives=motives1,
            deterministic=False
        )
        
        char2_rand = Character(
            char_id="char2",
            name="Luna",
            backstory="A wise mage", 
            motives=motives2,
            deterministic=False
        )
        
        # In deterministic mode, should always pick first motive
        assert char1_det.selected_motive.id == "motive1"
        assert char2_det.selected_motive.id == "motive3"
        
        # In non-deterministic mode, could pick any motive (we can't predict which)
        assert char1_rand.selected_motive.id in ["motive1", "motive2"]
        assert char2_rand.selected_motive.id in ["motive3", "motive4"]
        
        # Test that deterministic mode is consistent across multiple runs
        char1_det2 = Character(
            char_id="char1",
            name="Arion",
            backstory="A brave hero",
            motives=motives1,
            deterministic=True
        )
        
        assert char1_det.selected_motive.id == char1_det2.selected_motive.id

    def test_character_assignment_error_handling(self):
        """Test that character assignment errors when there are more players than characters."""
        from motive.game_initializer import GameInitializer
        import logging
        
        # Create a mock logger
        logger = logging.getLogger("test")
        
        # Create game config with only 1 character but 2 players
        game_config = GameConfig(
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
        
        # Create game initializer
        initializer = GameInitializer(game_config, "test_game", logger, deterministic=True)
        
        # Mock the character types (only 1 character available)
        initializer.game_character_types = {
            "char1": CharacterConfig(
                id="char1",
                name="Arion",
                backstory="A brave hero",
                motive="Test motive"
            )
        }
        
        # Mock the rooms
        initializer.game_rooms = {
            "room1": Room(room_id="room1", name="Test Room", description="A test room", exits={})
        }
        
        # Create mock players (avoiding real Player creation)
        mock_player1 = Mock()
        mock_player1.name = "Player1"
        mock_player1.id = "player1"
        mock_player1.character = None  # Ensure no character initially
        
        mock_player2 = Mock()
        mock_player2.name = "Player2"
        mock_player2.id = "player2"
        mock_player2.character = None  # Ensure no character initially
        
        players = [mock_player1, mock_player2]
        
        # This should log an error message about not enough characters and return early
        initializer._instantiate_player_characters(players)
        
        # Verify that no characters were assigned due to the error
        assigned_characters = 0
        for player in players:
            if hasattr(player, 'character') and player.character is not None:
                assigned_characters += 1
        
        # Should assign 0 characters since the function should return early on error
        assert assigned_characters == 0
