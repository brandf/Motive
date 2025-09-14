"""
Tests for config_validator.py critical validation paths.
These tests focus on validation logic that could allow invalid configs to break the game.
"""
import pytest
from unittest.mock import MagicMock
from motive.config_validator import ConfigValidator, ConfigValidationError
from motive.config import GameConfig


class TestConfigValidatorCritical:
    """Test critical validation paths in config_validator.py"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ConfigValidator()
    
    def test_validate_merged_config_success(self):
        """Test successful config validation - happy path"""
        valid_config = {
            "theme": "fantasy",
            "edition": "hearth_and_shadow",
            "game_settings": {
                "num_rounds": 10,
                "manual": "test_manual.md",
                "initial_ap_per_turn": 3
            },
            "players": [
                {"name": "Player_1", "provider": "google", "model": "gemini-2.5-flash"},
                {"name": "Player_2", "provider": "google", "model": "gemini-2.5-flash"}
            ]
        }
        
        result = self.validator.validate_merged_config(valid_config)
        
        assert isinstance(result, GameConfig)
        assert result.game_settings.num_rounds == 10
        assert result.game_settings.manual == "test_manual.md"
    
    def test_validate_merged_config_missing_required_fields(self):
        """Test validation failure for missing required fields - critical config issue"""
        invalid_config = {
            "theme": "fantasy"
            # Missing required fields like game_settings, players, etc.
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            self.validator.validate_merged_config(invalid_config)
        
        assert "validation failed" in str(exc_info.value).lower()
        assert exc_info.value.validation_errors is not None
    
    def test_validate_merged_config_invalid_field_types(self):
        """Test validation failure for wrong field types - common config mistake"""
        invalid_config = {
            "theme": "fantasy",
            "edition": "hearth_and_shadow",
            "game_settings": {
                "num_rounds": "not_a_number",  # Should be int
                "manual": "test_manual.md",
                "initial_ap_per_turn": 3
            },
            "players": [
                {"name": "Player_1", "provider": "google", "model": "gemini-2.5-flash"}
            ]
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            self.validator.validate_merged_config(invalid_config)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_validate_merged_config_invalid_field_types(self):
        """Test validation failure for wrong field types - common config mistake"""
        invalid_config = {
            "theme": "fantasy",
            "edition": "hearth_and_shadow",
            "game_settings": {
                "num_rounds": "not_a_number",  # Should be int
                "manual": "test_manual.md",
                "initial_ap_per_turn": 3
            },
            "players": [
                {"name": "Player_1", "provider": "google", "model": "gemini-2.5-flash"}
            ]
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            self.validator.validate_merged_config(invalid_config)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_validate_merged_config_invalid_player_count(self):
        """Test validation failure for invalid player count - game logic issue"""
        invalid_config = {
            "theme": "fantasy",
            "edition": "hearth_and_shadow",
            "game_settings": {
                "num_rounds": 10,
                "manual": "test_manual.md",
                "initial_ap_per_turn": 3
            },
            "players": []  # Invalid: must have at least one player
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            self.validator.validate_merged_config(invalid_config)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_validate_merged_config_invalid_rounds(self):
        """Test validation failure for invalid rounds - game logic issue"""
        invalid_config = {
            "theme": "fantasy",
            "edition": "hearth_and_shadow",
            "game_settings": {
                "num_rounds": -1,  # Invalid: must be > 0
                "manual": "test_manual.md",
                "initial_ap_per_turn": 3
            },
            "players": [
                {"name": "Player_1", "provider": "google", "model": "gemini-2.5-flash"}
            ]
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            self.validator.validate_merged_config(invalid_config)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_validate_merged_config_invalid_rounds(self):
        """Test validation failure for invalid rounds - game logic issue"""
        invalid_config = {
            "theme": "fantasy",
            "edition": "hearth_and_shadow",
            "game_settings": {
                "num_rounds": -1,  # Invalid: must be > 0
                "manual": "test_manual.md",
                "initial_ap_per_turn": 3
            },
            "players": [
                {"name": "Player_1", "provider": "google", "model": "gemini-2.5-flash"}
            ]
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            self.validator.validate_merged_config(invalid_config)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_validate_merged_config_empty_dict(self):
        """Test validation failure for empty config - edge case"""
        with pytest.raises(ConfigValidationError) as exc_info:
            self.validator.validate_merged_config({})
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_config_validation_error_with_errors(self):
        """Test ConfigValidationError with validation errors list"""
        errors = ["Field 'players' is required", "Field 'rounds' must be positive"]
        error = ConfigValidationError("Validation failed", errors)
        
        assert error.validation_errors == errors
        assert len(error.validation_errors) == 2
    
    def test_config_validation_error_without_errors(self):
        """Test ConfigValidationError without validation errors list"""
        error = ConfigValidationError("Validation failed")
        
        assert error.validation_errors == []
