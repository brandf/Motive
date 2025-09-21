"""
Unified configuration merging system.

This module provides version-agnostic YAML configuration merging capabilities,
supporting flexible merge strategies for lists and dictionaries. It operates
at the raw YAML level, independent of config versions (v1, v2, v3, etc.).
"""

from typing import Dict, Any, List, Union
import logging
from .list_merge_strategies import ListMerger, ListMergeStrategy


class ConfigMerger:
    """Unified configuration merger for all config versions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.list_merger = ListMerger()
    
    def merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries with support for flexible merge strategies.
        
        Args:
            base: Base configuration (will be overridden)
            override: Override configuration (takes precedence)
            
        Returns:
            Merged configuration dictionary
        """
        result = base.copy()
        
        # Remove includes from result if present
        if 'includes' in result:
            del result['includes']
        
        for key, value in override.items():
            if key == 'includes':
                # Skip includes in merged configs
                continue
            elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = self.merge_configs(result[key], value)
            elif isinstance(value, list):
                # Check for merge strategy markers first
                if self._is_merge_strategy_list(value):
                    # Handle merge strategy - create empty base list if key doesn't exist
                    base_list = result.get(key, [])
                    result[key] = self._apply_merge_strategy_list(base_list, value)
                elif key in result and isinstance(result[key], list):
                    # Handle patch-based list operations
                    if self._is_patch_list(value):
                        result[key] = self._apply_patch_list(result[key], value)
                    else:
                        # Simple append strategy - most intuitive for users
                        result[key] = result[key] + value
                else:
                    # New list - just assign it
                    result[key] = value
            elif key in result and isinstance(result[key], dict) and isinstance(value, list):
                # Handle case where base is dict but override is list (advanced merging)
                result[key] = self._apply_patch_list(list(result[key].values()), value)
            elif self._is_patch_reference(value):
                # Handle patch-based references
                result[key] = self._apply_patch_reference(result.get(key, {}), value)
            elif self._is_patch_list(value):
                # Handle patch-based list operations
                result[key] = self._apply_patch_list(result.get(key, []), value)
            else:
                # Simple override with new value
                result[key] = value
        
        return result
    
    def _is_merge_strategy_list(self, value: Any) -> bool:
        """Check if a value is a merge strategy list operation."""
        return (isinstance(value, list) and 
                len(value) > 0 and 
                isinstance(value[0], dict) and 
                '__merge_strategy__' in value[0])
    
    def _apply_merge_strategy_list(self, base_list: List[Any], merge_list: List[Any]) -> List[Any]:
        """Apply merge strategy list operations to a base list."""
        if not merge_list:
            return base_list.copy()
        
        # Extract merge strategy from first item
        strategy_item = merge_list[0]
        strategy = strategy_item.get('__merge_strategy__', 'append')
        params = strategy_item.get('__merge_params__', {})
        
        # Remove strategy item from the list to get clean items
        clean_items = merge_list[1:] if len(merge_list) > 1 else []
        
        # Use the list merger for advanced operations
        try:
            return self.list_merger.merge_lists(base_list, clean_items, strategy, **params)
        except ValueError:
            # Fall back to append behavior for invalid strategies
            self.logger.warning(f"Unknown merge strategy '{strategy}', falling back to append")
            return base_list.copy() + clean_items
    
    def _is_patch_reference(self, value: Any) -> bool:
        """Check if a value is a patch reference."""
        return (isinstance(value, dict) and 
                '__ref__' in value and 
                '__patches__' in value)
    
    def _is_patch_list(self, value: Any) -> bool:
        """Check if a value is a patch-based list operation."""
        return (isinstance(value, list) and 
                value and 
                isinstance(value[0], dict) and 
                '__patch_list__' in value[0])
    
    def _apply_patch_reference(self, base_value: Any, patch_ref: Dict[str, Any]) -> Any:
        """Apply a patch reference to a base value."""
        # For now, just return the base value (patch references not fully implemented)
        return base_value
    
    def _apply_patch_list(self, base_list: List[Any], patch_list: List[Any]) -> List[Any]:
        """Apply patch list operations to a base list."""
        result = base_list.copy()
        
        for patch_item in patch_list:
            if '__patch_list__' in patch_item:
                operation = patch_item['__patch_list__']
                
                if operation == 'append':
                    # Append new items
                    new_items = patch_item.get('items', [])
                    result.extend(new_items)
                elif operation == 'prepend':
                    # Prepend new items
                    new_items = patch_item.get('items', [])
                    result = new_items + result
                elif operation == 'remove':
                    # Remove specific items
                    items_to_remove = patch_item.get('items', [])
                    result = [item for item in result if item not in items_to_remove]
                elif operation == 'replace':
                    # Replace entire list
                    result = patch_item.get('items', [])
            else:
                result.append(patch_item)
        
        return result


# Global instance for easy access
_global_merger = ConfigMerger()


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to merge two configuration dictionaries.
    
    Args:
        base: Base configuration (will be overridden)
        override: Override configuration (takes precedence)
        
    Returns:
        Merged configuration dictionary
    """
    return _global_merger.merge_configs(base, override)
