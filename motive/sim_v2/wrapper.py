"""V1 entity wrapper for backwards compatibility.

This wrapper allows existing v1 entities (rooms, objects, characters) to be used
as v2 entities while maintaining backwards compatibility during migration.
"""

from typing import Any, Set
from .definitions import EntityDefinition, DefinitionRegistry


class V1EntityWrapper:
    """Wraps a v1 entity to provide v2 interface while maintaining v1 compatibility."""
    
    def __init__(self, v1_entity: Any, definition: EntityDefinition, registry: DefinitionRegistry):
        """Initialize wrapper with v1 entity and its v2 definition."""
        self.v1_entity = v1_entity
        self.definition = definition
        self.registry = registry
    
    def get_property(self, name: str) -> Any:
        """Get a property value, converting tags to string format."""
        # Handle tags conversion
        if name == "tags":
            tags = getattr(self.v1_entity, 'tags', set())
            if isinstance(tags, set):
                return ",".join(sorted(tags)) if tags else ""
            return str(tags) if tags else ""
        
        # Handle other properties from v1 entity
        if hasattr(self.v1_entity, 'properties') and name in self.v1_entity.properties:
            return self.v1_entity.properties[name]
        
        # Fall back to definition default
        if name in self.definition.properties:
            return self.definition.properties[name].default
        
        # Fall back to direct attribute access
        if hasattr(self.v1_entity, name):
            return getattr(self.v1_entity, name)
        
        return None
    
    def set_property(self, name: str, value: Any) -> None:
        """Set a property value on the v1 entity."""
        if name == "tags":
            # Convert string back to set
            if isinstance(value, str):
                tags_set = set(value.split(",")) if value else set()
                self.v1_entity.tags = tags_set
            else:
                self.v1_entity.tags = value
        else:
            # Set on v1 entity properties
            if not hasattr(self.v1_entity, 'properties'):
                self.v1_entity.properties = {}
            self.v1_entity.properties[name] = value
