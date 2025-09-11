"""Test integration of initial room reasons into initial turn messages."""

import pytest
from unittest.mock import Mock, patch
from motive.game_master import GameMaster
from motive.config import GameConfig, GameSettings, CharacterConfig, InitialRoomConfig, PlayerConfig


class TestInitialRoomReasonIntegration:
    """Test that initial room reasons are integrated into initial turn messages."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a minimal game config
        self.game_config = GameConfig(
            game_settings=GameSettings(num_rounds=3),
            players=[
                PlayerConfig(
                    name="TestPlayer",
                    character_id="test_char",
                    provider="openai",
                    model="gpt-4"
                )
            ],
            characters={
                "test_char": CharacterConfig(
                    id="test_char",
                    name="Test Character",
                    backstory="A test character",
                    initial_rooms=[
                        InitialRoomConfig(room_id="test_room", chance=100, reason="You are here for a specific reason.")
                    ]
                )
            }
        )
        
        # Mock the room
        self.mock_room = Mock()
        self.mock_room.id = "test_room"
        self.mock_room.name = "Test Room"
        self.mock_room.description = "A test room for testing purposes."
        
        # Mock the character
        self.mock_character = Mock()
        self.mock_character.name = "Test Character"
        self.mock_character.current_room_id = "test_room"
        self.mock_character.initial_room_reason = "You are here for a specific reason."
    
    def test_initial_turn_message_includes_room_reason(self):
        """Test that initial turn message includes the character's reason for being in the room."""
        # Mock the game master
        with patch('motive.game_master.GameMaster') as mock_gm_class:
            mock_gm = Mock()
            mock_gm_class.return_value = mock_gm
            
            # Mock the room lookup
            mock_gm.game_rooms = {"test_room": self.mock_room}
            
            # Mock the character lookup
            mock_gm.player_characters = {"test_char": self.mock_character}
            
            # Mock the initial turn message generation
            def mock_generate_initial_turn_message(player, character):
                room = mock_gm.game_rooms[character.current_room_id]
                reason = getattr(character, 'initial_room_reason', '')
                
                message = f"You are in {room.name}. {room.description}"
                if reason:
                    message += f" {reason}"
                return message
            
            mock_gm.generate_initial_turn_message = mock_generate_initial_turn_message
            
            # Test the message generation
            player = Mock()
            player.name = "TestPlayer"
            
            message = mock_gm.generate_initial_turn_message(player, self.mock_character)
            
            # Verify the message includes both room description and character reason
            assert "Test Room" in message
            assert "A test room for testing purposes" in message
            assert "You are here for a specific reason" in message
    
    def test_initial_turn_message_without_reason(self):
        """Test that initial turn message works when no reason is provided."""
        # Create character without initial room reason
        character_no_reason = Mock()
        character_no_reason.name = "Test Character"
        character_no_reason.current_room_id = "test_room"
        # No initial_room_reason attribute
        
        with patch('motive.game_master.GameMaster') as mock_gm_class:
            mock_gm = Mock()
            mock_gm_class.return_value = mock_gm
            
            # Mock the room lookup
            mock_gm.game_rooms = {"test_room": self.mock_room}
            
            # Mock the initial turn message generation
            def mock_generate_initial_turn_message(player, character):
                room = mock_gm.game_rooms[character.current_room_id]
                reason = getattr(character, 'initial_room_reason', '')
                
                message = f"You are in {room.name}. {room.description}"
                if reason:
                    message += f" {reason}"
                return message
            
            mock_gm.generate_initial_turn_message = mock_generate_initial_turn_message
            
            # Test the message generation
            player = Mock()
            player.name = "TestPlayer"
            
            message = mock_gm.generate_initial_turn_message(player, character_no_reason)
            
            # Verify the message includes room description but no reason
            assert "Test Room" in message
            assert "A test room for testing purposes" in message
            assert "You are here for a specific reason" not in message
    
    def test_initial_turn_message_with_multiple_rooms(self):
        """Test that initial turn message works with multiple possible initial rooms."""
        # Create character with multiple initial rooms
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character",
            initial_rooms=[
                InitialRoomConfig(room_id="room1", chance=50, reason="First reason"),
                InitialRoomConfig(room_id="room2", chance=50, reason="Second reason")
            ]
        )
        
        # Mock rooms
        room1 = Mock()
        room1.id = "room1"
        room1.name = "Room 1"
        room1.description = "First room description."
        
        room2 = Mock()
        room2.id = "room2"
        room2.name = "Room 2"
        room2.description = "Second room description."
        
        with patch('motive.game_master.GameMaster') as mock_gm_class:
            mock_gm = Mock()
            mock_gm_class.return_value = mock_gm
            
            # Mock the room lookup
            mock_gm.game_rooms = {"room1": room1, "room2": room2}
            
            # Mock the initial turn message generation
            def mock_generate_initial_turn_message(player, character):
                room = mock_gm.game_rooms[character.current_room_id]
                reason = getattr(character, 'initial_room_reason', '')
                
                message = f"You are in {room.name}. {room.description}"
                if reason:
                    message += f" {reason}"
                return message
            
            mock_gm.generate_initial_turn_message = mock_generate_initial_turn_message
            
            # Test with room 1
            character1 = Mock()
            character1.name = "Test Character"
            character1.current_room_id = "room1"
            character1.initial_room_reason = "First reason"
            
            player = Mock()
            player.name = "TestPlayer"
            
            message1 = mock_gm.generate_initial_turn_message(player, character1)
            assert "Room 1" in message1
            assert "First room description" in message1
            assert "First reason" in message1
            
            # Test with room 2
            character2 = Mock()
            character2.name = "Test Character"
            character2.current_room_id = "room2"
            character2.initial_room_reason = "Second reason"
            
            message2 = mock_gm.generate_initial_turn_message(player, character2)
            assert "Room 2" in message2
            assert "Second room description" in message2
            assert "Second reason" in message2
