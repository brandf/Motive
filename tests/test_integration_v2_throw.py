#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_v2_throw_adjacent(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_throw")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> pickup \"Rock\"\n> throw \"Rock\" \"east\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_throw", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) == 2
        p1, p2 = gm.players
        rooms = list(gm.rooms.keys())
        p1.character.current_room_id = rooms[0]
        p2.character.current_room_id = rooms[1]

        await gm._execute_player_turn(p1, round_num=1)
        obs = gm.player_observations.get(p2.character.id, [])
        # Throw uses observers: player, room_players, adjacent_rooms (core); assert adjacent heard something
        assert len(obs) >= 1


