#!/usr/bin/env python3
"""
Deterministic v2 integration test: movement via exit alias with mocked LLM.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_movement_alias(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_move")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    async def fake_get_response_and_update_history(self, messages_for_llm):
        return type("_AI", (), {"content": "> move east\n> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual")
    ):
        gm = GameMaster(config, game_id="it_move", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        player = gm.players[0]
        start_room_id = player.character.current_room_id
        assert start_room_id in ("room_a", "room_b")

        await gm._execute_player_turn(player, round_num=1)

        end_room_id = player.character.current_room_id
        assert end_room_id != start_room_id
        assert end_room_id in ("room_a", "room_b")


