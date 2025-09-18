"""Integration tests for drop action with sandboxed game master."""

import pytest
from unittest.mock import Mock
from motive.character import Character
from motive.room import Room
from motive.game_object import GameObject
from motive.hooks.core_hooks import handle_drop_action


@pytest.mark.sandbox_integration
class TestDropActionIntegration:
    """Test drop action integration with GameMaster."""

    def setup_method(self):
        """Set up test environment."""
        # Create test room
        self.test_room = Room(
            room_id="test_room",
            name="Test Room",
            description="A test room for dropping items",
            exits={}
        )
        
        # Create test object
        self.test_object = GameObject(
            obj_id="test_torch",
            name="Torch",
            description="A wooden torch",
            current_location_id="test_room",
            properties={"readable": True}
        )
        
        # Create test character with object in inventory
        self.test_character = Character(
            char_id="test_player",
            name="TestPlayer",
            backstory="A test character",
            motive="Test the drop action",
            current_room_id="test_room"
        )
        self.test_character.inventory = {"test_torch": self.test_object}
        
        # Create mock game master
        self.mock_game_master = Mock()
        self.mock_game_master.rooms = {"test_room": self.test_room}

    def test_drop_action_successful_integration(self):
        """Test successful drop action integration."""
        # Verify initial state
        assert "test_torch" in self.test_character.inventory
        assert "test_torch" not in self.test_room.objects
        
        # Execute drop action directly
        action_config = Mock()
        events, feedback = handle_drop_action(
            self.mock_game_master,
            self.test_character,
            action_config,
            {"object_name": "Torch"}
        )
        
        # Verify action execution
        assert len(events) == 3  # player, room_characters, adjacent_rooms_characters
        assert len(feedback) == 1
        assert "You drop the Torch" in feedback[0]
        
        # Verify state changes
        assert "test_torch" not in self.test_character.inventory
        assert "test_torch" in self.test_room.objects
        assert self.test_room.objects["test_torch"] == self.test_object
        assert self.test_object.current_location_id == "test_room"

    def test_drop_action_object_not_in_inventory(self):
        """Test drop action when object is not in inventory."""
        # Clear inventory
        self.test_character.inventory = {}
        
        # Execute drop action
        action_config = Mock()
        events, feedback = handle_drop_action(
            self.mock_game_master,
            self.test_character,
            action_config,
            {"object_name": "Torch"}
        )
        
        # Verify error handling
        assert len(events) == 1  # error event
        assert len(feedback) == 1
        assert "not in inventory" in feedback[0]
        
        # Verify no state changes
        assert "test_torch" not in self.test_character.inventory
        assert "test_torch" not in self.test_room.objects

    def test_drop_action_case_insensitive(self):
        """Test drop action with case insensitive object name matching."""
        # Execute drop action with different case
        action_config = Mock()
        events, feedback = handle_drop_action(
            self.mock_game_master,
            self.test_character,
            action_config,
            {"object_name": "torch"}  # lowercase
        )
        
        # Verify successful drop
        assert len(events) == 3
        assert "You drop the Torch" in feedback[0]
        assert "test_torch" not in self.test_character.inventory
        assert "test_torch" in self.test_room.objects

    def test_drop_action_room_description_update(self):
        """Test that dropped items appear in room descriptions."""
        # Verify initial room description doesn't include the object
        room_desc = self.test_room.get_formatted_description()
        assert "Torch" not in room_desc
        
        # Execute drop action
        action_config = Mock()
        handle_drop_action(
            self.mock_game_master,
            self.test_character,
            action_config,
            {"object_name": "Torch"}
        )
        
        # Verify object appears in room description
        room_desc = self.test_room.get_formatted_description()
        assert "Torch" in room_desc
        # Note: Room descriptions only show object names, not descriptions

    def test_drop_action_events_observers(self):
        """Test that drop action generates events with correct observers."""
        # Execute drop action
        action_config = Mock()
        events, feedback = handle_drop_action(
            self.mock_game_master,
            self.test_character,
            action_config,
            {"object_name": "Torch"}
        )
        
        # Verify event types and observers
        assert len(events) == 3
        
        # Player event
        player_event = events[0]
        assert player_event.event_type == "item_drop"
        assert player_event.observers == ["player"]
        assert "You drop the Torch" in player_event.message
        
        # Room players event
        room_event = events[1]
        assert room_event.event_type == "player_action"
        assert room_event.observers == ["room_characters"]
        assert "TestPlayer drops the Torch" in room_event.message
        
        # Adjacent rooms event
        adjacent_event = events[2]
        assert adjacent_event.event_type == "player_action"
        assert adjacent_event.observers == ["adjacent_rooms_characters"]
        assert "TestPlayer drops something" in adjacent_event.message
