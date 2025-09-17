#!/usr/bin/env python3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import asyncio

from motive.cli import load_config, run_game


@pytest.mark.asyncio
async def test_minimal_v2_cli_loader_and_run(tmp_path):
    base_path = Path(tmp_path)
    cfg_path = base_path / "minimal_v2.yaml"

    cfg_path.write_text(
        """
entity_definitions:
  room_a:
    behaviors: [room]
    attributes:
      name: Room A
      description: A simple room.
    properties:
      exits: {}
      objects: {}
  tester:
    behaviors: [character]
    attributes:
      name: Tester
      description: A testing character.
    properties: {}

action_definitions:
  pass:
    name: pass
    description: End turn.
    cost: -1
    category: system
    parameters: []
    requirements: []
    effects: []

game_settings:
  title: CLI Minimal
  rounds: 1
players:
  - name: Player_1
    character_type_id: tester
    provider: dummy
    model: test
        """,
        encoding="utf-8",
    )

    # load_config should detect a standalone v2 config and return a v2 config object
    game_config = load_config(str(cfg_path), validate=True)
    # Basic shape assertions
    assert hasattr(game_config, "game_settings")
    assert hasattr(game_config, "players")
    assert hasattr(game_config, "entity_definitions")
    assert hasattr(game_config, "action_definitions")

    async def fake_get_response_and_update_history(self, messages_for_llm):
        return type("_AI", (), {"content": "> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual"),
    ):
        # Run one deterministic round to ensure no errors
        await run_game(
            config_path=str(cfg_path),
            game_id="cli_minimal",
            validate=True,
            rounds=1,
            deterministic=True,
            players=1,
            log_dir=str(base_path / "logs"),
            no_file_logging=True,
        )
