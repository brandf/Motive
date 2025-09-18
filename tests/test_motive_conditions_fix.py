#!/usr/bin/env python3
"""
Test to verify that motive conditions are now parsed correctly from v2 configs.
"""

import pytest
from motive.game_initializer import GameInitializer
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


class TestMotiveConditionsFix:
    """Test that motive conditions are parsed correctly from v2 configs."""
    
    def test_motive_conditions_not_dummy(self):
        """Test that motive conditions are real, not dummy placeholders."""
        # Load v2 config
        config = load_and_validate_v2_config("game.yaml", "configs")
        
        # Create GameInitializer
        import logging
        logger = logging.getLogger("test")
        initializer = GameInitializer(config, "test_game", logger)
        
        # Load configurations
        initializer._load_configurations()
        
        # Check that character types have real motives
        for char_id, char_config in initializer.game_character_types.items():
            if hasattr(char_config, 'motives') and char_config.motives:
                for motive in char_config.motives:
                    # Check success conditions
                    if hasattr(motive, 'success_conditions') and motive.success_conditions:
                        success_str = str(motive.success_conditions)
                        assert "dummy" not in success_str.lower(), f"Character {char_id} motive {motive.id} has dummy success conditions: {success_str}"
                    
                    # Check failure conditions
                    if hasattr(motive, 'failure_conditions') and motive.failure_conditions:
                        failure_str = str(motive.failure_conditions)
                        assert "dummy" not in failure_str.lower(), f"Character {char_id} motive {motive.id} has dummy failure conditions: {failure_str}"
    
    def test_condition_conversion_v2_format(self):
        """Test that _convert_conditions handles v2 format correctly."""
        import logging
        logger = logging.getLogger("test")
        initializer = GameInitializer(None, "test", logger)
        
        # Test v2 format: [{'operator': 'AND'}, {'type': '...', 'property': '...', 'value': '...'}]
        v2_conditions = [
            {'operator': 'AND'},
            {'type': 'character_has_property', 'property': 'found_mayor', 'value': True},
            {'type': 'character_has_property', 'property': 'cult_exposed', 'value': True}
        ]
        
        result = initializer._convert_conditions(v2_conditions)
        
        # Should not be dummy
        result_str = str(result)
        assert "dummy" not in result_str.lower(), f"Converted conditions should not be dummy: {result_str}"
        
        # Should contain the real properties
        assert "found_mayor" in result_str, f"Should contain found_mayor: {result_str}"
        assert "cult_exposed" in result_str, f"Should contain cult_exposed: {result_str}"
