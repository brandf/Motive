#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_two_object_use_unlocks_target(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

    Path(base_path, "game.yaml").write_text(
        """
game_settings:
  title: Minimal Two-Object Use
  num_rounds: 1
  initial_ap_per_turn: 50
  manual: manual.md
  log_path: minimal/{game_id}

players:
  - name: Player_1
    character_type_id: tester
    provider: dummy
    model: test

entity_definitions:
  room:
    behaviors: [room]
    attributes:
      name: Room
      description: A room with a locked chest.
    properties:
      exits: {}
      objects:
        Key:
          id: key_inst
          name: Key
          object_type_id: key
          current_room_id: room
          description: A small key.
        Chest:
          id: chest_inst
          name: Chest
          object_type_id: chest
          current_room_id: room
          description: A wooden chest.
  tester:
    behaviors: [character]
    attributes:
      name: Tester
      description: A test character.
    properties: {}

  key:
    behaviors: [object]
    attributes:
      name: Key
      description: A key.
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
              - type: generate_event
                message: '{player_name} unlocks the {target_name}.'
                observers: [room_characters]

  chest:
    behaviors: [object]
    attributes:
      name: Chest
      description: A chest that can be locked.
    properties:
      pickupable: false
      is_locked: true

action_definitions:
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

    with llm_script({
            "Player_1": "> pickup \"Key\"\n> use Key on Chest\n> pass",
    }):
        gm = GameMaster(config, game_id="min_two_use", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        p1 = gm.players[0]
        # Ensure player is in the only room
        if p1.character.current_room_id != 'room':
            if p1.character.current_room_id in gm.rooms:
                gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
            gm.rooms['room'].add_player(p1.character)
        await gm._execute_player_turn(p1, round_num=1)
        # Validate chest unlocked
        chest = gm.rooms['room'].get_object('Chest')
        is_locked = False
        if chest is not None:
            try:
                is_locked = bool(chest.get_property('is_locked', False))
            except Exception:
                is_locked = bool(getattr(chest, 'properties', {}).get('is_locked', False))
        assert is_locked is False


