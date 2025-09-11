"""Test initial room weight normalization for user-friendly story writing."""

import pytest
from unittest.mock import Mock, patch
from motive.game_initializer import GameInitializer
from motive.config import GameConfig, GameSettings, CharacterConfig, InitialRoomConfig


class TestInitialRoomNormalization:
    """Test that initial room weights are normalized when they exceed 100%."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a minimal GameInitializer for testing
        self.gi = Mock()
        self.gi.deterministic = False
        self.gi.game_rooms = {
            'room1': Mock(),
            'room2': Mock(),
            'room3': Mock()
        }
        
        # Import the method we want to test
        from motive.game_initializer import GameInitializer
        self.gi._select_initial_room = GameInitializer._select_initial_room.__get__(self.gi, GameInitializer)
    
    def test_normalize_weights_over_100_percent(self):
        """Test that weights over 100% are normalized proportionally."""
        # Create character config with weights that sum to 150%
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
        
        # Test normalization
        result = self.gi._select_initial_room(char_config, "room1")
        
        # Should return one of the valid rooms
        assert result in ["room1", "room2", "room3"]
    
    def test_normalize_weights_exactly_100_percent(self):
        """Test that weights exactly at 100% are not changed."""
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character",
            initial_rooms=[
                InitialRoomConfig(room_id="room1", chance=40, reason="First room"),
                InitialRoomConfig(room_id="room2", chance=35, reason="Second room"),
                InitialRoomConfig(room_id="room3", chance=25, reason="Third room")
            ]
        )
        
        # Test that 100% weights work normally
        result = self.gi._select_initial_room(char_config, "room1")
        assert result in ["room1", "room2", "room3"]
    
    def test_normalize_weights_under_100_percent(self):
        """Test that weights under 100% are not changed."""
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character",
            initial_rooms=[
                InitialRoomConfig(room_id="room1", chance=30, reason="First room"),
                InitialRoomConfig(room_id="room2", chance=20, reason="Second room"),
                InitialRoomConfig(room_id="room3", chance=10, reason="Third room")
            ]
        )
        
        # Test that under 100% weights work normally
        result = self.gi._select_initial_room(char_config, "room1")
        assert result in ["room1", "room2", "room3"]
    
    def test_deterministic_mode_ignores_weights(self):
        """Test that deterministic mode always picks first room regardless of weights."""
        self.gi.deterministic = True
        
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character",
            initial_rooms=[
                InitialRoomConfig(room_id="room1", chance=10, reason="First room"),
                InitialRoomConfig(room_id="room2", chance=80, reason="Second room"),
                InitialRoomConfig(room_id="room3", chance=10, reason="Third room")
            ]
        )
        
        # Should always return the first room in deterministic mode
        result = self.gi._select_initial_room(char_config, "room1")
        assert result == "room1"
    
    def test_no_initial_rooms_uses_default(self):
        """Test that missing initial_rooms uses default room."""
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character"
            # No initial_rooms
        )
        
        result = self.gi._select_initial_room(char_config, "default_room")
        assert result == "default_room"
    
    def test_invalid_rooms_ignored(self):
        """Test that rooms not in game_rooms are ignored."""
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character",
            initial_rooms=[
                InitialRoomConfig(room_id="nonexistent_room", chance=50, reason="Invalid room"),
                InitialRoomConfig(room_id="room1", chance=50, reason="Valid room")
            ]
        )
        
        result = self.gi._select_initial_room(char_config, "default_room")
        assert result == "room1"  # Should pick the valid room
    
    def test_all_rooms_invalid_uses_default(self):
        """Test that if all rooms are invalid, uses default."""
        char_config = CharacterConfig(
            id="test_char",
            name="Test Character",
            backstory="A test character",
            initial_rooms=[
                InitialRoomConfig(room_id="nonexistent_room1", chance=50, reason="Invalid room 1"),
                InitialRoomConfig(room_id="nonexistent_room2", chance=50, reason="Invalid room 2")
            ]
        )
        
        result = self.gi._select_initial_room(char_config, "default_room")
        assert result == "default_room"
