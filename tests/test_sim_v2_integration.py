import pytest
import yaml
from pathlib import Path

from motive.sim_v2.adapters import V1ToV2Adapter
from motive.sim_v2.definitions import DefinitionRegistry
from motive.sim_v2.wrapper import V1EntityWrapper
from motive.sim_v2.conditions import ConditionParser, ConditionEvaluator
from motive.sim_v2.query import QueryEngine
from motive.sim_v2.effects import EffectEngine, SetPropertyEffect, MoveEntityEffect
from motive.sim_v2.exits import ExitManager


def load_real_yaml_config(file_path: str) -> dict:
    """Load a real YAML config file."""
    config_path = Path(__file__).parent.parent / file_path
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_adapter_converts_real_room_config():
    """Test adapter against real hearth_and_shadow_rooms.yaml."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Load real room config
    config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    
    # Convert first room (town_square)
    room_config = config["rooms"]["town_square"]
    definition = adapter.room_to_definition(room_config)
    registry.add(definition)
    
    # Verify conversion
    assert definition.definition_id == "town_square"
    assert "room" in definition.types
    assert definition.properties["name"].default == "Town Square"
    assert "The heart of Blackwater" in definition.properties["description"].default
    
    # Test that we can create an entity from the definition
    entity = registry.create_entity("town_square", "town_square_instance")
    assert entity.id == "town_square_instance"
    assert entity.get_property("name") == "Town Square"


def test_adapter_converts_real_object_type_config():
    """Test adapter against real hearth_and_shadow_objects.yaml."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Load real object config
    config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml")
    
    # Convert notice_board object type
    object_config = config["object_types"]["notice_board"]
    definition = adapter.object_type_to_definition(object_config)
    registry.add(definition)
    
    # Verify conversion
    assert definition.definition_id == "notice_board"
    assert "object" in definition.types
    assert definition.properties["name"].default == "Notice Board"
    assert definition.properties["readable"].default is True
    assert "Various town announcements" in definition.properties["text"].default


def test_adapter_converts_real_object_instance():
    """Test adapter converts real object instances from rooms."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Load both configs
    rooms_config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    objects_config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml")
    
    # Convert object type definition first
    notice_board_type = objects_config["object_types"]["notice_board"]
    type_definition = adapter.object_type_to_definition(notice_board_type)
    registry.add(type_definition)
    
    # Convert object instance from room
    room_config = rooms_config["rooms"]["town_square"]
    notice_board_instance = room_config["objects"]["notice_board"]
    entity = adapter.object_instance_to_entity(notice_board_instance, registry)
    
    # Verify conversion
    assert entity.id == "notice_board"
    assert entity.definition_id == "notice_board"
    assert entity.get_property("name") == "Notice Board"
    assert entity.get_property("readable") is True
    assert entity.get_property("text") == "Various town announcements and missing person posters are posted here."


def test_wrapper_with_real_v1_entity():
    """Test V1EntityWrapper with real v1 entity structure."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Load and convert real config
    config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    room_config = config["rooms"]["town_square"]
    definition = adapter.room_to_definition(room_config)
    registry.add(definition)
    
    # Create mock v1 entity (simulating existing v1 room structure)
    class MockV1Room:
        def __init__(self, config):
            self.id = config["id"]
            self.name = config["name"]
            self.description = config["description"]
            self.tags = set()  # v1 rooms don't have tags in this config
            self.properties = {}
    
    v1_room = MockV1Room(room_config)
    wrapper = V1EntityWrapper(v1_room, definition, registry)
    
    # Test wrapper functionality
    assert wrapper.get_property("name") == "Town Square"
    assert wrapper.get_property("description") == room_config["description"]
    assert wrapper.get_property("tags") == ""  # Empty tags handled gracefully
    assert wrapper.v1_entity.id == "town_square"  # v1 interface preserved


