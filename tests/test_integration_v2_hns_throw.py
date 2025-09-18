#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_throw_torch_to_square_observed_in_target(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> pickup \"Torch\"\n> throw \"Torch\" \"square\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_throw", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]

        # Place both players in Adventurer's Guild (torch is here)
        if p1.character.current_room_id in gm.rooms:
            gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
        if p2.character.current_room_id in gm.rooms:
            gm.rooms[p2.character.current_room_id].remove_player(p2.character.id)
        gm.rooms['adventurer_guild'].add_player(p1.character)
        gm.rooms['adventurer_guild'].add_player(p2.character)

        # Move P2 to Town Square to observe target-room event
        gm.rooms['adventurer_guild'].remove_player(p2.character.id)
        gm.rooms['town_square'].add_player(p2.character)

        await gm._execute_player_turn(p1, round_num=1)

        # P1 no longer has the torch
        assert not p1.character.has_item_in_inventory("Torch")

        # Target room observation received by P2
        p2_obs = gm.player_observations.get(p2.character.id, [])
        assert any(getattr(ev, "source_room_id", None) == "town_square" for ev in p2_obs)



