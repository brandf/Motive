import pytest
from unittest.mock import Mock

from motive.sim_v2.visibility import VisibilityEngine, VisibilityRule
from motive.sim_v2.relations import RelationsGraph


def test_visibility_engine_default_visibility():
    """Test that entities are visible by default."""
    engine = VisibilityEngine()
    relations = RelationsGraph()
    
    # Setup entities in same room
    relations.place_entity("torch_1", "room_1")
    relations.place_entity("character_1", "room_1")
    
    # Mock entity properties
    entities = {
        "torch_1": {"name": "Torch", "visible": True},
        "character_1": {"name": "Character", "visible": True}
    }
    
    # Test default visibility
    assert engine.can_see("character_1", "torch_1", entities, relations) is True
    assert engine.can_see("torch_1", "character_1", entities, relations) is True


def test_visibility_engine_hidden_entities():
    """Test that hidden entities are not visible."""
    engine = VisibilityEngine()
    relations = RelationsGraph()
    
    # Setup entities
    relations.place_entity("torch_1", "room_1")
    relations.place_entity("character_1", "room_1")
    relations.place_entity("hidden_key", "room_1")
    
    # Mock entity properties
    entities = {
        "torch_1": {"name": "Torch", "visible": True},
        "character_1": {"name": "Character", "visible": True},
        "hidden_key": {"name": "Hidden Key", "visible": False}
    }
    
    # Test hidden entity visibility
    assert engine.can_see("character_1", "hidden_key", entities, relations) is False
    assert engine.can_see("character_1", "torch_1", entities, relations) is True


def test_visibility_engine_different_rooms():
    """Test that entities in different rooms are not visible."""
    engine = VisibilityEngine()
    relations = RelationsGraph()
    
    # Setup entities in different rooms
    relations.place_entity("character_1", "room_1")
    relations.place_entity("torch_1", "room_2")
    
    # Mock entity properties
    entities = {
        "character_1": {"name": "Character", "visible": True},
        "torch_1": {"name": "Torch", "visible": True}
    }
    
    # Test cross-room visibility
    assert engine.can_see("character_1", "torch_1", entities, relations) is False


def test_visibility_engine_search_action():
    """Test that search action can reveal hidden entities."""
    engine = VisibilityEngine()
    relations = RelationsGraph()
    
    # Setup entities
    relations.place_entity("character_1", "room_1")
    relations.place_entity("hidden_key", "room_1")
    
    # Mock entity properties
    entities = {
        "character_1": {"name": "Character", "visible": True},
        "hidden_key": {"name": "Hidden Key", "visible": False, "searchable": True}
    }
    
    # Test search action
    engine.perform_search("character_1", "room_1", entities, relations)
    
    # Hidden key should now be visible
    assert engine.can_see("character_1", "hidden_key", entities, relations) is True


def test_visibility_engine_search_non_searchable():
    """Test that search doesn't reveal non-searchable entities."""
    engine = VisibilityEngine()
    relations = RelationsGraph()
    
    # Setup entities
    relations.place_entity("character_1", "room_1")
    relations.place_entity("hidden_key", "room_1")
    
    # Mock entity properties
    entities = {
        "character_1": {"name": "Character", "visible": True},
        "hidden_key": {"name": "Hidden Key", "visible": False, "searchable": False}
    }
    
    # Test search action
    engine.perform_search("character_1", "room_1", entities, relations)
    
    # Hidden key should still be hidden
    assert engine.can_see("character_1", "hidden_key", entities, relations) is False


def test_visibility_engine_get_visible_entities():
    """Test getting all visible entities for a character."""
    engine = VisibilityEngine()
    relations = RelationsGraph()
    
    # Setup entities
    relations.place_entity("character_1", "room_1")
    relations.place_entity("torch_1", "room_1")
    relations.place_entity("hidden_key", "room_1")
    relations.place_entity("torch_2", "room_2")
    
    # Mock entity properties
    entities = {
        "character_1": {"name": "Character", "visible": True},
        "torch_1": {"name": "Torch", "visible": True},
        "hidden_key": {"name": "Hidden Key", "visible": False, "searchable": True},
        "torch_2": {"name": "Torch 2", "visible": True}
    }
    
    # Test getting visible entities
    visible = engine.get_visible_entities("character_1", entities, relations)
    
    # Should only see torch_1 (same room, visible)
    assert "torch_1" in visible
    assert "hidden_key" not in visible
    assert "torch_2" not in visible  # Different room
    assert "character_1" not in visible  # Don't see self