def test_condition_evaluation_with_real_properties():
    """Test condition evaluation against real entity properties."""
    parser = ConditionParser()
    evaluator = ConditionEvaluator()
    
    # Load real object config
    config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml")
    notice_board = config["object_types"]["notice_board"]
    
    # Test condition evaluation
    ast = parser.parse("readable == true")
    result = evaluator.evaluate(ast, notice_board["properties"])
    assert result is True
    
    # Test string condition
    ast = parser.parse("text contains 'missing person'")
    # Note: This would need "contains" operator implementation
    # For now, test basic equality
    ast = parser.parse("text == 'Various town announcements and missing person posters are posted here.'")
    result = evaluator.evaluate(ast, notice_board["properties"])
    assert result is True


def test_query_system_with_real_relations():
    """Test query system with real room-object relationships."""
    engine = QueryEngine()
    from motive.sim_v2.relations import RelationsGraph
    
    relations = RelationsGraph()
    
    # Load real room config
    config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    room_config = config["rooms"]["town_square"]
    
    # Setup relations based on real room objects
    for obj_id, obj_data in room_config["objects"].items():
        relations.place_entity(obj_id, "town_square")
    
    # Mock entity properties
    entities = {}
    for obj_id, obj_data in room_config["objects"].items():
        entities[obj_id] = {
            "name": obj_data["name"],
            "description": obj_data["description"]
        }
    
    # Test query
    results = engine.execute("town_square.contains.notice_board", relations, entities)
    assert "notice_board" in results
    
    # Test query with condition (if we had readable property)
    # This would need the object type properties merged with instance
    # For now, test basic query
    results = engine.execute("town_square.contains.broken_fountain", relations, entities)
    assert "broken_fountain" in results


def test_effects_with_real_entities():
    """Test effects system with real entity structures."""
    engine = EffectEngine()
    from motive.sim_v2.relations import RelationsGraph
    
    relations = RelationsGraph()
    
    # Load real configs
    rooms_config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    objects_config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml")
    
    # Create mock entities based on real data
    class MockEntity:
        def __init__(self, properties):
            self.properties = properties.copy()
    
    # Create entities
    notice_board_props = objects_config["object_types"]["notice_board"]["properties"]
    entities = {
        "notice_board": MockEntity(notice_board_props),
        "broken_fountain": MockEntity(objects_config["object_types"]["broken_fountain"]["properties"])
    }
    
    # Setup relations
    relations.place_entity("notice_board", "town_square")
    relations.place_entity("broken_fountain", "town_square")
    
    # Test set property effect
    effect = SetPropertyEffect("notice_board", "text", "Updated notice board text")
    engine.execute_effect(effect, entities)
    assert entities["notice_board"].properties["text"] == "Updated notice board text"
    
    # Test move entity effect
    effect = MoveEntityEffect("notice_board", "tavern")
    engine.execute_effect(effect, relations=relations)
    assert relations.get_container_of("notice_board") == "tavern"


def test_exit_manager_with_real_room_exits():
    """Test exit manager with real room exit data."""
    manager = ExitManager()
    from motive.sim_v2.relations import RelationsGraph
    
    relations = RelationsGraph()
    
    # Load real room config
    config = load_real_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms.yaml")
    room_config = config["rooms"]["town_square"]
    
    # Create exits based on real room data
    exit_ids = {}
    for direction, exit_data in room_config["exits"].items():
        exit_id = manager.create_exit(
            "town_square", 
            exit_data["destination_room_id"], 
            direction, 
            relations
        )
        exit_ids[direction] = exit_id
    
    # Test exit creation
    assert "tavern" in exit_ids
    assert "church" in exit_ids
    assert "bank" in exit_ids
    
    # Test exit state
    tavern_exit = manager.get_exit_by_direction("town_square", "tavern")
    assert tavern_exit is not None
    assert manager.can_traverse_exit(tavern_exit) is True
    
    # Test exit modification
    manager.set_exit_locked(tavern_exit, True)
    assert manager.can_traverse_exit(tavern_exit) is False
