import pytest
from unittest.mock import MagicMock

from motive.character import Character
from motive.room import Room
from motive.game_object import GameObject
from motive.hooks.core_hooks import look_at_target


def test_player_feedback_does_not_include_properties_listing():
    # Real room and object with properties
    room = Room(
        room_id="test_room",
        name="Test Room",
        description="A room",
        objects={},
        exits={},
    )
    obj = GameObject(
        obj_id="evidence",
        name="Fresh Evidence",
        description="Recently disturbed earth and strange markings near the fountain.",
        current_location_id="test_room",
        properties={"readable": True, "immovable": True, "size": "medium", "text": "Hidden text"},
    )
    room.add_object(obj)

    character = Character(
        char_id="pc",
        name="Detective",
        backstory="",
        motive="",
        current_room_id="test_room",
    )

    gm = MagicMock()
    gm.rooms = {"test_room": room}

    class AC: pass
    events, feedback = look_at_target(gm, character, AC(), {"target": "Fresh Evidence"})

    # Ensure feedback contains description but not raw properties listing
    combined = "\n".join(feedback)
    assert "You look at the Fresh Evidence." in combined
    assert "It has properties:" not in combined

