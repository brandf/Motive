"""
V2 Configuration Validator

This module provides Pydantic models for validating v2 runtime configurations.
The pre-processor merges all includes into a single dict, then these models
validate and provide typed access to the configuration data.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .definitions import EntityDefinition
from .actions_pipeline import ActionDefinition


class V2ConfigValidationError(Exception):
    """Exception raised when v2 config validation fails."""
    pass


class GameSettingsV2(BaseModel):
    """Game settings for v2 configuration."""
    num_rounds: int = Field(default=10, ge=1, le=1000)
    initial_ap_per_turn: int = Field(default=30, ge=1, le=1000)
    manual: str = Field(default="docs/MANUAL.md")
    log_path: Optional[str] = Field(default=None, description="Relative path for game logs (e.g., 'fantasy/hearth_and_shadow/{game_id}')")


class PlayerConfigV2(BaseModel):
    """Player configuration for v2."""
    name: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)


class V2GameConfig(BaseModel):
    """
    Complete v2 game configuration after pre-processing and validation.
    
    This represents the final merged configuration that the GameMaster will use.
    """
    # Core game settings
    game_settings: Optional[GameSettingsV2] = None
    players: List[PlayerConfigV2] = Field(default_factory=list)
    
    # V2 entity definitions
    entity_definitions: Dict[str, EntityDefinition] = Field(default_factory=dict)
    action_definitions: Dict[str, ActionDefinition] = Field(default_factory=dict)
    
    # No theme/edition metadata needed - config includes handle organization
    
    # Allow extra fields for backward compatibility (Pydantic v2 style)
    model_config = ConfigDict(extra="allow")
    
    @field_validator('entity_definitions', mode='before')
    @classmethod
    def parse_entity_definitions(cls, v):
        """Parse entity definitions from dict format."""
        if isinstance(v, dict):
            result = {}
            for entity_id, entity_data in v.items():
                if isinstance(entity_data, dict):
                    # Separate core fields from immutable attributes and runtime properties
                    core_fields = {}
                    attributes_fields = {}
                    
                    # Map 'behaviors' to 'types' for compatibility
                    if 'behaviors' in entity_data:
                        core_fields['types'] = entity_data.pop('behaviors')
                    elif 'types' in entity_data:
                        core_fields['types'] = entity_data.pop('types')
                    
                    # Extract properties (mutable runtime state)
                    if 'properties' in entity_data:
                        core_fields['properties'] = entity_data.pop('properties')
                    # Extract attributes (immutable config)
                    if 'attributes' in entity_data:
                        attributes_fields = entity_data.pop('attributes')
                    
                    # Everything else previously fell into 'config'; reject it in v2
                    if 'config' in entity_data:
                        raise V2ConfigValidationError("Entity uses legacy 'config'. Move fields to 'attributes' or 'properties'.")
                    # Preserve remaining fields under attributes to avoid data loss
                    attributes_fields = {**attributes_fields, **entity_data}
                    
                    # Add definition_id
                    core_fields['definition_id'] = entity_id
                    # Emit explicit attributes only. Do not emit legacy 'config'.
                    core_fields['attributes'] = attributes_fields
                    
                    result[entity_id] = EntityDefinition(**core_fields)
                else:
                    result[entity_id] = entity_data
            return result
        return v
    
    @field_validator('action_definitions', mode='before')
    @classmethod
    def parse_action_definitions(cls, v):
        """Parse action definitions from dict format."""
        if isinstance(v, dict):
            result = {}
            for action_id, action_data in v.items():
                if isinstance(action_data, dict):
                    # Add action_id if missing
                    if 'action_id' not in action_data:
                        action_data = action_data.copy()
                        action_data['action_id'] = action_id
                    result[action_id] = ActionDefinition(**action_data)
                else:
                    result[action_id] = action_data
            return result
        return v


def validate_v2_config(config_data: Dict[str, Any]) -> V2GameConfig:
    """
    Validate a merged v2 configuration dictionary.
    
    Args:
        config_data: Merged configuration dictionary from pre-processor
        
    Returns:
        Validated V2GameConfig object
        
    Raises:
        V2ConfigValidationError: If validation fails
    """
    try:
        return V2GameConfig(**config_data)
    except Exception as e:
        raise V2ConfigValidationError(f"V2 config validation failed: {e}")


def validate_v2_config_from_file(config_path: str, base_path: str = "configs") -> V2GameConfig:
    """
    Load and validate a v2 configuration from file.
    
    Args:
        config_path: Path to the config file
        base_path: Base directory for config files
        
    Returns:
        Validated V2GameConfig object
        
    Raises:
        V2ConfigLoadError: If config loading fails
        V2ConfigValidationError: If validation fails
    """
    from .v2_config_preprocessor import load_v2_config, V2ConfigLoadError
    
    try:
        config_data = load_v2_config(config_path, base_path)
        return validate_v2_config(config_data)
    except V2ConfigLoadError as e:
        raise V2ConfigLoadError(f"Failed to load v2 config: {e}")
    except Exception as e:
        raise V2ConfigValidationError(f"Failed to validate v2 config: {e}")
