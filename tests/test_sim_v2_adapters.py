import pytest
from unittest.mock import Mock

from motive.sim_v2.adapters import V1ToV2Adapter
from motive.sim_v2.definitions import EntityDefinition, DefinitionRegistry
from motive.sim_v2.properties import PropertySchema, PropertyType


def test_adapter_converts_v1_room_to_v2_definition():
    """Test that v1 room config converts to v2 entity definition."""
    adapter = V1ToV2Adapter()
    
    # Mock v1 room config (simplified from hearth_and_shadow_rooms.yaml)
    v1_room = {
        "id": "tavern",
        "name": "The Rusty Anchor Tavern", 
        "description": "A cozy tavern with warm lighting.",
        "tags": ["cozy", "public"],
        "properties": {"lighting": "warm", "capacity": 50}
    }
    
    definition = adapter.room_to_definition(v1_room)
    
    assert isinstance(definition, EntityDefinition)
    assert definition.definition_id == "tavern"
    assert "room" in definition.types
    assert definition.properties["name"].default == "The Rusty Anchor Tavern"
    assert definition.properties["description"].default == "A cozy tavern with warm lighting."
    assert definition.properties["lighting"].default == "warm"
    assert definition.properties["capacity"].default == 50


def test_adapter_converts_v1_object_to_v2_definition():
    """Test that v1 object type config converts to v2 entity definition."""
    adapter = V1ToV2Adapter()
    
    # Mock v1 object type config (simplified from hearth_and_shadow_objects.yaml)
    v1_object_type = {
        "id": "torch",
        "name": "Torch",
        "description": "A wooden torch that can be lit.",
        "properties": {
            "readable": True,
            "text": "This torch can provide light when lit.",
            "is_lit": False,
            "fuel": 100
        }
    }
    
    definition = adapter.object_type_to_definition(v1_object_type)
    
    assert isinstance(definition, EntityDefinition)
    assert definition.definition_id == "torch"
    assert "object" in definition.types
    assert definition.properties["name"].default == "Torch"
    assert definition.properties["description"].default == "A wooden torch that can be lit."
    assert definition.properties["readable"].default is True
    assert definition.properties["is_lit"].default is False
    assert definition.properties["fuel"].default == 100


def test_adapter_converts_v1_character_to_v2_definition():
    """Test that v1 character config converts to v2 entity definition."""
    adapter = V1ToV2Adapter()
    
    # Mock v1 character config (simplified from hearth_and_shadow_characters.yaml)
    v1_character = {
        "id": "detective_thorne",
        "name": "Detective James Thorne",
        "backstory": "A former city guard turned private investigator.",
        "motive": "avenge_partner",
        "properties": {"investigation_skill": 8, "reputation": "good"}
    }
    
    definition = adapter.character_to_definition(v1_character)
    
    assert isinstance(definition, EntityDefinition)
    assert definition.definition_id == "detective_thorne"
    assert "character" in definition.types
    assert definition.properties["name"].default == "Detective James Thorne"
    assert definition.properties["backstory"].default == "A former city guard turned private investigator."
    assert definition.properties["motive"].default == "avenge_partner"
    assert definition.properties["investigation_skill"].default == 8
    assert definition.properties["reputation"].default == "good"


def test_adapter_converts_v1_object_instance_to_v2_entity():
    """Test that v1 object instance converts to v2 entity instance."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # First create the definition
    v1_object_type = {
        "id": "torch",
        "name": "Torch", 
        "description": "A wooden torch.",
        "properties": {"is_lit": False, "fuel": 100}
    }
    definition = adapter.object_type_to_definition(v1_object_type)
    registry.add(definition)
    
    # Then create instance
    v1_instance = {
        "id": "torch_1",
        "name": "Tavern Torch",
        "object_type_id": "torch",
        "current_room_id": "tavern",
        "description": "A torch mounted on the tavern wall."
    }
    
    entity = adapter.object_instance_to_entity(v1_instance, registry)
    
    assert entity.id == "torch_1"
    assert entity.definition_id == "torch"
    assert entity.properties.get("name") == "Tavern Torch"
    assert entity.properties.get("description") == "A torch mounted on the tavern wall."
    assert entity.properties.get("is_lit") is False  # from definition
    assert entity.properties.get("fuel") == 100  # from definition


def test_adapter_handles_missing_properties_gracefully():
    """Test that adapter handles missing or malformed properties without crashing."""
    adapter = V1ToV2Adapter()
    
    # Minimal room config
    v1_room = {
        "id": "minimal_room",
        "name": "Minimal Room"
        # No description, tags, or properties
    }
    
    definition = adapter.room_to_definition(v1_room)
    
    assert definition.definition_id == "minimal_room"
    assert definition.properties["name"].default == "Minimal Room"
    assert definition.properties["description"].default == ""  # default empty string
    # Should not crash on missing optional fields
