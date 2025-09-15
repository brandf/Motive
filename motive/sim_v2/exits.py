"""Unified exit management system.

This module provides a unified system for managing exits between rooms,
including state properties like visibility, traversability, and locking.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from .relations import RelationsGraph


@dataclass
class ExitState:
    """State of an exit (visible, traversable, locked)."""
    visible: bool = True
    traversable: bool = True
    is_locked: bool = False


class ExitManager:
    """Manages exits between rooms with state properties."""
    
    def __init__(self):
        self._exits: Dict[str, ExitState] = {}
        self._exit_directions: Dict[str, Dict[str, str]] = {}  # room_id -> direction -> exit_id
    
    def create_exit(self, from_room: str, to_room: str, direction: str, relations: RelationsGraph) -> str:
        """Create an exit between rooms."""
        exit_id = f"exit_{from_room}_{direction}_{to_room}"
        
        # Create exit state
        self._exits[exit_id] = ExitState()
        
        # Track direction mapping
        if from_room not in self._exit_directions:
            self._exit_directions[from_room] = {}
        self._exit_directions[from_room][direction] = exit_id
        
        # Add to relations graph (simplified - just track the connection)
        # In a full implementation, we'd have more sophisticated exit relations
        relations.place_entity(to_room, from_room)  # Simplified: to_room is "contained" by from_room for exit purposes
        
        return exit_id
    
    def get_exit_state(self, exit_id: str) -> Optional[ExitState]:
        """Get the state of an exit."""
        return self._exits.get(exit_id)
    
    def set_exit_visible(self, exit_id: str, visible: bool) -> None:
        """Set the visibility of an exit."""
        if exit_id in self._exits:
            self._exits[exit_id].visible = visible
    
    def set_exit_traversable(self, exit_id: str, traversable: bool) -> None:
        """Set the traversability of an exit."""
        if exit_id in self._exits:
            self._exits[exit_id].traversable = traversable
    
    def set_exit_locked(self, exit_id: str, locked: bool) -> None:
        """Set the locked state of an exit."""
        if exit_id in self._exits:
            self._exits[exit_id].is_locked = locked
    
    def can_traverse_exit(self, exit_id: str) -> bool:
        """Check if an exit can be traversed."""
        exit_state = self._exits.get(exit_id)
        if exit_state is None:
            return False
        
        return exit_state.visible and exit_state.traversable and not exit_state.is_locked
    
    def get_exit_by_direction(self, room_id: str, direction: str) -> Optional[str]:
        """Get exit ID by direction from a room."""
        room_exits = self._exit_directions.get(room_id, {})
        return room_exits.get(direction)
