import pytest
from unittest.mock import Mock

from motive.character import Character
from motive.config import MotiveConfig, ActionRequirementConfig


@pytest.mark.sandbox_integration
def test_failure_overrides_success_precedence_at_end():
    motive = MotiveConfig(
        id="protect",
        description="Protect the mayor",
        success_conditions={"type": "player_has_tag", "tag": "mayor_safe"},
        failure_conditions={"type": "player_has_tag", "tag": "mayor_dead"},
    )
    character = Character(
        char_id="pc",
        name="Protector",
        backstory="",
        selected_motive=motive,
        current_room_id="r",
    )

    # Simulate end-of-game evaluation where both tags are true
    def side_effect(_character, condition_dict, _params):
        tag = condition_dict.get("requirements", [{}])[0].get("tag")
        return (tag in {"mayor_safe", "mayor_dead"}), "", None

    gm = Mock()
    gm._check_requirements.side_effect = side_effect

    debug = character.get_motive_debug_info(gm)
    assert debug["success"] is True
    assert debug["failure"] is True
    assert debug["final_status"] == "FAIL"  # failure overrides success


@pytest.mark.sandbox_integration
def test_redemption_removes_failure_before_end():
    motive = MotiveConfig(
        id="rescue",
        description="Rescue the captive",
        success_conditions={"type": "player_has_tag", "tag": "rescued"},
        failure_conditions={"type": "player_has_tag", "tag": "captive_dead"},
    )
    character = Character(
        char_id="pc",
        name="Rescuer",
        backstory="",
        selected_motive=motive,
        current_room_id="r",
    )

    # Mid-game: failure true, success false
    def side_effect_mid(_character, condition_dict, _params):
        tag = condition_dict.get("requirements", [{}])[0].get("tag")
        return (tag == "captive_dead"), "", None

    gm = Mock()
    gm._check_requirements.side_effect = side_effect_mid
    # DM status should indicate failing
    msg_mid = character.get_motive_status_message(gm)
    assert msg_mid and msg_mid.startswith("⚠️ **Case Outlook:**")

    # End-game: failure cleared, success true
    def side_effect_end(_character, condition_dict, _params):
        tag = condition_dict.get("requirements", [{}])[0].get("tag")
        return (tag == "rescued"), "", None

    gm._check_requirements.side_effect = side_effect_end
    debug_end = character.get_motive_debug_info(gm)
    assert debug_end["success"] is True
    assert debug_end["failure"] is False
    assert debug_end["final_status"] == "WIN"


