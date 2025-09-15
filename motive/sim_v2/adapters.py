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
        
        # Core character properties
        properties["name"] = PropertySchema(
            type=PropertyType.STRING,
            default=v1_character.get("name", "")
        )
        properties["backstory"] = PropertySchema(
            type=PropertyType.STRING,
            default=v1_character.get("backstory", "")
        )
        
        # Preserve the single motive field if it exists
        if "motive" in v1_character:
            properties["motive"] = PropertySchema(
                type=PropertyType.STRING,
                default=v1_character.get("motive", "")
            )
        
        # CRITICAL: Preserve the complex motives array
        if "motives" in v1_character:
            properties["motives"] = PropertySchema(
                type=PropertyType.STRING,  # Store as JSON string for now
                default=str(v1_character["motives"])  # Convert to string representation
            )
        
        # CRITICAL: Preserve initial_rooms
        if "initial_rooms" in v1_character:
            properties["initial_rooms"] = PropertySchema(
                type=PropertyType.STRING,  # Store as JSON string for now
                default=str(v1_character["initial_rooms"])
            )
        
        # CRITICAL: Preserve aliases
        if "aliases" in v1_character:
            properties["aliases"] = PropertySchema(
                type=PropertyType.STRING,  # Store as JSON string for now
                default=str(v1_character["aliases"])
            )
        
        # Convert v1 character properties to typed properties
        v1_props = v1_character.get("properties", {})
        for key, value in v1_props.items():
            prop_type = self._infer_property_type(value)
            properties[key] = PropertySchema(type=prop_type, default=value)
        
        # CRITICAL: Convert v1 tags to boolean properties (tags are deprecated in v2)
        tags = v1_character.get("tags", [])
        for tag in tags:
            properties[tag] = PropertySchema(
                type=PropertyType.BOOLEAN,
                default=True
            )
        
        return EntityDefinition(
            definition_id=v1_character["id"],
            types=["character"],
            properties=properties
        )
    
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
        else:
            # Default to string for unknown types
            return PropertyType.STRING
