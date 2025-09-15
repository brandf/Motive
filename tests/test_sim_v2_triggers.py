import pytest
from unittest.mock import Mock

from motive.sim_v2.triggers import TriggerEngine, Trigger, TriggerState
from motive.sim_v2.conditions import ConditionParser, ConditionAST
from motive.sim_v2.effects import SetPropertyEffect, MoveEntityEffect


def test_trigger_engine_registers_trigger():
    """Test registering a trigger with the engine."""
    engine = TriggerEngine()
    parser = ConditionParser()
    
    # Create trigger condition
    condition = parser.parse("fuel > 50")
    
    # Create trigger
    trigger = Trigger(
        trigger_id="fuel_warning",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "warning", "Fuel running low")]
    )
    
    # Register trigger
    engine.register_trigger(trigger)
    
    # Verify trigger is registered
    assert engine.get_trigger("fuel_warning") == trigger


def test_trigger_engine_evaluates_conditions():
    """Test that trigger engine evaluates conditions against entity state."""
    engine = TriggerEngine()
    parser = ConditionParser()
    
    # Create trigger for fuel > 50
    condition = parser.parse("fuel > 50")
    trigger = Trigger(
        trigger_id="fuel_warning",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "warning", "Fuel running low")]
    )
    
    engine.register_trigger(trigger)
    
    # Mock entity with high fuel
    entities = {"torch_1": {"fuel": 100}}
    
    # Evaluate triggers
    engine.evaluate_triggers(entities)
    
    # Trigger should be active (fuel > 50)
    assert engine.get_trigger_state("fuel_warning").is_active is True


def test_trigger_engine_edge_detection():
    """Test that triggers detect condition edge changes (false->true, true->false)."""
    engine = TriggerEngine()
    parser = ConditionParser()
    
    # Create trigger for fuel > 50
    condition = parser.parse("fuel > 50")
    trigger = Trigger(
        trigger_id="fuel_warning",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "warning", "Fuel running low")]
    )
    
    engine.register_trigger(trigger)
    
    # Mock entity with low fuel initially
    entities = {"torch_1": {"fuel": 30}}
    
    # First evaluation - trigger should be inactive
    engine.evaluate_triggers(entities)
    assert engine.get_trigger_state("fuel_warning").is_active is False
    
    # Increase fuel - trigger should activate
    entities["torch_1"]["fuel"] = 100
    engine.evaluate_triggers(entities)
    assert engine.get_trigger_state("fuel_warning").is_active is True
    
    # Decrease fuel - trigger should deactivate
    entities["torch_1"]["fuel"] = 30
    engine.evaluate_triggers(entities)
    assert engine.get_trigger_state("fuel_warning").is_active is False


def test_trigger_engine_executes_effects_on_activation():
    """Test that trigger executes effects when condition becomes true."""
    engine = TriggerEngine()
    parser = ConditionParser()
    
    # Create trigger with effects
    condition = parser.parse("fuel > 50")
    trigger = Trigger(
        trigger_id="fuel_warning",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "warning", "Fuel running low")]
    )
    
    engine.register_trigger(trigger)
    
    # Mock entity
    entity = Mock()
    entity.properties = {"fuel": 30}
    entities = {"torch_1": entity}
    
    # First evaluation - trigger inactive
    engine.evaluate_triggers(entities)
    
    # Increase fuel to activate trigger
    entity.properties["fuel"] = 100
    engine.evaluate_triggers(entities)
    
    # Effect should have been executed
    assert entity.properties["warning"] == "Fuel running low"


def test_trigger_engine_undoes_effects_on_deactivation():
    """Test that trigger undoes effects when condition becomes false."""
    engine = TriggerEngine()
    parser = ConditionParser()
    
    # Create trigger with undo effects
    condition = parser.parse("fuel > 50")
    trigger = Trigger(
        trigger_id="fuel_warning",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "warning", "Fuel running low")],
        undo_effects=[SetPropertyEffect("torch_1", "warning", "")]
    )
    
    engine.register_trigger(trigger)
    
    # Mock entity
    entity = Mock()
    entity.properties = {"fuel": 100, "warning": ""}
    entities = {"torch_1": entity}
    
    # First evaluation - trigger active
    engine.evaluate_triggers(entities)
    assert entity.properties["warning"] == "Fuel running low"
    
    # Decrease fuel to deactivate trigger
    entity.properties["fuel"] = 30
    engine.evaluate_triggers(entities)
    
    # Undo effect should have been executed
    assert entity.properties["warning"] == ""


def test_trigger_engine_handles_missing_entities():
    """Test that trigger engine handles missing entities gracefully."""
    engine = TriggerEngine()
    parser = ConditionParser()
    
    # Create trigger for non-existent entity
    condition = parser.parse("fuel > 50")
    trigger = Trigger(
        trigger_id="fuel_warning",
        condition=condition,
        effects=[SetPropertyEffect("missing_entity", "warning", "Fuel running low")]
    )
    
    engine.register_trigger(trigger)
    
    # Evaluate with empty entities - should not crash
    engine.evaluate_triggers({})
    
    # Trigger should be inactive due to missing property
    assert engine.get_trigger_state("fuel_warning").is_active is False
