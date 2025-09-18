#!/usr/bin/env python3
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_hns_investigate_readable_journal_broadcast(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> look\n> investigate \"Mayor's Journal\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_investigate_journal", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]

        # Co-locate both players in 'bank' where Mayor's Journal exists
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

        # Room-scoped investigation event should be visible to p2
        p2_msgs = [(getattr(ev, 'message', '') or '').lower() for ev in gm.player_observations.get(p2.character.id, [])]
        assert any('looked at' in m for m in p2_msgs)


@pytest.mark.asyncio
async def test_hns_investigate_guild_desk_broadcast(tmp_path):
    base_path = "configs"
    config = load_and_validate_v2_config("game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> look\n> investigate \"Guild Master's Desk\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="hns_investigate_guild_desk", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) >= 2
        p1, p2 = gm.players[:2]

        # Co-locate both players in 'adventurer_guild'
        if p1.character.current_room_id in gm.rooms:
            gm.rooms[p1.character.current_room_id].remove_player(p1.character.id)
        if p2.character.current_room_id in gm.rooms:
            gm.rooms[p2.character.current_room_id].remove_player(p2.character.id)
        gm.rooms['adventurer_guild'].add_player(p1.character)
        gm.rooms['adventurer_guild'].add_player(p2.character)

        await gm._execute_player_turn(p1, round_num=1)

        # Room-scoped investigation event should be visible to p2
        p2_msgs = [(getattr(ev, 'message', '') or '').lower() for ev in gm.player_observations.get(p2.character.id, [])]
        assert any('looked at' in m for m in p2_msgs)


