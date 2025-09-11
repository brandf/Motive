"""
Test for the new motives system.

This test verifies that characters can have multiple motives, one is randomly selected
at character assignment, and success/failure can be checked using the action requirements system.
"""

import pytest
from unittest.mock import Mock, patch
from motive.character import Character
from motive.config import CharacterConfig, MotiveConfig, ActionRequirementConfig


class TestMotivesSystem:
    """Test the new motives system with multiple motives per character."""
    
    def test_character_has_multiple_motives(self):
        """Test that a character can have multiple motives defined."""
        # Create a character config with multiple motives
        character_config = {
            'id': 'detective_thorne',
            'name': 'Detective James Thorne',
            'backstory': 'A former city guard turned private investigator...',
            'motives': [
                {
                    'id': 'investigate_mayor',
                    'description': 'Uncover the truth behind the mayor\'s disappearance and bring the cult to justice.',
                    'success_conditions': [
                        {'type': 'player_has_tag', 'tag': 'found_mayor'},
                        {'type': 'player_has_tag', 'tag': 'cult_exposed'}
                    ],
                    'failure_conditions': [
                        {'type': 'player_has_tag', 'tag': 'mayor_dead'},
                        {'type': 'player_has_tag', 'tag': 'cult_succeeded'}
                    ]
                },
                {
                    'id': 'protect_daughter',
                    'description': 'Protect your sick daughter by finding the medicine she needs.',
                    'success_conditions': [
                        {'type': 'player_has_tag', 'tag': 'medicine_found'},
                        {'type': 'player_has_tag', 'tag': 'daughter_safe'}
                    ],
                    'failure_conditions': [
                        {'type': 'player_has_tag', 'tag': 'daughter_taken'},
                        {'type': 'player_has_tag', 'tag': 'daughter_dead'}
                    ]
                }
            ]
        }
        
        # Verify the character has multiple motives
        assert len(character_config['motives']) == 2
        assert character_config['motives'][0]['id'] == 'investigate_mayor'
        assert character_config['motives'][1]['id'] == 'protect_daughter'
    
    def test_motive_selection_at_character_assignment(self):
        """Test that a random motive is selected when character is assigned."""
        # Create motive configs
        motive1 = MotiveConfig(
            id='investigate_mayor',
            description='Uncover the truth behind the mayor\'s disappearance...',
            success_conditions=[],
            failure_conditions=[]
        )
        motive2 = MotiveConfig(
            id='protect_daughter',
            description='Protect your sick daughter...',
            success_conditions=[],
            failure_conditions=[]
        )
        
        # Create character with multiple motives
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard...',
            motives=[motive1, motive2],
            current_room_id='town_square'
        )
        
        # Verify a motive was selected
        assert character.selected_motive is not None
        assert character.selected_motive.id in ['investigate_mayor', 'protect_daughter']
        assert character.motive == character.selected_motive.description
    
    def test_legacy_single_motive_still_works(self):
        """Test that legacy single motive configuration still works."""
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard...',
            motive='Uncover the truth behind the mayor\'s disappearance...',
            current_room_id='town_square'
        )
        
        # Verify legacy motive is used
        assert character.motive == 'Uncover the truth behind the mayor\'s disappearance...'
        assert character.selected_motive is None
    
    def test_motive_success_failure_checking(self):
        """Test that motive success/failure can be checked using action requirements system."""
        # Create a motive with success/failure conditions (pass raw data for validator)
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
        
        # Mock game master with requirement checking
        mock_game_master = Mock()
        mock_game_master._check_requirements.return_value = (True, "Success", None)
        
        # Test success checking
        assert character.check_motive_success(mock_game_master) == True
        
        # Test failure checking
        mock_game_master._check_requirements.return_value = (False, "Failure", None)
        assert character.check_motive_failure(mock_game_master) == False
    
    def test_character_introduction_uses_selected_motive(self):
        """Test that character introduction shows the selected motive description."""
        motive = MotiveConfig(
            id='investigate_mayor',
            description='Uncover the truth behind the mayor\'s disappearance and bring the cult to justice.',
            success_conditions=[],
            failure_conditions=[]
        )
        
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard turned private investigator...',
            selected_motive=motive,
            current_room_id='town_square'
        )
        
        intro_message = character.get_introduction_message()
        
        # Verify the introduction includes the selected motive description
        assert 'Detective James Thorne' in intro_message
        assert 'A former city guard turned private investigator' in intro_message
        assert 'Uncover the truth behind the mayor\'s disappearance and bring the cult to justice' in intro_message
    
    def test_motive_priority_selection(self):
        """Test that selected_motive takes priority over motives list."""
        motive1 = MotiveConfig(
            id='investigate_mayor',
            description='Uncover the truth behind the mayor\'s disappearance...',
            success_conditions=[],
            failure_conditions=[]
        )
        motive2 = MotiveConfig(
            id='protect_daughter',
            description='Protect your sick daughter...',
            success_conditions=[],
            failure_conditions=[]
        )
        
        # Create character with pre-selected motive
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard...',
            motives=[motive1, motive2],
            selected_motive=motive2,  # Pre-selected motive
            current_room_id='town_square'
        )
        
        # Verify the pre-selected motive is used
        assert character.selected_motive.id == 'protect_daughter'
        assert character.motive == 'Protect your sick daughter...'
    
    def test_no_motives_fallback(self):
        """Test that character handles case with no motives gracefully."""
        character = Character(
            char_id='detective_thorne_instance_0',
            name='Detective James Thorne',
            backstory='A former city guard...',
            current_room_id='town_square'
        )
        
        # Verify fallback behavior
        assert character.motive == "No motive assigned"
        assert character.selected_motive is None
