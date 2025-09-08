import pytest
import yaml
from motive.config import (
    GameConfig,
    GameSettings,
    PlayerConfig,
    ThemeConfig,
    EditionConfig,
    ObjectTypeConfig,
    ActionConfig,
    ActionRequirementConfig,
    ActionEffectConfig,
    RoomConfig,
    ExitConfig,
    ObjectInstanceConfig,
    CharacterConfig,
    ParameterConfig
)

# --- Test individual Pydantic Models --- #

def test_player_config_valid():
    config = PlayerConfig(name="TestPlayer", provider="mock", model="mock-model")
    assert config.name == "TestPlayer"

def test_parameter_config_valid():
    config = ParameterConfig(name="object_name", type="string", description="The object.")
    assert config.name == "object_name"

def test_action_requirement_config_valid():
    config = ActionRequirementConfig(type="player_has_tag", tag="has_key")
    assert config.type == "player_has_tag"
    assert config.tag == "has_key"

def test_action_effect_config_valid():
    config = ActionEffectConfig(type="add_tag", target_type="player", tag="has_torch_effect")
    assert config.type == "add_tag"
    assert config.target_type == "player"

def test_action_config_valid():
    config = ActionConfig(
        id="look",
        name="look",
        cost=1,
        description="Look around.",
        parameters=[ParameterConfig(name="direction", type="string", description="direction")],
        requirements=[ActionRequirementConfig(type="player_in_room")],
        effects=[ActionEffectConfig(type="generate_event", message="You see things.")]
    )
    assert config.id == "look"
    assert len(config.parameters) == 1

def test_action_config_minimum_cost():
    # Now that conint(gt=0) is removed, 0 is a valid cost
    action_data = {
        "id": "test_action",
        "name": "test action",
        "cost": 0, # Should now be valid
        "description": "A test action."
    }
    action = ActionConfig(**action_data)
    assert action.cost == 0

def test_object_type_config_valid():
    config = ObjectTypeConfig(id="torch", name="Torch", description="A light source.", tags=["light"], properties={"is_lit": False})
    assert config.id == "torch"
    assert "light" in config.tags

def test_object_instance_config_valid():
    config = ObjectInstanceConfig(id="my_torch", name="My Torch", object_type_id="torch", current_room_id="room1")
    assert config.object_type_id == "torch"

def test_exit_config_valid():
    config = ExitConfig(id="east_exit", name="East Exit", destination_room_id="room2")
    assert config.destination_room_id == "room2"

def test_room_config_valid():
    config = RoomConfig(
        id="room1",
        name="Starting Room",
        description="A dim room.",
        exits={"east": ExitConfig(id="east_exit", name="East Exit", destination_room_id="room2")},
        objects={"torch": ObjectInstanceConfig(id="torch_instance", name="Torch", object_type_id="torch")}
    )
    assert config.id == "room1"
    assert "east" in config.exits

def test_character_config_valid():
    config = CharacterConfig(id="hero", name="Hero", backstory="A brave one.", motive="Find treasure.")
    assert config.id == "hero"

def test_theme_config_valid():
    config = ThemeConfig(
        id="fantasy",
        name="Fantasy Theme",
        object_types={"torch": ObjectTypeConfig(id="torch", name="Torch", description="A light source.")},
        actions={"look": ActionConfig(id="look", name="look", cost=1, description="Look around.")},
        character_types={"hero": CharacterConfig(id="hero", name="Hero", backstory="A brave one.", motive="Win.")}
    )
    assert config.id == "fantasy"
    assert "torch" in config.object_types

def test_edition_config_valid():
    config = EditionConfig(
        id="hearth_and_shadow",
        name="Hearth and Shadow",
        theme_id="fantasy",
        rooms={"start_room": RoomConfig(id="start_room", name="Start", description="A room.")},
        objects={"key": ObjectInstanceConfig(id="key_instance", name="Key", object_type_id="key")},
        characters={"rogue": CharacterConfig(id="rogue", name="Rogue", backstory="Stealthy.", motive="Steal.")}
    )
    assert config.id == "hearth_and_shadow"
    assert "start_room" in config.rooms

