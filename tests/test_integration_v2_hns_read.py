#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_read_room_object_event(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game_v2.yaml", base_path, validate=True)

    with llm_script({
        # 'Mayor's Journal' object is in 'bank' per migrated rooms
        "Player_1": "> read \"Mayor's Journal\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_read", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]
        # Move both players to 'bank' where Mayor's Journal exists
        old1 = p1.character.current_room_id
        old2 = p2.character.current_room_id
        if old1 in gm.rooms:
            gm.rooms[old1].remove_player(p1.character.id)
        if old2 in gm.rooms:
            gm.rooms[old2].remove_player(p2.character.id)
        p1.character.current_room_id = 'bank'
        p2.character.current_room_id = 'bank'
        gm.rooms['bank'].add_player(p1.character)
        gm.rooms['bank'].add_player(p2.character)

        await gm._execute_player_turn(p1, round_num=1)
        p2_obs = gm.player_observations.get(p2.character.id, [])
        # Read alias redirects to look, so check for "looked at" message
        combined = p2_obs + gm.player_observations.get(p1.character.id, [])
        assert any("looked at" in (getattr(ev, "message", "") or "") for ev in combined)


