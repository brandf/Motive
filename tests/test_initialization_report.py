import pytest
from unittest.mock import MagicMock

from motive.game_initializer import GameInitializer


@pytest.mark.sandbox_integration
def test_initialization_report_contains_key_sections(monkeypatch):
    gi = GameInitializer.__new__(GameInitializer)
    gi.game_logger = MagicMock()
    gi.game_object_types = {"o": {}}
    gi.game_actions = {"a": {}}
    gi.game_character_types = {"ct": {}}
    gi.game_characters = {"c": {}}
    gi.game_rooms = {"r1": {}, "r2": {}}

    init_data = {
        'config_loaded': True,
        'rooms_created': 2,
        'objects_placed': 3,
        'characters_assigned': ["Alice to Player_1", "Bob to Player_2"],
        'warnings': ["Something minor"],
    }

    # Invoke the reporter
    GameInitializer._log_initialization_report(gi, init_data)

    # Capture the logged report
    args, kwargs = gi.game_logger.info.call_args
    report = args[0]

    # Assert key sections without overfitting formatting
    assert "🏗️ Game Initialization Report:" in report
    assert "📊 Configuration:" in report
    assert "🏠 Rooms:" in report
    assert "🎭 Characters:" in report
    assert "⚠️ Warnings:" in report
    assert "Alice to Player_1" in report
    assert "Bob to Player_2" in report


