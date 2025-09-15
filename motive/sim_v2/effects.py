"""Effect primitives for declarative state changes.

This module provides basic effect primitives for modifying entity properties
and relations in a declarative way.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from .relations import RelationsGraph


@dataclass
class Effect:
    """Base class for all effects."""
    pass


@dataclass
class SetPropertyEffect(Effect):
    """Effect to set a property on an entity."""
    target_entity: str
    property_name: str
    value: Any


@dataclass
class MoveEntityEffect(Effect):
    """Effect to move an entity to a new container."""
    entity_id: str
    new_container: str


class EffectEngine:
    """Executes effects against entities and relations."""
    
    def execute_effect(
        self, 
        effect: Effect, 
        entities: Optional[Dict[str, Any]] = None,
        relations: Optional[RelationsGraph] = None
    ) -> None:
        """Execute a single effect."""
        if isinstance(effect, SetPropertyEffect):
            self._execute_set_property(effect, entities or {})
        elif isinstance(effect, MoveEntityEffect):
            self._execute_move_entity(effect, relations or RelationsGraph())
        else:
            raise ValueError(f"Unknown effect type: {type(effect)}")
    
    def execute_effects(
        self,
        effects: List[Effect],
        entities: Optional[Dict[str, Any]] = None,
        relations: Optional[RelationsGraph] = None
    ) -> None:
        """Execute multiple effects in sequence."""
        for effect in effects:
            self.execute_effect(effect, entities, relations)
    
    def _execute_set_property(self, effect: SetPropertyEffect, entities: Dict[str, Any]) -> None:
        """Execute a set property effect."""
        entity = entities.get(effect.target_entity)
        if entity is not None:
            # Handle dict entities (direct property access)
            if isinstance(entity, dict):
                entity[effect.property_name] = effect.value
            else:
                # Handle object entities with properties attribute
                if not hasattr(entity, 'properties'):
                    entity.properties = {}
                entity.properties[effect.property_name] = effect.value
    
    def _execute_move_entity(self, effect: MoveEntityEffect, relations: RelationsGraph) -> None:
        """Execute a move entity effect."""
        # RelationsGraph.place_entity handles moving entities safely
        relations.place_entity(effect.entity_id, effect.new_container)
