import pytest
from unittest.mock import MagicMock

from motive.config import Event
from motive.character import Character
from motive.room import Room
from motive.game_master import GameMaster


@pytest.mark.sandbox_integration
def test_observation_report_includes_player_checkboxes_and_reasons(monkeypatch):
    # Create minimal GameMaster without running full init
    gm = GameMaster.__new__(GameMaster)
    gm.game_logger = MagicMock()
    gm.players = []
    gm.rooms = {}
    gm.event_queue = []

    # Create rooms
    room_a = Room(room_id="room_a", name="Room A", description="A room")
    room_b = Room(room_id="room_b", name="Room B", description="B room")
    gm.rooms = {"room_a": room_a, "room_b": room_b}

    # Create two players/characters
    class P:
        def __init__(self, name, char):
            self.name = name
            self.character = char
            self.logger = MagicMock()

    char1 = Character(char_id="c1", name="Player_1_Char", backstory="", motive="", current_room_id="room_a")
    char2 = Character(char_id="c2", name="Player_2_Char", backstory="", motive="", current_room_id="room_a")
    player1 = P("Player_1", char1)
    player2 = P("Player_2", char2)
    gm.players = [player1, player2]

    room_a.add_player(char1)
    room_a.add_player(char2)

    # Event initiated by player1 in room_a, observed by room players
    e = Event(
        message="Player Player_1_Char looked at Message Board.",
        event_type="player_action",
        source_room_id="room_a",
        timestamp="t",
        related_player_id="c1",
        observers=["room_characters"],
    )
    gm.event_queue = [e]

    # Call the private method that logs observation report block
    # Construct minimal pieces used in the code path
    player_char = char1
    observation_report_lines = [f"👁️ Observation Report for {player_char.name}:"]
    observation_report_lines.append(f"  • {e.message} (Type: {e.event_type})")
    details = gm._get_event_observation_details(e)
    observation_report_lines.extend(details)

    report = "\n".join(observation_report_lines)

    # Check that both players in the room are listed with checkboxes and reasons
    assert "☐ Player_1 (Player_1_Char)" in report or "☑️ Player_1 (Player_1_Char)" in report
    assert "☐ Player_2 (Player_2_Char)" in report or "☑️ Player_2 (Player_2_Char)" in report
    assert "Room players observer" in report or "Event originator" in report


