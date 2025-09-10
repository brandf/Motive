"""
List merging strategies for hierarchical configuration system.

This module provides different strategies for merging lists in hierarchical configs,
supporting various use cases like override, append, prepend, and remove operations.
"""

from typing import Any, List, Dict, Union
from enum import Enum


class ListMergeStrategy(Enum):
    """Strategies for merging lists in hierarchical configs."""
    
    # Basic strategies
    OVERRIDE = "override"  # Replace the entire list
    APPEND = "append"      # Add items to the end
    PREPEND = "prepend"    # Add items to the beginning
    
    # Advanced strategies
    MERGE_UNIQUE = "merge_unique"  # Merge and remove duplicates
    REMOVE_ITEMS = "remove_items"  # Remove specific items from the list
    INSERT_AT = "insert_at"        # Insert items at specific positions
    INSERT = "insert"              # Alias for INSERT_AT
    
    # Smart strategies
    SMART_MERGE = "smart_merge"    # Automatically choose strategy based on content
    KEY_BASED_MERGE = "key_based"  # Merge based on a key field (for objects)


class ListMerger:
    """Handles merging of lists with different strategies."""
    
    def __init__(self):
        self.strategies = {
            ListMergeStrategy.OVERRIDE: self._override_strategy,
            ListMergeStrategy.APPEND: self._append_strategy,
            ListMergeStrategy.PREPEND: self._prepend_strategy,
            ListMergeStrategy.MERGE_UNIQUE: self._merge_unique_strategy,
            ListMergeStrategy.REMOVE_ITEMS: self._remove_items_strategy,
            ListMergeStrategy.INSERT_AT: self._insert_at_strategy,
            ListMergeStrategy.INSERT: self._insert_at_strategy,  # Alias
            ListMergeStrategy.SMART_MERGE: self._smart_merge_strategy,
            ListMergeStrategy.KEY_BASED_MERGE: self._key_based_merge_strategy,
        }
    
    def merge_lists(self, base_list: List[Any], override_list: List[Any], 
                   strategy: Union[str, ListMergeStrategy] = ListMergeStrategy.APPEND,
                   **kwargs) -> List[Any]:
        """
        Merge two lists using the specified strategy.
        
        Args:
            base_list: The base list to merge into
            override_list: The list to merge from
            strategy: The merge strategy to use
            **kwargs: Additional arguments for specific strategies
            
        Returns:
            The merged list
        """
        if not isinstance(strategy, ListMergeStrategy):
            try:
                strategy = ListMergeStrategy(strategy)
            except ValueError:
                raise ValueError(f"Unknown merge strategy: {strategy}")
        
        if strategy not in self.strategies:
            raise ValueError(f"Unsupported merge strategy: {strategy}")
        
        return self.strategies[strategy](base_list, override_list, **kwargs)
    
    def _override_strategy(self, base_list: List[Any], override_list: List[Any], **kwargs) -> List[Any]:
        """Replace the entire list with the override list."""
        return override_list.copy()
    
    def _append_strategy(self, base_list: List[Any], override_list: List[Any], **kwargs) -> List[Any]:
        """Add items from override list to the end of base list."""
        return base_list.copy() + override_list.copy()
    
    def _prepend_strategy(self, base_list: List[Any], override_list: List[Any], **kwargs) -> List[Any]:
        """Add items from override list to the beginning of base list."""
        return override_list.copy() + base_list.copy()
    
    def _merge_unique_strategy(self, base_list: List[Any], override_list: List[Any], **kwargs) -> List[Any]:
        """Merge lists and remove duplicates, preserving order."""
        result = base_list.copy()
        for item in override_list:
            if item not in result:
                result.append(item)
        return result
    
    def _remove_items_strategy(self, base_list: List[Any], override_list: List[Any], **kwargs) -> List[Any]:
        """Remove items in override_list from base_list."""
        items_to_remove = set(override_list)
        return [item for item in base_list if item not in items_to_remove]
    
    def _insert_at_strategy(self, base_list: List[Any], override_list: List[Any], 
                          position: int = 0, **kwargs) -> List[Any]:
        """Insert items from override_list at a specific position."""
        result = base_list.copy()
        for i, item in enumerate(override_list):
            result.insert(position + i, item)
        return result
    
    def _smart_merge_strategy(self, base_list: List[Any], override_list: List[Any], **kwargs) -> List[Any]:
        """Automatically choose merge strategy based on content analysis."""
        # If override list is empty, return base list
        if not override_list:
            return base_list.copy()
        
        # If base list is empty, return override list
        if not base_list:
            return override_list.copy()
        
        # If both lists contain dictionaries, use key-based merge
        if (isinstance(base_list[0], dict) and isinstance(override_list[0], dict) and
            'id' in base_list[0] and 'id' in override_list[0]):
            return self._key_based_merge_strategy(base_list, override_list, key_field='id')
        
        # If override list contains special markers, handle them
        if any(isinstance(item, str) and item.startswith('__') for item in override_list):
            return self._handle_special_markers(base_list, override_list)
        
        # Default to append strategy
        return self._append_strategy(base_list, override_list)
    
    def _key_based_merge_strategy(self, base_list: List[Any], override_list: List[Any], 
                                 key_field: str = 'id', **kwargs) -> List[Any]:
        """Merge lists based on a key field, updating existing items and adding new ones."""
        # If no items have the key field, fall back to append strategy
        if not any(isinstance(item, dict) and key_field in item for item in base_list + override_list):
            return self._append_strategy(base_list, override_list)
        
        # Convert base list to dict for easy lookup
        base_dict = {item[key_field]: item for item in base_list if isinstance(item, dict) and key_field in item}
        
        # Process override list
        for item in override_list:
            if isinstance(item, dict) and key_field in item:
                base_dict[item[key_field]] = item
        
        # Convert back to list, preserving original order where possible
        result = []
        # Add items from base list in original order
        for item in base_list:
            if isinstance(item, dict) and key_field in item:
                result.append(base_dict[item[key_field]])
            else:
                result.append(item)
        
        # Add new items from override list
        for item in override_list:
            if isinstance(item, dict) and key_field in item:
                if item[key_field] not in [existing.get(key_field) for existing in base_list 
                                         if isinstance(existing, dict) and key_field in existing]:
                    result.append(item)
        
        return result
    
    def _handle_special_markers(self, base_list: List[Any], override_list: List[Any]) -> List[Any]:
        """Handle special markers in override list for advanced operations."""
        result = base_list.copy()
        
        for item in override_list:
            if isinstance(item, str):
                if item == "__CLEAR__":
                    result.clear()
                elif item.startswith("__REMOVE__:"):
                    # Remove items matching the pattern after __REMOVE__:
                    pattern = item[11:]  # Remove "__REMOVE__:" prefix
                    result = [existing for existing in result if str(existing) != pattern]
                elif item.startswith("__INSERT_AT__:"):
                    # Insert items at specific position: __INSERT_AT__:2:item1:item2
                    parts = item.split(":")
                    if len(parts) >= 3:
                        try:
                            position = int(parts[1])
                            items_to_insert = parts[2:]
                            for i, insert_item in enumerate(items_to_insert):
                                result.insert(position + i, insert_item)
                        except ValueError:
                            # If position is not a number, treat as regular item
                            result.append(item)
                else:
                    result.append(item)
            else:
                result.append(item)
        
        return result


