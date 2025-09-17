#!/usr/bin/env python3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_player_initialization_and_pass(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

    # Self-contained minimal game config
    Path(base_path, "minimal_game.yaml").write_text(
        """
game_settings:
  title: Player Init Minimal
  rounds: 1
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
      description: A simple room.
    properties:
      exits: {}
      objects: {}
  tester:
    behaviors: [character]
    attributes:
      name: Tester
      description: A testing character.
    properties: {}
action_definitions:
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
        return type("_AI", (), {"content": "> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual"),
    ):
        gm = GameMaster(config, game_id="it_player_minimal", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)

        # One player created, character assigned, starts in a valid room
        assert len(gm.players) == 1
        player = gm.players[0]
        assert player.name == "Player_1"
        assert player.character is not None
        assert player.character.current_room_id == "room_a"

        # Execute a turn to ensure no crashes with mocked LLM
        await gm._execute_player_turn(player, round_num=1)


