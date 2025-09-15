import pytest
from unittest.mock import Mock

from motive.sim_v2.affordances import AffordanceEngine, Affordance, AffordanceRule
from motive.sim_v2.conditions import ConditionParser, ConditionAST
from motive.sim_v2.effects import SetPropertyEffect, MoveEntityEffect


def test_affordance_engine_registers_affordance():
    """Test registering an affordance with the engine."""
    engine = AffordanceEngine()
    parser = ConditionParser()
    
    # Create affordance condition
    condition = parser.parse("is_lit == true")
    
    # Create affordance
    affordance = Affordance(
        affordance_id="light_torch",
        action_name="light",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", True)]
    )
    
    # Register affordance
    engine.register_affordance(affordance)
    
    # Verify affordance is registered
    assert engine.get_affordance("light_torch") == affordance


def test_affordance_engine_get_available_actions():
    """Test getting available actions for an entity based on affordances."""
    engine = AffordanceEngine()
    parser = ConditionParser()
    
    # Create affordance for lit torch
    condition = parser.parse("is_lit == true")
    affordance = Affordance(
        affordance_id="light_torch",
        action_name="light",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", True)]
    )
    
    engine.register_affordance(affordance)
    
    # Mock entity properties
    entities = {"torch_1": {"is_lit": True, "fuel": 100}}
    
    # Get available actions
    actions = engine.get_available_actions("torch_1", entities)
    
    # Should include the affordance action
    assert "light" in actions


def test_affordance_engine_condition_filtering():
    """Test that affordances are filtered by conditions."""
    engine = AffordanceEngine()
    parser = ConditionParser()
    
    # Create affordance for lit torch only
    condition = parser.parse("is_lit == true")
    affordance = Affordance(
        affordance_id="light_torch",
        action_name="light",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", True)]
    )
    
    engine.register_affordance(affordance)
    
    # Mock unlit torch
    entities = {"torch_1": {"is_lit": False, "fuel": 100}}
    
    # Get available actions
    actions = engine.get_available_actions("torch_1", entities)
    
    # Should not include the affordance action (condition not met)
    assert "light" not in actions


def test_affordance_engine_execute_action():
    """Test executing an action through affordances."""
    engine = AffordanceEngine()
    parser = ConditionParser()
    
    # Create affordance
    condition = parser.parse("fuel > 0")
    affordance = Affordance(
        affordance_id="light_torch",
        action_name="light",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", True)]
    )
    
    engine.register_affordance(affordance)
    
    # Mock entity
    entity = Mock()
    entity.properties = {"fuel": 100, "is_lit": False}
    entities = {"torch_1": entity}
    
    # Execute action
    result = engine.execute_action("torch_1", "light", entities)
    
    # Should succeed and execute effects
    assert result is True
    assert entity.properties["is_lit"] is True


def test_affordance_engine_execute_invalid_action():
    """Test executing an invalid action."""
    engine = AffordanceEngine()
    
    # Mock entity
    entities = {"torch_1": {"fuel": 100}}
    
    # Execute non-existent action
    result = engine.execute_action("torch_1", "invalid_action", entities)
    
    # Should fail
    assert result is False


def test_affordance_engine_multiple_affordances():
    """Test multiple affordances for the same entity."""
    engine = AffordanceEngine()
    parser = ConditionParser()
    
    # Create multiple affordances
    light_condition = parser.parse("fuel > 0")
    light_affordance = Affordance(
        affordance_id="light_torch",
        action_name="light",
        condition=light_condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", True)]
    )
    
    extinguish_condition = parser.parse("is_lit == true")
    extinguish_affordance = Affordance(
        affordance_id="extinguish_torch",
        action_name="extinguish",
        condition=extinguish_condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", False)]
    )
    
    engine.register_affordance(light_affordance)
    engine.register_affordance(extinguish_affordance)
    
    # Mock lit torch
    entities = {"torch_1": {"fuel": 100, "is_lit": True}}
    
    # Get available actions
    actions = engine.get_available_actions("torch_1", entities)
    
    # Should include both actions
    assert "light" in actions
    assert "extinguish" in actions


def test_affordance_engine_entity_specific_affordances():
    """Test that affordances can be entity-specific."""
    engine = AffordanceEngine()
    parser = ConditionParser()
    
    # Create entity-specific affordance
    condition = parser.parse("name == 'magic_torch'")
    affordance = Affordance(
        affordance_id="magic_light",
        action_name="magic_light",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", True)]
    )
    
    engine.register_affordance(affordance)
    
    # Mock magic torch
    entities = {"torch_1": {"name": "magic_torch", "fuel": 100}}
    
    # Get available actions
    actions = engine.get_available_actions("torch_1", entities)
    
    # Should include magic action
    assert "magic_light" in actions
    
    # Mock regular torch
    entities = {"torch_1": {"name": "regular_torch", "fuel": 100}}
    
    # Get available actions
    actions = engine.get_available_actions("torch_1", entities)
    
    # Should not include magic action
    assert "magic_light" not in actions
