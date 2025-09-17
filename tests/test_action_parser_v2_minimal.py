#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.action_parser import parse_player_response
from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


def _bootstrap_minimal_config(tmp_path, fixture_dir: str):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path(fixture_dir)
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    return base_path


@pytest.mark.asyncio
async def test_action_parser_pickup_strips_quotes(tmp_path):
    base_path = _bootstrap_minimal_config(tmp_path, "tests/configs/v2/minimal_inventory")
    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    # Build a GameMaster to get normalized actions mapping (v2→runtime)
    with llm_script({"Player_1": "> pass"}):
        gm = GameMaster(config, game_id="parser_smoke", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)

    actions = gm.game_actions
    player_input = '> pickup "Large Sword"'

    parsed_actions, errors = parse_player_response(player_input, actions)
    assert not errors
    assert parsed_actions, "Expected one parsed action"

    action, params = parsed_actions[0]
    object_name = params.get("object_name", "")
    assert object_name == "Large Sword"
    assert not object_name.startswith('"') and not object_name.endswith('"')
    assert not object_name.startswith("'") and not object_name.endswith("'")


