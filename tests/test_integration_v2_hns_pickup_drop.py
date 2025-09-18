#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_pickup_and_drop_broadcast(tmp_path):
    # Use real H&S content: Bank contains "Mayor's Journal" which is pickupable
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    # Turn 1: pickup
    with llm_script({
        "Player_1": "> pickup \"Mayor's Journal\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_pickup_drop", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]

        # Co-locate both players in bank where the journal exists
        for p in (p1, p2):
            old = p.character.current_room_id
            if old in gm.rooms:
                gm.rooms[old].remove_player(p.character.id)
        gm.rooms['bank'].add_player(p1.character)
        gm.rooms['bank'].add_player(p2.character)

        await gm._execute_player_turn(p1, round_num=1)
        p2_obs = gm.player_observations.get(p2.character.id, [])
        messages = [getattr(ev, "message", "") or "" for ev in p2_obs]
        assert any("picks up the Mayor's Journal" in m for m in messages), messages

    # Turn 2: drop
    # Top up AP for next round since previous block ended the turn
    p1.character.action_points = gm.game_initializer.initial_ap_per_turn
    with llm_script({
        "Player_1": "> drop \"Mayor's Journal\"\n> pass",
        "Player_2": "> pass",
    }):
        await gm._execute_player_turn(p1, round_num=2)
        p2_obs = gm.player_observations.get(p2.character.id, [])
        messages = [getattr(ev, "message", "") or "" for ev in p2_obs]
        assert any("drops the Mayor's Journal" in m for m in messages), messages


