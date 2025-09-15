"""Affordances system for object-contributed actions.

This module allows objects to declaratively add/enable new actions
based on their properties and state.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .conditions import ConditionAST
from .effects import Effect, EffectEngine


@dataclass
class AffordanceRule:
    """Rule for determining when an affordance is available."""
    condition: ConditionAST
    available: bool = True


@dataclass
class Affordance:
    """An affordance that adds an action to an entity."""
    affordance_id: str
    action_name: str
    condition: ConditionAST
    effects: List[Effect]
    description: Optional[str] = None


class AffordanceEngine:
    """Manages affordances and their execution."""
    
    def __init__(self):
        self._affordances: Dict[str, Affordance] = {}
        self._effect_engine = EffectEngine()
    
    def register_affordance(self, affordance: Affordance) -> None:
        """Register an affordance with the engine."""
        self._affordances[affordance.affordance_id] = affordance
    
    def get_affordance(self, affordance_id: str) -> Optional[Affordance]:
        """Get a registered affordance."""
        return self._affordances.get(affordance_id)
    
    def get_available_actions(self, entity_id: str, entities: Dict[str, Any]) -> List[str]:
        """Get all available actions for an entity based on affordances."""
        available_actions = []
        
        for affordance in self._affordances.values():
            if self._is_affordance_available(affordance, entity_id, entities):
                available_actions.append(affordance.action_name)
        
        return available_actions
    
    def execute_action(self, entity_id: str, action_name: str, entities: Dict[str, Any]) -> bool:
        """Execute an action through affordances."""
        # Find affordance for this action
        affordance = self._find_affordance_for_action(entity_id, action_name, entities)
        
        if affordance is None:
            return False
        
        # Execute effects
        self._effect_engine.execute_effects(affordance.effects, entities)
        return True
    
    def _is_affordance_available(self, affordance: Affordance, entity_id: str, entities: Dict[str, Any]) -> bool:
        """Check if an affordance is available for an entity."""
        from .conditions import ConditionEvaluator
        
        evaluator = ConditionEvaluator()
        
        # Get entity properties
        entity = entities.get(entity_id)
        if entity is None:
            return False
        
        # Convert entity to properties dict
        if isinstance(entity, dict):
            entity_props = entity
        elif hasattr(entity, 'properties'):
            entity_props = entity.properties
        else:
            entity_props = {}
        
        # Evaluate condition
        return evaluator.evaluate(affordance.condition, entity_props)
    
    def _find_affordance_for_action(self, entity_id: str, action_name: str, entities: Dict[str, Any]) -> Optional[Affordance]:
        """Find an affordance that provides the specified action for the entity."""
        for affordance in self._affordances.values():
            if (affordance.action_name == action_name and 
                self._is_affordance_available(affordance, entity_id, entities)):
                return affordance
        
        return None
    
    def remove_affordance(self, affordance_id: str) -> None:
        """Remove an affordance from the engine."""
        if affordance_id in self._affordances:
            del self._affordances[affordance_id]
    
    def clear_all_affordances(self) -> None:
        """Clear all registered affordances."""
        self._affordances.clear()
    
    def get_affordance_description(self, entity_id: str, action_name: str, entities: Dict[str, Any]) -> Optional[str]:
        """Get the description for an affordance action."""
        affordance = self._find_affordance_for_action(entity_id, action_name, entities)
        if affordance:
            return affordance.description
        return None
