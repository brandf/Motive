"""Trigger system for reactive behavior.

This module provides triggers that respond to condition changes and execute
effects when conditions transition from false to true or true to false.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .conditions import ConditionAST
from .effects import Effect, EffectEngine


@dataclass
class TriggerState:
    """State of a trigger (active/inactive, last evaluation)."""
    is_active: bool = False
    last_evaluation: bool = False


@dataclass
class Trigger:
    """A trigger that responds to condition changes."""
    trigger_id: str
    condition: ConditionAST
    effects: List[Effect]
    undo_effects: Optional[List[Effect]] = None


class TriggerEngine:
    """Manages triggers and their reactive behavior."""
    
    def __init__(self):
        self._triggers: Dict[str, Trigger] = {}
        self._trigger_states: Dict[str, TriggerState] = {}
        self._effect_engine = EffectEngine()
    
    def register_trigger(self, trigger: Trigger) -> None:
        """Register a trigger with the engine."""
        self._triggers[trigger.trigger_id] = trigger
        self._trigger_states[trigger.trigger_id] = TriggerState()
    
    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        """Get a registered trigger."""
        return self._triggers.get(trigger_id)
    
    def get_trigger_state(self, trigger_id: str) -> Optional[TriggerState]:
        """Get the state of a trigger."""
        return self._trigger_states.get(trigger_id)
    
    def evaluate_triggers(self, entities: Dict[str, Any]) -> None:
        """Evaluate all triggers against current entity state."""
        for trigger_id, trigger in self._triggers.items():
            self._evaluate_trigger(trigger, entities)
    
    def _evaluate_trigger(self, trigger: Trigger, entities: Dict[str, Any]) -> None:
        """Evaluate a single trigger."""
        from .conditions import ConditionEvaluator
        
        evaluator = ConditionEvaluator()
        state = self._trigger_states[trigger.trigger_id]
        
        # Evaluate condition
        # For simplicity, assume condition evaluates against first entity
        # In a full implementation, this would be more sophisticated
        entity_props = {}
        for entity_id, entity in entities.items():
            if hasattr(entity, 'properties'):
                entity_props.update(entity.properties)
            elif isinstance(entity, dict):
                entity_props.update(entity)
        
        current_evaluation = evaluator.evaluate(trigger.condition, entity_props)
        
        # Check for edge transitions
        if current_evaluation != state.last_evaluation:
            if current_evaluation:  # False -> True
                self._execute_effects(trigger.effects, entities)
            else:  # True -> False
                if trigger.undo_effects:
                    self._execute_effects(trigger.undo_effects, entities)
        
        # Update state
        state.is_active = current_evaluation
        state.last_evaluation = current_evaluation
    
    def _execute_effects(self, effects: List[Effect], entities: Dict[str, Any]) -> None:
        """Execute a list of effects."""
        for effect in effects:
            self._effect_engine.execute_effect(effect, entities)
    
    def remove_trigger(self, trigger_id: str) -> None:
        """Remove a trigger from the engine."""
        if trigger_id in self._triggers:
            del self._triggers[trigger_id]
            del self._trigger_states[trigger_id]
    
    def clear_all_triggers(self) -> None:
        """Clear all registered triggers."""
        self._triggers.clear()
        self._trigger_states.clear()
