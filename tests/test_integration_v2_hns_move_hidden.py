#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_move_hidden_exit_blocked(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> move thieves\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_move_hidden", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 1
        p1 = gm.players[0]

        # Place P1 in tavern; thieves_den exit is hidden from tavern
        if p1.character.current_room_id in gm.rooms:
            gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
        gm.rooms['tavern'].add_player(p1.character)
        start_room = p1.character.current_room_id

        await gm._execute_player_turn(p1, round_num=1)

        # Hidden exit should prevent movement
        assert p1.character.current_room_id == start_room



