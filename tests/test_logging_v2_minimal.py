#!/usr/bin/env python3
import os
from pathlib import Path
import pytest

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from tests.utils.llm_mock import llm_script


def _write_minimal_logging_config(tmp_path, log_path_template: str):
    base = Path(tmp_path) / "configs"
    base.mkdir(parents=True, exist_ok=True)
    (base / "minimal_actions.yaml").write_text("action_definitions: { pass: { name: pass, description: End, cost: -1, category: system, parameters: [], requirements: [], effects: [] } }", encoding="utf-8")
    (base / "minimal_rooms.yaml").write_text("entity_definitions: { room_a: { behaviors: [room], attributes: { name: A, description: X }, properties: { exits: {}, objects: {} } } }", encoding="utf-8")
    (base / "minimal_characters.yaml").write_text("entity_definitions: { c1: { behaviors: [character], attributes: { name: P1, backstory: x, motives: [{ id: test_motive, description: Test motive, success_conditions: [], failure_conditions: [] }] } } }", encoding="utf-8")
    game_yaml = f"""
includes:
  - minimal_actions.yaml
  - minimal_rooms.yaml
  - minimal_characters.yaml

game_settings:
  num_rounds: 1
  initial_ap_per_turn: 1
  manual: "../docs/MANUAL.md"
  log_path: "{log_path_template}"

players:
  - name: "Player_1"
    provider: "dummy"
    model: "test"
"""
    (base / "minimal_game.yaml").write_text(game_yaml, encoding="utf-8")
    return str(base)


def test_logging_structure_single_game(tmp_path):
    cfg_base = _write_minimal_logging_config(tmp_path, "fantasy/hearth_and_shadow/{game_id}")
    config = load_and_validate_v2_config("minimal_game.yaml", cfg_base, validate=True)
    with llm_script({"Player_1": "> pass"}):
        gm = GameMaster(config, game_id="single_game_001", deterministic=True, log_dir=str(tmp_path), no_file_logging=False)
    expected = Path(tmp_path) / "fantasy" / "hearth_and_shadow" / "single_game_001"
    assert Path(gm.log_dir) == expected
    assert expected.exists()


def test_logging_structure_parallel_worker(tmp_path):
    cfg_base = _write_minimal_logging_config(tmp_path, "fantasy/hearth_and_shadow/{game_id}")
    config = load_and_validate_v2_config("minimal_game.yaml", cfg_base, validate=True)
    with llm_script({"Player_1": "> pass"}):
        gm = GameMaster(config, game_id="experiment_123_worker_1", deterministic=True, log_dir=str(tmp_path), no_file_logging=False)
    expected = Path(tmp_path) / "fantasy" / "hearth_and_shadow" / "experiment_123" / "experiment_123_worker_1"
    assert Path(gm.log_dir) == expected
    assert expected.exists()


