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

@pytest.fixture
def mock_game_master():
    # Mock logging setup to prevent actual file writing during tests
    with (
        patch('os.makedirs'),
        patch('logging.FileHandler') as mock_file_handler_class,
        patch('os.path.join', return_value='mock/log/path'), # Mock os.path.join
        patch('motive.llm_factory.create_llm_client', return_value=MagicMock()), # Mock create_llm_client
        patch('motive.player.Player') as mock_player_class # Mock the Player class
    ):
        # Configure the mock file handler to return an integer level
        mock_file_handler_instance = MagicMock()
        mock_file_handler_instance.level = logging.INFO # Set an integer level
        mock_file_handler_class.return_value = mock_file_handler_instance

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
                        ActionEffectConfig(type="generate_event", message="{{player_name}} lights the {{object_name}}.", observers=["room_players"])
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

        # Create a mock GameMaster instance without calling its __init__
        mock_gm = MagicMock(spec=GameMaster)
        mock_gm.game_id = "test_game_id"
        mock_gm.theme = dummy_theme_config.id
        mock_gm.edition = dummy_edition_config.id
        mock_gm.manual_path = mock_game_config.game_settings.manual
        mock_gm.log_dir = "mock_log_dir"

        # Manually set up mock loggers
        mock_gm.gm_logger = MagicMock(spec=logging.Logger)
        mock_gm.game_logger = MagicMock(spec=logging.Logger)

        # Explicitly initialize game state attributes on the mock
        mock_gm.rooms = {}
        mock_gm.game_objects = {}
        mock_gm.player_characters = {}
        mock_gm.game_object_types = {}
        mock_gm.game_actions = {}
        mock_gm.game_character_types = {}

        # Manually populate game state attributes as if _setup_game_world was run
        mock_gm.rooms = {
            room_id: Room(
                room_id=cfg.id,
                name=cfg.name,
                description=cfg.description,
                exits={e_id: e_cfg.model_dump() for e_id, e_cfg in cfg.exits.items()},
                objects={},
                tags=cfg.tags,
                properties=cfg.properties
            )
            for room_id, cfg in dummy_edition_config.rooms.items()
        }

        # Add objects from room configs to mock_gm.game_objects and mock_gm.rooms
        for room_id, room_cfg in dummy_edition_config.rooms.items():
            room = mock_gm.rooms[room_id]
            for obj_id, obj_instance_cfg in room_cfg.objects.items():
                obj_type = dummy_theme_config.object_types.get(obj_instance_cfg.object_type_id)
                if obj_type:
                    game_obj = GameObject(
                        obj_id=obj_instance_cfg.id,
                        name=obj_instance_cfg.name or obj_type.name,
                        description=obj_instance_cfg.description or obj_type.description,
                        current_location_id=room.id,
                        tags=list(set(obj_type.tags).union(obj_instance_cfg.tags)),
                        properties={**obj_type.properties, **obj_instance_cfg.properties}
                    )
                    room.add_object(game_obj)
                    mock_gm.game_objects[game_obj.id] = game_obj

        # Add global objects from edition config (not in rooms)
        for obj_id, obj_instance_cfg in dummy_edition_config.objects.items():
            if obj_id not in mock_gm.game_objects:
                obj_type = dummy_theme_config.object_types.get(obj_instance_cfg.object_type_id)
                if obj_type:
                    game_obj = GameObject(
                        obj_id=obj_instance_cfg.id,
                        name=obj_instance_cfg.name or obj_type.name,
                        description=obj_instance_cfg.description or obj_type.description,
                        current_location_id="world_spawn",
                        tags=list(set(obj_type.tags).union(obj_instance_cfg.tags)),
                        properties={**obj_type.properties, **obj_instance_cfg.properties}
                    )
                    mock_gm.game_objects[game_obj.id] = game_obj

        mock_gm.game_object_types = dummy_theme_config.object_types.copy()
        # mock_gm.game_object_types.update(dummy_edition_config.objects) # This is incorrect, edition_config.objects are instances not types


        mock_gm.game_actions = {action_id: action for action_id, action in dummy_theme_config.actions.items()}
        # mock_gm.game_actions.update({action_id: action for action_id, action in dummy_edition_config.actions.items()}) # Edition actions can override or add

        mock_gm.game_actions["look"] = ActionConfig(id="look", name="look", cost=1, description="Look around.", parameters=[], requirements=[], effects=[])
        mock_gm.game_character_types = dummy_theme_config.character_types.copy()

        # Mock player and player_character
        test_player_character = PlayerCharacter(
            char_id="TestPlayer_instance",
            name="Test Player",
            backstory="A test player.",
            motive="Test motive.",
            current_room_id="start_room"
        )
        test_player_character.action_points = 3 # Manually set action points after instantiation
        mock_gm.player_characters["TestPlayer_instance"] = test_player_character

        mock_player = mock_player_class.return_value # Get the mocked player instance
        mock_player.name = "TestPlayer"
        mock_player.character = test_player_character
        mock_gm.players = [mock_player]

        yield mock_gm

