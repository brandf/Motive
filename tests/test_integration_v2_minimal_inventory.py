#!/usr/bin/env python3
"""
Deterministic v2 integration test: pickup and drop in a minimal room.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_inventory_pickup_drop(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_inventory")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    async def fake_get_response_and_update_history(self, messages_for_llm):
        return type("_AI", (), {"content": "> look\n> pickup \"Note\"\n> look inventory\n> drop \"Note\"\n> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual")
    ):
        gm = GameMaster(config, game_id="it_inventory", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        player = gm.players[0]
        start_room = gm.rooms.get(player.character.current_room_id)
        assert start_room is not None

        # Ensure note is present initially
        assert any(obj.name == "Note" for obj in start_room.objects.values())

        await gm._execute_player_turn(player, round_num=1)

        # After pickup and drop, the Note should be back in the room
        end_room = gm.rooms.get(player.character.current_room_id)
        assert end_room is not None
        assert any(obj.name == "Note" for obj in end_room.objects.values())


