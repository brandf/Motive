#!/usr/bin/env python3
"""Portals system for sim_v2."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class PortalType(Enum):
    """Type of portal."""
    STATIC = "static"      # Fixed destination
    DYNAMIC = "dynamic"    # Destination can change


@dataclass
class PortalDestination:
    """Represents a portal's destination."""
    room_id: str
    portal_type: PortalType
    conditions: List[str]  # Conditions for traversal


class PortalManager:
    """Manages portal-like objects (magic mirror, teleportation circle)."""
    
    def __init__(self):
        self._portals: Dict[str, PortalDestination] = {}  # portal_id -> destination
        self._portal_properties: Dict[str, Dict[str, Any]] = {}  # portal_id -> properties
    
    def create_portal(self, portal_id: str, destination_room: str, portal_type: PortalType = PortalType.STATIC) -> bool:
        """Create a portal with a destination. Returns True if created."""
        if portal_id in self._portals:
            return False  # Portal already exists
        
        # Create portal destination
        destination = PortalDestination(
            room_id=destination_room,
            portal_type=portal_type,
            conditions=["this.located_in.type == 'room'"]  # Default: can only traverse from room
        )
        
        # Store portal
        self._portals[portal_id] = destination
        
        # Initialize properties
        self._portal_properties[portal_id] = {
            "portal_type": portal_type,
            "destination": destination_room
        }
        
        return True
    
    def set_portal_destination(self, portal_id: str, destination_room: str) -> bool:
        """Update portal destination dynamically. Returns True if updated."""
        if portal_id not in self._portals:
            return False
        
        # Update destination
        self._portals[portal_id].room_id = destination_room
        self._portal_properties[portal_id]["destination"] = destination_room
        
        return True
    
    def get_portal_destination(self, portal_id: str) -> Optional[str]:
        """Get current portal destination."""
        if portal_id not in self._portals:
            return None
        
        return self._portals[portal_id].room_id
    
    def can_traverse_portal(self, portal_id: str, entity_id: str, current_location: str) -> bool:
        """Check if entity can traverse portal from current location."""
        if portal_id not in self._portals:
            return False
        
        # Simple condition: can only traverse from room (not inventory)
        # This is a simplified implementation - in a real system, we'd evaluate conditions
        if current_location.endswith("_inventory"):
            return False
        
        return True
    
    def traverse_portal(self, portal_id: str, entity_id: str, current_location: str) -> Optional[str]:
        """Traverse portal and return destination room. Returns None if cannot traverse."""
        if not self.can_traverse_portal(portal_id, entity_id, current_location):
            return None
        
        return self.get_portal_destination(portal_id)
    
    def destroy_portal(self, portal_id: str) -> bool:
        """Destroy a portal. Returns True if destroyed."""
        if portal_id not in self._portals:
            return False
        
        # Remove portal
        del self._portals[portal_id]
        del self._portal_properties[portal_id]
        
        return True
    
    def get_portal_properties(self, portal_id: str) -> Dict[str, Any]:
        """Get portal properties."""
        return self._portal_properties.get(portal_id, {}).copy()
    
    def set_portal_properties(self, portal_id: str, properties: Dict[str, Any]) -> None:
        """Set portal properties."""
        if portal_id not in self._portal_properties:
            self._portal_properties[portal_id] = {}
        
        # Update properties
        self._portal_properties[portal_id].update(properties)
