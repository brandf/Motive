#!/usr/bin/env python3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from motive.cli import load_config, run_game


@pytest.mark.asyncio
async def test_real_config_boot_smoke(tmp_path):
    cfg_path = Path("configs/game_v2.yaml").resolve()
    assert cfg_path.exists(), "configs/game_v2.yaml must exist for real-config boot smoke"

    # Ensure the v2 config loads successfully
    game_config = load_config(str(cfg_path), validate=True)
    assert hasattr(game_config, "game_settings")
    assert hasattr(game_config, "players")
    assert hasattr(game_config, "entity_definitions") or hasattr(game_config, "includes")

    async def fake_get_response_and_update_history(self, messages_for_llm):
        # Use a universally safe core action if present
        return type("_AI", (), {"content": "> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual"),
    ):
        await run_game(
            config_path=str(cfg_path),
            game_id="real_boot_smoke",
            validate=True,
            rounds=1,
            deterministic=True,
            players=2,
            log_dir=str(Path(tmp_path) / "logs"),
            no_file_logging=True,
        )


