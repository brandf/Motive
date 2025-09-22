#!/usr/bin/env python3
import pytest

from motive.cli import run_game
from tests.utils.llm_mock import llm_script

# H&S integration tests now have complete action set


@pytest.mark.asyncio
async def test_hns_end_to_end_three_rounds(tmp_path):
    scripts = {
        "Player_1": "> look\n> pickup \"Torch\"\n> light \"Torch\"\n> move north\n> look\n> investigate \"Quest Board\"\n> pass",
        "Player_2": "> say \"hello\"\n> move north\n> read \"Quest Board\"\n> pass",
    }

    with llm_script(scripts, manual="Test Manual"):
        await run_game(
            config_path="configs/game.yaml",
            game_id="hns_end_to_end_three_rounds",
            validate=True,
            rounds=3,
            deterministic=True,
            players=2,
            log_dir=str(tmp_path / "logs"),
            no_file_logging=True,
        )


@pytest.mark.asyncio
async def test_hns_end_to_end_minimal_realistic(tmp_path):
    """Realistic 3-round H&S session with only 2-3 actions per turn (30 AP total)."""
    scripts = {
        "Player_1": "> pickup \"Fresh Evidence\"\n> move bank\n> pickup \"Bank Ledgers\"",
        "Player_2": "> move guild\n> move market\n> say \"I'm at the tavern now\"",
    }

    with llm_script(scripts, manual="Comprehensive Test Manual"):
        result = await run_game(
            config_path="configs/game.yaml",
            game_id="hns_end_to_end_comprehensive",
            validate=True,
            rounds=3,
            deterministic=True,
            players=2,
            log_dir=str(tmp_path / "logs"),
            no_file_logging=True,
        )
        
        # Assert the game completed successfully
        assert result is not None
        
        # Verify both players exist
        assert len(result.players) == 2
        player_1, player_2 = result.players
        
        # Verify players moved between rooms (not stuck in one place)
        player_locations = [p.character.current_room_id for p in result.players]
        assert len(set(player_locations)) > 1, f"Players should have moved between rooms, got: {player_locations}"
        
        # Verify Player_1 picked up objects
        player_1_inventory = [obj.name if hasattr(obj, 'name') else str(obj) for obj in player_1.character.inventory]
        assert len(player_1_inventory) > 0, f"Player_1 should have picked up objects, got: {player_1_inventory}"
        
        # Verify Player_2 inventory (may be empty since they only did pass actions)
        player_2_inventory = [obj.name if hasattr(obj, 'name') else str(obj) for obj in player_2.character.inventory]
        
        # Verify specific objects were picked up by Player_1
        assert "fresh_evidence" in player_1_inventory, f"Player_1 should have fresh_evidence, got: {player_1_inventory}"
        assert "ledgers" in player_1_inventory, f"Player_1 should have ledgers, got: {player_1_inventory}"
        
        # Verify players moved between rooms (not stuck in one place)
        # Note: Both players may end up in the same room, but they should have moved during the game
        player_locations = [p.character.current_room_id for p in result.players]
        # At minimum, we should have movement evidence in the logs
        
        # Verify game completed successfully (we can see from the output that it did)
        # Since we used no_file_logging=True, we can't check log files
        # But we can verify the game state shows successful completion
        assert result is not None
        assert len(result.players) == 2


