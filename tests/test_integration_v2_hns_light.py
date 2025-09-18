#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_light_torch_room_observed(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game_v2.yaml", base_path, validate=True)

    gm = None
    # Turn 1: instantiate GM and pick up Torch in adventurer_guild
    with llm_script({
        "Player_1": "> pickup \"Torch\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_light", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]
        # Co-locate in adventurer_guild where Torch exists
        if p1.character.current_room_id in gm.rooms:
            gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
        if p2.character.current_room_id in gm.rooms:
            gm.rooms[p2.character.current_room_id].remove_player(p2.character.id)
        gm.rooms['adventurer_guild'].add_player(p1.character)
        gm.rooms['adventurer_guild'].add_player(p2.character)
        await gm._execute_player_turn(p1, round_num=1)
        assert p1.character.has_item_in_inventory("Torch")

    # Move P1 and P2 to a dark room (underground_tunnels)
    p1 = gm.players[0]
    p2 = gm.players[1]
    gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
    gm.rooms[p2.character.current_room_id].remove_player(p2.character.id)
    gm.rooms['underground_tunnels'].add_player(p1.character)
    gm.rooms['underground_tunnels'].add_player(p2.character)
    assert bool(getattr(gm.rooms['underground_tunnels'], 'properties', {}).get('dark', False)) is True

    # Turn 2: look only (should be dark, private to P1)
    # Reset AP for manual turn execution
    p1.character.action_points = gm.game_config['game_settings']['initial_ap_per_turn'] if isinstance(gm.game_config, dict) else gm.game_config.game_settings.initial_ap_per_turn
    with llm_script({
        "Player_1": "> look\n> pass",
        "Player_2": "> pass",
    }):
        await gm._execute_player_turn(p1, round_num=2)
        p1_obs = gm.player_observations.get(p1.character.id, [])
        messages = [(getattr(ev, 'message', '') or '').lower() for ev in p1_obs]
        assert any('struggles to see' in m or 'too dark' in m for m in messages)

    # Turn 3: use Torch to light it
    p1.character.action_points = gm.game_config['game_settings']['initial_ap_per_turn'] if isinstance(gm.game_config, dict) else gm.game_config.game_settings.initial_ap_per_turn
    with llm_script({
        "Player_1": "> use \"Torch\"\n> pass",
        "Player_2": "> pass",
    }):
        await gm._execute_player_turn(p1, round_num=3)
        # Torch should toggle lit state; check property
        torch_obj = p1.character.get_item_in_inventory("Torch")
        lit_state = False
        if torch_obj is not None:
            try:
                lit_state = bool(torch_obj.get_property('is_lit', False))
            except Exception:
                lit_state = bool(getattr(torch_obj, 'properties', {}).get('is_lit', False))
        assert lit_state is True

    # Turn 4: look again; now P2 should observe room broadcast of look
    p1.character.action_points = gm.game_config['game_settings']['initial_ap_per_turn'] if isinstance(gm.game_config, dict) else gm.game_config.game_settings.initial_ap_per_turn
    with llm_script({
        "Player_1": "> look\n> pass",
        "Player_2": "> pass",
    }):
        await gm._execute_player_turn(p1, round_num=4)
        p2_obs = gm.player_observations.get(p2.character.id, [])
        assert any('looks around the room' in (getattr(ev, 'message', '') or '').lower() for ev in p2_obs)


