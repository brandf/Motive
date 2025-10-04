import pytest
from unittest.mock import Mock

from motive.character import Character
from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup


class TestMotiveStatusDM:
    def _make_character_with_motive(self, success_conditions, failure_conditions):
        motive = MotiveConfig(
            id="investigate_mayor",
            description="Uncover the truth behind the mayor's disappearance...",
            success_conditions=success_conditions,
            failure_conditions=failure_conditions,
        )
        character = Character(
            char_id="detective_thorne_instance_0",
            name="Detective James Thorne",
            backstory="A former city guard...",
            selected_motive=motive,
            current_room_id="town_square",
        )
        return character

    def _make_gm_with_side_effect(self, success_true_tags=None, failure_true_tags=None):
        success_true_tags = set(success_true_tags or [])
        failure_true_tags = set(failure_true_tags or [])

        def side_effect(character, condition_dict, _params):
            # condition_dict: { 'type': ..., 'requirements': [ { 'type': 'player_has_tag', 'tag': '...' } ] }
            req = condition_dict.get("requirements", [{}])[0]
            tag = req.get("tag")
            if tag in success_true_tags or tag in failure_true_tags:
                return True, "ok", None
            return False, "no", None

        gm = Mock()
        gm._check_requirements.side_effect = side_effect
        return gm

    def test_dm_motive_status_failing(self):
        # Failure true regardless of success
        character = self._make_character_with_motive(
            success_conditions={"type": "player_has_tag", "tag": "found_mayor"},
            failure_conditions={"type": "player_has_tag", "tag": "mayor_dead"},
        )
        gm = self._make_gm_with_side_effect(success_true_tags=[], failure_true_tags=["mayor_dead"])

        msg = character.get_motive_status_message(gm)
        assert msg is not None
        assert msg.startswith("⚠️ **Case Outlook:**")
        assert "MOTIVE STATUS" not in msg
        assert "investigate_mayor" not in msg

    def test_dm_motive_status_succeeding_without_failure(self):
        # Success true and failure false
        character = self._make_character_with_motive(
            success_conditions={"type": "player_has_tag", "tag": "found_mayor"},
            failure_conditions={"type": "player_has_tag", "tag": "mayor_dead"},
        )
        gm = self._make_gm_with_side_effect(success_true_tags=["found_mayor"], failure_true_tags=[])

        msg = character.get_motive_status_message(gm)
        assert msg is not None
        assert msg.startswith("✅ **Case Outlook:**")
        assert "MOTIVE STATUS" not in msg

    def test_dm_motive_status_neutral_no_message(self):
        # Neither success nor failure true
        character = self._make_character_with_motive(
            success_conditions={"type": "player_has_tag", "tag": "found_mayor"},
            failure_conditions={"type": "player_has_tag", "tag": "mayor_dead"},
        )
        gm = self._make_gm_with_side_effect(success_true_tags=[], failure_true_tags=[])

        msg = character.get_motive_status_message(gm)
        assert msg is None


class TestConditionTreeEmojis:
    def _make_character_with_groups(self, success_true_tags, failure_true_tags):
        success_group = MotiveConditionGroup(
            operator="AND",
            conditions=[
                ActionRequirementConfig(type="player_has_tag", tag="found_mayor"),
                ActionRequirementConfig(type="player_has_tag", tag="cult_exposed"),
            ],
        )
        failure_group = MotiveConditionGroup(
            operator="OR",
            conditions=[
                ActionRequirementConfig(type="player_has_tag", tag="mayor_dead"),
                ActionRequirementConfig(type="player_has_tag", tag="cult_succeeded"),
            ],
        )
        motive = MotiveConfig(
            id="investigate_mayor",
            description="Investigate and expose the cult.",
            success_conditions=success_group,
            failure_conditions=failure_group,
        )
        character = Character(
            char_id="detective_thorne_instance_1",
            name="Detective James Thorne",
            backstory="A former city guard...",
            selected_motive=motive,
            current_room_id="town_square",
        )

        def side_effect(_character, condition_dict, _params):
            req = condition_dict.get("requirements", [{}])[0]
            tag = req.get("tag")
            if tag in success_true_tags or tag in failure_true_tags:
                return True, "ok", None
            return False, "no", None

        gm = Mock()
        gm._check_requirements.side_effect = side_effect
        return character, gm

    def test_condition_tree_emojis_and_group_results(self):
        # Make success pass (both true for AND) and failure fail (both false for OR)
        character, gm = self._make_character_with_groups(
            success_true_tags={"found_mayor", "cult_exposed"}, failure_true_tags=set()
        )

        tree = character.get_motive_condition_tree(gm)

        # Headings
        assert "👍 SUCCESS CONDITIONS:" in tree
        assert "👎 FAILURE CONDITIONS:" in tree

        # Group lines and leaf checkboxes
        assert "☑️ AND (all must pass)" in tree
        assert "☐ OR (any must pass)" in tree
        assert "☑️ Player has tag 'found_mayor'" in tree
        assert "☑️ Player has tag 'cult_exposed'" in tree
        assert "☐ Player has tag 'mayor_dead'" in tree

        # Final status should be WIN
        assert "🏆 FINAL STATUS: WIN" in tree


