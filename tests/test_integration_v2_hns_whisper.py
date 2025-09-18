#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_whisper_private(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> whisper \"Player_2\" \"secret\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_whisper", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]
        # Ensure same room for whisper
        p2.character.current_room_id = p1.character.current_room_id

        # Run P1 turn: whisper generates a player-scoped event for the target only
        await gm._execute_player_turn(p1, round_num=1)
        p1_obs = gm.player_observations.get(p1.character.id, [])
        p2_obs = gm.player_observations.get(p2.character.id, [])
        # Speaker should not receive the private whisper event
        assert not any("whispers" in (getattr(ev, "message", "") or "") for ev in p1_obs)
        # Target should receive the private whisper event
        assert any("whispers to you" in (getattr(ev, "message", "") or "") and "secret" in (getattr(ev, "message", "") or "") for ev in p2_obs)


