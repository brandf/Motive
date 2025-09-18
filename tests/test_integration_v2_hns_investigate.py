#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_investigate_basic(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> look\n> investigate \"Quest Board\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_investigate_basic", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        p1, p2 = gm.players[:2]
        # Ensure both players are in adventurer_guild where Quest Board exists
        if p1.character.current_room_id in gm.rooms:
            gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
        if p2.character.current_room_id in gm.rooms:
            gm.rooms[p2.character.current_room_id].remove_player(p2.character.id)
        gm.rooms['adventurer_guild'].add_player(p1.character)
        gm.rooms['adventurer_guild'].add_player(p2.character)

        await gm._execute_player_turn(p1, round_num=1)

        # Assert an investigation-style feedback/event occurred (room broadcast)
        room_msgs = [(getattr(ev, 'message', '') or '').lower() for ev in gm.player_observations.get(p2.character.id, [])]
        assert any('investigates' in m or 'looks around the room' in m for m in room_msgs)

