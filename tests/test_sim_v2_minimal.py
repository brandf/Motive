import pytest


def test_entity_definition_and_instance_creation():
    from motive.sim_v2.definitions import EntityDefinition, DefinitionRegistry
    from motive.sim_v2.properties import PropertySchema, PropertyType
    from motive.sim_v2.entity import MotiveEntity

    # Define a simple torch with typed properties
    torch_def = EntityDefinition(
        definition_id="torch",
        types=["object"],
        properties={
            "is_lit": PropertySchema(type=PropertyType.BOOLEAN, default=False),
            "fuel": PropertySchema(type=PropertyType.NUMBER, default=100),
            "name": PropertySchema(type=PropertyType.STRING, default="Torch"),
        },
    )

    registry = DefinitionRegistry()
    registry.add(torch_def)

    ent: MotiveEntity = registry.instantiate(
        definition_id="torch",
        entity_id="torch_1",
        overrides={"fuel": 50},
    )

    assert ent.id == "torch_1"
    assert ent.definition_id == "torch"
    assert ent.types == ["object"]
    assert ent.properties.get("is_lit") is False
    assert ent.properties.get("fuel") == 50
    assert ent.properties.get("name") == "Torch"


def test_type_enforcement_in_properties():
    from motive.sim_v2.properties import PropertySchema, PropertyType, PropertyStore

    schema = {
        "is_lit": PropertySchema(type=PropertyType.BOOLEAN, default=False),
        "fuel": PropertySchema(type=PropertyType.NUMBER, default=100),
        "title": PropertySchema(type=PropertyType.STRING, default="Untitled"),
    }

    props = PropertyStore(schema=schema)
    props.set("fuel", 25)
    props.set("is_lit", True)
    props.set("title", "My Torch")

    assert props.get("fuel") == 25
    assert props.get("is_lit") is True
    assert props.get("title") == "My Torch"

    with pytest.raises(TypeError):
        props.set("fuel", "a lot")  # wrong type

    with pytest.raises(KeyError):
        props.set("unknown", 1)


def test_relations_move_and_contains():
    from motive.sim_v2.relations import RelationsGraph

    graph = RelationsGraph()

    room_id = "room_1"
    item_id = "torch_1"
    bag_id = "bag_1"

    # Place item in room
    graph.place_entity(entity_id=item_id, container_id=room_id)
    assert graph.get_container_of(item_id) == room_id
    assert item_id in graph.get_contents_of(room_id)

    # Move item to bag
    graph.place_entity(entity_id=bag_id, container_id=room_id)
    graph.move_entity(entity_id=item_id, new_container_id=bag_id)
    assert graph.get_container_of(item_id) == bag_id
    assert item_id in graph.get_contents_of(bag_id)
    assert item_id not in graph.get_contents_of(room_id)


