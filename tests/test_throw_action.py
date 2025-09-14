"""
Comprehensive tests for the throw action implementation.

Tests cover:
- Action parsing (throw <object> <exit>)
- Requirements validation (object in inventory, exit exists)
- Action execution (inventory removal, object placement)
- Error handling and feedback
- Edge cases and invalid inputs
"""

import pytest
from unittest.mock import MagicMock, patch
from motive.action_parser import parse_player_response
from motive.config import ActionConfig, ParameterConfig, ActionRequirementConfig, ActionEffectConfig
from motive.game_master import GameMaster
from motive.character import Character
from motive.game_object import GameObject
from motive.room import Room


class TestThrowActionParsing:
    """Test throw action parsing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.throw_action_config = ActionConfig(
            id="throw",
            name="throw",
            cost=10,
            description="Throw an object from your inventory through an exit to an adjacent room.",
            category="inventory",
            parameters=[
                ParameterConfig(name="object_name", type="string", description="The name of the object to throw."),
                ParameterConfig(name="exit", type="string", description="The exit/direction to throw the object through.")
            ],
            requirements=[
                ActionRequirementConfig(type="object_in_inventory", object_name_param="object_name"),
                ActionRequirementConfig(type="exit_exists", direction_param="exit")
            ],
            effects=[
                ActionEffectConfig(
                    type="code_binding",
                    function_name="handle_throw_action",
                    observers=["player", "room_players", "adjacent_rooms"]
                )
            ]
        )
        
        self.available_actions = {"throw": self.throw_action_config}
    
    def test_throw_action_parsing_basic(self):
        """Test basic throw action parsing."""
        response = "> throw torch north"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "throw"
        assert params["object_name"] == "torch"
        assert params["exit"] == "north"
    
    def test_throw_action_parsing_with_quotes(self):
        """Test throw action parsing with quoted parameters."""
        response = '> throw "magic sword" "Rusty Anchor Tavern"'
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "throw"
        assert params["object_name"] == "magic sword"
        assert params["exit"] == "Rusty Anchor Tavern"
    
    def test_throw_action_parsing_mixed_quotes(self):
        """Test throw action parsing with mixed quoted/unquoted parameters."""
        response = '> throw torch "Rusty Anchor Tavern"'
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "throw"
        assert params["object_name"] == "torch"
        assert params["exit"] == "Rusty Anchor Tavern"
    
    def test_throw_action_parsing_case_insensitive(self):
        """Test throw action parsing is case insensitive."""
        response = "> THROW TORCH NORTH"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "throw"
        assert params["object_name"] == "TORCH"
        assert params["exit"] == "NORTH"
    
    def test_throw_action_parsing_multiple_actions(self):
        """Test throw action parsing with multiple actions."""
        response = "> throw torch north\n> throw sword south"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 2
        assert len(invalid_actions) == 0
        
        # First action
        action_config, params = parsed_actions[0]
        assert action_config.name == "throw"
        assert params["object_name"] == "torch"
        assert params["exit"] == "north"
        
        # Second action
        action_config, params = parsed_actions[1]
        assert action_config.name == "throw"
        assert params["object_name"] == "sword"
        assert params["exit"] == "south"
    
    def test_throw_action_parsing_invalid_missing_params(self):
        """Test throw action parsing with missing parameters."""
        response = "> throw torch"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 0
        assert len(invalid_actions) == 1
        assert "throw torch" in invalid_actions[0]
    
    def test_throw_action_parsing_invalid_no_params(self):
        """Test throw action parsing with no parameters."""
        response = "> throw"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 0
        assert len(invalid_actions) == 1
        assert "throw" in invalid_actions[0]
    
    def test_throw_action_parsing_invalid_extra_params(self):
        """Test throw action parsing with extra parameters."""
        response = "> throw torch north south"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 0
        assert len(invalid_actions) == 1
        assert "throw torch north south" in invalid_actions[0]


class TestThrowActionExecution:
    """Test throw action execution functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock game master
        self.game_master = MagicMock(spec=GameMaster)
        self.game_master.game_logger = MagicMock()
        
        # Create mock character
        self.player = MagicMock(spec=Character)
        self.player.name = "Player_1"
        self.player.id = "player_1_id"
        self.player.current_room_id = "tavern"
        
        # Create mock object
        self.torch = MagicMock(spec=GameObject)
        self.torch.name = "torch"
        self.torch.id = "torch_id"
        
        # Create mock rooms
        self.current_room = MagicMock(spec=Room)
        self.current_room.id = "tavern"
        self.current_room.name = "Tavern"
        self.current_room.exits = {"north": {"room_id": "library"}}
        
        self.target_room = MagicMock(spec=Room)
        self.target_room.id = "library"
        self.target_room.name = "Library"
        
        # Set up game master mocks
        self.game_master.rooms = {"tavern": self.current_room, "library": self.target_room}
        
        # Set up character inventory
        self.player.get_item_in_inventory.return_value = self.torch
        self.player.remove_item_from_inventory.return_value = self.torch
    
    def test_throw_action_execution_success(self):
        """Test successful throw action execution."""
        from motive.hooks.core_hooks import handle_throw_action
        
        params = {"object_name": "torch", "exit": "north"}
        action_config = MagicMock()
        
        events, feedback = handle_throw_action(self.game_master, self.player, action_config, params)
        
        # Verify object removal from inventory
        self.player.remove_item_from_inventory.assert_called_once_with("torch")
        
        # Verify object placement in target room
        self.target_room.add_object.assert_called_once_with(self.torch)
        
        # Verify feedback
        assert len(feedback) == 1
        assert "You throw the torch north" in feedback[0]
        
        # Verify events
        assert len(events) == 2  # One for current room, one for target room
        current_room_event = events[0]
        target_room_event = events[1]
        
        assert "Player_1 throws a torch north" in current_room_event.message
        assert current_room_event.observers == ["player", "room_players"]
        
        assert "A torch is thrown into the Library from the Tavern" in target_room_event.message
        assert target_room_event.observers == ["room_players"]
    
    def test_throw_action_execution_object_not_in_inventory(self):
        """Test throw action when object is not in player's inventory."""
        from motive.hooks.core_hooks import handle_throw_action
        
        # Object not in inventory
        self.player.get_item_in_inventory.return_value = None
        
        params = {"object_name": "torch", "exit": "north"}
        action_config = MagicMock()
        
        events, feedback = handle_throw_action(self.game_master, self.player, action_config, params)
        
        # Verify no transfer occurred
        self.player.remove_item_from_inventory.assert_not_called()
        self.target_room.add_object.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "You don't have a torch in your inventory" in feedback[0]
        
        # Verify no events
        assert len(events) == 0
    
    def test_throw_action_execution_exit_not_exists(self):
        """Test throw action when exit doesn't exist."""
        from motive.hooks.core_hooks import handle_throw_action
        
        # Exit doesn't exist
        self.current_room.exits = {"south": {"room_id": "kitchen"}}
        
        params = {"object_name": "torch", "exit": "north"}
        action_config = MagicMock()
        
        events, feedback = handle_throw_action(self.game_master, self.player, action_config, params)
        
        # Verify no transfer occurred
        self.player.remove_item_from_inventory.assert_not_called()
        self.target_room.add_object.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "There is no exit 'north' from this room" in feedback[0]
        
        # Verify no events
        assert len(events) == 0
    
    def test_throw_action_execution_target_room_not_found(self):
        """Test throw action when target room doesn't exist."""
        from motive.hooks.core_hooks import handle_throw_action
        
        # Target room doesn't exist
        self.current_room.exits = {"north": {"room_id": "nonexistent_room"}}
        
        params = {"object_name": "torch", "exit": "north"}
        action_config = MagicMock()
        
        events, feedback = handle_throw_action(self.game_master, self.player, action_config, params)
        
        # Verify no transfer occurred
        self.player.remove_item_from_inventory.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "Target room 'nonexistent_room' not found" in feedback[0]
        
        # Verify no events
        assert len(events) == 0
    
    def test_throw_action_execution_remove_failed(self):
        """Test throw action when object removal fails."""
        from motive.hooks.core_hooks import handle_throw_action
        
        # Object removal fails
        self.player.remove_item_from_inventory.return_value = None
        
        params = {"object_name": "torch", "exit": "north"}
        action_config = MagicMock()
        
        events, feedback = handle_throw_action(self.game_master, self.player, action_config, params)
        
        # Verify object removal was attempted
        self.player.remove_item_from_inventory.assert_called_once_with("torch")
        
        # Verify no placement occurred
        self.target_room.add_object.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "Failed to remove torch from your inventory" in feedback[0]
        
        # Verify no events
        assert len(events) == 0


