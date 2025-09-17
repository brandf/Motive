#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_v2_say_broadcast(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_say")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    # Player_1 will say; Player_2 listens in same room
    with llm_script({
        "Player_1": "> say \"hello\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_say", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)

        # Sanity: two players
        assert len(gm.players) == 2
        p1, p2 = gm.players
        # Force both players to same starting room
        p2.character.current_room_id = p1.character.current_room_id

        # Run P1 turn and assert P2 received the observation (before P2 consumes it)
        await gm._execute_player_turn(p1, round_num=1)
        p2_obs = gm.player_observations.get(p2.character.id, [])
        assert any("says:" in ev.message for ev in p2_obs), f"Expected say event for Player_2, got: {[getattr(ev,'message',None) for ev in p2_obs]}"


