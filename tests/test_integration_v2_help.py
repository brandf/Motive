#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_v2_help_player_only(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_help")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> help\n> pass",
    }):
        gm = GameMaster(config, game_id="it_help", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        p1 = gm.players[0]
        await gm._execute_player_turn(p1, round_num=1)
        # Minimal assertion: no crash and AP is non-negative
        assert p1.character.action_points >= 0


# Note: Category-specific cost/message behavior will be covered in a dedicated test once
# parameter parsing and event routing semantics for help are finalized.


