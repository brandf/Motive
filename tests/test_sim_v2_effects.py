import pytest
from unittest.mock import Mock

from motive.sim_v2.effects import EffectEngine, SetPropertyEffect, MoveEntityEffect
from motive.sim_v2.relations import RelationsGraph


def test_set_property_effect():
    """Test setting a property on an entity."""
    engine = EffectEngine()
    
    # Mock entity with properties
    entity = Mock()
    entity.properties = {"name": "torch", "fuel": 100}
    
    # Create and execute set property effect
    effect = SetPropertyEffect(target_entity="torch_1", property_name="fuel", value=50)
    engine.execute_effect(effect, {"torch_1": entity})
    
    # Verify property was set
    assert entity.properties["fuel"] == 50


def test_move_entity_effect():
    """Test moving an entity between containers."""
    engine = EffectEngine()
    relations = RelationsGraph()
    
    # Setup initial state
    relations.place_entity("torch_1", "room_1")
    
    # Create and execute move effect
    effect = MoveEntityEffect(entity_id="torch_1", new_container="room_2")
    engine.execute_effect(effect, relations=relations)
    
    # Verify entity was moved
    assert relations.get_container_of("torch_1") == "room_2"
    assert "torch_1" in relations.get_contents_of("room_2")
    assert "torch_1" not in relations.get_contents_of("room_1")


def test_effect_engine_executes_multiple_effects():
    """Test that effect engine can execute multiple effects in sequence."""
    engine = EffectEngine()
    relations = RelationsGraph()
    
    # Mock entity
    entity = Mock()
    entity.properties = {"name": "torch", "fuel": 100, "is_lit": False}
    
    # Setup initial state
    relations.place_entity("torch_1", "room_1")
    
    # Create multiple effects
    effects = [
        SetPropertyEffect(target_entity="torch_1", property_name="fuel", value=50),
        SetPropertyEffect(target_entity="torch_1", property_name="is_lit", value=True),
        MoveEntityEffect(entity_id="torch_1", new_container="room_2")
    ]
    
    # Execute all effects
    engine.execute_effects(effects, entities={"torch_1": entity}, relations=relations)
    
    # Verify all effects were applied
    assert entity.properties["fuel"] == 50
    assert entity.properties["is_lit"] is True
    assert relations.get_container_of("torch_1") == "room_2"


def test_effect_handles_missing_entity():
    """Test that effects handle missing entities gracefully."""
    engine = EffectEngine()
    
    # Create effect for non-existent entity
    effect = SetPropertyEffect(target_entity="missing_entity", property_name="fuel", value=50)
    
    # Should not crash when entity doesn't exist
    engine.execute_effect(effect, entities={})
    
    # No exception should be raised


def test_effect_handles_missing_container():
    """Test that move effects handle missing containers gracefully."""
    engine = EffectEngine()
    relations = RelationsGraph()
    
    # Create move effect for non-existent entity
    effect = MoveEntityEffect(entity_id="missing_entity", new_container="room_1")
    
    # Should not crash when entity doesn't exist
    engine.execute_effect(effect, relations=relations)
    
    # No exception should be raised
