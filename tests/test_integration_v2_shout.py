#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_v2_shout_adjacent(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_shout")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> shout \"hey\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_shout", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) == 2
        p1, p2 = gm.players
        # Place players in adjacent rooms
        rooms = list(gm.rooms.keys())
        assert len(rooms) == 2
        p1.character.current_room_id = rooms[0]
        p2.character.current_room_id = rooms[1]

        await gm._execute_player_turn(p1, round_num=1)
        obs = gm.player_observations.get(p2.character.id, [])
        assert any("shouts:" in ev.message for ev in obs), f"Expected shout event for Player_2, got: {[getattr(ev,'message',None) for ev in obs]}"


@pytest.mark.asyncio
async def test_minimal_v2_shout_no_adjacent_hear(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_shout")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> shout \"hey\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_shout_neg", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) == 2
        p1, p2 = gm.players
        rooms = list(gm.rooms.keys())
        # Place p1 in room_a and move p2 to an isolated room with no adjacency
        p1.character.current_room_id = rooms[0]
        from motive.room import Room
        isolated_id = "isolated_neg_shout"
        gm.rooms[isolated_id] = Room(room_id=isolated_id, name="Isolated", description="", exits={}, objects={})
        p2.character.current_room_id = isolated_id

        await gm._execute_player_turn(p1, round_num=1)
        obs = gm.player_observations.get(p2.character.id, [])
        assert not any("shouts:" in getattr(ev, 'message', '') for ev in obs)

