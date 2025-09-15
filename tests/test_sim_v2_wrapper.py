import pytest
from unittest.mock import Mock

from motive.sim_v2.wrapper import V1EntityWrapper
from motive.sim_v2.adapters import V1ToV2Adapter
from motive.sim_v2.definitions import DefinitionRegistry


def test_wrapper_converts_tags_to_properties():
    """Test that v1 entity tags are converted to typed properties."""
    # Mock v1 room with tags
    v1_room = Mock()
    v1_room.tags = {"cozy", "public", "lighted"}
    v1_room.properties = {"capacity": 50}
    
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Create definition from v1 room
    room_config = {
        "id": "tavern",
        "name": "Tavern",
        "description": "A cozy tavern.",
        "tags": ["cozy", "public", "lighted"],
        "properties": {"capacity": 50}
    }
    definition = adapter.room_to_definition(room_config)
    registry.add(definition)
    
    # Create wrapper
    wrapper = V1EntityWrapper(v1_room, definition, registry)
    
    # Test that tags are accessible as properties (sorted alphabetically)
    assert wrapper.get_property("tags") == "cozy,lighted,public"
    assert wrapper.get_property("capacity") == 50
    assert wrapper.get_property("name") == "Tavern"


def test_wrapper_maintains_v1_interface():
    """Test that wrapper maintains compatibility with existing v1 code."""
    # Mock v1 room
    v1_room = Mock()
    v1_room.tags = {"cozy"}
    v1_room.properties = {"capacity": 50}
    v1_room.id = "tavern"
    v1_room.name = "Tavern"
    
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    room_config = {
        "id": "tavern", 
        "name": "Tavern",
        "description": "A tavern.",
        "tags": ["cozy"],
        "properties": {"capacity": 50}
    }
    definition = adapter.room_to_definition(room_config)
    registry.add(definition)
    
    wrapper = V1EntityWrapper(v1_room, definition, registry)
    
    # Should still access v1 attributes directly
    assert wrapper.v1_entity.id == "tavern"
    assert wrapper.v1_entity.name == "Tavern"
    assert wrapper.v1_entity.tags == {"cozy"}


def test_wrapper_handles_missing_tags():
    """Test that wrapper handles entities without tags gracefully."""
    # Mock v1 room without tags
    v1_room = Mock()
    v1_room.tags = set()  # Empty tags
    v1_room.properties = {}
    
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    room_config = {
        "id": "minimal_room",
        "name": "Minimal Room",
        "description": "A minimal room."
    }
    definition = adapter.room_to_definition(room_config)
    registry.add(definition)
    
    wrapper = V1EntityWrapper(v1_room, definition, registry)
    
    # Should handle empty tags gracefully
    assert wrapper.get_property("tags") == ""  # Empty string for no tags
    assert wrapper.get_property("name") == "Minimal Room"
