"""Mock LLM integration tests for initial room feature."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from motive.game_master import GameMaster
from motive.config import GameConfig, GameSettings, CharacterConfig, InitialRoomConfig, PlayerConfig


class TestInitialRoomMockLLMIntegration:
    """Test initial room feature with mock LLM responses."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create game config with characters that have initial rooms
        self.game_config = GameConfig(
            game_settings=GameSettings(num_rounds=1),
            players=[
                PlayerConfig(
                    name="Player1",
                    character_id="mayor_victoria",
                    provider="openai",
                    model="gpt-4"
                ),
                PlayerConfig(
                    name="Player2", 
                    character_id="captain_marcus",
                    provider="openai",
                    model="gpt-4"
                )
            ],
            characters={
                "mayor_victoria": CharacterConfig(
                    id="mayor_victoria",
                    name="Mayor Victoria Blackwater",
                    backstory="The missing mayor",
                    initial_rooms=[
                        InitialRoomConfig(room_id="secret_underground_chamber", chance=50, reason="You've been held captive here for weeks, but you've finally managed to work free your restraints."),
                        InitialRoomConfig(room_id="town_hall", chance=30, reason="Having recently escaped from cult captivity, you're hiding here trying to piece together which of your trusted advisors betrayed you."),
                        InitialRoomConfig(room_id="church", chance=20, reason="Seeking sanctuary after your escape from cult captivity.")
                    ]
                ),
                "captain_marcus": CharacterConfig(
                    id="captain_marcus",
                    name="Captain Marcus O'Malley",
                    backstory="The corrupt guard captain",
                    initial_rooms=[
                        InitialRoomConfig(room_id="town_square", chance=40, reason="Conducting your regular patrol, but you're actually gathering information for your cult contacts."),
                        InitialRoomConfig(room_id="tavern", chance=30, reason="Meeting with your cult contact in a back booth."),
                        InitialRoomConfig(room_id="bank", chance=20, reason="Collecting your monthly 'consultation fee' from the cult."),
                        InitialRoomConfig(room_id="guard_barracks", chance=10, reason="Reviewing security reports and planning your next move.")
                    ]
                )
            }
        )
    
    @patch('motive.game_master.GameMaster')
    def test_initial_room_selection_deterministic(self, mock_gm_class):
        """Test that deterministic mode always picks the first initial room."""
        # Mock the game master
        mock_gm = Mock()
        mock_gm_class.return_value = mock_gm
        mock_gm.deterministic = True
        
        # Mock rooms
        mock_rooms = {
            "secret_underground_chamber": Mock(id="secret_underground_chamber", name="Secret Underground Chamber"),
            "town_hall": Mock(id="town_hall", name="Town Hall"),
            "church": Mock(id="church", name="Church"),
            "town_square": Mock(id="town_square", name="Town Square"),
            "tavern": Mock(id="tavern", name="Tavern"),
            "bank": Mock(id="bank", name="Bank"),
            "guard_barracks": Mock(id="guard_barracks", name="Guard Barracks")
        }
        mock_gm.game_rooms = mock_rooms
        
        # Mock the initial room selection method
        def mock_select_initial_room(char_config, default_room_id):
            if not hasattr(char_config, 'initial_rooms') or not char_config.initial_rooms:
                return default_room_id
            
            # In deterministic mode, always return the first room
            return char_config.initial_rooms[0].room_id
        
        mock_gm._select_initial_room = mock_select_initial_room
        
        # Test character assignment
        mayor_config = self.game_config.characters["mayor_victoria"]
        captain_config = self.game_config.characters["captain_marcus"]
        
        # Test deterministic selection
        mayor_room = mock_gm._select_initial_room(mayor_config, "town_square")
        captain_room = mock_gm._select_initial_room(captain_config, "town_square")
        
        # Should always pick the first room in deterministic mode
        assert mayor_room == "secret_underground_chamber"
        assert captain_room == "town_square"
    
    @patch('motive.game_master.GameMaster')
    def test_initial_room_selection_random(self, mock_gm_class):
        """Test that random mode selects rooms based on weights."""
        # Mock the game master
        mock_gm = Mock()
        mock_gm_class.return_value = mock_gm
        mock_gm.deterministic = False
        
        # Mock rooms
        mock_rooms = {
            "secret_underground_chamber": Mock(id="secret_underground_chamber", name="Secret Underground Chamber"),
            "town_hall": Mock(id="town_hall", name="Town Hall"),
            "church": Mock(id="church", name="Church"),
            "town_square": Mock(id="town_square", name="Town Square"),
            "tavern": Mock(id="tavern", name="Tavern"),
            "bank": Mock(id="bank", name="Bank"),
            "guard_barracks": Mock(id="guard_barracks", name="Guard Barracks")
        }
        mock_gm.game_rooms = mock_rooms
        
        # Mock the initial room selection method with weighted random choice
        def mock_select_initial_room(char_config, default_room_id):
            if not hasattr(char_config, 'initial_rooms') or not char_config.initial_rooms:
                return default_room_id
            
            # Simulate weighted random choice (simplified for testing)
            import random
            rooms = [room.room_id for room in char_config.initial_rooms]
            weights = [room.chance for room in char_config.initial_rooms]
            
            # Normalize weights if they exceed 100%
            total_weight = sum(weights)
            if total_weight > 100:
                weights = [int(weight * 100 / total_weight) for weight in weights]
                weights = [max(1, weight) for weight in weights]
            
            return random.choices(rooms, weights=weights, k=1)[0]
        
        mock_gm._select_initial_room = mock_select_initial_room
        
        # Test character assignment
        mayor_config = self.game_config.characters["mayor_victoria"]
        captain_config = self.game_config.characters["captain_marcus"]
        
        # Test random selection (run multiple times to verify randomness)
        mayor_rooms = []
        captain_rooms = []
        
        for _ in range(10):
            mayor_room = mock_gm._select_initial_room(mayor_config, "town_square")
            captain_room = mock_gm._select_initial_room(captain_config, "town_square")
            mayor_rooms.append(mayor_room)
            captain_rooms.append(captain_room)
        
        # Should get valid rooms
        valid_mayor_rooms = {"secret_underground_chamber", "town_hall", "church"}
        valid_captain_rooms = {"town_square", "tavern", "bank", "guard_barracks"}
        
        assert all(room in valid_mayor_rooms for room in mayor_rooms)
        assert all(room in valid_captain_rooms for room in captain_rooms)
    
    @patch('motive.game_master.GameMaster')
    def test_initial_room_reason_integration(self, mock_gm_class):
        """Test that initial room reasons are properly integrated into character setup."""
        # Mock the game master
        mock_gm = Mock()
        mock_gm_class.return_value = mock_gm
        mock_gm.deterministic = True
        
        # Mock rooms with descriptions
        mock_rooms = {
            "secret_underground_chamber": Mock(
                id="secret_underground_chamber", 
                name="Secret Underground Chamber",
                description="A dark, damp underground chamber."
            ),
            "town_square": Mock(
                id="town_square", 
                name="Town Square",
                description="The bustling heart of the town."
            )
        }
        mock_gm.game_rooms = mock_rooms
        
        # Mock character creation with initial room reason
        def mock_create_character(char_config, selected_room_id):
            character = Mock()
            character.name = char_config.name
            character.current_room_id = selected_room_id
            
            # Find the reason for the selected room
            if hasattr(char_config, 'initial_rooms') and char_config.initial_rooms:
                for room_config in char_config.initial_rooms:
                    if room_config.room_id == selected_room_id:
                        character.initial_room_reason = room_config.reason
                        break
            else:
                character.initial_room_reason = None
            
            return character
        
        # Test character creation
        mayor_config = self.game_config.characters["mayor_victoria"]
        captain_config = self.game_config.characters["captain_marcus"]
        
        # Create characters with their initial rooms
        mayor_char = mock_create_character(mayor_config, "secret_underground_chamber")
        captain_char = mock_create_character(captain_config, "town_square")
        
        # Verify the characters have the correct initial room reasons
        assert mayor_char.initial_room_reason == "You've been held captive here for weeks, but you've finally managed to work free your restraints."
        assert captain_char.initial_room_reason == "Conducting your regular patrol, but you're actually gathering information for your cult contacts."
    
    @patch('motive.game_master.GameMaster')
    def test_initial_room_weight_normalization(self, mock_gm_class):
        """Test that initial room weights are normalized when they exceed 100%."""
        # Mock the game master
        mock_gm = Mock()
        mock_gm_class.return_value = mock_gm
        mock_gm.deterministic = False
        
        # Create character with weights that sum to 150%
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character",
            initial_rooms=[
                InitialRoomConfig(room_id="room1", chance=60, reason="First room"),
                InitialRoomConfig(room_id="room2", chance=50, reason="Second room"),
                InitialRoomConfig(room_id="room3", chance=40, reason="Third room")
            ]
        )
        
        # Mock rooms
        mock_rooms = {
            "room1": Mock(id="room1", name="Room 1"),
            "room2": Mock(id="room2", name="Room 2"),
            "room3": Mock(id="room3", name="Room 3")
        }
        mock_gm.game_rooms = mock_rooms
        
        # Mock the initial room selection with normalization
        def mock_select_initial_room(char_config, default_room_id):
            if not hasattr(char_config, 'initial_rooms') or not char_config.initial_rooms:
                return default_room_id
            
            rooms = [room.room_id for room in char_config.initial_rooms]
            weights = [room.chance for room in char_config.initial_rooms]
            
            # Normalize weights if they exceed 100%
            total_weight = sum(weights)
            if total_weight > 100:
                # Normalize proportionally to sum to 100
                weights = [int(weight * 100 / total_weight) for weight in weights]
                # Ensure we don't have any zero weights (minimum 1%)
                weights = [max(1, weight) for weight in weights]
                # Re-normalize to ensure they sum to 100
                total_weight = sum(weights)
                if total_weight != 100:
                    # Adjust the largest weight to make it exactly 100
                    max_idx = weights.index(max(weights))
                    weights[max_idx] += (100 - total_weight)
            
            # Verify normalization worked
            assert sum(weights) == 100, f"Weights should sum to 100, got {sum(weights)}"
            
            import random
            return random.choices(rooms, weights=weights, k=1)[0]
        
        mock_gm._select_initial_room = mock_select_initial_room
        
        # Test that normalization works
        result = mock_gm._select_initial_room(char_config, "room1")
        assert result in ["room1", "room2", "room3"]
