#!/usr/bin/env python3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_move_hidden_exit_fails(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

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
          - room_players
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

    Path(base_path, "rooms.yaml").write_text(
        """
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
      objects: {}
  room_b:
    behaviors: [room]
    attributes:
      name: Room B
      description: Destination room.
    properties:
      exits: {}
      objects: {}
""",
        encoding="utf-8",
    )

    Path(base_path, "characters.yaml").write_text(
        """
entity_definitions:
  mover:
    behaviors: [character]
    attributes:
      name: Mover
      description: Moves around.
    properties: {}
""",
        encoding="utf-8",
    )

    Path(base_path, "game.yaml").write_text(
        """
game_settings:
  title: Move Hidden Exit
  rounds: 1
players:
  - name: Player_1
    character_type_id: mover
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
    provider: dummy
    model: test
entity_definitions: {}
action_definitions:
  <<: *id001
""",
        encoding="utf-8",
    )

    # Self-contained minimal game config
    Path(base_path, "minimal_game.yaml").write_text(
        """
game_settings:
  title: Move Hidden Exit
  rounds: 1
players:
  - name: Player_1
    character_type_id: mover
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
      objects: {}
  room_b:
    behaviors: [room]
    attributes:
      name: Room B
      description: Destination room.
    properties:
      exits: {}
      objects: {}
  mover:
    behaviors: [character]
    attributes:
      name: Mover
      description: Moves around.
    properties: {}
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
          - room_players
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

    async def fake_get_response_and_update_history(self, messages_for_llm):
        return type("_AI", (), {"content": "> move east\n> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual"),
    ):
        gm = GameMaster(config, game_id="it_move_hidden", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        player = gm.players[0]
        start_room = player.character.current_room_id
        await gm._execute_player_turn(player, round_num=1)
        # Hidden exit should not be usable -> still in same room
        assert player.character.current_room_id == start_room


