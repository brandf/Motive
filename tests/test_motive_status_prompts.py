import pytest

from motive.character import Character
from motive.config import MotiveConfig
from motive.requirements_evaluator import evaluate_requirement


class DummyGameMaster:
    def __init__(self):
        self.rooms = {}

    def _check_requirements(self, player_char, action_config, params):
        requirements = action_config.get("requirements", [])
        for req in requirements:
            handled, passed, err = evaluate_requirement(player_char, self, req, params)
            if not handled:
                raise AssertionError(f"Unsupported requirement in test: {req}")
            if not passed:
                return False, err or "Requirement not met", None
        return True, "", None


def build_motive(status_prompts):
    return MotiveConfig(
        id="test_motive",
        description="A test motive",
        success_conditions=[
            {"operator": "AND"},
            {
                "type": "character_has_property",
                "property": "clue_a",
                "value": True,
            },
        ],
        status_prompts=status_prompts,
    )


def test_status_prompt_falls_back_to_default_message():
    motive = build_motive(
        [
            {"message": "**🧭 Case Outlook:** Trust your instincts."},
        ]
    )
    character = Character(
        char_id="det",
        name="Detective",
        backstory="Testing detective",
        motives=[motive],
        deterministic=True,
    )
    gm = DummyGameMaster()

    message = character.get_motive_status_message(gm)

    assert message == "**🧭 Case Outlook:** Trust your instincts."


def test_status_prompt_selects_first_matching_condition():
    motive = build_motive(
        [
            {
                "condition": {
                    "type": "character_has_property",
                    "property": "clue_a",
                    "value": True,
                },
                "message": "**🧭 Case Outlook:** You connected the captain to the cult meetings—prepare the raid.",
            },
            {"message": "**🧭 Case Outlook:** Keep mapping the cult's inner circle."},
        ]
    )
    character = Character(
        char_id="det",
        name="Detective",
        backstory="Testing detective",
        motives=[motive],
        deterministic=True,
        properties={"clue_a": True},
    )
    gm = DummyGameMaster()

    message = character.get_motive_status_message(gm)

    assert message == "**🧭 Case Outlook:** You connected the captain to the cult meetings—prepare the raid."
