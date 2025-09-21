#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_v2_movement_structure(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    (Path(base_path)).mkdir(parents=True, exist_ok=True)

    Path(base_path, "actions.yaml").write_text(
        """
action_definitions:
  move:
    name: move
    description: Move between rooms.
    cost: 1
    category: navigation
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
        observers:
          - player
          - room_characters
""",
        encoding="utf-8",
    )

    Path(base_path, "rooms.yaml").write_text(
        """
entity_definitions:
  r1:
    behaviors: [room]
    attributes:
      name: R1
      description: Room 1
    properties:
      exits:
        east:
          id: east
          name: East Door
          destination_room_id: r2
          aliases: ["east", "e"]
      objects: {}
  r2:
    behaviors: [room]
    attributes:
      name: R2
      description: Room 2
    properties:
      exits:
        west:
          id: west
          name: West Door
          destination_room_id: r1
          aliases: ["west", "w"]
      objects: {}
""",
        encoding="utf-8",
    )

    Path(base_path, "characters.yaml").write_text(
        """
entity_definitions:
  c1:
    behaviors: [character]
    attributes:
      name: Walker
      backstory: test
      motives:
        - id: test_motive
          description: Test motive for movement structure
          success_conditions: []
          failure_conditions: []
""",
        encoding="utf-8",
    )

    Path(base_path, "game.yaml").write_text(
        """
includes:
  - actions.yaml
  - rooms.yaml
  - characters.yaml

game_settings:
  num_rounds: 1
  initial_ap_per_turn: 3
  manual: "../docs/MANUAL.md"

players:
  - name: "Walker"
    provider: "dummy"
    model: "test"
""",
        encoding="utf-8",
    )

    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({"Walker": "> move east"}):
        gm = GameMaster(config, game_id="it_move_struct", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        p = gm.players[0]
        start_room = p.character.current_room_id
        await gm._execute_player_turn(p, round_num=1)
        end_room = p.character.current_room_id
        assert start_room != end_room

