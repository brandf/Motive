#!/usr/bin/env python3
"""Containers system for sim_v2."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ContainerType(Enum):
    """Type of container."""
    BAG = "bag"           # Bag of holding, backpack
    HOLE = "hole"         # Portable hole, pocket dimension
    TENT = "tent"         # Magic tent, portable shelter


@dataclass
class ContainerInterior:
    """Represents a container's interior space."""
    room_id: str
    container_type: ContainerType
    capacity: int
    owner_id: str  # ID of the container object


class ContainerManager:
    """Manages container-like objects (bag of holding, portable hole)."""
    
    def __init__(self):
        self._containers: Dict[str, ContainerInterior] = {}  # container_id -> interior
        self._container_properties: Dict[str, Dict[str, Any]] = {}  # container_id -> properties
        self._container_locations: Dict[str, str] = {}  # container_id -> current_location
        self._next_room_counter = 1
    
    def create_container(self, container_id: str, container_type: ContainerType, capacity: int = 100) -> bool:
        """Create a container with owned interior space. Returns True if created."""
        if container_id in self._containers:
            return False  # Container already exists
        
        # Generate unique interior room ID
        interior_room_id = f"{container_id}_interior_{self._next_room_counter}"
        self._next_room_counter += 1
        
        # Create container interior
        interior = ContainerInterior(
            room_id=interior_room_id,
            container_type=container_type,
            capacity=capacity,
            owner_id=container_id
        )
        
        # Store container
        self._containers[container_id] = interior
        
        # Initialize properties
        self._container_properties[container_id] = {
            "container_type": container_type,
            "capacity": capacity,
            "interior_room": interior_room_id
        }
        
        return True
    
    def get_container_interior(self, container_id: str) -> Optional[str]:
        """Get the interior room ID for a container."""
        if container_id not in self._containers:
            return None
        
        return self._containers[container_id].room_id
    
    def can_enter_container(self, container_id: str, entity_id: str, current_location: str) -> bool:
        """Check if entity can enter container from current location."""
        if container_id not in self._containers:
            return False
        
        # Simple condition: can only enter from room (not inventory)
        # This is a simplified implementation - in a real system, we'd evaluate conditions
        if current_location.endswith("_inventory"):
            return False
        
        return True
    
    def enter_container(self, container_id: str, entity_id: str, current_location: str) -> Optional[str]:
        """Enter container and return interior room ID. Returns None if cannot enter."""
        if not self.can_enter_container(container_id, entity_id, current_location):
            return None
        
        # Track the original location for exit
        self._container_locations[container_id] = current_location
        
        return self.get_container_interior(container_id)
    
    def exit_container(self, container_id: str, entity_id: str, interior_location: str) -> Optional[str]:
        """Exit container and return exterior room ID. Returns None if cannot exit."""
        if container_id not in self._containers:
            return None
        
        # Return the original location where the container was entered from
        return self._container_locations.get(container_id, "exterior_room")
    
    def destroy_container(self, container_id: str) -> bool:
        """Destroy a container and its interior space. Returns True if destroyed."""
        if container_id not in self._containers:
            return False
        
        # Remove container
        del self._containers[container_id]
        del self._container_properties[container_id]
        
        return True
    
    def get_container_properties(self, container_id: str) -> Dict[str, Any]:
        """Get container properties."""
        return self._container_properties.get(container_id, {}).copy()
    
    def set_container_properties(self, container_id: str, properties: Dict[str, Any]) -> None:
        """Set container properties."""
        if container_id not in self._container_properties:
            self._container_properties[container_id] = {}
        
        # Update properties
        self._container_properties[container_id].update(properties)
    
    def get_container_capacity(self, container_id: str) -> int:
        """Get container capacity."""
        if container_id not in self._containers:
            return 0
        
        return self._containers[container_id].capacity
    
    def set_container_capacity(self, container_id: str, capacity: int) -> bool:
        """Set container capacity. Returns True if updated."""
        if container_id not in self._containers:
            return False
        
        # Update capacity
        self._containers[container_id].capacity = capacity
        self._container_properties[container_id]["capacity"] = capacity
        
        return True
