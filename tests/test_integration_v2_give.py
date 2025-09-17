#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_minimal_v2_give_room_players(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_give")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> pickup \"Coin\"\n> give \"Listener\" \"Coin\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_give", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) == 2
        p1, p2 = gm.players
        # Same room
        p2.character.current_room_id = p1.character.current_room_id

        await gm._execute_player_turn(p1, round_num=1)
        obs = gm.player_observations.get(p2.character.id, [])
        assert len(obs) >= 1, "Expected room_players observation for give action"


@pytest.mark.asyncio
async def test_minimal_v2_give_target_not_present_no_room_obs(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_give")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    with llm_script({
        "Player_1": "> pickup \"Coin\"\n> give \"Listener\" \"Coin\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_give_neg", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) == 2
        p1, p2 = gm.players
        # Move target to an isolated room to fail player_in_room requirement
        from motive.room import Room
        new_room_id = "isolated_neg_give"
        gm.rooms[new_room_id] = Room(room_id=new_room_id, name="Isolated", description="", exits={}, objects={})
        p2.character.current_room_id = new_room_id

        await gm._execute_player_turn(p1, round_num=1)
        # No give-specific room observation due to requirement failure; coin remains with giver
        obs_other = gm.player_observations.get(p2.character.id, [])
        assert not any(" gives a " in getattr(ev, 'message', '').lower() for ev in obs_other)
        assert any(item.name == "Coin" for item in p1.character.inventory.values())


@pytest.mark.asyncio
async def test_minimal_v2_give_object_not_owned_no_room_obs(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    src_dir = Path("tests/configs/v2/minimal_give")
    dst_dir = Path(base_path)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.yaml"):
        (dst_dir / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    # Attempt to give without picking up first
    with llm_script({
        "Player_1": "> give \"Listener\" \"Coin\"\n> pass",
        "Player_2": "> pass",
    }):
        gm = GameMaster(config, game_id="it_give_not_owned", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        assert len(gm.players) == 2
        p1, p2 = gm.players
        # Ensure same room for requirement isolation (ownership will fail)
        p2.character.current_room_id = p1.character.current_room_id

        await gm._execute_player_turn(p1, round_num=1)
        # No give-specific room observation due to ownership requirement failure
        obs = gm.player_observations.get(p2.character.id, [])
        assert not any(" gives a " in getattr(ev, 'message', '').lower() for ev in obs)
        # Coin should not be in p2 inventory
        assert not any(item.name == "Coin" for item in p2.character.inventory.values())

