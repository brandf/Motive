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
class IncrementPropertyEffect(Effect):
    """Effect to increment a numeric property on an entity."""
    target_entity: str
    property_name: str
    increment_value: int = 1


@dataclass
class MoveEntityEffect(Effect):
    """Effect to move an entity to a new container."""
    entity_id: str
    new_container: str


@dataclass
class CodeBindingEffect(Effect):
    """Effect that calls a code function."""
    function_name: str
    observers: Optional[List[str]] = None


@dataclass
class GenerateEventEffect(Effect):
    """Effect that represents an event emission (message + observers).

    Note: The v2 EffectEngine is entity/relations focused and does not handle
    event distribution. This class exists to faithfully round-trip v1 effects
    during migration and for potential future v2 event handling.
    """
    message: str
    observers: Optional[List[str]] = None


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
        elif isinstance(effect, IncrementPropertyEffect):
            self._execute_increment_property(effect, entities or {})
        elif isinstance(effect, MoveEntityEffect):
            self._execute_move_entity(effect, relations or RelationsGraph())
        elif isinstance(effect, GenerateEventEffect):
            # No-op in v2 engine (events are handled by the GM pipeline in v1 path)
            return
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
                # Handle MotiveEntity with PropertyStore
                if hasattr(entity, 'properties') and hasattr(entity.properties, 'set'):
                    entity.properties.set(effect.property_name, effect.value)
                # Handle object entities with properties attribute (dict)
                elif hasattr(entity, 'properties'):
                    entity.properties[effect.property_name] = effect.value
                else:
                    # Fallback: create properties dict
                    entity.properties = {effect.property_name: effect.value}
    
    def _execute_increment_property(self, effect: IncrementPropertyEffect, entities: Dict[str, Any]) -> None:
        """Execute an increment property effect."""
        entity = entities.get(effect.target_entity)
        if entity is not None:
            # Get current value (default to 0 if not set)
            current_value = 0
            if isinstance(entity, dict):
                current_value = entity.get(effect.property_name, 0)
            else:
                # Handle MotiveEntity with PropertyStore
                if hasattr(entity, 'properties') and hasattr(entity.properties, 'get'):
                    current_value = entity.properties.get(effect.property_name, 0)
                # Handle object entities with properties attribute (dict)
                elif hasattr(entity, 'properties'):
                    current_value = entity.properties.get(effect.property_name, 0)
            
            # Increment the value
            new_value = current_value + effect.increment_value
            
            # Set the new value
            if isinstance(entity, dict):
                entity[effect.property_name] = new_value
            else:
                # Handle MotiveEntity with PropertyStore
                if hasattr(entity, 'properties') and hasattr(entity.properties, 'set'):
                    entity.properties.set(effect.property_name, new_value)
                # Handle object entities with properties attribute (dict)
                elif hasattr(entity, 'properties'):
                    entity.properties[effect.property_name] = new_value
                else:
                    # Fallback: create properties dict
                    entity.properties = {effect.property_name: new_value}
    
    def _execute_move_entity(self, effect: MoveEntityEffect, relations: RelationsGraph) -> None:
        """Execute a move entity effect."""
        # RelationsGraph.place_entity handles moving entities safely
        relations.place_entity(effect.entity_id, effect.new_container)
