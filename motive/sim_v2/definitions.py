from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .properties import PropertySchema, PropertyStore
from .entity import MotiveEntity


@dataclass
class EntityDefinition:
    definition_id: str
    types: List[str]
    properties: Dict[str, PropertySchema] = field(default_factory=dict)


class DefinitionRegistry:
    def __init__(self):
        self._defs: Dict[str, EntityDefinition] = {}

    def add(self, definition: EntityDefinition) -> None:
        if definition.definition_id in self._defs:
            raise ValueError(f"Definition already exists: {definition.definition_id}")
        self._defs[definition.definition_id] = definition

    def get(self, definition_id: str) -> EntityDefinition:
        try:
            return self._defs[definition_id]
        except KeyError:
            raise KeyError(f"Unknown definition: {definition_id}")

    def instantiate(
        self,
        definition_id: str,
        entity_id: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> MotiveEntity:
        definition = self.get(definition_id)
        store = PropertyStore(schema=definition.properties)
        if overrides:
            for key, value in overrides.items():
                store.set(key, value)
        ent = MotiveEntity(
            entity_id=entity_id,
            definition_id=definition.definition_id,
            types=list(definition.types),
            properties=store,
        )
        return ent
    
    def create_entity(self, definition_id: str, entity_id: str) -> MotiveEntity:
        """Create an entity from a definition (alias for instantiate)."""
        return self.instantiate(definition_id, entity_id)


