"""
Patch and reference system for hierarchical configuration management.

This module provides a powerful system for referencing existing configuration
objects and applying patches to them, enabling complex composition patterns.
"""

from typing import Any, Dict, List, Union, Optional, Callable
from enum import Enum
import copy
import re


class PatchOperation(Enum):
    """Types of patch operations that can be applied."""
    
    # Basic operations
    SET = "set"                    # Set a field to a value
    UNSET = "unset"               # Remove a field
    ADD = "add"                   # Add to a list
    REMOVE = "remove"             # Remove from a list
    
    # Advanced operations
    MERGE = "merge"               # Merge dictionaries
    REPLACE = "replace"           # Replace entire value
    TRANSFORM = "transform"       # Apply a transformation function
    
    # List operations
    INSERT = "insert"             # Insert at specific position
    PREPEND = "prepend"           # Add to beginning of list
    APPEND = "append"             # Add to end of list
    REMOVE_ITEM = "remove_item"   # Remove specific item from list
    
    # Conditional operations
    IF = "if"                     # Conditional patch
    UNLESS = "unless"             # Negative conditional patch
    
    # Path operations
    SET_PATH = "set_path"         # Set value at nested path
    UNSET_PATH = "unset_path"     # Remove value at nested path


class PatchReference:
    """Represents a reference to an existing configuration object."""
    
    def __init__(self, ref_path: str, patches: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize a patch reference.
        
        Args:
            ref_path: Path to the referenced object (e.g., "actions.move", "object_types.sword")
            patches: List of patch operations to apply
        """
        self.ref_path = ref_path
        self.patches = patches or []
    
    def add_patch(self, operation: Union[str, PatchOperation], **kwargs):
        """Add a patch operation to this reference."""
        if isinstance(operation, str):
            operation = PatchOperation(operation)
        
        patch = {
            "operation": operation.value,
            **kwargs
        }
        self.patches.append(patch)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "__ref__": self.ref_path,
            "__patches__": self.patches
        }


class PatchProcessor:
    """Processes patch operations on configuration objects."""
    
    def __init__(self):
        self.operation_handlers = {
            PatchOperation.SET: self._handle_set,
            PatchOperation.UNSET: self._handle_unset,
            PatchOperation.ADD: self._handle_add,
            PatchOperation.REMOVE: self._handle_remove,
            PatchOperation.MERGE: self._handle_merge,
            PatchOperation.REPLACE: self._handle_replace,
            PatchOperation.TRANSFORM: self._handle_transform,
            PatchOperation.INSERT: self._handle_insert,
            PatchOperation.PREPEND: self._handle_prepend,
            PatchOperation.APPEND: self._handle_append,
            PatchOperation.REMOVE_ITEM: self._handle_remove_item,
            PatchOperation.IF: self._handle_if,
            PatchOperation.UNLESS: self._handle_unless,
            PatchOperation.SET_PATH: self._handle_set_path,
            PatchOperation.UNSET_PATH: self._handle_unset_path,
        }
    
    def apply_patches(self, base_object: Any, patches: List[Dict[str, Any]], 
                     context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Apply a list of patches to a base object.
        
        Args:
            base_object: The object to patch
            patches: List of patch operations
            context: Additional context for conditional operations
            
        Returns:
            The patched object
        """
        result = copy.deepcopy(base_object)
        context = context or {}
        
        for patch in patches:
            operation = PatchOperation(patch["operation"])
            handler = self.operation_handlers.get(operation)
            
            if not handler:
                raise ValueError(f"Unknown patch operation: {operation}")
            
            # Check conditions
            if not self._evaluate_conditions(patch, context):
                continue
            
            result = handler(result, patch, context)
        
        return result
    
    def _evaluate_conditions(self, patch: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate conditions for conditional patches."""
        if "if" in patch:
            return self._evaluate_expression(patch["if"], context)
        if "unless" in patch:
            return not self._evaluate_expression(patch["unless"], context)
        return True
    
    def _evaluate_expression(self, expression: Union[str, Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression."""
        if isinstance(expression, str):
            # Simple path evaluation
            return self._get_nested_value(context, expression) is not None
        elif isinstance(expression, dict):
            # Complex expression
            if "path" in expression and "equals" in expression:
                value = self._get_nested_value(context, expression["path"])
                return value == expression["equals"]
            elif "path" in expression and "in" in expression:
                value = self._get_nested_value(context, expression["path"])
                return value in expression["in"]
        return False
    
    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get a value from a nested object using dot notation."""
        parts = path.split(".")
        current = obj
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, obj: Any, path: str, value: Any) -> None:
        """Set a value in a nested object using dot notation."""
        parts = path.split(".")
        current = obj
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _handle_set(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Set a field to a value."""
        if "field" in patch and "value" in patch:
            if isinstance(obj, dict):
                obj[patch["field"]] = patch["value"]
        return obj
    
    def _handle_unset(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Remove a field."""
        if "field" in patch and isinstance(obj, dict):
            obj.pop(patch["field"], None)
        return obj
    
    def _handle_add(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Add items to a list."""
        if "field" in patch and "items" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                if not isinstance(obj[patch["field"]], list):
                    obj[patch["field"]] = []
                obj[patch["field"]].extend(patch["items"])
        return obj
    
    def _handle_remove(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Remove items from a list."""
        if "field" in patch and "items" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                if isinstance(obj[patch["field"]], list):
                    for item in patch["items"]:
                        if item in obj[patch["field"]]:
                            obj[patch["field"]].remove(item)
        return obj
    
    def _handle_merge(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Merge dictionaries."""
        if "field" in patch and "value" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                if isinstance(obj[patch["field"]], dict) and isinstance(patch["value"], dict):
                    obj[patch["field"]].update(patch["value"])
        return obj
    
    def _handle_replace(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Replace entire value."""
        if "field" in patch and "value" in patch:
            if isinstance(obj, dict):
                obj[patch["field"]] = patch["value"]
        return obj
    
    def _handle_transform(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Apply a transformation function."""
        if "field" in patch and "function" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                # This would need to be implemented with actual function resolution
                # For now, we'll just return the object
                pass
        return obj
    
    def _handle_insert(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Insert items at specific position in list."""
        if "field" in patch and "items" in patch and "position" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                if isinstance(obj[patch["field"]], list):
                    position = patch["position"]
                    for i, item in enumerate(patch["items"]):
                        obj[patch["field"]].insert(position + i, item)
        return obj
    
    def _handle_prepend(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Add items to beginning of list."""
        if "field" in patch and "items" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                if not isinstance(obj[patch["field"]], list):
                    obj[patch["field"]] = []
                obj[patch["field"]] = patch["items"] + obj[patch["field"]]
        return obj
    
    def _handle_append(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Add items to end of list."""
        if "field" in patch and "items" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                if not isinstance(obj[patch["field"]], list):
                    obj[patch["field"]] = []
                obj[patch["field"]].extend(patch["items"])
        return obj
    
    def _handle_remove_item(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Remove specific item from list."""
        if "field" in patch and "item" in patch:
            if isinstance(obj, dict) and patch["field"] in obj:
                if isinstance(obj[patch["field"]], list):
                    item = patch["item"]
                    if item in obj[patch["field"]]:
                        obj[patch["field"]].remove(item)
        return obj
    
    def _handle_if(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Conditional patch (handled in main apply_patches method)."""
        return obj
    
    def _handle_unless(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Negative conditional patch (handled in main apply_patches method)."""
        return obj
    
    def _handle_set_path(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Set value at nested path."""
        if "path" in patch and "value" in patch:
            self._set_nested_value(obj, patch["path"], patch["value"])
        return obj
    
    def _handle_unset_path(self, obj: Any, patch: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Remove value at nested path."""
        if "path" in patch:
            parts = patch["path"].split(".")
            current = obj
            
            for part in parts[:-1]:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return obj
            
            if isinstance(current, dict) and parts[-1] in current:
                del current[parts[-1]]
        
        return obj


def create_reference(ref_path: str, patches: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Create a reference to an existing configuration object.
    
    Args:
        ref_path: Path to the referenced object
        patches: List of patch operations to apply
        
    Returns:
        Dictionary representation of the reference
    """
    return PatchReference(ref_path, patches).to_dict()


def create_patch(operation: Union[str, PatchOperation], **kwargs) -> Dict[str, Any]:
    """
    Create a patch operation.
    
    Args:
        operation: The patch operation type
        **kwargs: Additional parameters for the operation
        
    Returns:
        Dictionary representation of the patch
    """
    if isinstance(operation, str):
        operation = PatchOperation(operation)
    
    return {
        "operation": operation.value,
        **kwargs
    }


# Convenience functions for common operations
def set_field(field: str, value: Any) -> Dict[str, Any]:
    """Create a set field patch."""
    return create_patch(PatchOperation.SET, field=field, value=value)


def unset_field(field: str) -> Dict[str, Any]:
    """Create an unset field patch."""
    return create_patch(PatchOperation.UNSET, field=field)


def add_to_list(field: str, items: List[Any]) -> Dict[str, Any]:
    """Create an add to list patch."""
    return create_patch(PatchOperation.ADD, field=field, items=items)


def remove_from_list(field: str, items: List[Any]) -> Dict[str, Any]:
    """Create a remove from list patch."""
    return create_patch(PatchOperation.REMOVE, field=field, items=items)


def merge_dict(field: str, value: Dict[str, Any]) -> Dict[str, Any]:
    """Create a merge dictionary patch."""
    return create_patch(PatchOperation.MERGE, field=field, value=value)


def conditional_patch(condition: Union[str, Dict[str, Any]], patches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a conditional patch."""
    return create_patch(PatchOperation.IF, if_=condition, patches=patches)

