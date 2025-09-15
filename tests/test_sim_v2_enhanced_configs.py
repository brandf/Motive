import pytest
import yaml
from pathlib import Path

from motive.sim_v2.adapters import V1ToV2Adapter
from motive.sim_v2.definitions import DefinitionRegistry
from motive.sim_v2.conditions import ConditionParser, ConditionEvaluator
from motive.sim_v2.query import QueryEngine
from motive.sim_v2.effects import EffectEngine
from motive.sim_v2.exits import ExitManager
from motive.sim_v2.visibility import VisibilityEngine
from motive.sim_v2.triggers import TriggerEngine
from motive.sim_v2.affordances import AffordanceEngine


def load_enhanced_yaml_config(file_path: str) -> dict:
    """Load an enhanced YAML config file."""
    config_path = Path(__file__).parent.parent / file_path
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_enhanced_objects_config_conversion():
    """Test that enhanced objects config converts to v2 definitions."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Load enhanced objects config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_v2.yaml")
    
    # Convert torch object type
    torch_config = config["object_types"]["torch"]
    definition = adapter.object_type_to_definition(torch_config)
    registry.add(definition)
    
    # Verify conversion
    assert definition.definition_id == "torch"
    assert "object" in definition.types
    assert definition.properties["name"].default == "Torch"
    assert definition.properties["is_lit"].default is False
    assert definition.properties["fuel"].default == 100
    assert definition.properties["visible"].default is True
    assert definition.properties["searchable"].default is False


def test_enhanced_rooms_config_conversion():
    """Test that enhanced rooms config converts to v2 definitions."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Load enhanced rooms config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_v2.yaml")
    
    # Convert town_square room
    room_config = config["rooms"]["town_square"]
    definition = adapter.room_to_definition(room_config)
    registry.add(definition)
    
    # Verify conversion
    assert definition.definition_id == "town_square"
    assert "room" in definition.types
    assert definition.properties["name"].default == "Town Square"
    assert "The heart of Blackwater" in definition.properties["description"].default


def test_enhanced_characters_config_conversion():
    """Test that enhanced characters config converts to v2 definitions."""
    adapter = V1ToV2Adapter()
    registry = DefinitionRegistry()
    
    # Load enhanced characters config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_v2.yaml")
    
    # Convert detective_thorne character
    char_config = config["characters"]["detective_thorne"]
    definition = adapter.character_to_definition(char_config)
    registry.add(definition)
    
    # Verify conversion
    assert definition.definition_id == "detective_thorne"
    assert "character" in definition.types
    assert definition.properties["name"].default == "Detective James Thorne"
    assert definition.properties["investigation_skill"].default == 8
    assert definition.properties["reputation"].default == "good"
    assert definition.properties["corruption_level"].default == 0


def test_enhanced_visibility_mechanics():
    """Test visibility mechanics with enhanced configs."""
    engine = VisibilityEngine()
    from motive.sim_v2.relations import RelationsGraph
    
    relations = RelationsGraph()
    
    # Load enhanced objects config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_v2.yaml")
    
    # Setup entities based on enhanced config
    entities = {
        "torch_1": {
            "name": "Torch",
            "visible": True,
            "searchable": False,
            "is_lit": False,
            "fuel": 100
        },
        "hidden_key": {
            "name": "Hidden Key",
            "visible": False,  # Hidden by default
            "searchable": True,  # Can be discovered
            "key_type": "ornate",
            "magical": True
        },
        "cult_symbol": {
            "name": "Cult Symbol",
            "visible": False,  # Hidden until discovered
            "searchable": True,
            "evil_energy": True,
            "corrupting": True
        }
    }
    
    # Setup relations
    relations.place_entity("character_1", "room_1")
    relations.place_entity("torch_1", "room_1")
    relations.place_entity("hidden_key", "room_1")
    relations.place_entity("cult_symbol", "room_1")
    
    # Test visibility
    assert engine.can_see("character_1", "torch_1", entities, relations) is True
    assert engine.can_see("character_1", "hidden_key", entities, relations) is False
    assert engine.can_see("character_1", "cult_symbol", entities, relations) is False
    
    # Test search action
    discovered = engine.perform_search("character_1", "room_1", entities, relations)
    assert "hidden_key" in discovered
    assert "cult_symbol" in discovered
    
    # After search, hidden entities should be visible
    assert engine.can_see("character_1", "hidden_key", entities, relations) is True
    assert engine.can_see("character_1", "cult_symbol", entities, relations) is True


