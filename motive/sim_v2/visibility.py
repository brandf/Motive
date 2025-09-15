"""Visibility and search mechanics.

This module provides computed visibility properties and search mechanics
for entities, allowing hidden objects to be discovered through actions.
"""

from typing import Dict, List, Set, Any
from dataclasses import dataclass
from .relations import RelationsGraph


@dataclass
class VisibilityRule:
    """Rule for determining entity visibility."""
    condition: str  # Condition expression
    visible: bool   # Whether entity is visible when condition is true


class VisibilityEngine:
    """Manages entity visibility and search mechanics."""
    
    def __init__(self):
        self._search_results: Dict[str, Set[str]] = {}  # character_id -> set of discovered entity_ids
    
    def can_see(self, observer_id: str, target_id: str, entities: Dict[str, Dict[str, Any]], relations: RelationsGraph) -> bool:
        """Check if observer can see target entity."""
        # Don't see self
        if observer_id == target_id:
            return False
        
        # Check if entities are in same room
        observer_container = relations.get_container_of(observer_id)
        target_container = relations.get_container_of(target_id)
        
        if observer_container != target_container:
            return False
        
        # Check target visibility
        target_entity = entities.get(target_id)
        if target_entity is None:
            return False
        
        # Default visibility
        target_visible = target_entity.get("visible", True)
        if not target_visible:
            # Check if target was discovered through search
            if observer_id in self._search_results and target_id in self._search_results[observer_id]:
                return True
            return False
        
        return True
    
    def perform_search(self, searcher_id: str, room_id: str, entities: Dict[str, Dict[str, Any]], relations: RelationsGraph) -> List[str]:
        """Perform search action to discover hidden entities."""
        discovered = []
        
        # Get all entities in the room
        room_contents = relations.get_contents_of(room_id)
        
        # Initialize search results for searcher if needed
        if searcher_id not in self._search_results:
            self._search_results[searcher_id] = set()
        
        # Search for hidden, searchable entities
        for entity_id in room_contents:
            entity = entities.get(entity_id)
            if entity is None:
                continue
            
            # Check if entity is hidden and searchable
            if (not entity.get("visible", True) and 
                entity.get("searchable", False) and 
                entity_id not in self._search_results[searcher_id]):
                
                # Discover the entity
                self._search_results[searcher_id].add(entity_id)
                discovered.append(entity_id)
        
        return discovered
    
    def get_visible_entities(self, observer_id: str, entities: Dict[str, Dict[str, Any]], relations: RelationsGraph) -> List[str]:
        """Get all entities visible to the observer."""
        visible = []
        
        # Get observer's container
        observer_container = relations.get_container_of(observer_id)
        if observer_container is None:
            return visible
        
        # Get all entities in same container
        room_contents = relations.get_contents_of(observer_container)
        
        # Check visibility for each entity
        for entity_id in room_contents:
            if self.can_see(observer_id, entity_id, entities, relations):
                visible.append(entity_id)
        
        return visible
    
    def is_discovered(self, searcher_id: str, entity_id: str) -> bool:
        """Check if entity was discovered through search."""
        return (searcher_id in self._search_results and 
                entity_id in self._search_results[searcher_id])
    
    def reset_search_results(self, searcher_id: str) -> None:
        """Reset search results for a character (useful for testing)."""
        if searcher_id in self._search_results:
            self._search_results[searcher_id].clear()