def detect_list_merge_strategy(config_key: str, value: Any) -> ListMergeStrategy:
    """
    Automatically detect the appropriate merge strategy for a config key.
    
    Args:
        config_key: The configuration key
        value: The value being merged
        
    Returns:
        The recommended merge strategy
    """
    # Special keys that should always use specific strategies
    if config_key in ['includes', 'dependencies']:
        return ListMergeStrategy.APPEND
    
    if config_key in ['exclude', 'blacklist', 'deny']:
        return ListMergeStrategy.REMOVE_ITEMS
    
    if config_key in ['priority', 'order']:
        return ListMergeStrategy.OVERRIDE
    
    # If value contains special markers, use smart merge
    if isinstance(value, list) and any(isinstance(item, str) and item.startswith('__') for item in value):
        return ListMergeStrategy.SMART_MERGE
    
    # If value contains dictionaries with 'id' field, use key-based merge
    if isinstance(value, list) and value and isinstance(value[0], dict) and 'id' in value[0]:
        return ListMergeStrategy.KEY_BASED_MERGE
    
    # Default strategy
    return ListMergeStrategy.APPEND


def create_merge_metadata(merge_strategy: ListMergeStrategy, **kwargs) -> Dict[str, Any]:
    """
    Create metadata for merge operations that can be embedded in configs.
    
    Args:
        merge_strategy: The merge strategy to use
        **kwargs: Additional parameters for the strategy
        
    Returns:
        Metadata dictionary
    """
    return {
        "__merge_strategy__": merge_strategy.value,
        "__merge_params__": kwargs
    }
