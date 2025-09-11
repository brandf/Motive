"""Test the new explicit operator system for motives."""

import pytest
from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
from motive.character import Character


class TestExplicitOperators:
    """Test the explicit operator system for motive conditions."""

    def test_single_condition(self):
        """Test that single conditions work as before."""
        motive = MotiveConfig(
            id="test_single",
            description="Test single condition",
            success_conditions=ActionRequirementConfig(type="player_has_tag", tag="found_mayor"),
            failure_conditions=ActionRequirementConfig(type="player_has_tag", tag="mayor_dead")
        )
        
        character = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            motives=[motive],
            selected_motive=motive
        )
        
        # Mock game master
        class MockGameMaster:
            def _check_requirements(self, char, condition_dict, params):
                if condition_dict['requirements'][0]['tag'] == 'found_mayor':
                    return True, "", None
                elif condition_dict['requirements'][0]['tag'] == 'mayor_dead':
                    return False, "", None
                return False, "", None
        
        game_master = MockGameMaster()
        
        # Test success condition
        assert character.check_motive_success(game_master) == True
        
        # Test failure condition
        assert character.check_motive_failure(game_master) == False

    def test_and_operator(self):
        """Test AND operator with multiple conditions."""
        motive = MotiveConfig(
            id="test_and",
            description="Test AND operator",
            success_conditions=MotiveConditionGroup(
                operator="AND",
                conditions=[
                    ActionRequirementConfig(type="player_has_tag", tag="found_mayor"),
                    ActionRequirementConfig(type="player_has_tag", tag="cult_exposed")
                ]
            ),
            failure_conditions=MotiveConditionGroup(
                operator="OR",
                conditions=[
                    ActionRequirementConfig(type="player_has_tag", tag="mayor_dead"),
                    ActionRequirementConfig(type="player_has_tag", tag="cult_succeeded")
                ]
            )
        )
        
        character = Character(
            char_id="test_char",
            name="Test Character", 
            backstory="A test character",
            motives=[motive],
            selected_motive=motive
        )
        
        # Mock game master that returns True for both success conditions
        class MockGameMaster:
            def _check_requirements(self, char, condition_dict, params):
                tag = condition_dict['requirements'][0]['tag']
                if tag in ['found_mayor', 'cult_exposed']:
                    return True, "", None
                elif tag in ['mayor_dead', 'cult_succeeded']:
                    return False, "", None
                return False, "", None
        
        game_master = MockGameMaster()
        
        # Test AND success - both conditions must be True
        assert character.check_motive_success(game_master) == True
        
        # Test OR failure - neither condition is True
        assert character.check_motive_failure(game_master) == False

    def test_or_operator(self):
        """Test OR operator with multiple conditions."""
        motive = MotiveConfig(
            id="test_or",
            description="Test OR operator",
            success_conditions=MotiveConditionGroup(
                operator="OR",
                conditions=[
                    ActionRequirementConfig(type="player_has_tag", tag="congregation_warned"),
                    ActionRequirementConfig(type="player_has_tag", tag="cult_stopped")
                ]
            ),
            failure_conditions=MotiveConditionGroup(
                operator="OR",
                conditions=[
                    ActionRequirementConfig(type="player_has_tag", tag="congregation_harmed"),
                    ActionRequirementConfig(type="player_has_tag", tag="ritual_completed")
                ]
            )
        )
        
        character = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character", 
            motives=[motive],
            selected_motive=motive
        )
        
        # Mock game master that returns True for only one success condition
        class MockGameMaster:
            def _check_requirements(self, char, condition_dict, params):
                tag = condition_dict['requirements'][0]['tag']
                if tag == 'congregation_warned':
                    return True, "", None
                elif tag == 'cult_stopped':
                    return False, "", None
                elif tag == 'congregation_harmed':
                    return True, "", None
                elif tag == 'ritual_completed':
                    return False, "", None
                return False, "", None
        
        game_master = MockGameMaster()
        
        # Test OR success - only one condition needs to be True
        assert character.check_motive_success(game_master) == True
        
        # Test OR failure - one condition is True
        assert character.check_motive_failure(game_master) == True
