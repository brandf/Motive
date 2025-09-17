#!/usr/bin/env python3
from pathlib import Path

from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


def test_v2_config_has_core_sections(tmp_path):
    base = Path(tmp_path) / "configs"
    base.mkdir(parents=True, exist_ok=True)
    (base / "minimal_actions.yaml").write_text("action_definitions: {}", encoding="utf-8")
    (base / "minimal_rooms.yaml").write_text("entity_definitions: {}", encoding="utf-8")
    (base / "minimal_characters.yaml").write_text("entity_definitions: {}", encoding="utf-8")
    (base / "minimal_game.yaml").write_text(
        """
includes:
  - minimal_actions.yaml
  - minimal_rooms.yaml
  - minimal_characters.yaml

game_settings:
  num_rounds: 1
  initial_ap_per_turn: 1
  manual: "../docs/MANUAL.md"

players:
  - name: "P1"
    provider: "dummy"
    model: "test"
""".strip(),
        encoding="utf-8",
    )

    cfg = load_and_validate_v2_config("minimal_game.yaml", str(base), validate=True)
    assert cfg.game_settings is not None
    assert isinstance(cfg.entity_definitions, dict)
    assert isinstance(cfg.action_definitions, dict)


