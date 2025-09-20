#!/usr/bin/env python3
"""Actions pipeline for sim_v2."""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pydantic import field_validator
from motive.sim_v2.effects import Effect, SetPropertyEffect, IncrementPropertyEffect, GenerateEventEffect, MoveEntityEffect
from motive.sim_v2.conditions import ConditionAST, ConditionEvaluator
from motive.sim_v2.relations import RelationsGraph


@dataclass
class ActionParameter:
    """Defines a parameter for an action."""
    name: str
    type: str  # "string", "integer", "boolean", etc.
    description: str
    required: bool = True
    default_value: Optional[Any] = None


@dataclass
class ActionRequirement:
    """Defines a requirement for an action."""
    type: str  # "condition", "exit_exists", "object_in_room", etc.
    condition: Optional[ConditionAST] = None
    description: Optional[str] = None
    # Optional v1-compatible fields for various requirement types
    tag: Optional[str] = None
    object_name_param: Optional[str] = None
    property: Optional[str] = None
    value: Optional[Any] = None
    target_player_param: Optional[str] = None
    direction_param: Optional[str] = None


@dataclass
class ActionDefinition:
    """Defines a complete action with parameters, requirements, and effects."""
    action_id: str
    name: str
    description: str
    cost: int
    parameters: List[ActionParameter]
    requirements: List[ActionRequirement]
    effects: List[Effect]
    category: str = "general"
    
    @field_validator('effects', mode='before')
    @classmethod
    def parse_effects(cls, v):
        """Parse effects from dict format to Effect objects."""
        if isinstance(v, list):
            result = []
            for effect_data in v:
                if isinstance(effect_data, dict):
                    effect_type = effect_data.get('type')
                    if effect_type == 'set_property':
                        result.append(SetPropertyEffect(
                            target_entity=effect_data.get('target', 'player'),
                            property_name=effect_data.get('property'),
                            value=effect_data.get('value')
                        ))
                    elif effect_type == 'increment_property':
                        result.append(IncrementPropertyEffect(
                            target_entity=effect_data.get('target', 'player'),
                            property_name=effect_data.get('property'),
                            increment_value=effect_data.get('increment_value', 1)
                        ))
                    elif effect_type == 'generate_event':
                        result.append(GenerateEventEffect(
                            message=effect_data.get('message'),
                            observers=effect_data.get('observers')
                        ))
                    else:
                        raise ValueError(f"Unknown effect type: {effect_type}")
                else:
                    result.append(effect_data)
            return result
        return v


@dataclass
class ActionResult:
    """Result of action execution."""
    success: bool
    error_message: Optional[str] = None
    events_generated: List[Any] = None  # Will be Event objects
    feedback_messages: List[str] = None


@dataclass
class ParameterValidationResult:
    """Result of parameter validation."""
    is_valid: bool
    error_message: Optional[str] = None
    validated_parameters: Optional[Dict[str, Any]] = None


@dataclass
class RequirementEvaluationResult:
    """Result of requirement evaluation."""
    requirements_met: bool
    error_message: Optional[str] = None
    failed_requirements: List[str] = None


