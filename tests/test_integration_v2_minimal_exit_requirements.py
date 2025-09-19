#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_exit_visibility_and_travel_requirements(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

    Path(base_path, "game.yaml").write_text(
        """
game_settings:
  title: Minimal Exit Requirements
  num_rounds: 2
  initial_ap_per_turn: 50
  manual: manual.md
  log_path: minimal/{game_id}

players:
  - name: Player_1
    character_type_id: tester
    provider: dummy
    model: test

entity_definitions:
  room_a:
    behaviors: [room]
    attributes:
      name: Room A
      description: A dark chamber.
    properties:
      exits:
        east:
          id: east
          name: East
          destination_room_id: room_b
          aliases: [east]
          visibility_requirements:
            - type: character_has_property
              property: can_see_secret
              value: true
          travel_requirements:
            - type: character_has_property
              property: can_see_secret
              value: true
      objects:
        Gate:
          id: gate_obj
          name: Gate
          object_type_id: gate
          current_room_id: room_a
          description: A sturdy gate blocks the way east.
          properties:
            is_locked: true
            pickupable: false
        Key:
          id: key_inst
          name: Key
          object_type_id: key
          current_room_id: room_a
          description: A simple key lies here.
          properties:
            interactions:
              use:
                - when:
                    target_has_property:
                      property: is_locked
                      equals: true
                  effects:
                    - type: set_property
                      target: target
                      property: is_locked
                      value: false
                    - type: set_property
                      target: player
                      property: can_see_secret
                      value: true
  room_b:
    behaviors: [room]
    attributes:
      name: Room B
      description: The other side of the gate.
    properties:
      exits: {}
      objects: {}
  tester:
    behaviors: [character]
    attributes:
      name: Tester
      description: A test character.
    properties: {}

  gate:
    behaviors: [object]
    attributes:
      name: Gate
      description: A gate that can be unlocked.
    properties:
      pickupable: false
      is_locked: true

  key:
    behaviors: [object]
    attributes:
      name: Key
      description: A key that unlocks things.
    properties:
      pickupable: true
      interactions:
        use:
          - when:
              target_has_property:
                property: is_locked
                equals: true
            effects:
              - type: set_property
                target: target
                property: is_locked
                value: false
              - type: set_property
                target: player
                property: can_see_secret
                value: true
              - type: generate_event
                message: '{player_name} unlocks the {target_name}.'
                observers: [room_characters]

action_definitions:
  look:
    name: look
    description: Look around.
    cost: 5
    category: observation
    parameters:
      - name: target
        type: string
        description: Optional target
        required: false
        default_value: null
    requirements: []
    effects:
      - type: code_binding
        function_name: look_at_target
  move:
    name: move
    description: Move in a direction.
    cost: 10
    category: movement
    parameters:
      - name: direction
        type: string
        description: Direction to move
        required: true
        default_value: null
    requirements:
      - type: exit_exists
        direction_param: direction
    effects:
      - type: code_binding
        function_name: handle_move_action
  pickup:
    name: pickup
    description: Pick up an object.
    cost: 5
    category: inventory
    parameters:
      - name: object_name
        type: string
        description: Object to pick up
        required: true
        default_value: null
    requirements:
      - type: object_in_room
        object_name_param: object_name
    effects:
      - type: code_binding
        function_name: handle_pickup_action
  use:
    name: use
    description: Use an object in inventory, optionally on a target.
    cost: 5
    category: interaction
    parameters:
      - name: object_name
        type: string
        description: Object to use
        required: true
        default_value: null
      - name: target
        type: string
        description: Optional target to use on
        required: false
        default_value: null
    requirements:
      - type: object_in_inventory
        object_name_param: object_name
    effects:
      - type: code_binding
        function_name: handle_use_action
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

    Path(base_path, "manual.md").write_text("Testing manual", encoding="utf-8")

    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    # Single turn: pickup key, use on gate (which sets can_see_secret), then move
    with llm_script({
        "Player_1": "> pickup \"Key\"\n> use Key on Gate\n> move east\n> pass",
    }):
        gm = GameMaster(config, game_id="min_exit_reqs", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        p1 = gm.players[0]
        if p1.character.current_room_id in gm.rooms:
            gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
        gm.rooms['room_a'].add_player(p1.character)
        await gm._execute_player_turn(p1, round_num=1)
        assert p1.character.current_room_id == 'room_b'


