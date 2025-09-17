#!/usr/bin/env python3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_move_invalid_exit_no_room_obs(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

    # Self-contained minimal game config
    Path(base_path, "minimal_game.yaml").write_text(
        """
game_settings:
  title: Move Invalid Exit
  rounds: 1
players:
  - name: Player_1
    character_type_id: mover
    provider: dummy
    model: test
  - name: Player_2
    character_type_id: listener
    provider: dummy
    model: test
entity_definitions:
  room_a:
    behaviors: [room]
    attributes:
      name: Room A
      description: A room with no exits.
    properties:
      exits: {}
      objects: {}
  mover:
    behaviors: [character]
    attributes:
      name: Mover
      description: Moves around.
    properties: {}
  listener:
    behaviors: [character]
    attributes:
      name: Listener
      description: Observes movement.
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
        gm = GameMaster(config, game_id="it_move_invalid", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        player_1 = gm.players[0]
        other_player = gm.players[1]
        start_room = player_1.character.current_room_id

        await gm._execute_player_turn(player_1, round_num=1)

        # No exits: movement should fail; player stays in same room
        assert player_1.character.current_room_id == start_room

        # Other player should not receive a move-specific room event
        obs = gm.player_observations.get(other_player.character.id, [])
        assert not any("moves" in (o.get("message") or "") for o in obs)


