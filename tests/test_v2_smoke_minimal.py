#!/usr/bin/env python3
import pytest
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


def _write_smoke_configs(tmp_path):
    base = Path(tmp_path) / "configs"
    base.mkdir(parents=True, exist_ok=True)

    (base / "a.yaml").write_text(
        """
action_definitions:
  say:
    name: say
    description: Say something.
    cost: 1
    category: communication
    parameters:
      - name: phrase
        type: string
        description: What to say
        required: true
        default_value: null
    requirements: []
    effects:
      - type: generate_event
        message: '{player_name} says: "{phrase}".'
        observers: [room_characters]
""",
        encoding="utf-8",
    )

    (base / "b.yaml").write_text(
        """
entity_definitions:
  r1:
    behaviors: [room]
    attributes:
      name: R1
      description: First room
    properties:
      exits: {}
      objects: {}
  c1:
    behaviors: [character]
    attributes:
      name: Alpha
      backstory: test
      motives:
        - id: test_motive
          description: Test motive for Alpha
          success_conditions: []
          failure_conditions: []
  c2:
    behaviors: [character]
    attributes:
      name: Beta
      backstory: test
      motives:
        - id: test_motive
          description: Test motive for Beta
          success_conditions: []
          failure_conditions: []
""",
        encoding="utf-8",
    )

    (base / "game.yaml").write_text(
        """
includes:
  - a.yaml
  - b.yaml

game_settings:
  num_rounds: 1
  initial_ap_per_turn: 3
  manual: "../docs/MANUAL.md"

players:
  - name: "Alpha"
    provider: "dummy"
    model: "test"
  - name: "Beta"
    provider: "dummy"
    model: "test"
""",
        encoding="utf-8",
    )

    return str(base)


@pytest.mark.asyncio
async def test_v2_smoke_say_flow(tmp_path):
    base = _write_smoke_configs(tmp_path)
    cfg = load_and_validate_v2_config("game.yaml", base, validate=True)

    with llm_script({"Alpha": "> say \"hi\"", "Beta": "> pass"}):
        gm = GameMaster(cfg, game_id="smoke", deterministic=True, log_dir=str(tmp_path), no_file_logging=True)
        p_alpha, p_beta = gm.players
        p_beta.character.current_room_id = p_alpha.character.current_room_id
        await gm._execute_player_turn(p_alpha, round_num=1)
        obs = gm.player_observations.get(p_beta.character.id, [])
        assert any("says:" in e.message for e in obs)


