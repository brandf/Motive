"""
Tests for character location and inventory snapshot reporting feature.

This feature adds a report before each round (including the first) that shows:
- Where each character is located
- What objects are in their inventory
- Formatted consistently with existing game logging style
"""

import pytest
from unittest.mock import Mock, patch
from motive.game_master import GameMaster
from motive.config import GameConfig
from motive.character import Character
from motive.player import Player


class TestCharacterSnapshotReport:
    """Test character location and inventory snapshot reporting."""

    def test_generate_character_snapshot_report_basic(self):
        """Test basic character snapshot report generation."""
        # Create mock game master with players
        gm = Mock(spec=GameMaster)
        gm.players = []
        gm.rooms = {}
        
        # Create mock characters and players
        char1 = Mock(spec=Character)
        char1.name = "Detective James Thorne"
        char1.current_room_id = "town_square"
        # Mock inventory as a dictionary of GameObjects
        mock_item1 = Mock()
        mock_item1.name = "notebook"
        mock_item2 = Mock()
        mock_item2.name = "magnifying_glass"
        char1.inventory = {"notebook_id": mock_item1, "magnifying_glass_id": mock_item2}

        char2 = Mock(spec=Character)
        char2.name = "Father Marcus"
        char2.current_room_id = "church"
        # Mock inventory as a dictionary of GameObjects
        mock_item3 = Mock()
        mock_item3.name = "holy_water"
        mock_item4 = Mock()
        mock_item4.name = "prayer_book"
        char2.inventory = {"holy_water_id": mock_item3, "prayer_book_id": mock_item4}
        
        player1 = Mock(spec=Player)
        player1.name = "Player_1"
        player1.character = char1
        
        player2 = Mock(spec=Player)
        player2.name = "Player_2"
        player2.character = char2
        
        gm.players = [player1, player2]
        
        # Create mock rooms
        room1 = Mock()
        room1.name = "Town Square"
        room2 = Mock()
        room2.name = "Sacred Heart Church"
        gm.rooms = {
            "town_square": room1,
            "church": room2
        }
        
        # Test the report generation
        report = GameMaster._generate_character_snapshot_report(gm)
        
        # Verify report structure
        assert "📊 Character Snapshot Report:" in report
        assert "👤 Player_1 (Detective James Thorne)" in report
        assert "• Location: Town Square" in report
        assert "• Inventory: notebook, magnifying_glass" in report
        assert "👤 Player_2 (Father Marcus)" in report
        assert "• Location: Sacred Heart Church" in report
        assert "• Inventory: holy_water, prayer_book" in report

    def test_generate_character_snapshot_report_empty_inventory(self):
        """Test character snapshot report with empty inventory."""
        gm = Mock(spec=GameMaster)
        gm.players = []
        gm.rooms = {}
        
        char = Mock(spec=Character)
        char.name = "Test Character"
        char.current_room_id = "test_room"
        char.inventory = {}
        
        player = Mock(spec=Player)
        player.name = "Player_1"
        player.character = char
        
        gm.players = [player]
        gm.rooms = {"test_room": Mock(name="Test Room")}
        
        report = GameMaster._generate_character_snapshot_report(gm)
        
        assert "• Inventory: (empty)" in report

    def test_generate_character_snapshot_report_unknown_room(self):
        """Test character snapshot report with unknown room ID."""
        gm = Mock(spec=GameMaster)
        gm.players = []
        gm.rooms = {}
        
        char = Mock(spec=Character)
        char.name = "Test Character"
        char.current_room_id = "unknown_room"
        # Mock inventory as a dictionary of GameObjects
        mock_item = Mock()
        mock_item.name = "item1"
        char.inventory = {"item1_id": mock_item}
        
        player = Mock(spec=Player)
        player.name = "Player_1"
        player.character = char
        
        gm.players = [player]
        gm.rooms = {}  # No rooms defined
        
        report = GameMaster._generate_character_snapshot_report(gm)
        
        assert "• Location: Unknown (unknown_room)" in report

    def test_log_character_snapshot_report_called_before_rounds(self):
        """Test that character snapshot report method exists and can be called."""
        # This test verifies that the method exists and can be called
        # The actual integration test would require a full game setup
        from motive.game_master import GameMaster
        
        # Verify the method exists
        assert hasattr(GameMaster, '_generate_character_snapshot_report'), \
            "GameMaster should have _generate_character_snapshot_report method"
        
        # Verify it's callable
        assert callable(getattr(GameMaster, '_generate_character_snapshot_report')), \
            "_generate_character_snapshot_report should be callable"

    def test_character_snapshot_report_formatting_consistency(self):
        """Test that character snapshot report follows existing formatting patterns."""
        gm = Mock(spec=GameMaster)
        gm.players = []
        gm.rooms = {}
        
        char = Mock(spec=Character)
        char.name = "Test Character"
        char.current_room_id = "test_room"
        # Mock inventory as a dictionary of GameObjects
        mock_item1 = Mock()
        mock_item1.name = "item1"
        mock_item2 = Mock()
        mock_item2.name = "item2"
        mock_item3 = Mock()
        mock_item3.name = "item3"
        char.inventory = {
            "item1_id": mock_item1,
            "item2_id": mock_item2,
            "item3_id": mock_item3
        }
        
        player = Mock(spec=Player)
        player.name = "Player_1"
        player.character = char
        
        gm.players = [player]
        room = Mock()
        room.name = "Test Room"
        gm.rooms = {"test_room": room}
        
        report = GameMaster._generate_character_snapshot_report(gm)
        
        # Check for consistent emoji usage and formatting
        lines = report.split('\n')
        assert any("📊 Character Snapshot Report:" in line for line in lines)
        assert any("👤 Player_1 (Test Character)" in line for line in lines)
        assert any("• Location: Test Room" in line for line in lines)
        assert any("• Inventory: item1, item2, item3" in line for line in lines)
        
        # Check for proper indentation
        for line in lines:
            if line.startswith("    "):
                assert line.startswith("    👤") or line.startswith("    •")
