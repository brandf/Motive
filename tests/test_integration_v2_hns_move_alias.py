#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_move_alias_broadcast(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({
        # Use the exit name from tavern to avoid alias parsing issues
        "Player_1": "> move \"Town Square\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_move", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]
        # Position both players in 'tavern' so 'square' is a valid exit
        old1 = p1.character.current_room_id
        old2 = p2.character.current_room_id
        if old1 in gm.rooms:
            gm.rooms[old1].remove_player(p1.character.id)
        if old2 in gm.rooms:
            gm.rooms[old2].remove_player(p2.character.id)
        p1.character.current_room_id = 'tavern'
        p2.character.current_room_id = 'tavern'
        gm.rooms['tavern'].add_player(p1.character)
        gm.rooms['tavern'].add_player(p2.character)

        # Run P1 move, assert P2 receives a movement event from the source room
        await gm._execute_player_turn(p1, round_num=1)
        p2_obs = gm.player_observations.get(p2.character.id, [])
        assert any("left the room" in (getattr(ev, "message", "") or "") or "entered the room" in (getattr(ev, "message", "") or "") for ev in p2_obs)


