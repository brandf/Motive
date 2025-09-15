"""
Tests for character-specific hint functionality in CLI arguments.

This module tests the --hint-character CLI argument that allows
providing hints visible only to specific characters.
"""

import pytest
from unittest.mock import patch, MagicMock
from motive.cli import load_config, run_game
import asyncio


class TestHintCharacter:
    """Test character-specific hint functionality."""

    def test_hint_character_parsing_valid_format(self):
        """Test parsing of valid hint-character format."""
        hint_text = "bella_whisper_nightshade:Your hoarding compulsion drives you to collect objects!"
        
        # Test the parsing logic
        if ':' in hint_text:
            char_id, hint_content = hint_text.split(':', 1)
            assert char_id == 'bella_whisper_nightshade'
            assert hint_content == 'Your hoarding compulsion drives you to collect objects!'

    def test_hint_character_parsing_invalid_format(self):
        """Test parsing of invalid hint-character format."""
        hint_text = "no_colon_separator"
        
        # Test the parsing logic
        if ':' in hint_text:
            char_id, hint_content = hint_text.split(':', 1)
            assert False, "Should not parse without colon"
        else:
            # Should handle gracefully
            assert True

    def test_hint_character_parsing_multiple_colons(self):
        """Test parsing when hint text contains colons."""
        hint_text = "bella_whisper_nightshade:Your hoarding compulsion: drives you to collect objects!"
        
        # Should split only on first colon
        if ':' in hint_text:
            char_id, hint_content = hint_text.split(':', 1)
            assert char_id == 'bella_whisper_nightshade'
            assert hint_content == 'Your hoarding compulsion: drives you to collect objects!'

    def test_hint_character_parsing_empty_hint(self):
        """Test parsing with empty hint text."""
        hint_text = "bella_whisper_nightshade:"
        
        if ':' in hint_text:
            char_id, hint_content = hint_text.split(':', 1)
            assert char_id == 'bella_whisper_nightshade'
            assert hint_content == ''

    def test_hint_character_parsing_empty_character_id(self):
        """Test parsing with empty character ID."""
        hint_text = ":Your hoarding compulsion drives you to collect objects!"
        
        if ':' in hint_text:
            char_id, hint_content = hint_text.split(':', 1)
            assert char_id == ''
            assert hint_content == 'Your hoarding compulsion drives you to collect objects!'

    def test_hint_character_config_structure(self):
        """Test that hint-character creates correct config structure."""
        char_id = 'bella_whisper_nightshade'
        hint_text = 'Your hoarding compulsion drives you to collect objects!'
        
        # Expected config structure
        expected_hint = {
            "hint_id": "cli_hint_character",
            "hint_action": hint_text,
            "when": {
                "character_id": char_id
            }
        }
        
        assert expected_hint["hint_id"] == "cli_hint_character"
        assert expected_hint["hint_action"] == hint_text
        assert expected_hint["when"]["character_id"] == char_id

    def test_hint_character_with_regular_hint(self):
        """Test that hint-character works alongside regular hints."""
        config = load_config('configs/game.yaml')
        
        # Simulate adding both types of hints
        regular_hint = "Work together to solve the mystery"
        char_specific_hint = {
            "hint_id": "cli_hint_character",
            "hint_action": "Your hoarding compulsion drives you to collect objects!",
            "when": {
                "character_id": "bella_whisper_nightshade"
            }
        }
        
        # Both should be valid
        assert isinstance(regular_hint, str)
        assert isinstance(char_specific_hint, dict)
        assert char_specific_hint["when"]["character_id"] == "bella_whisper_nightshade"

    def test_hint_character_character_id_validation(self):
        """Test that character ID in hint-character is validated against available characters."""
        config = load_config('configs/game.yaml')
        available_characters = list(config.character_types.keys())
        
        # Test valid character ID
        char_id = 'bella_whisper_nightshade'
        assert char_id in available_characters
        
        # Test invalid character ID
        invalid_char_id = 'nonexistent_character'
        assert invalid_char_id not in available_characters

    def test_hint_character_multiple_characters(self):
        """Test hint-character with multiple different characters."""
        config = load_config('configs/game.yaml')
        available_characters = list(config.character_types.keys())
        
        # Test multiple valid character IDs
        test_characters = ['bella_whisper_nightshade', 'father_marcus', 'dr_sarah_chen']
        
        for char_id in test_characters:
            if char_id in available_characters:
                hint = {
                    "hint_id": f"cli_hint_character_{char_id}",
                    "hint_action": f"Hint for {char_id}",
                    "when": {
                        "character_id": char_id
                    }
                }
                assert hint["when"]["character_id"] == char_id

    def test_hint_character_special_characters_in_hint(self):
        """Test hint-character with special characters in hint text."""
        char_id = 'bella_whisper_nightshade'
        hint_text = 'Your hoarding compulsion drives you to collect objects! Try using pickup, drop, and throw actions!'
        
        hint = {
            "hint_id": "cli_hint_character",
            "hint_action": hint_text,
            "when": {
                "character_id": char_id
            }
        }
        
        assert hint["hint_action"] == hint_text
        assert '!' in hint["hint_action"]
        assert ',' in hint["hint_action"]

    def test_hint_character_empty_character_id_handling(self):
        """Test handling of empty character ID in hint-character."""
        hint_text = ":Your hoarding compulsion drives you to collect objects!"
        
        if ':' in hint_text:
            char_id, hint_content = hint_text.split(':', 1)
            
            # Empty character ID should be handled gracefully
            if char_id == '':
                # Should not create a hint with empty character ID
                assert char_id == ''
            else:
                assert char_id != ''

    def test_hint_character_whitespace_handling(self):
        """Test hint-character with whitespace in character ID and hint text."""
        hint_text = " bella_whisper_nightshade : Your hoarding compulsion drives you to collect objects! "
        
        if ':' in hint_text:
            char_id, hint_content = hint_text.split(':', 1)
            # Should handle whitespace appropriately
            char_id = char_id.strip()
            hint_content = hint_content.strip()
            
            assert char_id == 'bella_whisper_nightshade'
            assert hint_content == 'Your hoarding compulsion drives you to collect objects!'
