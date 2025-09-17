#!/usr/bin/env python3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


@pytest.mark.asyncio
async def test_minimal_v2_character_override_assigns_to_first_player(tmp_path):
    base_path = str((tmp_path / "configs").resolve())
    Path(base_path).mkdir(parents=True, exist_ok=True)

    # Minimal config with two character types
    Path(base_path, "minimal_game.yaml").write_text(
        """
 game_settings:
   title: Character Override Minimal
   rounds: 1
 players:
   - name: Player_1
     character_type_id: alpha
     provider: dummy
     model: test
   - name: Player_2
     character_type_id: beta
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
     properties: {}
   beta:
     behaviors: [character]
     attributes:
       name: Beta
       description: Second character type.
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
            game_id="it_char_override",
            deterministic=True,
            log_dir=str(tmp_path),
            no_file_logging=True,
            character="beta",
        )

        # Override should assign Beta to Player_1 (instance ids are generated)
        p1, p2 = gm.players
        assert p1.character.name == "Beta"
        assert p2.character is not None
