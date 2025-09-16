"""V1 to V2 configuration adapters.

These adapters convert existing v1 YAML configurations into v2 entity definitions
and instances, maintaining backwards compatibility during the migration phase.
"""

from typing import Dict, Any, Optional
from .definitions import EntityDefinition, DefinitionRegistry
from .properties import PropertySchema, PropertyType
from .entity import MotiveEntity


class V1ToV2Adapter:
    """Converts v1 configuration formats to v2 entity definitions and instances."""
    
    def __init__(self):
        pass
    
    def room_to_definition(self, v1_room: Dict[str, Any]) -> EntityDefinition:
        """Convert v1 room config to v2 entity definition."""
        properties = {}
        
        # Core room properties
        properties["name"] = PropertySchema(
            type=PropertyType.STRING, 
            default=v1_room.get("name", "")
        )
        properties["description"] = PropertySchema(
            type=PropertyType.STRING,
            default=v1_room.get("description", "")
        )
        
        # CRITICAL: Preserve exits
        if "exits" in v1_room:
            properties["exits"] = PropertySchema(
                type=PropertyType.STRING,  # Store as JSON string for now
                default=str(v1_room["exits"])
            )
        
        # CRITICAL: Preserve objects
        if "objects" in v1_room:
            properties["objects"] = PropertySchema(
                type=PropertyType.STRING,  # Store as JSON string for now
                default=str(v1_room["objects"])
            )
        
        # Convert v1 properties to typed properties
        v1_props = v1_room.get("properties", {})
        for key, value in v1_props.items():
            prop_type = self._infer_property_type(value)
            properties[key] = PropertySchema(type=prop_type, default=value)
        
        # CRITICAL: Convert v1 tags to boolean properties (tags are deprecated in v2)
        tags = v1_room.get("tags", [])
        for tag in tags:
            # Skip complex objects (like merge strategies) - only process simple string tags
            if isinstance(tag, str):
                properties[tag] = PropertySchema(
                    type=PropertyType.BOOLEAN,
                    default=True
                )
        
        return EntityDefinition(
            definition_id=v1_room["id"],
            types=["room"],
            properties=properties
        )
    
    def object_type_to_definition(self, v1_object_type: Dict[str, Any]) -> EntityDefinition:
        """Convert v1 object type config to v2 entity definition."""
        properties = {}
        
        # Core object properties
        properties["name"] = PropertySchema(
            type=PropertyType.STRING,
            default=v1_object_type.get("name", "")
        )
        properties["description"] = PropertySchema(
            type=PropertyType.STRING,
            default=v1_object_type.get("description", "")
        )
        
        # Convert v1 object properties to typed properties
        v1_props = v1_object_type.get("properties", {})
        for key, value in v1_props.items():
            prop_type = self._infer_property_type(value)
            properties[key] = PropertySchema(type=prop_type, default=value)
        
        # CRITICAL: Convert v1 tags to boolean properties (tags are deprecated in v2)
        tags = v1_object_type.get("tags", [])
        for tag in tags:
            # Skip complex objects (like merge strategies) - only process simple string tags
            if isinstance(tag, str):
                properties[tag] = PropertySchema(
                    type=PropertyType.BOOLEAN,
                    default=True
                )
        
        return EntityDefinition(
            definition_id=v1_object_type["id"],
            types=["object"],
            properties=properties
        )
    
    def character_to_definition(self, v1_character: Dict[str, Any]) -> EntityDefinition:
        """Convert v1 character config to v2 entity definition."""
        properties = {}
        config = {}
        
        # Immutable configuration data (not runtime state)
        config["name"] = v1_character.get("name", "")
        config["backstory"] = v1_character.get("backstory", "")
        
        # Preserve the single motive field if it exists
        if "motive" in v1_character:
            config["motive"] = v1_character.get("motive", "")
        
        # CRITICAL: Preserve the complex motives array, converting player_has_tag to character_has_property
        if "motives" in v1_character:
            converted_motives = self._convert_motive_conditions(v1_character["motives"])
            config["motives"] = converted_motives  # Store as proper nested data
        
        # CRITICAL: Preserve initial_rooms
        if "initial_rooms" in v1_character:
            config["initial_rooms"] = v1_character["initial_rooms"]
        
        # CRITICAL: Preserve aliases
        if "aliases" in v1_character:
            config["aliases"] = v1_character["aliases"]
        
        # Convert v1 character properties to typed properties
        v1_props = v1_character.get("properties", {})
        for key, value in v1_props.items():
            prop_type = self._infer_property_type(value)
            properties[key] = PropertySchema(type=prop_type, default=value)
        
        # CRITICAL: Convert v1 tags to boolean properties (tags are deprecated in v2)
        tags = v1_character.get("tags", [])
        for tag in tags:
            # Skip complex objects (like merge strategies) - only process simple string tags
            if isinstance(tag, str):
                properties[tag] = PropertySchema(
                    type=PropertyType.BOOLEAN,
                    default=True
                )
        
        return EntityDefinition(
            definition_id=v1_character["id"],
            types=["character"],
            properties=properties,
            config=config
        )
    
    def _convert_motive_conditions(self, motives: list) -> list:
        """Convert player_has_tag conditions to character_has_property in motives."""
        converted_motives = []
        for motive in motives:
            if isinstance(motive, dict):
                converted_motive = motive.copy()
                
                # Convert success_conditions
                if "success_conditions" in converted_motive:
                    converted_motive["success_conditions"] = self._convert_condition_list(
                        converted_motive["success_conditions"]
                    )
                
                # Convert failure_conditions
                if "failure_conditions" in converted_motive:
                    converted_motive["failure_conditions"] = self._convert_condition_list(
                        converted_motive["failure_conditions"]
                    )
                
                converted_motives.append(converted_motive)
            else:
                converted_motives.append(motive)
        
        return converted_motives
    
    def _convert_condition_list(self, conditions: list) -> list:
        """Convert player_has_tag conditions to character_has_property in a condition list."""
        converted_conditions = []
        for condition in conditions:
            if isinstance(condition, dict):
                converted_condition = condition.copy()
                if condition.get("type") == "player_has_tag" and "tag" in condition:
                    converted_condition["type"] = "character_has_property"
                    converted_condition["property"] = condition["tag"]
                    converted_condition["value"] = True
                    # Remove the old tag field
                    converted_condition.pop("tag", None)
                converted_conditions.append(converted_condition)
            else:
                converted_conditions.append(condition)
        
        return converted_conditions
    
    def object_instance_to_entity(
        self, 
        v1_instance: Dict[str, Any], 
        registry: DefinitionRegistry
    ) -> MotiveEntity:
        """Convert v1 object instance to v2 entity instance."""
        definition_id = v1_instance["object_type_id"]
        definition = registry.get(definition_id)
        
        # Create property store from definition
        from .properties import PropertyStore
        store = PropertyStore(schema=definition.properties)
        
        # Override with instance-specific values
        overrides = {}
        if "name" in v1_instance:
            overrides["name"] = v1_instance["name"]
        if "description" in v1_instance:
            overrides["description"] = v1_instance["description"]
        
        # Apply overrides
        for key, value in overrides.items():
            store.set(key, value)
        
        return MotiveEntity(
            entity_id=v1_instance["id"],
            definition_id=definition_id,
            types=list(definition.types),
            properties=store
        )
    
    def _infer_property_type(self, value: Any) -> PropertyType:
        """Infer the appropriate PropertyType from a value."""
        if isinstance(value, bool):
            return PropertyType.BOOLEAN
        elif isinstance(value, (int, float)):
            return PropertyType.NUMBER
        elif isinstance(value, str):
            return PropertyType.STRING
        elif isinstance(value, (dict, list)):
            return PropertyType.OBJECT
        else:
            # Default to string for unknown types
            return PropertyType.STRING
