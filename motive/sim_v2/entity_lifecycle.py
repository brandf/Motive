#!/usr/bin/env python3
"""Entity lifecycle system for sim_v2."""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class EntityState(Enum):
    """State of an entity in the lifecycle."""
    ACTIVE = "active"
    DESTROYED = "destroyed"
    CLONED = "cloned"


@dataclass
class EntityLifecycleEvent:
    """Represents an event in an entity's lifecycle."""
    event_type: str  # "spawn", "destroy", "clone"
    entity_id: str
    timestamp: float
    metadata: Dict[str, Any]


class EntityLifecycleManager:
    """Manages entity lifecycle operations (spawn/destroy/clone)."""
    
    def __init__(self):
        self._entities: Dict[str, Dict[str, Any]] = {}  # entity_id -> entity_data
        self._entity_states: Dict[str, EntityState] = {}  # entity_id -> state
        self._lifecycle_events: List[EntityLifecycleEvent] = []
        self._next_id_counter = 1
    
    def spawn_entity(self, definition_id: str, spawn_location: str, custom_properties: Optional[Dict[str, Any]] = None) -> str:
        """Spawn a new entity from a definition. Returns the new entity ID."""
        # Generate unique entity ID
        entity_id = f"{definition_id}_{self._next_id_counter}"
        self._next_id_counter += 1
        
        # Create entity data
        entity_data = {
            "definition_id": definition_id,
            "location": spawn_location,
            "spawn_time": time.time()
        }
        
        # Add custom properties if provided
        if custom_properties:
            entity_data.update(custom_properties)
        
        # Store entity
        self._entities[entity_id] = entity_data
        self._entity_states[entity_id] = EntityState.ACTIVE
        
        # Record lifecycle event
        event = EntityLifecycleEvent(
            event_type="spawn",
            entity_id=entity_id,
            timestamp=time.time(),
            metadata={
                "definition_id": definition_id,
                "location": spawn_location,
                "custom_properties": custom_properties or {}
            }
        )
        self._lifecycle_events.append(event)
        
        return entity_id
    
    def destroy_entity(self, entity_id: str, reason: str = "manual") -> bool:
        """Destroy an entity. Returns True if destroyed."""
        if entity_id not in self._entities:
            return False
        
        if self._entity_states[entity_id] == EntityState.DESTROYED:
            return False  # Already destroyed
        
        # Mark as destroyed
        self._entity_states[entity_id] = EntityState.DESTROYED
        
        # Record lifecycle event
        event = EntityLifecycleEvent(
            event_type="destroy",
            entity_id=entity_id,
            timestamp=time.time(),
            metadata={
                "reason": reason,
                "definition_id": self._entities[entity_id]["definition_id"]
            }
        )
        self._lifecycle_events.append(event)
        
        return True
    
    def clone_entity(self, source_entity_id: str, new_location: Optional[str] = None) -> Optional[str]:
        """Clone an entity. Returns new entity ID or None if failed."""
        if source_entity_id not in self._entities:
            return None
        
        if self._entity_states[source_entity_id] == EntityState.DESTROYED:
            return None  # Can't clone destroyed entity
        
        # Get source entity data
        source_data = self._entities[source_entity_id]
        
        # Generate new entity ID
        clone_id = f"{source_data['definition_id']}_clone_{self._next_id_counter}"
        self._next_id_counter += 1
        
        # Create clone data (copy all properties except location)
        clone_data = source_data.copy()
        clone_data["location"] = new_location or source_data["location"]
        clone_data["spawn_time"] = time.time()
        
        # Store clone
        self._entities[clone_id] = clone_data
        self._entity_states[clone_id] = EntityState.CLONED
        
        # Record lifecycle event
        event = EntityLifecycleEvent(
            event_type="clone",
            entity_id=clone_id,
            timestamp=time.time(),
            metadata={
                "source_entity": source_entity_id,
                "definition_id": source_data["definition_id"],
                "location": clone_data["location"]
            }
        )
        self._lifecycle_events.append(event)
        
        return clone_id
    
    def get_entity_state(self, entity_id: str) -> Optional[EntityState]:
        """Get the current state of an entity."""
        return self._entity_states.get(entity_id)
    
    def get_entity_data(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity data (only for active entities)."""
        if entity_id not in self._entities:
            return None
        
        if self._entity_states[entity_id] == EntityState.DESTROYED:
            return None
        
        return self._entities[entity_id].copy()
    
    def get_lifecycle_events(self, entity_id: Optional[str] = None) -> List[EntityLifecycleEvent]:
        """Get lifecycle events, optionally filtered by entity_id."""
        if entity_id is None:
            return self._lifecycle_events.copy()
        
        return [event for event in self._lifecycle_events if event.entity_id == entity_id]
    
    def is_entity_active(self, entity_id: str) -> bool:
        """Check if an entity is active (not destroyed)."""
        if entity_id not in self._entity_states:
            return False
        
        return self._entity_states[entity_id] != EntityState.DESTROYED
    
    def get_active_entities(self) -> List[str]:
        """Get list of all active entity IDs."""
        return [entity_id for entity_id, state in self._entity_states.items() 
                if state != EntityState.DESTROYED]
