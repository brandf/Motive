"""
Test Configuration Validation

Tests for the comprehensive config validation system that catches content issues early.
Following TDD workflow: write failing tests first, then implement validation.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motive.sim_v2.v2_config_validator import V2GameConfig, V2ConfigValidationError


class TestConfigValidation:
    """Test comprehensive config validation for catching content issues early."""
    
    def test_validate_missing_object_type_references(self):
        """Test detection of rooms referencing undefined object types."""
        # Arrange: Create config with room referencing undefined object type
        config_data = {
            "entity_definitions": {
                "room_with_bad_object": {
                    "types": ["room"],
                    "attributes": {
                        "properties": {
                            "objects": {
                                "some_object": {
                                    "object_type_id": "undefined_object_type"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about missing object type reference
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "MISSING OBJECT TYPE REFERENCES DETECTED" in warning_call
                assert "undefined_object_type" in warning_call
    
    def test_validate_missing_room_references(self):
        """Test detection of rooms with exits pointing to undefined rooms."""
        # Arrange: Create config with room exit pointing to undefined room
        config_data = {
            "entity_definitions": {
                "room_with_bad_exit": {
                    "types": ["room"],
                    "attributes": {
                        "description": "A room with a bad exit",
                        "properties": {
                            "exits": {
                                "north": {
                                    "destination_room_id": "undefined_room"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about missing room reference
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "MISSING ROOM REFERENCES DETECTED" in warning_call
                assert "undefined_room" in warning_call
    
    def test_validate_object_interaction_issues(self):
        """Test detection of objects with pickup_action but no corresponding interaction."""
        # Arrange: Create config with object having pickup_action but no interaction
        config_data = {
            "entity_definitions": {
                "broken_object": {
                    "types": ["object"],
                    "attributes": {
                        "description": "A broken object",
                        "properties": {
                            "pickup_action": "use"
                        },
                        "interactions": {
                            "look": {"effects": []}
                            # Missing "use" interaction despite pickup_action: use
                        }
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about interaction issues
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "OBJECT INTERACTION ISSUES DETECTED" in warning_call
                assert "broken_object" in warning_call
                assert "pickup_action 'use' but no corresponding interaction" in warning_call
    
    def test_validate_action_alias_issues(self):
        """Test detection of objects with action aliases pointing to non-existent interactions."""
        # Arrange: Create config with object having action alias pointing to missing interaction
        config_data = {
            "entity_definitions": {
                "object_with_bad_alias": {
                    "types": ["object"],
                    "attributes": {
                        "description": "An object with bad aliases",
                        "interactions": {
                            "look": {"effects": []}
                        },
                        "action_aliases": {
                            "examine": "look",  # This is fine
                            "use": "activate"   # This is bad - no "activate" interaction
                        }
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about action alias issues
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "OBJECT INTERACTION ISSUES DETECTED" in warning_call
                assert "object_with_bad_alias" in warning_call
                assert "action alias 'use' -> 'activate' but no 'activate' interaction" in warning_call
    
    def test_validate_valid_config_passes(self):
        """Test that valid configs pass all validation checks."""
        # Arrange: Create valid config with proper object types, rooms, and interactions
        config_data = {
            "entity_definitions": {
                "valid_object_type": {
                    "types": ["object"],
                    "attributes": {
                        "description": "A valid object type",
                        "properties": {
                            "pickup_action": "use"
                        },
                        "interactions": {
                            "use": {"effects": []},
                            "look": {"effects": []}
                        },
                        "action_aliases": {
                            "activate": "use"
                        }
                    }
                },
                "valid_room": {
                    "types": ["room"],
                    "attributes": {
                        "description": "A valid room",
                        "properties": {
                            "objects": {
                                "object_instance": {
                                    "object_type_id": "valid_object_type"
                                }
                            },
                            "exits": {
                                "north": {
                                    "destination_room_id": "another_valid_room"
                                }
                            }
                        }
                    }
                },
                "another_valid_room": {
                    "types": ["room"],
                    "attributes": {
                        "description": "Another valid room",
                        "properties": {}
                    }
                }
            }
        }
        
        # Act & Assert: Should not warn about anything
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception or log warnings
                config = V2GameConfig(**config_data)
                
                # Verify no warnings were logged
                mock_logger_instance.warning.assert_not_called()
    
    def test_validate_character_motives_still_works(self):
        """Test that existing character motive validation still works."""
        # Arrange: Create config with character without motives
        config_data = {
            "entity_definitions": {
                "character_without_motive": {
                    "types": ["character"],
                    "attributes": {
                        "name": "Test Character"
                        # No motives defined
                    }
                }
            }
        }
        
        # Act & Assert: Should still raise validation error for characters without motives
        with pytest.raises(V2ConfigValidationError) as exc_info:
            V2GameConfig(**config_data)
        
        assert "Characters without motives found" in str(exc_info.value)
        assert "character_without_motive" in str(exc_info.value)
    
    def test_validate_character_motive_conditions_empty_motives(self):
        """Test that characters with empty motives are warned."""
        # Arrange: Create config with character having motive with no success conditions
        config_data = {
            "entity_definitions": {
                "character_with_empty_motive": {
                    "types": ["character"],
                    "attributes": {
                        "name": "Test Character",
                        "description": "A test character",
                        "motives": [
                            {
                                "id": "test_motive",
                                "description": "Test motive",
                                "success_conditions": []  # Empty success conditions
                            }
                        ]
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about empty motives
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "CHARACTER MOTIVE ISSUES DETECTED" in warning_call
                assert "test_motive' with no success conditions" in warning_call
    
    def test_validate_character_motive_conditions_invalid_property(self):
        """Test that motives with invalid property conditions are warned."""
        # Arrange: Create config with character having motive with invalid property condition
        config_data = {
            "entity_definitions": {
                "character_with_bad_motive": {
                    "types": ["character"],
                    "attributes": {
                        "name": "Test Character",
                        "description": "A test character",
                        "motives": [
                            {
                                "id": "test_motive",
                                "description": "Test motive",
                                "success_conditions": [
                                    {
                                        "type": "character_has_property",
                                        "property": "",  # Empty property name
                                        "value": True
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about invalid property condition
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "CHARACTER MOTIVE ISSUES DETECTED" in warning_call
                assert "invalid property condition (missing property name)" in warning_call
    
    def test_validate_content_consistency_missing_descriptions(self):
        """Test that entities without descriptions are warned."""
        # Arrange: Create config with entities missing descriptions (excluding characters to avoid motive validation)
        config_data = {
            "entity_definitions": {
                "object_no_desc": {
                    "types": ["object"],
                    "attributes": {
                        "name": "Object Without Description"
                        # No description field
                    }
                },
                "room_no_desc": {
                    "types": ["room"],
                    "attributes": {
                        "name": "Room Without Description"
                        # No description field
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about missing descriptions
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "CONTENT CONSISTENCY ISSUES DETECTED" in warning_call
                assert "Object 'object_no_desc' has no description" in warning_call
                assert "Room 'room_no_desc' has no description" in warning_call
    
    def test_validate_action_system_integrity_missing_interactions(self):
        """Test that objects with properties but missing interactions are warned."""
        # Arrange: Create config with objects missing required interactions
        config_data = {
            "entity_definitions": {
                "usable_no_use": {
                    "types": ["object"],
                    "attributes": {
                        "name": "Usable Object",
                        "description": "An object that can be used",
                        "properties": {
                            "usable": True
                            # No 'use' interaction
                        }
                    }
                },
                "readable_no_read": {
                    "types": ["object"],
                    "attributes": {
                        "name": "Readable Object",
                        "description": "An object that can be read",
                        "properties": {
                            "readable": True
                            # No 'read' interaction
                        }
                    }
                },
                "pickupable_no_pickup": {
                    "types": ["object"],
                    "attributes": {
                        "name": "Pickupable Object",
                        "description": "An object that can be picked up",
                        "properties": {
                            "pickupable": True
                            # No 'pickup' interaction
                        }
                    }
                }
            }
        }
        
        # Act & Assert: Should warn about missing interactions
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception (just warn)
                config = V2GameConfig(**config_data)
                
                # Verify warning was logged
                mock_logger_instance.warning.assert_called()
                warning_call = mock_logger_instance.warning.call_args[0][0]
                assert "ACTION SYSTEM ISSUES DETECTED" in warning_call
                assert "Object 'usable_no_use' is marked as usable but has no 'use' interaction" in warning_call
                assert "Object 'readable_no_read' is marked as readable but has no 'read' interaction" in warning_call
                assert "Object 'pickupable_no_pickup' is marked as pickupable but has no 'pickup' interaction" in warning_call
    
    def test_validate_action_system_integrity_valid_interactions(self):
        """Test that objects with proper interactions pass validation."""
        # Arrange: Create config with properly configured object
        config_data = {
            "entity_definitions": {
                "valid_object": {
                    "types": ["object"],
                    "attributes": {
                        "name": "Valid Object",
                        "description": "A properly configured object",
                        "properties": {
                            "usable": True,
                            "readable": True,
                            "pickupable": True
                        },
                        "interactions": {
                            "use": {"effects": []},
                            "read": {"effects": []},
                            "pickup": {"effects": []}
                        }
                    }
                }
            }
        }
        
        # Act & Assert: Should not warn about anything
        with patch('sys.stderr') as mock_stderr:
            with patch('logging.getLogger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                # This should not raise an exception or log warnings
                config = V2GameConfig(**config_data)
                
                # Verify no warnings were logged
                mock_logger_instance.warning.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