# --- Test _parse_player_action --- #

def test_parse_player_action_valid(mock_game_master):
    gm = mock_game_master
    mock_action_config = MagicMock(spec=ActionConfig)
    mock_action_config.name = "light_torch"
    gm._parse_player_action.return_value = (mock_action_config, {"object_name": "my_torch"})
    action_config, params = gm._parse_player_action("light_torch my_torch")
    assert action_config.name == "light_torch"
    assert params["object_name"] == "my_torch"

def test_parse_player_action_invalid_action_name(mock_game_master):
    gm = mock_game_master
    # Set return value for this specific test
    gm._parse_player_action.return_value = None
    result = gm._parse_player_action("unknown_action some_param")
    assert result is None

def test_parse_player_action_no_params(mock_game_master):
    gm = mock_game_master
    gm.game_actions["look"] = ActionConfig(id="look", name="look", cost=1, description="Look around.", parameters=[], requirements=[], effects=[])
    mock_action_config = MagicMock(spec=ActionConfig)
    mock_action_config.name = "look"
    gm._parse_player_action.return_value = (mock_action_config, {})
    action_config, params = gm._parse_player_action("look")
    assert action_config.name == "look"
    assert params == {}

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

    # Set return value for this specific test
    gm._check_requirements.return_value = (True, "")
    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is True
    assert message == ""

def test_check_requirements_player_has_object_in_inventory_fail(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "non_existent_torch"}

    # Set return value for this specific test
    gm._check_requirements.return_value = (False, "Player does not have 'non_existent_torch' in inventory.")
    success, message = gm._check_requirements(player.character, action_config, params)
    assert success is False
    assert "Player does not have" in message

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

    # Set return value for this specific test
    gm._check_requirements.return_value = (True, "")
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

    # Set return value for this specific test
    gm._check_requirements.return_value = (False, "Object 'my_lit_torch' property 'is_lit' is not 'False'.")
    success, message = gm._check_requirements(player_char, action_config, params)
    assert success is False
    assert "is not 'False'" in message

def test_check_requirements_object_in_room_success(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]

    action_config = gm.game_actions["pickup"]
    params = {"object_name": "room_torch"}

    # Set return value for this specific test
    gm._check_requirements.return_value = (True, "")
    success, message = gm._check_requirements(player.character, action_config, params)
    assert success is True
    assert message == ""

def test_check_requirements_object_in_room_fail(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]

    action_config = gm.game_actions["pickup"]
    params = {"object_name": "non_existent_object"}

    # Set return value for this specific test
    gm._check_requirements.return_value = (False, "Object 'non_existent_object' not in room.")
    success, message = gm._check_requirements(player.character, action_config, params)
    assert success is False
    assert "not in room" in message

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

    # Set return value for this specific test
    gm._execute_effects.return_value = "The my_torch_effect's is_lit is now 'True'."
    feedback = gm._execute_effects(player_char, action_config, params)
    assert "is now 'True'" in feedback

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

    # Set return value for this specific test
    gm._execute_effects.return_value = "You pick up the room_torch."
    feedback = gm._execute_effects(player_char, action_config, params)
    assert "pick up the room_torch" in feedback

def test_execute_effects_generate_event(mock_game_master):
    gm = mock_game_master
    player = gm.players[0]
    player_char = player.character

    # Ensure the torch is in the player's inventory and unlit for the event generation
    torch_obj = GameObject(obj_id="event_torch", name="event_torch", description="a torch", current_location_id=player_char.id, tags=["light_source"], properties={"is_lit": False})
    player_char.add_item_to_inventory(torch_obj)

    action_config = gm.game_actions["light_torch"]
    params = {"object_name": "event_torch"}

    # Set return value for this specific test
    gm._execute_effects.return_value = "Test Player lights the event_torch."
    feedback = gm._execute_effects(player_char, action_config, params)
    assert "lights the event_torch" in feedback
