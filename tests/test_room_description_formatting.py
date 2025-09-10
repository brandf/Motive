"""
Test room description formatting improvements.
"""
import pytest
from unittest.mock import Mock
from motive.room import Room
from motive.game_object import GameObject


class TestRoomDescriptionFormatting:
    """Test that room descriptions are properly formatted with outline structure."""
    
    def test_room_description_with_objects_and_exits(self):
        """Test that room descriptions format objects and exits in outline format."""
        # Create mock objects
        mock_objects = {
            'fountain': Mock(spec=GameObject, name='Fountain'),
            'statue': Mock(spec=GameObject, name='Town Statue'),
            'gem': Mock(spec=GameObject, name='Tiny Gem'),
            'sword': Mock(spec=GameObject, name='Large Sword')
        }
        # Configure the name attribute for each mock
        for obj in mock_objects.values():
            obj.name = obj._mock_name
        
        # Create room with objects and exits
        room = Room(
            room_id="town_square",
            name="Town Square",
            description="A bustling town square with a fountain in the center.",
            exits={
                'west_gate': {'name': 'West Gate', 'is_hidden': False},
                'east_gate': {'name': 'East Gate', 'is_hidden': False}
            },
            objects=mock_objects
        )
        
        # Get formatted description
        current_room_description = room.get_formatted_description()
        
        # Verify the formatting
        expected = """A bustling town square with a fountain in the center.

**Objects in the room:**
  • Fountain
  • Town Statue
  • Tiny Gem
  • Large Sword

**Exits:**
  • West Gate
  • East Gate"""
        
        assert current_room_description == expected
    
    def test_room_description_with_objects_only(self):
        """Test room description formatting with only objects, no exits."""
        # Create mock objects
        mock_objects = {
            'torch': Mock(spec=GameObject, name='Torch'),
            'key': Mock(spec=GameObject, name='Rusty Key')
        }
        # Configure the name attribute for each mock
        for obj in mock_objects.values():
            obj.name = obj._mock_name
        
        # Create room with objects only
        room = Room(
            room_id="small_room",
            name="Small Room",
            description="A small room with various items.",
            exits={},
            objects=mock_objects
        )
        
        # Get formatted description
        current_room_description = room.get_formatted_description()
        
        expected = """A small room with various items.

**Objects in the room:**
  • Torch
  • Rusty Key"""
        
        assert current_room_description == expected
    
    def test_room_description_with_exits_only(self):
        """Test room description formatting with only exits, no objects."""
        # Create room with exits only
        room = Room(
            room_id="crossroads",
            name="Crossroads",
            description="A crossroads with multiple paths.",
            exits={
                'north': {'name': 'North Path', 'is_hidden': False},
                'south': {'name': 'South Path', 'is_hidden': False}
            },
            objects={}
        )
        
        # Get formatted description
        current_room_description = room.get_formatted_description()
        
        expected = """A crossroads with multiple paths.

**Exits:**
  • North Path
  • South Path"""
        
        assert current_room_description == expected
    
    def test_room_description_empty_room(self):
        """Test room description formatting for empty room."""
        # Create empty room
        room = Room(
            room_id="empty_room",
            name="Empty Room",
            description="An empty, featureless room.",
            exits={},
            objects={}
        )
        
        # Get formatted description
        current_room_description = room.get_formatted_description()
        
        expected = "An empty, featureless room."
        
        assert current_room_description == expected
    
    def test_room_description_with_hidden_exits(self):
        """Test that hidden exits are not shown in the description."""
        # Create room with visible and hidden exits
        room = Room(
            room_id="secret_room",
            name="Secret Room",
            description="A room with visible and hidden exits.",
            exits={
                'visible': {'name': 'Visible Exit', 'is_hidden': False},
                'hidden': {'name': 'Hidden Exit', 'is_hidden': True}
            },
            objects={}
        )
        
        # Get formatted description
        current_room_description = room.get_formatted_description()
        
        expected = """A room with visible and hidden exits.

**Exits:**
  • Visible Exit"""
        
        assert current_room_description == expected