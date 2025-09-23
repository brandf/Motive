"""
V2 Configuration Validator

This module provides Pydantic models for validating v2 runtime configurations.
The pre-processor merges all includes into a single dict, then these models
validate and provide typed access to the configuration data.
"""

import sys
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
    hints: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of hints to show to players")


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
    
    @field_validator('entity_definitions')
    @classmethod
    def validate_no_string_encoded_yaml(cls, v):
        """Validate that no entity definitions contain string-encoded YAML structures."""
        import re
        
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'properties') and entity_def.properties:
                props_str = str(entity_def.properties)
                # Check for string-encoded patterns (dictionaries/lists stored as strings)
                # This catches patterns like: exits: '{''north'': {...}}' or objects: '{''key'': {...}}'
                # But NOT message templates like: message: '{{player_name}} uses {object_name}.'
                if re.search(r":\s*'\{.*''.*\}", props_str) and not re.search(r":\s*'\{\{", props_str):
                    raise V2ConfigValidationError(
                        f"String-encoded YAML detected in entity '{entity_id}'. "
                        f"Use proper YAML structure instead of string encoding. "
                        f"See AGENT.md for proper YAML formatting guidelines."
                    )
        return v
    
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
    
    @field_validator('entity_definitions', mode='after')
    @classmethod
    def validate_character_motives(cls, v):
        """Validate that all characters have motives defined."""
        characters_without_motives = []
        
        for entity_id, entity_def in v.items():
            # Check if this is a character entity
            if hasattr(entity_def, 'types') and 'character' in entity_def.types:
                # Check if character has motives
                has_motives = False
                if hasattr(entity_def, 'attributes'):
                    attributes = entity_def.attributes
                    if isinstance(attributes, dict):
                        # Check for motives (new format) or motive (legacy format)
                        motives = attributes.get('motives', [])
                        motive = attributes.get('motive')
                        if motives and len(motives) > 0:
                            has_motives = True
                        elif motive:
                            has_motives = True
                
                if not has_motives:
                    characters_without_motives.append(entity_id)
        
        if characters_without_motives:
            raise V2ConfigValidationError(
                f"Characters without motives found: {characters_without_motives}. "
                f"All characters must have motives defined. Characters without motives should be removed "
                f"or moved to a separate NPCs configuration file."
            )
        
        return v
    
    @field_validator('entity_definitions', mode='after')
    @classmethod
    def validate_room_navigation(cls, v):
        """Validate that all room exits point to existing rooms."""
        import logging
        
        # Get all defined room IDs
        defined_rooms = set()
        room_exits = {}  # room_id -> list of destination_room_ids
        
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types'):
                types = entity_def.types
                if isinstance(types, list):
                    if 'room' in types:
                        defined_rooms.add(entity_id)
                        # Check for exits in this room
                        if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                            properties = entity_def.attributes.get('properties', {})
                            if isinstance(properties, dict):
                                exits = properties.get('exits', {})
                                if isinstance(exits, dict):
                                    room_exits[entity_id] = []
                                    for exit_id, exit_data in exits.items():
                                        if isinstance(exit_data, dict):
                                            destination = exit_data.get('destination_room_id')
                                            if destination:
                                                room_exits[entity_id].append(destination)
        
        # Check for missing room references
        missing_rooms = []
        for room_id, destinations in room_exits.items():
            for destination in destinations:
                if destination not in defined_rooms:
                    missing_rooms.append(f"Room '{room_id}' has exit pointing to undefined room '{destination}'")
        
        if missing_rooms:
            logger = logging.getLogger(__name__)
            warning_msg = "🚨 MISSING ROOM REFERENCES DETECTED 🚨\n" + "\n".join(missing_rooms)
            logger.warning(warning_msg)
            print(f"WARNING: {warning_msg}", file=sys.stderr)
        
        return v
    
    @field_validator('entity_definitions', mode='after')
    @classmethod
    def validate_object_interactions(cls, v):
        """Validate that objects have proper interaction definitions."""
        import logging
        
        interaction_issues = []
        
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types'):
                types = entity_def.types
                if isinstance(types, list):
                    if 'object' in types:
                        # Check for pickup_action without corresponding interaction
                        if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                            properties = entity_def.attributes.get('properties', {})
                            if isinstance(properties, dict):
                                pickup_action = properties.get('pickup_action')
                                if pickup_action:
                                    # Check if the pickup_action has a corresponding interaction
                                    interactions = entity_def.attributes.get('interactions', {})
                                    if isinstance(interactions, dict):
                                        if pickup_action not in interactions:
                                            interaction_issues.append(
                                                f"Object '{entity_id}' has pickup_action '{pickup_action}' but no corresponding interaction"
                                            )
                        
                        # Check for action aliases that don't map to valid interactions
                        action_aliases = entity_def.attributes.get('action_aliases', {})
                        if isinstance(action_aliases, dict):
                            interactions = entity_def.attributes.get('interactions', {})
                            if isinstance(interactions, dict):
                                for alias, target_action in action_aliases.items():
                                    if target_action not in interactions:
                                        interaction_issues.append(
                                            f"Object '{entity_id}' has action alias '{alias}' -> '{target_action}' but no '{target_action}' interaction"
                                        )
        
        if interaction_issues:
            logger = logging.getLogger(__name__)
            warning_msg = "🚨 OBJECT INTERACTION ISSUES DETECTED 🚨\n" + "\n".join(interaction_issues)
            logger.warning(warning_msg)
            print(f"WARNING: {warning_msg}", file=sys.stderr)
        
        return v
    
    @field_validator('entity_definitions', mode='after')
    @classmethod
    def validate_character_motive_conditions(cls, v):
        """Validate that character motives have proper success conditions."""
        import logging
        
        motive_issues = []
        
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types') and 'character' in entity_def.types:
                if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                    motives = entity_def.attributes.get('motives', [])
                    if isinstance(motives, list):
                        for motive in motives:
                            if isinstance(motive, dict):
                                success_conditions = motive.get('success_conditions', [])
                                if not success_conditions:
                                    motive_issues.append(f"Character '{entity_id}' has motive '{motive.get('id', 'unnamed')}' with no success conditions")
                                
                                # Check for common issues in success conditions
                                for condition in success_conditions:
                                    if isinstance(condition, dict):
                                        condition_type = condition.get('type')
                                        if condition_type == 'character_has_property':
                                            property_name = condition.get('property')
                                            if not property_name:
                                                motive_issues.append(f"Character '{entity_id}' has motive with invalid property condition (missing property name)")
        
        if motive_issues:
            logger = logging.getLogger(__name__)
            warning_msg = "🚨 CHARACTER MOTIVE ISSUES DETECTED 🚨\n" + "\n".join(motive_issues)
            logger.warning(warning_msg)
            print(f"WARNING: {warning_msg}", file=sys.stderr)
        
        return v
    
    @field_validator('entity_definitions', mode='after')
    @classmethod
    def validate_content_consistency(cls, v):
        """Validate content consistency across entities."""
        import logging
        
        consistency_issues = []
        
        # Check for duplicate entity IDs
        entity_ids = []
        for entity_id, entity_def in v.items():
            entity_ids.append(entity_id)
        
        if len(entity_ids) != len(set(entity_ids)):
            duplicates = [x for x in entity_ids if entity_ids.count(x) > 1]
            consistency_issues.append(f"Duplicate entity IDs found: {set(duplicates)}")
        
        # Check for objects without descriptions
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types') and 'object' in entity_def.types:
                if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                    description = entity_def.attributes.get('description', '')
                    if not description or description.strip() == '':
                        consistency_issues.append(f"Object '{entity_id}' has no description")
        
        # Check for rooms without descriptions
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types') and 'room' in entity_def.types:
                if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                    description = entity_def.attributes.get('description', '')
                    if not description or description.strip() == '':
                        consistency_issues.append(f"Room '{entity_id}' has no description")
        
        # Check for characters without descriptions
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types') and 'character' in entity_def.types:
                if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                    description = entity_def.attributes.get('description', '')
                    if not description or description.strip() == '':
                        consistency_issues.append(f"Character '{entity_id}' has no description")
        
        if consistency_issues:
            logger = logging.getLogger(__name__)
            warning_msg = "🚨 CONTENT CONSISTENCY ISSUES DETECTED 🚨\n" + "\n".join(consistency_issues)
            logger.warning(warning_msg)
            print(f"WARNING: {warning_msg}", file=sys.stderr)
        
        return v
    
    @field_validator('entity_definitions', mode='after')
    @classmethod
    def validate_action_system_integrity(cls, v):
        """Validate action system integrity."""
        import logging
        
        action_issues = []
        
        # Check for objects with required interactions missing
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types') and 'object' in entity_def.types:
                if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                    properties = entity_def.attributes.get('properties', {})
                    interactions = entity_def.attributes.get('interactions', {})
                    
                    # Check if object is usable but has no 'use' interaction
                    if properties.get('usable', False) and 'use' not in interactions:
                        action_issues.append(f"Object '{entity_id}' is marked as usable but has no 'use' interaction")
                    
                    # Check if object is readable but has no 'read' interaction
                    if properties.get('readable', False) and 'read' not in interactions:
                        action_issues.append(f"Object '{entity_id}' is marked as readable but has no 'read' interaction")
                    
                    # Check if object is pickupable but has no 'pickup' interaction
                    if properties.get('pickupable', False) and 'pickup' not in interactions:
                        action_issues.append(f"Object '{entity_id}' is marked as pickupable but has no 'pickup' interaction")
        
        if action_issues:
            logger = logging.getLogger(__name__)
            warning_msg = "🚨 ACTION SYSTEM ISSUES DETECTED 🚨\n" + "\n".join(action_issues)
            logger.warning(warning_msg)
            print(f"WARNING: {warning_msg}", file=sys.stderr)
        
        return v
    
    @field_validator('entity_definitions', mode='after')
    @classmethod
    def validate_object_references(cls, v):
        """Validate that all object references in rooms point to existing object types."""
        import logging
        
        # Get all defined object types
        defined_object_types = set()
        room_object_references = {}  # room_id -> list of object_type_ids
        
        for entity_id, entity_def in v.items():
            if hasattr(entity_def, 'types'):
                types = entity_def.types
                if isinstance(types, list):
                    if 'object' in types:
                        defined_object_types.add(entity_id)
                    elif 'room' in types:
                        # Check for objects in this room
                        if hasattr(entity_def, 'attributes') and isinstance(entity_def.attributes, dict):
                            properties = entity_def.attributes.get('properties', {})
                            if isinstance(properties, dict):
                                objects = properties.get('objects', {})
                                if isinstance(objects, dict):
                                    room_object_references[entity_id] = []
                                    for obj_id, obj_data in objects.items():
                                        if isinstance(obj_data, dict):
                                            object_type_id = obj_data.get('object_type_id')
                                            if object_type_id:
                                                room_object_references[entity_id].append(object_type_id)
        
        # Check for missing object type references
        missing_references = []
        for room_id, object_type_ids in room_object_references.items():
            for object_type_id in object_type_ids:
                if object_type_id not in defined_object_types:
                    missing_references.append(f"Room '{room_id}' references undefined object type '{object_type_id}'")
        
        if missing_references:
            # Log warnings to stdout and game.log
            logger = logging.getLogger(__name__)
            warning_msg = "🚨 MISSING OBJECT TYPE REFERENCES DETECTED 🚨\n" + "\n".join(missing_references)
            logger.warning(warning_msg)
            print(f"WARNING: {warning_msg}", file=sys.stderr)
            
            # For now, just warn instead of failing validation
            # This allows games to run while we fix content issues
            # TODO: Change this to raise V2ConfigValidationError once all content is fixed
        
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
