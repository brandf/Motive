#!/usr/bin/env python3
"""Status effects system for sim_v2."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class StackingPolicy(Enum):
    """Policy for how status effects stack."""
    NO_STACK = "no_stack"  # New effect replaces old one
    REFRESH = "refresh"     # New effect refreshes duration
    LIMITED_STACK = "limited_stack"  # Stack up to a limit


class StatusEffectSource(Enum):
    """Source of a status effect."""
    INHERENT = "inherent"      # Character trait/ability
    INVENTORY = "inventory"    # Item carried in inventory
    ACTION = "action"          # Applied by an action


@dataclass
class StatusEffect:
    """Represents a status effect with duration and properties."""
    name: str
    duration_turns: Optional[int]  # None = permanent until manually removed
    stacking_policy: StackingPolicy
    source: StatusEffectSource
    overlays: Dict[str, Any]  # Property overlays to apply
    description: str = ""


class StatusEffectManager:
    """Manages status effects on entities."""
    
    def __init__(self):
        self._effects: Dict[str, Dict[str, StatusEffect]] = {}  # entity_id -> {effect_name -> effect}
    
    def apply_effect(self, entity_id: str, effect: StatusEffect) -> bool:
        """Apply a status effect to an entity. Returns True if applied."""
        if entity_id not in self._effects:
            self._effects[entity_id] = {}
        
        # Handle stacking policy
        if effect.name in self._effects[entity_id]:
            existing_effect = self._effects[entity_id][effect.name]
            
            if effect.stacking_policy == StackingPolicy.NO_STACK:
                # Replace existing effect
                self._effects[entity_id][effect.name] = effect
            elif effect.stacking_policy == StackingPolicy.REFRESH:
                # Refresh duration
                self._effects[entity_id][effect.name] = effect
            elif effect.stacking_policy == StackingPolicy.LIMITED_STACK:
                # For now, just replace (could implement stacking later)
                self._effects[entity_id][effect.name] = effect
        else:
            # New effect
            self._effects[entity_id][effect.name] = effect
        
        return True
    
    def remove_effect(self, entity_id: str, effect_name: str) -> bool:
        """Remove a status effect from an entity. Returns True if removed."""
        if entity_id not in self._effects:
            return False
        
        if effect_name not in self._effects[entity_id]:
            return False
        
        del self._effects[entity_id][effect_name]
        
        # Clean up empty entity entry
        if not self._effects[entity_id]:
            del self._effects[entity_id]
        
        return True
    
    def get_effects(self, entity_id: str) -> Dict[str, StatusEffect]:
        """Get all status effects on an entity."""
        return self._effects.get(entity_id, {}).copy()
    
    def has_effect(self, entity_id: str, effect_name: str) -> bool:
        """Check if an entity has a specific status effect."""
        if entity_id not in self._effects:
            return False
        return effect_name in self._effects[entity_id]
    
    def advance_turn(self, entity_id: str) -> List[str]:
        """Advance turn for an entity, returning list of expired effect names."""
        if entity_id not in self._effects:
            return []
        
        expired_effects = []
        
        for effect_name, effect in list(self._effects[entity_id].items()):
            if effect.duration_turns is not None:
                effect.duration_turns -= 1
                
                if effect.duration_turns <= 0:
                    expired_effects.append(effect_name)
                    del self._effects[entity_id][effect_name]
        
        # Clean up empty entity entry
        if not self._effects[entity_id]:
            del self._effects[entity_id]
        
        return expired_effects
    
    def get_effective_properties(self, entity_id: str, base_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Get effective properties after applying status effect overlays."""
        effective_properties = base_properties.copy()
        
        if entity_id not in self._effects:
            return effective_properties
        
        # Apply overlays from all active effects
        for effect in self._effects[entity_id].values():
            for property_name, overlay_value in effect.overlays.items():
                if property_name in effective_properties:
                    # Apply overlay (assume numeric addition for now)
                    if isinstance(effective_properties[property_name], (int, float)) and isinstance(overlay_value, (int, float)):
                        effective_properties[property_name] += overlay_value
                    else:
                        # For non-numeric properties, overlay replaces
                        effective_properties[property_name] = overlay_value
                else:
                    # New property
                    effective_properties[property_name] = overlay_value
        
        return effective_properties