class TestThrowActionIntegration:
    """Test throw action integration with the full game system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a minimal game master with real components
        self.game_master = MagicMock(spec=GameMaster)
        self.game_master.game_logger = MagicMock()
        self.game_master.rooms = {}
    
    def test_throw_action_with_real_character_objects(self):
        """Test throw action with real Character and GameObject instances."""
        from motive.character import Character
        from motive.game_object import GameObject
        from motive.room import Room
        from motive.hooks.core_hooks import handle_throw_action
        
        # Create real character instance
        player = Character(
            char_id="player_1_id",
            name="Player_1",
            backstory="Test character",
            motive="test_motive",
            motives=[],
            current_room_id="tavern",
            action_points=30
        )
        
        # Create real object
        torch = GameObject(
            obj_id="torch_id",
            name="torch",
            description="A wooden torch",
            current_location_id="player_1_id"
        )
        
        # Create real rooms
        current_room = Room(
            room_id="tavern",
            name="Tavern",
            description="A cozy tavern",
            exits={"north": {"room_id": "library"}}
        )
        
        target_room = Room(
            room_id="library",
            name="Library", 
            description="A quiet library",
            exits={"south": {"room_id": "tavern"}}
        )
        
        # Add torch to player's inventory
        player.add_item_to_inventory(torch)
        
        # Set up game master
        self.game_master.rooms = {"tavern": current_room, "library": target_room}
        
        # Execute throw action
        params = {"object_name": "torch", "exit": "north"}
        action_config = MagicMock()
        
        events, feedback = handle_throw_action(self.game_master, player, action_config, params)
        
        # Verify transfer
        assert player.get_item_in_inventory("torch") is None
        assert target_room.get_object("torch") is not None
        
        # Verify feedback
        assert len(feedback) == 1
        assert "You throw the torch north" in feedback[0]
        
        # Verify events
        assert len(events) == 2
        current_room_event = events[0]
        target_room_event = events[1]
        
        assert "Player_1 throws a torch north" in current_room_event.message
        assert "A torch is thrown into the Library from the Tavern" in target_room_event.message

