#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_give_in_same_room(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game_v2.yaml", base_path, validate=True)

    # Turn 1: pickup
    with llm_script({
        "Player_1": "> pickup \"Mayor's Journal\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_give", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]

        # Move both to bank where the journal is located
        for p in (p1, p2):
            old = p.character.current_room_id
            if old in gm.rooms:
                gm.rooms[old].remove_player(p.character.id)
        gm.rooms['bank'].add_player(p1.character)
        gm.rooms['bank'].add_player(p2.character)

        await gm._execute_player_turn(p1, round_num=1)

    # Turn 2: give (address target by actual character name)
    # Restore AP for next action
    p1.character.action_points = gm.game_initializer.initial_ap_per_turn
    target_name = p2.character.name
    with llm_script({
        "Player_1": f"> give \"{target_name}\" \"Mayor's Journal\"\n> pass",
        "Player_2": "> pass",
    }):
        await gm._execute_player_turn(p1, round_num=2)
        # Inventory: p1 no longer has it, p2 should have it
        assert not p1.character.get_item_in_inventory("Mayor's Journal")
        assert p2.character.get_item_in_inventory("Mayor's Journal") is not None


