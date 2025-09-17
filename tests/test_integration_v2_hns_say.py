#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_say_event_observed(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game_v2.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> say \"hello\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_say", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]
        # Co-locate players to ensure room broadcast
        p2.character.current_room_id = p1.character.current_room_id

        # Run P1 turn and assert P2 sees the say event
        await gm._execute_player_turn(p1, round_num=1)
        p2_obs = gm.player_observations.get(p2.character.id, [])
        assert any("says:" in (getattr(ev, "message", "") or "") for ev in p2_obs)


