#!/usr/bin/env python3
"""Deterministic integration test for Father Marcus' restore_divine_connection motive."""

from pathlib import Path

import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from motive.sim_v2.v2_config_validator import PlayerConfigV2
from tests.utils.llm_mock import llm_script


@pytest.mark.asyncio
async def test_father_marcus_motive_completion(tmp_path):
    """Father Marcus should complete his multi-step motive within 20 rounds at 40 AP."""
    base_path = Path("configs/themes/fantasy/editions/hearth_and_shadow")
    config = load_and_validate_v2_config("hearth_and_shadow_v2.yaml", str(base_path), validate=True)

    # Reduce player setup to a single deterministic Father Marcus dummy player
    config = config.model_copy(
        update={
            "players": [
                PlayerConfigV2(name="Player_1", provider="dummy", model="test")
            ]
        }
    )

    # Scripted sequence covering the full motive flow
    actions = [
        '> look "Altar"',
        '> pickup "Blessed Incense"',
        '> move square',
        '> pickup "Consecration Vial"',
        '> move cemetery',
        '> look "Desecrated Gravestone"',
        '> move mausoleum',
        '> pickup "Saint\'s Bone"',
        '> move cemetery',
        '> move forest',
        '> move shrine',
        '> look "Tainted Shrine Altar"',
        '> use "Consecration Vial" on "Shrine Spring"',
        '> use "Consecration Vial" on "Tainted Shrine Altar"',
        '> move forest',
        '> move cemetery',
        '> use "Saint\'s Bone" on "Desecrated Gravestone"',
        '> move church',
        '> use "Blessed Incense" on "Altar"',
        '> use "Blessed Incense" on "Altar"',
    ]

    with llm_script({"Player_1": "\n".join(actions)}):
        gm = GameMaster(
            config,
            game_id="it_father_marcus_motive",
            deterministic=True,
            log_dir=str(tmp_path / "logs"),
            no_file_logging=True,
            character="father_marcus",
        )

        assert len(gm.players) == 1
        player = gm.players[0]

        # Start the test from the church so the scripted path is deterministic
        player.character.current_room_id = "church"

        # Execute scripted turns; llm_script will consume one line per turn
        for round_num in range(1, len(actions) + 1):
            await gm._execute_player_turn(player, round_num=round_num)

        character = player.character
        assert character.get_property("church_taint_identified") is True
        assert character.get_property("cemetery_taint_identified") is True
        assert character.get_property("shrine_taint_identified") is True
        assert character.get_property("church_cleansed") is True
        assert character.get_property("cemetery_cleansed") is True
        assert character.get_property("shrine_cleansed") is True
        assert character.get_property("final_sermon_delivered") is True

        assert character.check_motive_success(gm), "Father Marcus should complete restore_divine_connection"
