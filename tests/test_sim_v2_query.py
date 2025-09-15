import pytest
from unittest.mock import Mock

from motive.sim_v2.query import QueryEngine, QueryAST
from motive.sim_v2.conditions import ConditionParser, ConditionAST
from motive.sim_v2.relations import RelationsGraph


def test_parse_simple_query():
    """Test parsing a simple query string."""
    engine = QueryEngine()
    
    # Parse "room.contains.torch"
    query_ast = engine.parse("room.contains.torch")
    
    assert isinstance(query_ast, QueryAST)
    assert query_ast.start_entity == "room"
    assert query_ast.relation == "contains"
    assert query_ast.target_entity == "torch"


def test_parse_query_with_condition():
    """Test parsing a query with a condition."""
    engine = QueryEngine()
    
    # Parse "room.contains.torch where fuel > 50"
    query_ast = engine.parse("room.contains.torch where fuel > 50")
    
    assert query_ast.start_entity == "room"
    assert query_ast.relation == "contains"
    assert query_ast.target_entity == "torch"
    assert isinstance(query_ast.condition, ConditionAST)
    assert query_ast.condition.operator == ">"
    assert query_ast.condition.left == "fuel"
    assert query_ast.condition.right == 50


def test_execute_simple_query():
    """Test executing a simple query against relations graph."""
    engine = QueryEngine()
    relations = RelationsGraph()
    
    # Setup relations
    relations.place_entity("torch_1", "room_1")
    relations.place_entity("torch_2", "room_1")
    relations.place_entity("torch_3", "room_2")
    
    # Mock entity properties
    entities = {
        "room_1": {"name": "Tavern", "capacity": 50},
        "torch_1": {"name": "Torch", "fuel": 100},
        "torch_2": {"name": "Torch", "fuel": 30},
        "torch_3": {"name": "Torch", "fuel": 80}
    }
    
    # Execute query: "room_1.contains.torch"
    results = engine.execute("room_1.contains.torch", relations, entities)
    
    # Should return torch_1 and torch_2 (both in room_1)
    assert len(results) == 2
    assert "torch_1" in results
    assert "torch_2" in results


def test_execute_query_with_condition():
    """Test executing a query with a condition filter."""
    engine = QueryEngine()
    relations = RelationsGraph()
    
    # Setup relations
    relations.place_entity("torch_1", "room_1")
    relations.place_entity("torch_2", "room_1")
    
    # Mock entity properties
    entities = {
        "torch_1": {"name": "Torch", "fuel": 100},
        "torch_2": {"name": "Torch", "fuel": 30}
    }
    
    # Execute query: "room_1.contains.torch where fuel > 50"
    results = engine.execute("room_1.contains.torch where fuel > 50", relations, entities)
    
    # Should only return torch_1 (fuel=100 > 50)
    assert len(results) == 1
    assert "torch_1" in results


def test_execute_query_no_results():
    """Test executing a query that returns no results."""
    engine = QueryEngine()
    relations = RelationsGraph()
    
    # Setup relations
    relations.place_entity("torch_1", "room_1")
    
    # Mock entity properties
    entities = {
        "torch_1": {"name": "Torch", "fuel": 30}
    }
    
    # Execute query: "room_1.contains.torch where fuel > 50"
    results = engine.execute("room_1.contains.torch where fuel > 50", relations, entities)
    
    # Should return empty list
    assert len(results) == 0
