#!/usr/bin/env python3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_motive_override_assigns_selected_motive(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

    # Minimal v2 config with a character type that has a motive
    Path(base_path, "minimal_game.yaml").write_text(
        """
 game_settings:
   title: Motive Override Minimal
   rounds: 1
 players:
   - name: Player_1
     character_type_id: alpha
     provider: dummy
     model: test
 entity_definitions:
   room_a:
     behaviors: [room]
     attributes:
       name: Room A
       description: A simple room.
     properties:
       exits: {}
       objects: {}
   alpha:
     behaviors: [character]
     attributes:
       name: Alpha
       description: First character type.
       motives:
         - id: test_motive
           description: Complete a trivial condition                                        
           success_conditions:
             - type: player_in_room
               target_player_param: player
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
        """,
        encoding="utf-8",
    )

    config = load_and_validate_v2_config("minimal_game.yaml", base_path, validate=True)

    async def fake_get_response_and_update_history(self, messages_for_llm):
        return type("_AI", (), {"content": "> pass"})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value="Test Manual"),
    ):
        gm = GameMaster(
            config,
            game_id="it_motive_override",
            deterministic=True,
            log_dir=str(tmp_path),
            no_file_logging=True,
            motive="test_motive",
        )

        p1 = gm.players[0]
        # Confirm the selected motive is assigned
        assert p1.character.selected_motive is not None
        assert p1.character.selected_motive.id == "test_motive"

        # Run a turn to ensure no errors
        await gm._execute_player_turn(p1, round_num=1)