def test_enhanced_triggers_mechanics():
    """Test triggers mechanics with enhanced configs."""
    engine = TriggerEngine()
    parser = ConditionParser()
    
    # Load enhanced objects config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_v2.yaml")
    
    # Create trigger based on enhanced config
    condition = parser.parse("fuel > 50")
    from motive.sim_v2.triggers import Trigger
    from motive.sim_v2.effects import SetPropertyEffect
    
    trigger = Trigger(
        trigger_id="fuel_warning",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "warning", "Fuel running low")]
    )
    
    engine.register_trigger(trigger)
    
    # Mock entity with high fuel
    entities = {"torch_1": {"fuel": 100}}
    
    # Evaluate triggers
    engine.evaluate_triggers(entities)
    
    # Trigger should be active (fuel > 50)
    assert engine.get_trigger_state("fuel_warning").is_active is True
    
    # Decrease fuel
    entities["torch_1"]["fuel"] = 30
    engine.evaluate_triggers(entities)
    
    # Trigger should be inactive (fuel <= 50)
    assert engine.get_trigger_state("fuel_warning").is_active is False


def test_enhanced_affordances_mechanics():
    """Test affordances mechanics with enhanced configs."""
    engine = AffordanceEngine()
    parser = ConditionParser()
    
    # Load enhanced objects config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_v2.yaml")
    
    # Create affordance based on enhanced config
    condition = parser.parse("is_lit == false AND fuel > 0")
    from motive.sim_v2.affordances import Affordance
    from motive.sim_v2.effects import SetPropertyEffect
    
    affordance = Affordance(
        affordance_id="light_torch",
        action_name="light",
        condition=condition,
        effects=[SetPropertyEffect("torch_1", "is_lit", True)]
    )
    
    engine.register_affordance(affordance)
    
    # Mock unlit torch
    entities = {"torch_1": {"is_lit": False, "fuel": 100}}
    
    # Get available actions
    actions = engine.get_available_actions("torch_1", entities)
    assert "light" in actions
    
    # Execute action
    result = engine.execute_action("torch_1", "light", entities)
    assert result is True
    assert entities["torch_1"]["is_lit"] is True


def test_enhanced_exits_mechanics():
    """Test enhanced exits mechanics."""
    manager = ExitManager()
    from motive.sim_v2.relations import RelationsGraph
    
    relations = RelationsGraph()
    
    # Load enhanced rooms config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_v2.yaml")
    
    # Create exits based on enhanced config
    room_config = config["rooms"]["town_square"]
    
    # Create tavern exit
    tavern_exit = manager.create_exit(
        "town_square", 
        "tavern", 
        "tavern", 
        relations
    )
    
    # Test exit creation
    assert tavern_exit is not None
    assert manager.can_traverse_exit(tavern_exit) is True
    
    # Test exit modification
    manager.set_exit_locked(tavern_exit, True)
    assert manager.can_traverse_exit(tavern_exit) is False
    
    # Test direction mapping
    exit_by_direction = manager.get_exit_by_direction("town_square", "tavern")
    assert exit_by_direction == tavern_exit


def test_enhanced_condition_evaluation():
    """Test enhanced condition evaluation with new operators."""
    parser = ConditionParser()
    evaluator = ConditionEvaluator()
    
    # Load enhanced objects config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_v2.yaml")
    
    # Test contains operator with enhanced config
    notice_board = config["object_types"]["notice_board"]
    
    # Test contains condition
    ast = parser.parse("text contains 'announcements'")
    result = evaluator.evaluate(ast, notice_board["properties"])
    assert result is True
    
    # Test boolean condition
    ast = parser.parse("readable == true")
    result = evaluator.evaluate(ast, notice_board["properties"])
    assert result is True


def test_enhanced_query_system():
    """Test enhanced query system with new features."""
    engine = QueryEngine()
    from motive.sim_v2.relations import RelationsGraph
    
    relations = RelationsGraph()
    
    # Load enhanced rooms config
    config = load_enhanced_yaml_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_v2.yaml")
    
    # Setup relations based on enhanced room objects
    room_config = config["rooms"]["town_square"]
    
    for obj_id, obj_data in room_config["objects"].items():
        relations.place_entity(obj_id, "town_square")
    
    # Mock entity properties
    entities = {}
    for obj_id, obj_data in room_config["objects"].items():
        entities[obj_id] = {
            "name": obj_data["name"],
            "description": obj_data["description"],
            "visible": obj_data.get("properties", {}).get("visible", True),
            "searchable": obj_data.get("properties", {}).get("searchable", False)
        }
    
    # Test query with visibility condition    
    results = engine.execute("town_square.contains.notice_board where visible == true", relations, entities)
    assert "notice_board" in results

    # Test query with searchable condition    
    results = engine.execute("town_square.contains.broken_fountain where searchable == true", relations, entities)
    assert "broken_fountain" in results
