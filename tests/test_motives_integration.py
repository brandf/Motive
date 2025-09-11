"""
Integration tests for the motives system.

This test verifies that the motives system works correctly with the core functionality.
"""

import pytest
from unittest.mock import Mock
from motive.character import Character
from motive.config import MotiveConfig, ActionRequirementConfig


class TestMotivesIntegration:
    """Integration tests for the motives system."""
    
    def test_character_with_multiple_motives_integration(self):
        """Test that Character correctly handles multiple motives in a realistic scenario."""
        # Create realistic motive configs with explicit operators
        investigate_motive = MotiveConfig(
            id='investigate_mayor',
            description='Uncover the truth behind the mayor\'s disappearance and bring the cult to justice.',
            success_conditions=[
                {'operator': 'AND'},
                {'type': 'player_has_tag', 'tag': 'found_mayor'},
                {'type': 'player_has_tag', 'tag': 'cult_exposed'}
            ],
            failure_conditions=[
                {'operator': 'OR'},
                {'type': 'player_has_tag', 'tag': 'mayor_dead'},
                {'type': 'player_has_tag', 'tag': 'cult_succeeded'}
            ]
        )
        
        protect_motive = MotiveConfig(
            id='protect_daughter',
            description='Protect your sick daughter by finding the medicine she needs.',
            success_conditions=[
                {'operator': 'AND'},
                {'type': 'player_has_tag', 'tag': 'medicine_found'},
                {'type': 'player_has_tag', 'tag': 'daughter_safe'}
            ],
            failure_conditions=[
                {'operator': 'OR'},
                {'type': 'player_has_tag', 'tag': 'daughter_taken'},
                {'type': 'player_has_tag', 'tag': 'daughter_dead'}
            ]
        )
        
        # Create character with multiple motives
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard turned private investigator...',
            motives=[investigate_motive, protect_motive],
            current_room_id='town_square'
        )
        
        # Verify character was created correctly
        assert character.selected_motive is not None
        assert character.selected_motive.id in ['investigate_mayor', 'protect_daughter']
        assert character.motive == character.selected_motive.description
        
        # Verify the character can check motive success/failure
        mock_game_master = Mock()
        mock_game_master._check_requirements.return_value = (True, "Success", None)
        
        # Test success checking
        success_result = character.check_motive_success(mock_game_master)
        assert isinstance(success_result, bool)
        
        # Test failure checking
        failure_result = character.check_motive_failure(mock_game_master)
        assert isinstance(failure_result, bool)
    
    def test_legacy_motive_integration(self):
        """Test that legacy single motive characters work correctly."""
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard turned private investigator...',
            motive='Uncover the truth behind the mayor\'s disappearance and bring the cult to justice.',
            current_room_id='town_square'
        )
        
        # Verify legacy motive is used correctly
        assert character.motive == 'Uncover the truth behind the mayor\'s disappearance and bring the cult to justice.'
        assert character.selected_motive is None
        
        # Verify character introduction works
        intro_message = character.get_introduction_message()
        assert 'Detective James Thorne' in intro_message
        assert 'A former city guard turned private investigator' in intro_message
        assert 'Uncover the truth behind the mayor\'s disappearance' in intro_message
    
    def test_motive_checking_integration(self):
        """Test that motive success/failure checking works with real game master."""
        # Create a character with a motive that has success/failure conditions
        motive = MotiveConfig(
            id='investigate_mayor',
            description='Uncover the truth behind the mayor\'s disappearance...',
            success_conditions=[{'type': 'player_has_tag', 'tag': 'found_mayor'}],
            failure_conditions=[{'type': 'player_has_tag', 'tag': 'mayor_dead'}]
        )
        
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard...',
            selected_motive=motive,
            current_room_id='town_square'
        )
        
        # Mock game master with realistic requirement checking
        mock_game_master = Mock()
        
        # Test success case - all success conditions met
        mock_game_master._check_requirements.return_value = (True, "Success", None)
        assert character.check_motive_success(mock_game_master) == True
        
        # Test failure case - one success condition not met
        def mock_check_requirements(char, req, params):
            if req.get('requirements', [{}])[0].get('tag') == 'found_mayor':
                return (False, "Mayor not found", None)
            return (True, "Success", None)

        mock_game_master._check_requirements.side_effect = mock_check_requirements
        assert character.check_motive_success(mock_game_master) == False
        
        # Test failure condition - one failure condition met
        def mock_check_requirements_failure(char, req, params):
            if req.get('requirements', [{}])[0].get('tag') == 'mayor_dead':
                return (True, "Mayor is dead", None)
            return (False, "Condition not met", None)
        
        mock_game_master._check_requirements.side_effect = mock_check_requirements_failure
        assert character.check_motive_failure(mock_game_master) == True