class ActionPipeline:
    """Manages action definitions and execution using sim_v2 systems."""
    
    def __init__(self):
        self._actions: Dict[str, ActionDefinition] = {}
        self._effect_engine = None  # Will be injected
        self._condition_evaluator = ConditionEvaluator()
    
    def register_action(self, action: ActionDefinition) -> None:
        """Register an action definition."""
        self._actions[action.action_id] = action
    
    def get_action(self, action_id: str) -> Optional[ActionDefinition]:
        """Get an action definition by ID."""
        return self._actions.get(action_id)
    
    def get_available_actions(self) -> List[str]:
        """Get list of all available action IDs."""
        return list(self._actions.keys())
    
    def get_action_cost(self, action_id: str) -> int:
        """Get the cost of an action."""
        action = self._actions.get(action_id)
        return action.cost if action else 0
    
    def validate_parameters(self, action_id: str, parameters: Dict[str, Any]) -> ParameterValidationResult:
        """Validate parameters for an action."""
        action = self._actions.get(action_id)
        if not action:
            return ParameterValidationResult(
                is_valid=False,
                error_message=f"Action '{action_id}' not found"
            )
        
        validated_params = {}
        
        # Check required parameters
        for param in action.parameters:
            if param.required and param.name not in parameters:
                return ParameterValidationResult(
                    is_valid=False,
                    error_message=f"Missing required parameter: {param.name}"
                )
            
            # Use parameter value or default
            value = parameters.get(param.name, param.default_value)
            if value is None and param.required:
                return ParameterValidationResult(
                    is_valid=False,
                    error_message=f"Parameter '{param.name}' is required but not provided"
                )
            
            validated_params[param.name] = value
        
        return ParameterValidationResult(
            is_valid=True,
            validated_parameters=validated_params
        )
    
    def evaluate_requirements(self, action_id: str, parameters: Dict[str, Any], entities: Dict[str, Any]) -> RequirementEvaluationResult:
        """Evaluate requirements for an action."""
        action = self._actions.get(action_id)
        if not action:
            return RequirementEvaluationResult(
                requirements_met=False,
                error_message=f"Action '{action_id}' not found"
            )
        
        failed_requirements = []
        
        for requirement in action.requirements:
            if requirement.type == "condition" and requirement.condition:
                # Evaluate condition against entity properties
                entity_props = self._get_entity_properties(entities)
                if not self._condition_evaluator.evaluate(requirement.condition, entity_props):
                    failed_requirements.append(f"Condition not met: {requirement.description or 'unknown'}")
            elif requirement.type == "exit_exists":
                # Check if exit exists (simplified)
                if "direction" in parameters:
                    # This would check room exits in a real implementation
                    pass
            elif requirement.type == "object_in_room":
                # Check if object exists in room (simplified)
                if "object_name" in parameters:
                    # This would check room objects in a real implementation
                    pass
        
        if failed_requirements:
            return RequirementEvaluationResult(
                requirements_met=False,
                error_message=f"Requirements not met: {', '.join(failed_requirements)}",
                failed_requirements=failed_requirements
            )
        
        return RequirementEvaluationResult(requirements_met=True)
    
    def execute_action(
        self, 
        action_id: str, 
        parameters: Dict[str, Any], 
        entities: Dict[str, Any],
        relations: Optional[RelationsGraph] = None
    ) -> ActionResult:
        """Execute an action."""
        # Validate parameters
        param_result = self.validate_parameters(action_id, parameters)
        if not param_result.is_valid:
            return ActionResult(
                success=False,
                error_message=param_result.error_message
            )
        
        # Evaluate requirements
        req_result = self.evaluate_requirements(action_id, param_result.validated_parameters, entities)
        if not req_result.requirements_met:
            return ActionResult(
                success=False,
                error_message=req_result.error_message
            )
        
        # Execute effects
        action = self._actions[action_id]
        try:
            self._execute_effects(action.effects, param_result.validated_parameters, entities, relations)
            return ActionResult(success=True)
        except Exception as e:
            return ActionResult(
                success=False,
                error_message=f"Error executing action: {str(e)}"
            )
    
    def _get_entity_properties(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Get properties from entities for condition evaluation."""
        properties = {}
        
        for entity_id, entity in entities.items():
            if isinstance(entity, dict):
                # Add entity properties with entity_id prefix
                for key, value in entity.items():
                    properties[f"{entity_id}.{key}"] = value
            elif hasattr(entity, 'properties'):
                # Add entity properties with entity_id prefix
                for key, value in entity.properties.items():
                    properties[f"{entity_id}.{key}"] = value
            elif hasattr(entity, '__dict__'):
                # Add entity attributes with entity_id prefix
                for key, value in entity.__dict__.items():
                    if not key.startswith('_'):  # Skip private attributes
                        properties[f"{entity_id}.{key}"] = value
        
        return properties
    
    def _execute_effects(
        self, 
        effects: List[Effect], 
        parameters: Dict[str, Any], 
        entities: Dict[str, Any],
        relations: Optional[RelationsGraph] = None
    ) -> None:
        """Execute effects with parameter substitution."""
        # Simple effect execution - in a full implementation this would be more sophisticated
        for effect in effects:
            if isinstance(effect, SetPropertyEffect):
                self._execute_set_property_effect(effect, parameters, entities)
            elif isinstance(effect, MoveEntityEffect):
                self._execute_move_entity_effect(effect, parameters, entities, relations)
    
    def _execute_set_property_effect(
        self, 
        effect: SetPropertyEffect, 
        parameters: Dict[str, Any], 
        entities: Dict[str, Any]
    ) -> None:
        """Execute a set property effect with parameter substitution."""
        # Substitute parameters in property name and value
        property_name = self._substitute_parameters(effect.property_name, parameters)
        value = self._substitute_parameters(effect.value, parameters)
        
        # Get target entity
        target_entity = entities.get(effect.target_entity)
        if target_entity:
            if isinstance(target_entity, dict):
                target_entity[property_name] = value
            elif hasattr(target_entity, 'properties'):
                target_entity.properties[property_name] = value
    
    def _execute_move_entity_effect(
        self, 
        effect: MoveEntityEffect, 
        parameters: Dict[str, Any], 
        entities: Dict[str, Any],
        relations: Optional[RelationsGraph] = None
    ) -> None:
        """Execute a move entity effect with parameter substitution."""
        # Substitute parameters in new container
        new_container = self._substitute_parameters(effect.new_container, parameters)
        
        # Move entity using relations graph
        if relations:
            relations.place_entity(effect.entity_id, new_container)
        
        # Update entity location
        entity = entities.get(effect.entity_id)
        if entity and hasattr(entity, 'current_location_id'):
            entity.current_location_id = new_container
    
    def _substitute_parameters(self, text: str, parameters: Dict[str, Any]) -> Any:
        """Substitute parameters in text (simple implementation)."""
        if isinstance(text, str):
            for param_name, param_value in parameters.items():
                placeholder = f"{{{param_name}}}"
                if placeholder in text:
                    text = text.replace(placeholder, str(param_value))
            return text
        return text
