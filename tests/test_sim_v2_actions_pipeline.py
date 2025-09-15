#!/usr/bin/env python3
"""Tests for sim_v2 actions pipeline."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from motive.sim_v2.actions_pipeline import (
    ActionDefinition, 
    ActionPipeline, 
    ActionResult,
    ActionParameter,
    ActionRequirement
)
from motive.sim_v2.effects import Effect, SetPropertyEffect, MoveEntityEffect
from motive.sim_v2.conditions import ConditionAST
from motive.sim_v2.relations import RelationsGraph


@dataclass
class MockEntity:
    """Mock entity for testing."""
    id: str
    name: str
    properties: Dict[str, Any]
    current_location_id: str = "room_1"


def test_action_definition_creation():
    """Test creating action definitions."""
    # Create move action definition
    move_action = ActionDefinition(
        action_id="move",
        name="move",
        description="Move in a specified direction",
        cost=10,
        parameters=[
            ActionParameter(
                name="direction",
                type="string",
                description="Direction to move (north, south, east, west)"
            )
        ],
        requirements=[
            ActionRequirement(
                type="exit_exists",
                condition="exits.{direction}.destination_room_id != null"
            )
        ],
        effects=[
            MoveEntityEffect(
                entity_id="player",
                new_container="exits.{direction}.destination_room_id"
            )
        ]
    )
    
    assert move_action.action_id == "move"
    assert move_action.cost == 10
    assert len(move_action.parameters) == 1
    assert len(move_action.requirements) == 1
    assert len(move_action.effects) == 1


def test_action_pipeline_registration():
    """Test registering actions with the pipeline."""
    pipeline = ActionPipeline()
    
    # Register move action
    move_action = ActionDefinition(
        action_id="move",
        name="move",
        description="Move in a specified direction",
        cost=10,
        parameters=[],
        requirements=[],
        effects=[]
    )
    
    pipeline.register_action(move_action)
    
    # Test retrieval
    retrieved_action = pipeline.get_action("move")
    assert retrieved_action is not None
    assert retrieved_action.action_id == "move"
    
    # Test non-existent action
    assert pipeline.get_action("nonexistent") is None


def test_action_pipeline_parameter_validation():
    """Test parameter validation for actions."""
    pipeline = ActionPipeline()
    
    # Register action with required parameter
    action = ActionDefinition(
        action_id="say",
        name="say",
        description="Say something",
        cost=10,
        parameters=[
            ActionParameter(
                name="message",
                type="string",
                description="Message to say",
                required=True
            )
        ],
        requirements=[],
        effects=[]
    )
    
    pipeline.register_action(action)
    
    # Test valid parameters
    result = pipeline.validate_parameters("say", {"message": "Hello!"})
    assert result.is_valid is True
    
    # Test missing required parameter
    result = pipeline.validate_parameters("say", {})
    assert result.is_valid is False
    assert "message" in result.error_message


def test_action_pipeline_requirement_evaluation():
    """Test requirement evaluation for actions."""
    pipeline = ActionPipeline()
    
    # Create condition for requirement
    condition = ConditionAST(
        operator="==",
        left="player.current_location_id",
        right="room_1"
    )
    
    # Register action with requirement
    action = ActionDefinition(
        action_id="pickup",
        name="pickup",
        description="Pick up an object",
        cost=10,
        parameters=[
            ActionParameter(
                name="object_name",
                type="string",
                description="Name of object to pick up"
            )
        ],
        requirements=[
            ActionRequirement(
                type="condition",
                condition=condition
            )
        ],
        effects=[]
    )
    
    pipeline.register_action(action)
    
    # Create mock entities
    entities = {
        "player": MockEntity("player", "Player", {"current_location_id": "room_1"}),
        "room_1": MockEntity("room_1", "Room 1", {})
    }
    
    # Test requirement evaluation
    result = pipeline.evaluate_requirements("pickup", {"object_name": "torch"}, entities)
    assert result.requirements_met is True
    
    # Test failing requirement
    entities["player"].properties["current_location_id"] = "room_2"
    result = pipeline.evaluate_requirements("pickup", {"object_name": "torch"}, entities)
    assert result.requirements_met is False


def test_action_pipeline_execution():
    """Test action execution through the pipeline."""
    pipeline = ActionPipeline()
    
    # Register action with effects
    action = ActionDefinition(
        action_id="set_property",
        name="set_property",
        description="Set a property on an entity",
        cost=5,
        parameters=[
            ActionParameter(
                name="property_name",
                type="string",
                description="Name of property to set"
            ),
            ActionParameter(
                name="property_value",
                type="string",
                description="Value to set"
            )
        ],
        requirements=[],
        effects=[
            SetPropertyEffect(
                target_entity="player",
                property_name="{property_name}",
                value="{property_value}"
            )
        ]
    )
    
    pipeline.register_action(action)
    
    # Create mock entities
    entities = {
        "player": MockEntity("player", "Player", {})
    }
    
    # Execute action
    result = pipeline.execute_action(
        "set_property",
        {"property_name": "mood", "property_value": "happy"},
        entities
    )
    
    assert result.success is True
    assert entities["player"].properties["mood"] == "happy"


def test_action_pipeline_cost_calculation():
    """Test action cost calculation."""
    pipeline = ActionPipeline()
    
    # Register action with cost
    action = ActionDefinition(
        action_id="expensive_action",
        name="expensive_action",
        description="An expensive action",
        cost=25,
        parameters=[],
        requirements=[],
        effects=[]
    )
    
    pipeline.register_action(action)
    
    # Test cost calculation
    cost = pipeline.get_action_cost("expensive_action")
    assert cost == 25
    
    # Test non-existent action
    cost = pipeline.get_action_cost("nonexistent")
    assert cost == 0


def test_action_pipeline_available_actions():
    """Test getting available actions for an entity."""
    pipeline = ActionPipeline()
    
    # Register multiple actions
    move_action = ActionDefinition(
        action_id="move",
        name="move",
        description="Move",
        cost=10,
        parameters=[],
        requirements=[],
        effects=[]
    )
    
    say_action = ActionDefinition(
        action_id="say",
        name="say",
        description="Say something",
        cost=10,
        parameters=[],
        requirements=[],
        effects=[]
    )
    
    pipeline.register_action(move_action)
    pipeline.register_action(say_action)
    
    # Test getting available actions
    available = pipeline.get_available_actions()
    assert len(available) == 2
    assert "move" in available
    assert "say" in available


def test_action_pipeline_error_handling():
    """Test error handling in action pipeline."""
    pipeline = ActionPipeline()
    
    # Test executing non-existent action
    result = pipeline.execute_action("nonexistent", {}, {})
    assert result.success is False
    assert "not found" in result.error_message.lower()
    
    # Test executing action with invalid parameters
    action = ActionDefinition(
        action_id="test_action",
        name="test_action",
        description="Test action",
        cost=10,
        parameters=[
            ActionParameter(
                name="required_param",
                type="string",
                description="Required parameter",
                required=True
            )
        ],
        requirements=[],
        effects=[]
    )
    
    pipeline.register_action(action)
    
    result = pipeline.execute_action("test_action", {}, {})
    assert result.success is False
    assert "parameter" in result.error_message.lower()


def test_action_pipeline_with_relations():
    """Test action pipeline with relations graph."""
    pipeline = ActionPipeline()
    relations = RelationsGraph()
    
    # Register move action that uses relations
    action = ActionDefinition(
        action_id="move",
        name="move",
        description="Move between rooms",
        cost=10,
        parameters=[
            ActionParameter(
                name="direction",
                type="string",
                description="Direction to move"
            )
        ],
        requirements=[],
        effects=[
            MoveEntityEffect(
                entity_id="player",
                new_container="room_2"
            )
        ]
    )
    
    pipeline.register_action(action)
    
    # Setup relations
    relations.place_entity("player", "room_1")
    relations.place_entity("room_2", "world")
    
    # Create entities
    entities = {
        "player": MockEntity("player", "Player", {}),
        "room_1": MockEntity("room_1", "Room 1", {}),
        "room_2": MockEntity("room_2", "Room 2", {})
    }
    
    # Execute move action
    result = pipeline.execute_action(
        "move",
        {"direction": "north"},
        entities,
        relations=relations
    )
    
    assert result.success is True
    assert relations.get_contents_of("room_2") == ["player"]
