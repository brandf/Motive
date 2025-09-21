#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_v2_throw_hidden_exit_no_adjacent(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

    Path(base_path, "minimal_game.yaml").write_text(
        """
game_settings:
  title: Throw Hidden Exit
  rounds: 1
players:
  - name: Player_1
    character_type_id: thrower
    provider: dummy
    model: test
  - name: Player_2
    character_type_id: receiver
    provider: dummy
    model: test
entity_definitions:
  room_a:
    behaviors: [room]
    attributes:
      name: Room A
      description: A room with a hidden exit.
    properties:
      exits:
        east:
          id: east
          name: East Door
          destination_room_id: room_b
          aliases: ["east", "e"]
          is_hidden: true
      objects:
        rock_1:
          id: rock_1
          name: Rock
          object_type_id: rock_type
          current_room_id: room_a
          description: A throwable rock.
          properties: {}
  room_b:
    behaviors: [room]
    attributes:
      name: Room B
      description: Destination room.
    properties:
      exits: {}
      objects: {}
  thrower:
    behaviors: [character]
    attributes:
      name: Thrower
      description: Throws rocks.
      motives:
        - id: test_motive
          description: Test motive for hidden exit throwing
          success_conditions: []
          failure_conditions: []
    properties: {}
  receiver:
    behaviors: [character]
    attributes:
      name: Receiver
      description: Listens in the other room.
      motives:
        - id: test_motive
          description: Test motive for hidden exit throwing
          success_conditions: []
          failure_conditions: []
    properties: {}
  rock_type:
    behaviors: [object]
    attributes:
      name: Rock Type
      description: Type for rock.
    properties: {}
action_definitions:
  pickup:
    name: pickup
    description: Pick up an object from the room.
    cost: 1
    category: inventory
    parameters:
      - name: object_name
        type: string
        description: Name of the object to pick up
        required: true
        default_value: null
    requirements:
      - type: object_in_room
        object_name_param: object_name
    effects:
      - type: code_binding
        function_name: handle_pickup_action
        observers:
          - player
  throw:
    name: throw
    description: Throw an object through an exit.
    cost: 1
    category: inventory
    parameters:
      - name: object_name
        type: string
        description: Name of the object to throw
        required: true
        default_value: null
      - name: exit
        type: string
        description: Exit/direction to throw through
        required: true
        default_value: null
    requirements:
      - type: object_in_inventory
        object_name_param: object_name
      - type: exit_exists
        direction_param: exit
    effects:
      - type: code_binding
        function_name: handle_throw_action
        observers:
          - player
          - room_characters
          - adjacent_rooms_characters
  pass:
    name: pass
    description: End turn.
    cost: -1
    category: system
    parameters: []
    requirements: []
    effects: []
""",
        encoding="utf-8",
    )

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> pickup \"Rock\"\n> throw \"Rock\" \"east\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_throw_hidden", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        p1, p2 = gm.players
        rooms = list(gm.rooms.keys())
        p1.character.current_room_id = rooms[0]
        p2.character.current_room_id = rooms[1]

        await gm._execute_player_turn(p1, round_num=1)
        # Hidden exit prevents throw effect; no adjacent event
        obs = gm.player_observations.get(p2.character.id, [])
        assert not any((" throws " in getattr(ev, 'message', '').lower()) or (" is thrown " in getattr(ev, 'message', '').lower()) for ev in obs)


