import pytest
import os
import logging
from unittest.mock import MagicMock, patch

from motive.game_master import GameMaster
from motive.config import (
    GameConfig, PlayerConfig, ThemeConfig, EditionConfig, ObjectTypeConfig, 
    ActionConfig, CharacterConfig, RoomConfig, ExitConfig, ObjectInstanceConfig, 
    ActionRequirementConfig, ActionEffectConfig, ParameterConfig, GameSettings
) # Added GameSettings and other config models
from motive.player import Player, PlayerCharacter
from motive.game_objects import GameObject
from motive.game_rooms import Room
from langchain_core.messages import AIMessage
from unittest.mock import AsyncMock

@pytest.fixture
def mock_game_master():
    # Mock logging setup to prevent actual file writing during tests
    with (
        patch('os.makedirs'),
        patch('logging.FileHandler') as mock_file_handler_class,
        patch('os.path.join', return_value='mock/log/path'), # Mock os.path.join
        patch('motive.player.create_llm_client', return_value=MagicMock()), # Mock create_llm_client
        patch('motive.player.Player') as mock_player_class, # Mock the Player class
        patch('motive.game_master.GameMaster._load_yaml_config') as mock_load_yaml_config,
        patch('motive.game_master.GameMaster._load_manual_content') as mock_load_manual_content,
        patch('sys.stdout') as mock_stdout # Mock sys.stdout to prevent console output during tests
    ):
        # Configure the mock file handler to return an integer level
        mock_file_handler_instance = MagicMock()
        mock_file_handler_instance.level = logging.INFO # Set an integer level
        mock_file_handler_class.return_value = mock_file_handler_instance

        # Configure mock_stdout for assertions if needed
        mock_stdout.write.return_value = None

        # Define a mock Player class that accepts log_dir and has a mocked logger
        class MockPlayer:
            def __init__(self, name: str, provider: str, model: str, log_dir: str):
                self.name = name
                self.llm_client = MagicMock() # Mock the LLM client
                self.chat_history = []
                self.log_dir = log_dir
                self.logger = MagicMock(spec=logging.Logger)
                self.logger.info = MagicMock()
                self.character = None

            def add_message(self, message):
                self.chat_history.append(message)

            async def get_response_and_update_history(self, messages_for_llm: list) -> AIMessage:
                return AIMessage(content="end turn") # Default AI response
        
        mock_player_class.side_effect = MockPlayer # Assign the mock class as a side effect

        # Create dummy theme and edition configs for basic initialization
        dummy_theme_config = ThemeConfig(
            id="test_theme",
            name="Test Theme",
            object_types={
                "torch": ObjectTypeConfig(id="torch", name="Torch", description="A torch.", tags=["light_source"], properties={"is_lit": False}),
                "generic_fountain": ObjectTypeConfig(id="generic_fountain", name="Fountain", description="A basic fountain.", tags=[], properties={}),
                "generic_sign": ObjectTypeConfig(id="generic_sign", name="Sign", description="A generic sign.", tags=[], properties={})
            },
            actions={
                "look": ActionConfig(id="look", name="look", cost=1, description="Look around.", parameters=[], requirements=[], effects=[]),
                "light_torch": ActionConfig(
                    id="light_torch",
                    name="light torch",
                    cost=1,
                    description="Light a torch you are holding.",
                    parameters=[ParameterConfig(name="object_name", type="string", description="The name of the torch to light.")],
                    requirements=[
                        ActionRequirementConfig(type="player_has_object_in_inventory", object_name_param="object_name"),
                        ActionRequirementConfig(type="object_property_equals", object_name_param="object_name", property="is_lit", value=False)
                    ],
                    effects=[
                        ActionEffectConfig(type="set_object_property", object_name_param="object_name", property="is_lit", value=True),
                        ActionEffectConfig(type="generate_event", message="{player_name} lights the {object_name}.", observers=["room_players"])
                    ]
                ),
                "pickup": ActionConfig(
                    id="pickup",
                    name="pickup",
                    cost=1,
                    description="Pick up an object.",
                    parameters=[ParameterConfig(name="object_name", type="string", description="The name of the object to pick up.")],
                    requirements=[
                        ActionRequirementConfig(type="object_in_room", object_name_param="object_name")
                    ],
                    effects=[
                        ActionEffectConfig(type="move_object", object_name_param="object_name", destination_type="player_inventory")
                    ]
                )
            },
            character_types={
                "hero": CharacterConfig(id="hero", name="Hero", backstory="A brave adventurer.", motive="Defeat evil.")
            }
        )

        dummy_edition_config = EditionConfig(
            id="test_edition",
            name="Test Edition",
            theme_id="test_theme",
            rooms={
                "start_room": RoomConfig(
                    id="start_room",
                    name="Starting Room",
                    description="A simple starting room.",
                    exits={"north": ExitConfig(id="north_exit", name="North", destination_room_id="other_room")},
                    objects={
                        "room_torch": ObjectInstanceConfig(id="room_torch", name="room_torch", object_type_id="torch", current_room_id="start_room"),
                        "room_fountain": ObjectInstanceConfig(id="room_fountain", name="Fountain", object_type_id="generic_fountain", current_room_id="start_room")
                    }
                ),
                "other_room": RoomConfig(
                    id="other_room",
                    name="Another Room",
                    description="A dark, dusty room.",
                    exits={"south": ExitConfig(id="south_exit", name="South", destination_room_id="start_room")}
                )
            },
            objects={
                "global_key": ObjectInstanceConfig(id="global_key", name="key", object_type_id="torch", current_room_id="start_room", tags=["key_tag"])
            },
            characters={
                "rogue": CharacterConfig(id="rogue", name="Rogue", backstory="A sneaky type.", motive="Find treasure.")
            }
        )

        mock_game_config = MagicMock(spec=GameConfig)
        mock_game_config.game_settings = MagicMock(spec=GameSettings)
        mock_game_config.game_settings.num_rounds = 1
        mock_game_config.game_settings.theme_config_path = "mock/theme.yaml"
        mock_game_config.game_settings.edition_config_path = "mock/edition.yaml"
        mock_game_config.game_settings.manual = "mock/manual.md"
        mock_game_config.players = [
            PlayerConfig(name="TestPlayer", provider="mock", model="mock-model"),
        ]
        mock_game_config.theme_config = dummy_theme_config
        mock_game_config.edition_config = dummy_edition_config

        # Configure the mocked _load_yaml_config and _load_manual_content
        mock_load_yaml_config.side_effect = [
            dummy_theme_config,
            dummy_edition_config
        ]
        mock_load_manual_content.return_value = "Mock manual content."

        # Instantiate a real GameMaster, which will call the mocked loaders
        gm = GameMaster(game_config=mock_game_config, game_id="test_game_id")
        gm.game_logger.setLevel(logging.DEBUG) # Set logging level to DEBUG for tests

        # Mock the player instance created by GameMaster._initialize_players
        # The mock_player_class.side_effect now handles returning the mock player instance.
        # We just need to get the instance that was created.
        mock_player_instance = gm.players[0] # GameMaster._initialize_players adds the player
        mock_player_instance.character = gm.player_characters["rogue_instance"] # Link to the real character
        mock_player_instance.add_message = MagicMock() # Mock add_message for isolation
        mock_player_instance.get_response_and_update_history = AsyncMock(return_value=AIMessage(content="end turn")) # Default AI response

        # Replace the real player list with our mocked player
        gm.players = [mock_player_instance]

        yield gm

