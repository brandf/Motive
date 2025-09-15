#!/usr/bin/env python3
"""Tests for status effects integration with enhanced configs."""

import pytest
import yaml
from motive.sim_v2.status_effects import (
    StatusEffect, 
    StatusEffectManager, 
    StackingPolicy, 
    StatusEffectSource
)


def load_enhanced_yaml_config(file_path):
    """Load enhanced YAML config file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def test_status_effects_in_enhanced_config():
    """Test that enhanced config includes status effects definitions."""
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_v2.yaml")
    
    # Check that detective_thorne has status_effects
    detective = config["characters"]["detective_thorne"]
    assert "status_effects" in detective
    
    status_effects = detective["status_effects"]
    assert len(status_effects) == 3
    
    # Check investigation_fatigue effect
    fatigue_effect = next(effect for effect in status_effects if effect["name"] == "investigation_fatigue")
    assert fatigue_effect["duration_turns"] == 3
    assert fatigue_effect["stacking_policy"] == "refresh"
    assert fatigue_effect["source"] == "action"
    assert "intelligence" in fatigue_effect["overlays"]
    assert fatigue_effect["overlays"]["intelligence"] == -1
    
    # Check cult_corruption effect
    corruption_effect = next(effect for effect in status_effects if effect["name"] == "cult_corruption")
    assert corruption_effect["duration_turns"] == 5
    assert corruption_effect["stacking_policy"] == "no_stack"
    assert corruption_effect["overlays"]["corruption_level"] == 1
    assert corruption_effect["overlays"]["evil_alignment"] == True
    
    # Check partner_memory effect (permanent)
    memory_effect = next(effect for effect in status_effects if effect["name"] == "partner_memory")
    assert memory_effect["duration_turns"] is None
    assert memory_effect["source"] == "inherent"
    assert memory_effect["overlays"]["investigation_skill"] == 2


def test_status_effects_manager_with_config_data():
    """Test StatusEffectManager with data from enhanced config."""
    manager = StatusEffectManager()
    
    # Create effects based on config data
    fatigue_effect = StatusEffect(
        name="investigation_fatigue",
        duration_turns=3,
        stacking_policy=StackingPolicy.REFRESH,
        source=StatusEffectSource.ACTION,
        overlays={"intelligence": -1, "investigation_skill": -1},
        description="Mental exhaustion from intense investigation"
    )
    
    corruption_effect = StatusEffect(
        name="cult_corruption",
        duration_turns=5,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"corruption_level": 1, "evil_alignment": True, "wisdom": -2},
        description="Dark influence from exposure to cult artifacts"
    )
    
    memory_effect = StatusEffect(
        name="partner_memory",
        duration_turns=None,  # Permanent
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.INHERENT,
        overlays={"investigation_skill": 2, "strength": 1},
        description="Motivation from memories of your fallen partner"
    )
    
    # Apply effects to detective
    manager.apply_effect("detective_thorne", fatigue_effect)
    manager.apply_effect("detective_thorne", corruption_effect)
    manager.apply_effect("detective_thorne", memory_effect)
    
    # Test that all effects are applied
    effects = manager.get_effects("detective_thorne")
    assert len(effects) == 3
    assert "investigation_fatigue" in effects
    assert "cult_corruption" in effects
    assert "partner_memory" in effects
    
    # Test property overlays
    base_properties = {
        "intelligence": 9,
        "investigation_skill": 8,
        "corruption_level": 0,
        "evil_alignment": False,
        "wisdom": 8,
        "strength": 6
    }
    
    effective_properties = manager.get_effective_properties("detective_thorne", base_properties)
    
    # Check overlays are applied correctly
    assert effective_properties["intelligence"] == 8  # 9 - 1 (fatigue)
    assert effective_properties["investigation_skill"] == 9  # 8 - 1 (fatigue) + 2 (memory)
    assert effective_properties["corruption_level"] == 1  # 0 + 1 (corruption)
    assert effective_properties["evil_alignment"] == True  # False -> True (corruption)
    assert effective_properties["wisdom"] == 6  # 8 - 2 (corruption)
    assert effective_properties["strength"] == 7  # 6 + 1 (memory)


def test_status_effects_turn_advancement_with_config():
    """Test turn advancement with effects from config."""
    manager = StatusEffectManager()
    
    # Create temporary effects
    fatigue_effect = StatusEffect(
        name="investigation_fatigue",
        duration_turns=3,
        stacking_policy=StackingPolicy.REFRESH,
        source=StatusEffectSource.ACTION,
        overlays={"intelligence": -1},
        description="Mental exhaustion from intense investigation"
    )
    
    corruption_effect = StatusEffect(
        name="cult_corruption",
        duration_turns=5,
        stacking_policy=StackingPolicy.NO_STACK,
        source=StatusEffectSource.ACTION,
        overlays={"corruption_level": 1},
        description="Dark influence from exposure to cult artifacts"
    )
    
    # Apply effects
    manager.apply_effect("detective_thorne", fatigue_effect)
    manager.apply_effect("detective_thorne", corruption_effect)
    
    # Advance turns
    expired = manager.advance_turn("detective_thorne")
    assert expired == []
    
    expired = manager.advance_turn("detective_thorne")
    assert expired == []
    
    expired = manager.advance_turn("detective_thorne")
    assert "investigation_fatigue" in expired
    assert "cult_corruption" not in expired  # Still has 2 turns left
    
    # Check remaining effects
    effects = manager.get_effects("detective_thorne")
    assert "investigation_fatigue" not in effects
    assert "cult_corruption" in effects
    assert effects["cult_corruption"].duration_turns == 2


def test_status_effects_stacking_policies_with_config():
    """Test stacking policies with effects from config."""
    manager = StatusEffectManager()
    
    # Create effects with different stacking policies
    fatigue_effect_1 = StatusEffect(
        name="investigation_fatigue",
        duration_turns=3,
        stacking_policy=StackingPolicy.REFRESH,
        source=StatusEffectSource.ACTION,
        overlays={"intelligence": -1},
        description="Mental exhaustion from intense investigation"
    )
    
    fatigue_effect_2 = StatusEffect(
        name="investigation_fatigue",
        duration_turns=5,  # Longer duration
        stacking_policy=StackingPolicy.REFRESH,
        source=StatusEffectSource.ACTION,
        overlays={"intelligence": -2},  # Stronger effect
        description="Severe mental exhaustion from intense investigation"
    )
    
    # Apply first effect
    manager.apply_effect("detective_thorne", fatigue_effect_1)
    effects = manager.get_effects("detective_thorne")
    assert effects["investigation_fatigue"].duration_turns == 3
    assert effects["investigation_fatigue"].overlays["intelligence"] == -1
    
    # Apply second effect (should refresh/replace)
    manager.apply_effect("detective_thorne", fatigue_effect_2)
    effects = manager.get_effects("detective_thorne")
    assert effects["investigation_fatigue"].duration_turns == 5
    assert effects["investigation_fatigue"].overlays["intelligence"] == -2
