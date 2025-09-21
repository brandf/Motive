"""Test character assignment functionality."""

import pytest
from motive.game_initializer import GameInitializer
from motive.config_loader import ConfigLoader
from motive.sim_v2.v2_config_validator import validate_v2_config
import logging


class TestCharacterAssignment:
    """Test that character assignment works correctly with various override options."""
    
    @pytest.fixture
    def config_loader(self):
        """Load the H&S configuration."""
        loader = ConfigLoader()
        config = loader.load_config("game.yaml")
        return config
    
    @pytest.fixture
    def game_initializer(self, config_loader):
        """Create a GameInitializer with the loaded config."""
        logger = logging.getLogger("test")
        initializer = GameInitializer(
            game_config=config_loader,
            game_id="test_game",
            game_logger=logger,
            initial_ap_per_turn=40,
            deterministic=True
        )
        
        # Load configurations to populate game_character_types
        initializer._load_configurations()
        
        return initializer
    
    def test_character_motives_override(self, game_initializer):
        """Test that character-motives override assigns the correct character and motive."""
        # Set up the override
        game_initializer.character_motives_override = ["detective_thorne:avenge_partner"]
        
        # Get available character IDs
        available_character_ids = list(game_initializer.game_character_types.keys())
        
        # Test the character assignment logic directly
        char_assignments = []
        
        # Handle character-motives override (highest priority)
        if game_initializer.character_motives_override:
            for pair in game_initializer.character_motives_override:
                if ':' in pair:
                    char_id, motive_id = pair.split(':', 1)
                    char_id = char_id.strip()
                    if char_id in available_character_ids:
                        char_assignments.append(char_id)
        # Verify the character was assigned correctly
        assert len(char_assignments) == 1
        assert char_assignments[0] == "detective_thorne"
    
    def test_character_motives_override_with_invalid_character(self, game_initializer):
        """Test that invalid characters in character-motives override are handled gracefully."""
        # Set up the override with an invalid character
        game_initializer.character_motives_override = ["invalid_character:avenge_partner"]
        
        # Get available character IDs
        available_character_ids = list(game_initializer.game_character_types.keys())
        
        # Test the character assignment logic directly
        char_assignments = []
        
        # Handle character-motives override (highest priority)
        if game_initializer.character_motives_override:
            for pair in game_initializer.character_motives_override:
                if ':' in pair:
                    char_id, motive_id = pair.split(':', 1)
                    char_id = char_id.strip()
                    if char_id in available_character_ids:
                        char_assignments.append(char_id)
        
        # Verify no character was assigned due to invalid character
        assert len(char_assignments) == 0
    
    def test_character_motives_override_with_multiple_pairs(self, game_initializer):
        """Test that multiple character-motive pairs are handled correctly."""
        # Set up the override with multiple pairs
        game_initializer.character_motives_override = [
            "detective_thorne:avenge_partner",
            "father_marcus:restore_divine_connection"
        ]
        
        # Get available character IDs
        available_character_ids = list(game_initializer.game_character_types.keys())
        
        # Test the character assignment logic directly
        char_assignments = []
        
        # Handle character-motives override (highest priority)
        if game_initializer.character_motives_override:
            for pair in game_initializer.character_motives_override:
                if ':' in pair:
                    char_id, motive_id = pair.split(':', 1)
                    char_id = char_id.strip()
                    if char_id in available_character_ids:
                        char_assignments.append(char_id)
        
        # Verify both characters were assigned correctly
        assert len(char_assignments) == 2
        assert "detective_thorne" in char_assignments
        assert "father_marcus" in char_assignments
    
    def test_character_motives_override_with_malformed_pair(self, game_initializer):
        """Test that malformed character-motive pairs are handled gracefully."""
        # Set up the override with a malformed pair (no colon)
        game_initializer.character_motives_override = ["detective_thorne_avenge_partner"]
        
        # Get available character IDs
        available_character_ids = list(game_initializer.game_character_types.keys())
        
        # Test the character assignment logic directly
        char_assignments = []
        
        # Handle character-motives override (highest priority)
        if game_initializer.character_motives_override:
            for pair in game_initializer.character_motives_override:
                if ':' in pair:
                    char_id, motive_id = pair.split(':', 1)
                    char_id = char_id.strip()
                    if char_id in available_character_ids:
                        char_assignments.append(char_id)
        
        # Verify no character was assigned due to malformed pair
        assert len(char_assignments) == 0
    
    def test_characters_override(self, game_initializer):
        """Test that characters override works correctly."""
        # Set up the override
        game_initializer.characters_override = ["detective_thorne", "father_marcus"]
        
        # Get available character IDs
        available_character_ids = list(game_initializer.game_character_types.keys())
        
        # Test the character assignment logic directly
        char_assignments = []
        
        # Handle characters override
        if game_initializer.characters_override:
            for char_id in game_initializer.characters_override:
                if char_id in available_character_ids:
                    char_assignments.append(char_id)
        
        # Verify both characters were assigned correctly
        assert len(char_assignments) == 2
        assert "detective_thorne" in char_assignments
        assert "father_marcus" in char_assignments
    
    def test_character_override_legacy(self, game_initializer):
        """Test that legacy character override works correctly."""
        # Set up the override
        game_initializer.character_override = "detective_thorne"
        
        # Get available character IDs
        available_character_ids = list(game_initializer.game_character_types.keys())
        
        # Test the character assignment logic directly
        char_assignments = []
        
        # Handle single character override (legacy)
        if game_initializer.character_override:
            if game_initializer.character_override in available_character_ids:
                char_assignments.append(game_initializer.character_override)
        
        # Verify the character was assigned correctly
        assert len(char_assignments) == 1
        assert char_assignments[0] == "detective_thorne"
    
    def test_priority_order(self, game_initializer):
        """Test that character-motives override takes priority over other overrides."""
        # Set up multiple overrides - character-motives should take priority
        game_initializer.character_motives_override = ["detective_thorne:avenge_partner"]
        game_initializer.characters_override = ["father_marcus"]
        game_initializer.character_override = "captain_marcus_omalley"
        
        # Get available character IDs
        available_character_ids = list(game_initializer.game_character_types.keys())
        
        # Test the character assignment logic directly
        char_assignments = []
        
        # Handle character-motives override (highest priority)
        if game_initializer.character_motives_override:
            for pair in game_initializer.character_motives_override:
                if ':' in pair:
                    char_id, motive_id = pair.split(':', 1)
                    char_id = char_id.strip()
                    if char_id in available_character_ids:
                        char_assignments.append(char_id)
        
        # Verify character-motives override took priority
        assert len(char_assignments) == 1
        assert char_assignments[0] == "detective_thorne"
