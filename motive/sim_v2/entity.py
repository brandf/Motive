from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .properties import PropertyStore


@dataclass
class MotiveEntity:
    entity_id: str
    definition_id: str
    types: List[str]
    properties: PropertyStore

    @property
    def id(self) -> str:
        return self.entity_id
    
    def get_property(self, name: str):
        """Get a property value from the entity."""
        return self.properties.get(name)
    
    def set_property(self, name: str, value) -> None:
        """Set a property value on the entity."""
        self.properties.set(name, value)


