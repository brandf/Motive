"""
Comprehensive tests for the give action implementation.

Tests cover:
- Action parsing (give <player> <object>)
- Requirements validation (player in room, object in inventory)
- Action execution (inventory transfer)
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


class TestGiveActionParsing:
    """Test give action parsing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.give_action_config = ActionConfig(
            id="give",
            name="give",
            cost=10,
            description="Give an object from your inventory to another player.",
            category="inventory",
            parameters=[
                ParameterConfig(name="player", type="string", description="The name of the player to give to."),
                ParameterConfig(name="object_name", type="string", description="The name of the object to give.")
            ],
            requirements=[
                ActionRequirementConfig(type="player_in_room", target_player_param="player"),
                ActionRequirementConfig(type="object_in_inventory", object_name_param="object_name")
            ],
            effects=[
                ActionEffectConfig(
                    type="code_binding",
                    function_name="handle_give_action",
                    observers=["player", "room_players"]
                )
            ]
        )
        
        self.available_actions = {"give": self.give_action_config}
    
    def test_give_action_parsing_basic(self):
        """Test basic give action parsing."""
        response = "> give Player_2 torch"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "give"
        assert params["player"] == "Player_2"
        assert params["object_name"] == "torch"
    
    def test_give_action_parsing_with_quotes(self):
        """Test give action parsing with quoted parameters."""
        response = '> give "Player_2" "magic sword"'
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "give"
        assert params["player"] == "Player_2"
        assert params["object_name"] == "magic sword"
    
    def test_give_action_parsing_mixed_quotes(self):
        """Test give action parsing with mixed quoted/unquoted parameters."""
        response = '> give Player_2 "magic sword"'
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "give"
        assert params["player"] == "Player_2"
        assert params["object_name"] == "magic sword"
    
    def test_give_action_parsing_case_insensitive(self):
        """Test give action parsing is case insensitive."""
        response = "> GIVE player_2 TORCH"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 1
        assert len(invalid_actions) == 0
        
        action_config, params = parsed_actions[0]
        assert action_config.name == "give"
        assert params["player"] == "player_2"
        assert params["object_name"] == "TORCH"
    
    def test_give_action_parsing_multiple_actions(self):
        """Test give action parsing with multiple actions."""
        response = "> give Player_2 torch\n> give Player_3 sword"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 2
        assert len(invalid_actions) == 0
        
        # First action
        action_config, params = parsed_actions[0]
        assert action_config.name == "give"
        assert params["player"] == "Player_2"
        assert params["object_name"] == "torch"
        
        # Second action
        action_config, params = parsed_actions[1]
        assert action_config.name == "give"
        assert params["player"] == "Player_3"
        assert params["object_name"] == "sword"
    
    def test_give_action_parsing_invalid_missing_params(self):
        """Test give action parsing with missing parameters."""
        response = "> give Player_2"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 0
        assert len(invalid_actions) == 1
        assert "give Player_2" in invalid_actions[0]
    
    def test_give_action_parsing_invalid_no_params(self):
        """Test give action parsing with no parameters."""
        response = "> give"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 0
        assert len(invalid_actions) == 1
        assert "give" in invalid_actions[0]
    
    def test_give_action_parsing_invalid_extra_params(self):
        """Test give action parsing with extra parameters."""
        response = "> give Player_2 torch sword"
        parsed_actions, invalid_actions = parse_player_response(response, self.available_actions)
        
        assert len(parsed_actions) == 0
        assert len(invalid_actions) == 1
        assert "give Player_2 torch sword" in invalid_actions[0]


