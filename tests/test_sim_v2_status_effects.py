#!/usr/bin/env python3
"""Tests for sim_v2 status effects system."""

import pytest
from motive.sim_v2.status_effects import (
    StatusEffect, 
    StatusEffectManager, 
    StackingPolicy, 
    StatusEffectSource
)


def test_status_effect_creation():
    """Test creating status effects with different configurations."""
    # Test basic status effect
    effect = StatusEffect(
        name="stunned",
        duration_turns=3,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"can_act": False, "movement_speed": 0},
        description="Unable to take actions"
    )
    
    assert effect.name == "stunned"
    assert effect.duration_turns == 3
    assert effect.stacking_policy == StackingPolicy.NO_STACK
    assert effect.source == StatusEffectSource.ACTION
    assert effect.overlays == {"can_act": False, "movement_speed": 0}
    assert effect.description == "Unable to take actions"
    
    # Test permanent effect
    permanent_effect = StatusEffect(
        name="dark_vision",
        duration_turns=None,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.INHERENT,
        overlays={"can_see_in_dark": True}
    )
    
    assert permanent_effect.duration_turns is None
    assert permanent_effect.source == StatusEffectSource.INHERENT


def test_status_effect_manager_apply_remove():
    """Test applying and removing status effects."""
    manager = StatusEffectManager()
    
    # Create test effect
    effect = StatusEffect(
        name="blessed",
        duration_turns=5,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"holy_power": 2, "resistance": 1}
    )
    
    # Apply effect
    result = manager.apply_effect("player_1", effect)
    assert result is True
    assert manager.has_effect("player_1", "blessed") is True
    
    # Get effects
    effects = manager.get_effects("player_1")
    assert "blessed" in effects
    assert effects["blessed"].duration_turns == 5
    
    # Remove effect
    result = manager.remove_effect("player_1", "blessed")
    assert result is True
    assert manager.has_effect("player_1", "blessed") is False


def test_status_effect_stacking_policies():
    """Test different stacking policies."""
    manager = StatusEffectManager()
    
    # Test NO_STACK policy
    effect1 = StatusEffect(
        name="shield",
        duration_turns=3,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"armor": 2}
    )
    
    effect2 = StatusEffect(
        name="shield",
        duration_turns=5,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"armor": 3}
    )
    
    # Apply first effect
    manager.apply_effect("player_1", effect1)
    effects = manager.get_effects("player_1")
    assert effects["shield"].duration_turns == 3
    assert effects["shield"].overlays["armor"] == 2
    
    # Apply second effect (should replace first)
    manager.apply_effect("player_1", effect2)
    effects = manager.get_effects("player_1")
    assert effects["shield"].duration_turns == 5
    assert effects["shield"].overlays["armor"] == 3


def test_status_effect_turn_advancement():
    """Test turn advancement and effect expiration."""
    manager = StatusEffectManager()
    
    # Create temporary effect
    effect = StatusEffect(
        name="poisoned",
        duration_turns=2,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"health_per_turn": -1}
    )
    
    # Apply effect
    manager.apply_effect("player_1", effect)
    
    # Advance turn once
    expired = manager.advance_turn("player_1")
    assert expired == []
    effects = manager.get_effects("player_1")
    assert effects["poisoned"].duration_turns == 1
    
    # Advance turn again (should expire)
    expired = manager.advance_turn("player_1")
    assert expired == ["poisoned"]
    assert manager.has_effect("player_1", "poisoned") is False


def test_status_effect_property_overlays():
    """Test property overlays from status effects."""
    manager = StatusEffectManager()
    
    # Create effect with overlays
    effect = StatusEffect(
        name="enhanced",
        duration_turns=3,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"strength": 2, "speed": 1}
    )
    
    # Apply effect
    manager.apply_effect("player_1", effect)
    
    # Test property overlays
    base_properties = {"strength": 10, "speed": 5, "health": 100}
    effective_properties = manager.get_effective_properties("player_1", base_properties)
    
    assert effective_properties["strength"] == 12  # 10 + 2
    assert effective_properties["speed"] == 6       # 5 + 1
    assert effective_properties["health"] == 100    # unchanged


def test_status_effect_multiple_effects():
    """Test multiple status effects on same entity."""
    manager = StatusEffectManager()
    
    # Create multiple effects
    blessed = StatusEffect(
        name="blessed",
        duration_turns=3,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"holy_power": 2}
    )
    
    cursed = StatusEffect(
        name="cursed",
        duration_turns=5,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"luck": -1}
    )
    
    # Apply both effects
    manager.apply_effect("player_1", blessed)
    manager.apply_effect("player_1", cursed)
    
    # Check both are present
    effects = manager.get_effects("player_1")
    assert "blessed" in effects
    assert "cursed" in effects
    
    # Test combined property overlays
    base_properties = {"holy_power": 5, "luck": 3}
    effective_properties = manager.get_effective_properties("player_1", base_properties)
    
    assert effective_properties["holy_power"] == 7  # 5 + 2
    assert effective_properties["luck"] == 2         # 3 - 1