# --- Test _check_requirements --- #

def test_check_requirements_player_has_object_in_inventory_success(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    # Give player a torch
    player_char.add_item_to_inventory(
        GameObject(obj_id="my_torch", name="my_torch", description="a torch", current_location_id=player_char.id, tags=["light_source"], properties={"is_lit": False})
    )

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "my_torch"}

    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is True
    assert message == ""

def test_check_requirements_player_has_object_in_inventory_fail(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "non_existent_torch"}

    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is False
    assert "Player does not have 'non_existent_torch' in inventory." in message

def test_check_requirements_object_property_equals_success(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    # Give player an unlit torch
    player_char.add_item_to_inventory(
        GameObject(obj_id="my_torch", name="my_torch", description="a torch", current_location_id=player_char.id, tags=["light_source"], properties={"is_lit": False})
    )

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "my_torch"}

    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is True
    assert message == ""

def test_check_requirements_object_property_equals_fail(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    # Give player an already lit torch
    player_char.add_item_to_inventory(
        GameObject(obj_id="my_lit_torch", name="my_lit_torch", description="a lit torch", current_location_id=player_char.id, tags=["light_source"], properties={"is_lit": True})
    )

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "my_lit_torch"}

    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is False
    assert "Object 'my_lit_torch' property 'is_lit' is not 'False'." in message

def test_check_requirements_object_in_room_success(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    action_config = gm.game_actions["pickup"]
    params = {"object_name": "room_torch"}

    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is True
    assert message == ""

def test_check_requirements_object_in_room_fail(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    action_config = gm.game_actions["pickup"]
    params = {"object_name": "non_existent_object"}

    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is False
    assert "Object 'non_existent_object' not in room." in message

# --- Test _execute_effects --- #

def test_execute_effects_set_object_property(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    # Give player an unlit torch
    torch_obj = GameObject(obj_id="my_torch_effect", name="my_torch_effect", description="a torch", current_location_id=player_char.id, tags=["light_source"], properties={"is_lit": False})
    player_char.add_item_to_inventory(torch_obj)

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "my_torch_effect"}

    feedback = gm._execute_effects(player_char, action_config, params)
    assert "The my_torch_effect's is_lit is now 'True'." in feedback
    assert player_char.get_item_in_inventory("my_torch_effect").get_property("is_lit") is True

def test_execute_effects_move_object_to_inventory(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character
    initial_room = gm.rooms.get(player_char.current_room_id)

    # Ensure the room_torch is in the initial room
    assert initial_room.get_object("room_torch") is not None
    assert not player_char.has_item_in_inventory("room_torch")

    action_config = gm.game_actions["pickup"]
    params = {"object_name": "room_torch"}

    feedback = gm._execute_effects(player_char, action_config, params)
    assert "You pick up the room_torch." in feedback
    assert player_char.has_item_in_inventory("room_torch")
    assert initial_room.get_object("room_torch") is None

def test_execute_effects_generate_event(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    # Ensure the torch is in the player's inventory and unlit for the event generation
    torch_obj = GameObject(obj_id="event_torch", name="event_torch", description="a torch", current_location_id=player_char.id, tags=["light_source"], properties={"is_lit": False})
    player_char.add_item_to_inventory(torch_obj)

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "event_torch"}

    feedback = gm._execute_effects(player_char, action_config, params)
    assert "Rogue lights the event_torch." in feedback