class TestGiveActionExecution:
    """Test give action execution functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock game master
        self.game_master = MagicMock(spec=GameMaster)
        self.game_master.game_logger = MagicMock()
        
        # Create mock characters
        self.giver = MagicMock(spec=Character)
        self.giver.name = "Player_1"
        self.giver.id = "player_1_id"
        self.giver.current_room_id = "tavern"
        
        self.receiver = MagicMock(spec=Character)
        self.receiver.name = "Player_2"
        self.receiver.id = "player_2_id"
        self.receiver.current_room_id = "tavern"
        
        # Create mock object
        self.torch = MagicMock(spec=GameObject)
        self.torch.name = "torch"
        self.torch.id = "torch_id"
        
        # Create mock room
        self.room = MagicMock(spec=Room)
        self.room.id = "tavern"
        self.room.name = "Tavern"
        
        # Set up game master mocks
        self.game_master.rooms = {"tavern": self.room}
        self.game_master.player_characters = {
            "player_1_id": self.giver,
            "player_2_id": self.receiver
        }
        
        # Set up character inventory
        self.giver.get_item_in_inventory.return_value = self.torch
        self.giver.remove_item_from_inventory.return_value = self.torch
        self.receiver.add_item_to_inventory.return_value = True
    
    def test_give_action_execution_success(self):
        """Test successful give action execution."""
        from motive.hooks.core_hooks import handle_give_action
        
        params = {"player": "Player_2", "object_name": "torch"}
        action_config = MagicMock()
        
        events, feedback = handle_give_action(self.game_master, self.giver, action_config, params)
        
        # Verify object transfer
        self.giver.remove_item_from_inventory.assert_called_once_with("torch")
        self.receiver.add_item_to_inventory.assert_called_once_with(self.torch)
        
        # Verify feedback
        assert len(feedback) == 1
        assert "You give the torch to Player_2" in feedback[0]
        
        # Verify events
        assert len(events) == 1
        event = events[0]
        assert "Player_1 gives a torch to Player_2" in event.message
        assert event.event_type == "item_transfer"
        assert event.observers == ["player", "room_players"]
    
    def test_give_action_execution_object_not_in_inventory(self):
        """Test give action when object is not in giver's inventory."""
        from motive.hooks.core_hooks import handle_give_action
        
        # Object not in inventory
        self.giver.get_item_in_inventory.return_value = None
        
        params = {"player": "Player_2", "object_name": "torch"}
        action_config = MagicMock()
        
        events, feedback = handle_give_action(self.game_master, self.giver, action_config, params)
        
        # Verify no transfer occurred
        self.giver.remove_item_from_inventory.assert_not_called()
        self.receiver.add_item_to_inventory.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "You don't have a torch in your inventory" in feedback[0]
        
        # Verify no events
        assert len(events) == 0
    
    def test_give_action_execution_player_not_in_room(self):
        """Test give action when target player is not in the same room."""
        from motive.hooks.core_hooks import handle_give_action
        
        # Receiver in different room
        self.receiver.current_room_id = "different_room"
        
        params = {"player": "Player_2", "object_name": "torch"}
        action_config = MagicMock()
        
        events, feedback = handle_give_action(self.game_master, self.giver, action_config, params)
        
        # Verify no transfer occurred
        self.giver.remove_item_from_inventory.assert_not_called()
        self.receiver.add_item_to_inventory.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "Player_2 is not in the same room as you" in feedback[0]
        
        # Verify no events
        assert len(events) == 0
    
    def test_give_action_execution_player_not_found(self):
        """Test give action when target player doesn't exist."""
        from motive.hooks.core_hooks import handle_give_action
        
        # Player not found
        self.game_master.player_characters = {"player_1_id": self.giver}
        
        params = {"player": "Player_2", "object_name": "torch"}
        action_config = MagicMock()
        
        events, feedback = handle_give_action(self.game_master, self.giver, action_config, params)
        
        # Verify no transfer occurred
        self.giver.remove_item_from_inventory.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "Player_2 is not a valid player" in feedback[0]
        
        # Verify no events
        assert len(events) == 0
    
    def test_give_action_execution_giving_to_self(self):
        """Test give action when trying to give to yourself."""
        from motive.hooks.core_hooks import handle_give_action
        
        params = {"player": "Player_1", "object_name": "torch"}
        action_config = MagicMock()
        
        events, feedback = handle_give_action(self.game_master, self.giver, action_config, params)
        
        # Verify no transfer occurred
        self.giver.remove_item_from_inventory.assert_not_called()
        self.giver.add_item_to_inventory.assert_not_called()
        
        # Verify error feedback
        assert len(feedback) == 1
        assert "You cannot give items to yourself" in feedback[0]
        
        # Verify no events
        assert len(events) == 0
    
    def test_give_action_execution_inventory_full(self):
        """Test give action when receiver's inventory is full.
        
        Note: Currently inventory limits are not implemented, so this test
        is skipped until inventory constraints are added.
        """
        pytest.skip("Inventory limits not yet implemented")


class TestGiveActionIntegration:
    """Test give action integration with the full game system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a minimal game master with real components
        self.game_master = MagicMock(spec=GameMaster)
        self.game_master.game_logger = MagicMock()
        self.game_master.rooms = {}
        self.game_master.player_characters = {}
    
    def test_give_action_with_real_character_objects(self):
        """Test give action with real Character and GameObject instances."""
        from motive.character import Character
        from motive.game_object import GameObject
        from motive.hooks.core_hooks import handle_give_action
        
        # Create real character instances
        giver = Character(
            char_id="player_1_id",
            name="Player_1",
            backstory="Test character",
            motive="test_motive",
            motives=[],
            current_room_id="tavern",
            action_points=30
        )
        
        receiver = Character(
            char_id="player_2_id", 
            name="Player_2",
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
        
        # Add torch to giver's inventory
        giver.add_item_to_inventory(torch)
        
        # Set up game master
        self.game_master.player_characters = {
            "player_1_id": giver,
            "player_2_id": receiver
        }
        
        # Execute give action
        params = {"player": "Player_2", "object_name": "torch"}
        action_config = MagicMock()
        
        events, feedback = handle_give_action(self.game_master, giver, action_config, params)
        
        # Verify transfer
        assert giver.get_item_in_inventory("torch") is None
        assert receiver.get_item_in_inventory("torch") is not None
        
        # Verify feedback
        assert len(feedback) == 1
        assert "You give the torch to Player_2" in feedback[0]
        
        # Verify events
        assert len(events) == 1
        event = events[0]
        assert "Player_1 gives a torch to Player_2" in event.message