def test_game_settings_valid():
    settings = GameSettings(num_rounds=5, core_config_path="core.yaml", theme_config_path="theme.yaml", edition_config_path="edition.yaml", manual="manual.md", initial_ap_per_turn=20)
    assert settings.num_rounds == 5
    assert settings.initial_ap_per_turn == 20

def test_game_config_valid():
    game_config = GameConfig(
        game_settings=GameSettings(num_rounds=5, core_config_path="core.yaml", theme_config_path="theme.yaml", edition_config_path="edition.yaml", manual="manual.md", initial_ap_per_turn=20),
        players=[PlayerConfig(name="Player1", provider="mock", model="mock-model")]
    )
    assert game_config.players[0].name == "Player1"

# --- Test YAML Loading --- #

def test_load_theme_config_from_yaml():
    yaml_content = """
id: fantasy
name: Fantasy Theme
object_types:
  torch:
    id: torch
    name: Torch
    description: A simple wooden torch
    tags: ["light_source"]
    properties:
      is_lit: false
actions:
  look:
    id: look
    name: look
    cost: 1
    description: Look around
    parameters: []
    requirements: []
    effects: []
character_types:
  hero:
    id: hero
    name: Hero
    backstory: A brave adventurer
    motive: Defeat the evil sorcerer
"""
    config_data = yaml.safe_load(yaml_content)
    theme_config = ThemeConfig(**config_data)
    assert theme_config.id == "fantasy"
    assert "torch" in theme_config.object_types
    assert theme_config.object_types["torch"].name == "Torch"

def test_load_edition_config_from_yaml():
    yaml_content = """
id: hearth_and_shadow
name: Hearth and Shadow
theme_id: fantasy
rooms:
  town_square:
    id: town_square
    name: Town Square
    description: A bustling town square
    exits:
      west_gate: {id: west_gate, name: West Gate, destination_room_id: old_forest_path}
    objects:
      fountain: {id: fountain, name: Fountain, object_type_id: fountain}
characters:
  elara:
    id: elara
    name: Elara
    backstory: A stealthy rogue
    motive: Steal the Amulet
"""
    config_data = yaml.safe_load(yaml_content)
    edition_config = EditionConfig(**config_data)
    assert edition_config.id == "hearth_and_shadow"
    assert "town_square" in edition_config.rooms
    assert edition_config.rooms["town_square"].name == "Town Square"

def test_load_game_config_from_yaml():
    yaml_content = """
game_settings:
  num_rounds: 3
  core_config_path: "configs/core.yaml"
  theme_config_path: "configs/themes/fantasy.yaml"
  edition_config_path: "configs/editions/hearth_and_shadow.yaml"
  manual: "MOTIVE_MANUAL.md"
  initial_ap_per_turn: 20
players:
  - name: "Arion"
    provider: "google"
    model: "gemini-2.5-flash"
"""
    config_data = yaml.safe_load(yaml_content)
    game_config = GameConfig(**config_data)
    assert game_config.game_settings.num_rounds == 3
    assert game_config.game_settings.initial_ap_per_turn == 20
    assert game_config.players[0].name == "Arion"

def test_load_game_config_invalid_num_rounds():
    yaml_content = """
game_settings:
  num_rounds: 0
  theme_config_path: "configs/themes/fantasy.yaml"
  edition_config_path: "configs/editions/hearth_and_shadow.yaml"
  manual: "MOTIVE_MANUAL.md"
players:
  - name: "Arion"
    provider: "google"
    model: "gemini-2.5-flash"
"""
    config_data = yaml.safe_load(yaml_content)
    with pytest.raises(ValueError):
        GameConfig(**config_data)
