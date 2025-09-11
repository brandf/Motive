"""
Pydantic validation for merged hierarchical configurations.

This module provides validation for merged configuration dictionaries,
ensuring they conform to the expected Pydantic models while maintaining
the flexibility of the hierarchical system.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import ValidationError, BaseModel
import logging

from .config import (
    GameConfig, GameSettings, PlayerConfig,
    ActionConfig, ObjectTypeConfig, CharacterConfig, RoomConfig,
    ObjectInstanceConfig, ExitConfig
)


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    def __init__(self, message: str, validation_errors: List[str] = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []


class ConfigValidator:
    """Validates merged configuration dictionaries against Pydantic models."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_merged_config(self, config_data: Dict[str, Any]) -> GameConfig:
        """
        Validate a merged configuration dictionary and return a validated GameConfig.
        
        Args:
            config_data: The merged configuration dictionary from hierarchical loading
            
        Returns:
            Validated GameConfig object
            
        Raises:
            ConfigValidationError: If validation fails
        """
        validation_errors = []
        
        try:
            # First, validate the top-level GameConfig structure
            # This will validate game_settings, players, and basic structure
            validated_config = GameConfig(**config_data)
            
            # Now validate the hierarchical components if they exist
            if 'actions' in config_data and config_data['actions']:
                self._validate_actions(config_data['actions'], validation_errors)
            
            if 'object_types' in config_data and config_data['object_types']:
                self._validate_object_types(config_data['object_types'], validation_errors)
            
            if 'character_types' in config_data and config_data['character_types']:
                self._validate_character_types(config_data['character_types'], validation_errors)
            
            if 'rooms' in config_data and config_data['rooms']:
                self._validate_rooms(config_data['rooms'], validation_errors)
            
            if 'characters' in config_data and config_data['characters']:
                self._validate_characters(config_data['characters'], validation_errors)
            
            # If we have validation errors, raise them
            if validation_errors:
                error_message = f"Configuration validation failed with {len(validation_errors)} errors:\n" + "\n".join(f"  - {error}" for error in validation_errors)
                raise ConfigValidationError(error_message, validation_errors)
            
            self.logger.info("Configuration validation successful")
            return validated_config
            
        except ValidationError as e:
            # Handle Pydantic validation errors
            error_details = self._format_pydantic_errors(e)
            validation_errors.extend(error_details)
            raise ConfigValidationError(
                f"Configuration validation failed: {len(error_details)} validation errors",
                validation_errors
            )
    
    def _validate_actions(self, actions: Dict[str, Any], validation_errors: List[str]):
        """Validate action configurations."""
        for action_id, action_data in actions.items():
            try:
                ActionConfig(**action_data)
                
                # Additional validation: ensure all actions have positive cost (except special -1 for pass)
                cost = action_data.get('cost', 0)
                if isinstance(cost, dict):
                    cost_value = cost.get('value', 0)
                else:
                    cost_value = cost
                
                if cost_value <= 0 and cost_value != -1:
                    error_msg = f"Action '{action_id}': Cost must be positive (got {cost_value}). Use -1 for 'consume all AP' actions like 'pass'."
                    validation_errors.append(error_msg)
                    self.logger.error(f"Action cost validation error: {error_msg}")
                
            except ValidationError as e:
                error_msg = f"Action '{action_id}': {self._format_single_pydantic_error(e)}"
                validation_errors.append(error_msg)
                self.logger.error(f"Action validation error: {error_msg}")
    
    def _validate_object_types(self, object_types: Dict[str, Any], validation_errors: List[str]):
        """Validate object type configurations."""
        for obj_type_id, obj_type_data in object_types.items():
            try:
                ObjectTypeConfig(**obj_type_data)
            except ValidationError as e:
                error_msg = f"Object type '{obj_type_id}': {self._format_single_pydantic_error(e)}"
                validation_errors.append(error_msg)
                self.logger.error(f"Object type validation error: {error_msg}")
    
    def _validate_character_types(self, character_types: Dict[str, Any], validation_errors: List[str]):
        """Validate character type configurations."""
        for char_type_id, char_type_data in character_types.items():
            try:
                CharacterConfig(**char_type_data)
            except ValidationError as e:
                error_msg = f"Character type '{char_type_id}': {self._format_single_pydantic_error(e)}"
                validation_errors.append(error_msg)
                self.logger.error(f"Character type validation error: {error_msg}")
    
    def _validate_rooms(self, rooms: Dict[str, Any], validation_errors: List[str]):
        """Validate room configurations."""
        for room_id, room_data in rooms.items():
            try:
                # Validate the room itself
                RoomConfig(**room_data)
                
                # Validate exits if they exist
                if 'exits' in room_data and room_data['exits']:
                    for exit_id, exit_data in room_data['exits'].items():
                        try:
                            ExitConfig(**exit_data)
                        except ValidationError as e:
                            error_msg = f"Room '{room_id}' exit '{exit_id}': {self._format_single_pydantic_error(e)}"
                            validation_errors.append(error_msg)
                            self.logger.error(f"Room exit validation error: {error_msg}")
                
                # Validate object instances if they exist
                if 'objects' in room_data and room_data['objects']:
                    for obj_id, obj_data in room_data['objects'].items():
                        try:
                            ObjectInstanceConfig(**obj_data)
                        except ValidationError as e:
                            error_msg = f"Room '{room_id}' object '{obj_id}': {self._format_single_pydantic_error(e)}"
                            validation_errors.append(error_msg)
                            self.logger.error(f"Room object validation error: {error_msg}")
                            
            except ValidationError as e:
                error_msg = f"Room '{room_id}': {self._format_single_pydantic_error(e)}"
                validation_errors.append(error_msg)
                self.logger.error(f"Room validation error: {error_msg}")
    
    def _validate_characters(self, characters: Dict[str, Any], validation_errors: List[str]):
        """Validate character configurations."""
        for char_id, char_data in characters.items():
            try:
                CharacterConfig(**char_data)
            except ValidationError as e:
                error_msg = f"Character '{char_id}': {self._format_single_pydantic_error(e)}"
                validation_errors.append(error_msg)
                self.logger.error(f"Character validation error: {error_msg}")
    
    def _format_pydantic_errors(self, validation_error: ValidationError) -> List[str]:
        """Format Pydantic validation errors into readable messages."""
        errors = []
        if hasattr(validation_error, 'errors') and validation_error.errors():
            for error in validation_error.errors():
                error_msg = self._format_single_pydantic_error(validation_error)
                errors.append(error_msg)
        else:
            errors.append(str(validation_error))
        return errors
    
    def _format_single_pydantic_error(self, error: ValidationError) -> str:
        """Format a single Pydantic validation error."""
        # Extract error details from ValidationError
        if hasattr(error, 'errors') and error.errors():
            # Get the first error
            first_error = error.errors()[0]
            field_path = " -> ".join(str(loc) for loc in first_error['loc'])
            error_type = first_error['type']
            error_msg = first_error['msg']
            return f"Field '{field_path}': {error_msg} (type: {error_type})"
        else:
            # Fallback to string representation
            return str(error)


def validate_merged_config(config_data: Dict[str, Any]) -> GameConfig:
    """
    Convenience function to validate a merged configuration.
    
    Args:
        config_data: The merged configuration dictionary
        
    Returns:
        Validated GameConfig object
        
    Raises:
        ConfigValidationError: If validation fails
    """
    validator = ConfigValidator()
    return validator.validate_merged_config(config_data)
