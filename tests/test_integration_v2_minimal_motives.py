#!/usr/bin/env python3
"""
Deterministic v2 integration test: motive success via set_property effect.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_motive_success(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_motives")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    # Use validate=False to preserve attributes in v2 YAML for this minimal test
    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=False)

    async def fake_get_response_and_update_history(self, messages_for_llm):
        return type("_AI", (), {"content": "> look\n> solve\n> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual")
    ):
        # load_and_validate_v2_config(validate=False) returns a dict, so wrap players to Pydantic path: reuse validated players from a small shim
        # Instead, call validate=True once to extract typed players, then merge entity_definitions from raw dict
        typed = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)
        merged = config
        merged["players"] = [
            {"name": p.name, "provider": p.provider, "model": p.model}
            for p in typed.players
        ]
        gm = GameMaster(merged, game_id="it_motives", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        player = gm.players[0]

        # Initially motive should not succeed
        assert not player.character.check_motive_success(gm)

        initial_ap = merged['game_settings']['initial_ap_per_turn']
        player.character.action_points = initial_ap
        await gm._execute_player_turn(player, round_num=1)

        # After solve action, motive success should be true
        assert player.character.check_motive_success(gm)
        msg = player.character.get_motive_status_message(gm)
        assert msg and msg.startswith("✅ **Case Outlook:**")


