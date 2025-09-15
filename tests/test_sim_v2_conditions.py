import pytest

from motive.sim_v2.conditions import ConditionParser, ConditionAST, ConditionEvaluator


def test_parse_simple_equals_condition():
    """Test parsing a simple equals condition."""
    parser = ConditionParser()
    
    # Parse "name == 'torch'"
    ast = parser.parse("name == 'torch'")
    
    assert isinstance(ast, ConditionAST)
    assert ast.operator == "=="
    assert ast.left == "name"
    assert ast.right == "torch"


def test_parse_numeric_comparison():
    """Test parsing numeric comparison conditions."""
    parser = ConditionParser()
    
    # Parse "fuel > 50"
    ast = parser.parse("fuel > 50")
    
    assert ast.operator == ">"
    assert ast.left == "fuel"
    assert ast.right == 50  # Should be parsed as number


def test_parse_boolean_condition():
    """Test parsing boolean conditions."""
    parser = ConditionParser()
    
    # Parse "is_lit == true"
    ast = parser.parse("is_lit == true")
    
    assert ast.operator == "=="
    assert ast.left == "is_lit"
    assert ast.right is True  # Should be parsed as boolean


def test_evaluate_simple_condition():
    """Test evaluating a simple condition against entity properties."""
    parser = ConditionParser()
    evaluator = ConditionEvaluator()
    
    # Parse condition
    ast = parser.parse("name == 'torch'")
    
    # Mock entity properties
    properties = {"name": "torch", "fuel": 100}
    
    # Evaluate
    result = evaluator.evaluate(ast, properties)
    assert result is True


def test_evaluate_numeric_condition():
    """Test evaluating numeric conditions."""
    parser = ConditionParser()
    evaluator = ConditionEvaluator()
    
    # Parse condition
    ast = parser.parse("fuel > 50")
    
    # Mock entity properties
    properties = {"name": "torch", "fuel": 100}
    
    # Evaluate
    result = evaluator.evaluate(ast, properties)
    assert result is True


def test_evaluate_false_condition():
    """Test evaluating conditions that return false."""
    parser = ConditionParser()
    evaluator = ConditionEvaluator()
    
    # Parse condition
    ast = parser.parse("fuel < 50")
    
    # Mock entity properties
    properties = {"name": "torch", "fuel": 100}
    
    # Evaluate
    result = evaluator.evaluate(ast, properties)
    assert result is False


def test_evaluate_missing_property():
    """Test evaluating conditions with missing properties."""
    parser = ConditionParser()
    evaluator = ConditionEvaluator()
    
    # Parse condition
    ast = parser.parse("missing_prop == 'value'")
    
    # Mock entity properties (missing the property)
    properties = {"name": "torch"}
    
    # Evaluate - should handle missing property gracefully
    result = evaluator.evaluate(ast, properties)
    assert result is False  # Missing property should evaluate to false
