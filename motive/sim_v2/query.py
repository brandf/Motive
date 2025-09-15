"""Query system for targeting entities with conditions.

This module provides a simple query DSL for finding entities based on
relations and conditions, inspired by graph query languages.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from .conditions import ConditionParser, ConditionAST
from .relations import RelationsGraph


@dataclass
class QueryAST:
    """Abstract Syntax Tree for query expressions."""
    start_entity: str
    relation: str
    target_entity: str
    condition: Optional[ConditionAST] = None


class QueryEngine:
    """Parses and executes queries against entity relations."""
    
    def __init__(self):
        self.condition_parser = ConditionParser()
    
    def parse(self, query_str: str) -> QueryAST:
        """Parse a query string into QueryAST."""
        query_str = query_str.strip()
        
        # Check for condition
        if " where " in query_str:
            main_query, condition_str = query_str.split(" where ", 1)
            condition = self.condition_parser.parse(condition_str.strip())
        else:
            main_query = query_str
            condition = None
        
        # Parse main query: "entity.relation.target"
        parts = main_query.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid query format: {query_str}")
        
        start_entity, relation, target_entity = parts
        
        return QueryAST(
            start_entity=start_entity,
            relation=relation,
            target_entity=target_entity,
            condition=condition
        )
    
    def execute(
        self, 
        query_str: str, 
        relations: RelationsGraph, 
        entities: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Execute a query and return matching entity IDs."""
        query_ast = self.parse(query_str)
        
        # Get entities related to start_entity (for "contains" relation)
        if query_ast.relation == "contains":
            related_entities = relations.get_contents_of(query_ast.start_entity)
        else:
            raise ValueError(f"Unsupported relation: {query_ast.relation}")
        
        # Filter by target entity type (simplified - just check if entity exists)
        matching_entities = []
        for entity_id in related_entities:
            if entity_id in entities:
                # Apply condition filter if present
                if query_ast.condition:
                    entity_props = entities[entity_id]
                    if self._evaluate_condition(query_ast.condition, entity_props):
                        matching_entities.append(entity_id)
                else:
                    matching_entities.append(entity_id)
        
        return matching_entities
    
    def _evaluate_condition(self, condition: ConditionAST, properties: Dict[str, Any]) -> bool:
        """Evaluate a condition against entity properties."""
        left_value = properties.get(condition.left)
        
        # Handle missing properties
        if left_value is None:
            return False
        
        # Evaluate based on operator
        if condition.operator == "==":
            return left_value == condition.right
        elif condition.operator == ">":
            return left_value > condition.right
        elif condition.operator == "<":
            return left_value < condition.right
        else:
            raise ValueError(f"Unsupported operator: {condition.operator}")
