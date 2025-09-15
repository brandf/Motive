"""Condition expression parsing and evaluation.

This module provides a simple DSL for parsing string conditions into AST
and evaluating them against entity properties.
"""

from typing import Any, Dict, Union
from dataclasses import dataclass


@dataclass
class ConditionAST:
    """Abstract Syntax Tree for condition expressions."""
    operator: str
    left: str
    right: Union[str, int, float, bool]


class ConditionParser:
    """Parses string conditions into ConditionAST."""
    
    def parse(self, condition_str: str) -> ConditionAST:
        """Parse a condition string into AST."""
        condition_str = condition_str.strip()

        # Parse AND first (lowest precedence)
        if " AND " in condition_str:
            left, right = condition_str.split(" AND ", 1)
            left_ast = self.parse(left.strip())
            right_ast = self.parse(right.strip())
            return ConditionAST(operator="AND", left=left_ast, right=right_ast)
        
        # Then parse comparison operators
        elif " == " in condition_str:
            left, right = condition_str.split(" == ", 1)
            right = self._parse_value(right.strip())
            return ConditionAST(operator="==", left=left.strip(), right=right)
        elif " > " in condition_str:
            left, right = condition_str.split(" > ", 1)
            right = self._parse_value(right.strip())
            return ConditionAST(operator=">", left=left.strip(), right=right)
        elif " < " in condition_str:
            left, right = condition_str.split(" < ", 1)
            right = self._parse_value(right.strip())
            return ConditionAST(operator="<", left=left.strip(), right=right)
        elif " contains " in condition_str:
            left, right = condition_str.split(" contains ", 1)
            right = self._parse_value(right.strip())
            return ConditionAST(operator="contains", left=left.strip(), right=right)
        else:
            raise ValueError(f"Unsupported condition: {condition_str}")
    
    def _parse_value(self, value_str: str) -> Union[str, int, float, bool]:
        """Parse a value string into appropriate type."""
        value_str = value_str.strip()
        
        # Remove quotes for strings
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]
        
        # Parse booleans
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False
        
        # Parse numbers
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            # If not a number, treat as string
            return value_str


class ConditionEvaluator:
    """Evaluates ConditionAST against entity properties."""
    
    def evaluate(self, ast: ConditionAST, properties: Dict[str, Any]) -> bool:
        """Evaluate a condition AST against entity properties."""
        # Handle AND operator with nested ASTs
        if ast.operator == "AND":
            left_result = self.evaluate(ast.left, properties)
            right_result = self.evaluate(ast.right, properties)
            return left_result and right_result
        
        # Handle simple operators
        left_value = properties.get(ast.left)
        
        # Handle missing properties
        if left_value is None:
            return False
        
        # Evaluate based on operator
        if ast.operator == "==":
            return left_value == ast.right
        elif ast.operator == ">":
            return left_value > ast.right
        elif ast.operator == "<":
            return left_value < ast.right
        elif ast.operator == "contains":
            # For string contains
            if isinstance(left_value, str) and isinstance(ast.right, str):
                return ast.right in left_value
            else:
                return False
        else:
            raise ValueError(f"Unsupported operator: {ast.operator}")
