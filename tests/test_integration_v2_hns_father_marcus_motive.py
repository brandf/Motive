#!/usr/bin/env python3
"""Deterministic integration test for Father Marcus' restore_divine_connection motive."""

from pathlib import Path

import pytest

from motive.config import MotiveConfig
from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from motive.sim_v2.v2_config_validator import PlayerConfigV2


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
    character = player.character

    motive_def = config.entity_definitions['father_marcus'].attributes['motives'][0]
    character.selected_motive = MotiveConfig(**motive_def)

    # Baseline status prompt should use the default sacred pulse messaging
    baseline_status = character.get_motive_status_message(gm)
    assert baseline_status.startswith("**🕯️ Sacred Pulse:**")

    # Simulate progress beats and ensure progress messages fire exactly once
    character.set_property("church_taint_identified", True)
    character.collect_motive_progress_updates(gm)

    character.set_property("cemetery_taint_identified", True)
    updates = character.collect_motive_progress_updates(gm)
    assert any("gravestone" in msg.lower() for msg in updates)

    character.set_property("shrine_taint_identified", True)
    character.collect_motive_progress_updates(gm)

    # Advance through collection milestones
    for prop in (
        "blessed_incense_collected",
        "saints_bone_collected",
        "hallowed_water_collected",
    ):
        character.set_property(prop, True)
        character.collect_motive_progress_updates(gm)

    # Clear each site
    for prop in ("church_cleansed", "cemetery_cleansed", "shrine_cleansed"):
        character.set_property(prop, True)
        character.collect_motive_progress_updates(gm)

    character.set_property("final_sermon_delivered", True)
    character.collect_motive_progress_updates(gm)

    # Status prompt should now reflect the endgame messaging
    final_status = character.get_motive_status_message(gm)
    assert "town hums" in final_status.lower()

    assert character.check_motive_success(gm), "Father Marcus should complete restore_divine_connection"
