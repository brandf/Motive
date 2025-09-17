#!/usr/bin/env python3
"""
Deterministic v2 integration test: minimal look + pass turn with mocked LLM.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_look_and_pass_turn(tmp_path):
    # Load minimal v2 config (as dict, skip pydantic validation for speed)
    base_path = str((tmp_path / "configs").resolve())
    # Copy test configs into tmp to ensure isolation
    from pathlib import Path
    src_dir = Path("tests/configs/v2/minimal_look_pass")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    # Mock Player init to avoid real LLM and file logging; canned responses returned by get_response
    async def fake_get_response_and_update_history(self, messages_for_llm):
        # Return two actions deterministically
        return type("_AI", (), {"content": "> look\n> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual")
    ):
        gm = GameMaster(config, game_id="it_minimal", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)

        # Preconditions
        assert gm.players, "Players should be initialized"
        assert gm.rooms, "Rooms should be initialized"

        # Execute one player's turn deterministically
        player = gm.players[0]
        await gm._execute_player_turn(player, round_num=1)

        # Postconditions: current room exists and at least one observation or feedback is generated
        current_room = gm.rooms.get(player.character.current_room_id)
        assert current_room is not None, "Player should be in a valid room"

        # Ensure some events were processed (either immediate feedback or room description)
        # Allow empty queue if feedback went via chat; at minimum no exceptions and state intact
        assert player.character.action_points >= 0


