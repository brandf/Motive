"""
Hierarchical configuration loader with include directive support.

This module provides a flexible configuration system where any YAML config file
can include other config files using an 'includes' directive. The included
configs are merged in order, with later configs overriding earlier ones.
"""

import os
import yaml
from typing import Dict, Any, List, Set, Optional
from pathlib import Path
import logging
from .config_merging import ConfigMerger


class ConfigLoadError(Exception):
    """Exception raised when there's an error loading a configuration file."""
    pass


class ConfigLoader:
    """Loads and merges YAML configuration files with include support."""
    
    def __init__(self, base_path: str = "configs"):
        self.base_path = Path(base_path)
        self.loaded_configs: Dict[str, Dict[str, Any]] = {}
        self.loading_stack: List[str] = []  # Track loading order for circular dependency detection
        self.logger = logging.getLogger(__name__)
        self.list_merger = ListMerger()
    
    def load_config(self, config_path: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a configuration file and all its includes.
        
        Args:
            config_path: Path to the config file relative to base_path
            base_path: Override the base path for this load operation
            
        Returns:
            Merged configuration dictionary
            
        Raises:
            FileNotFoundError: If config file or any included file is not found
            ValueError: If circular dependency is detected
            yaml.YAMLError: If YAML parsing fails
        """
        # Use provided base_path or fall back to instance base_path
        if base_path is not None:
            original_base_path = self.base_path
            self.base_path = Path(base_path)
            try:
                # Reset state for this load
                self.loaded_configs.clear()
                self.loading_stack.clear()
                return self._load_config_recursive(config_path)
            finally:
                self.base_path = original_base_path
        else:
            # Reset state for this load
            self.loaded_configs.clear()
            self.loading_stack.clear()
            return self._load_config_recursive(config_path)
    
    def _load_config_recursive(self, config_path: str) -> Dict[str, Any]:
        """
        Recursively load a config file and its includes.
        
        Args:
            config_path: Path to the config file relative to base_path
            
        Returns:
            Merged configuration dictionary
        """
        # Resolve absolute path, handling relative paths correctly
        if os.path.isabs(config_path):
            abs_path = Path(config_path)
        else:
            # Handle relative paths that go up directories
            if config_path.startswith('../'):
                # Go up from base_path and then follow the relative path
                # Remove '../' prefix and resolve relative to parent directory
                relative_path = config_path[3:]  # Remove '../'
                abs_path = (self.base_path.parent / relative_path).resolve()
            else:
                abs_path = (self.base_path / config_path).resolve()
        abs_path_str = str(abs_path)
        
        # Check for circular dependency
        if abs_path_str in self.loading_stack:
            cycle = " -> ".join(self.loading_stack + [config_path])
            raise ConfigLoadError(f"Circular dependency detected: {cycle}")
        
        # Return cached config if already loaded
        if abs_path_str in self.loaded_configs:
            return self.loaded_configs[abs_path_str]
        
        # Check if file exists
        if not abs_path.exists():
            # Show the loading chain for better debugging
            chain = " -> ".join(self.loading_stack + [config_path]) if self.loading_stack else config_path
            raise ConfigLoadError(f"File not found: '{abs_path}' (base_path: {self.base_path}, loading chain: {chain})")
        
        # Add to loading stack
        self.loading_stack.append(abs_path_str)
        
        try:
            # Load the YAML file
            with open(abs_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # Handle includes (C++ convention: includes at top, processed first)
            if 'includes' in config_data:
                includes = config_data.pop('includes')  # Remove includes from final config
                if not isinstance(includes, list):
                    includes = [includes]
                
                # Load all included configs first (like C++ #include)
                merged_config = {}
                for include_path in includes:
                    # Resolve include path relative to current config
                    if not os.path.isabs(include_path):
                        include_path = os.path.join(os.path.dirname(config_path), include_path)
                    
                    included_config = self._load_config_recursive(include_path)
                    merged_config = self._merge_configs(merged_config, included_config)
                
                # Merge current config on top of included configs (current config overrides)
                merged_config = self._merge_configs(merged_config, config_data)
            else:
                merged_config = config_data
            
            # Cache the result
            self.loaded_configs[abs_path_str] = merged_config
            
            return merged_config
            
        except yaml.YAMLError as e:
            # Show the loading chain for better debugging
            chain = " -> ".join(self.loading_stack + [config_path]) if self.loading_stack else config_path
            raise ConfigLoadError(f"YAML parsing error in '{abs_path}' (loading chain: {chain}): {e}")
        finally:
            # Remove from loading stack
            self.loading_stack.pop()
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries with support for both simple and patch-based merging.
        
        Args:
            base: Base configuration (will be overridden)
            override: Override configuration (takes precedence)
            
        Returns:
            Merged configuration dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = self._merge_configs(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # Simple append strategy - most intuitive for users
                result[key] = result[key] + value
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
    
    def _merge_lists_simple(self, base_list: List[Any], override_list: List[Any], key: str) -> List[Any]:
        """
        Simple list merging - just append by default.
        
        Args:
            base_list: Base list
            override_list: Override list
            key: The configuration key (for future extensibility)
            
        Returns:
            Merged list
        """
        # Simple append strategy - most intuitive for users
        return base_list.copy() + override_list.copy()
    
    
    def _is_patch_reference(self, value: Any) -> bool:
        """Check if a value is a patch reference."""
        return (isinstance(value, dict) and 
                "__ref__" in value and 
                "__patches__" in value)
    
    def _is_patch_list(self, value: Any) -> bool:
        """Check if a value is a patch-based list operation."""
        return (isinstance(value, list) and 
                value and 
                isinstance(value[0], dict) and 
                "__merge_strategy__" in value[0])
    
    def _apply_patch_reference(self, base_value: Any, patch_ref: Dict[str, Any]) -> Any:
        """Apply a patch reference to a base value."""
        from .patch_system import PatchProcessor
        
        ref_path = patch_ref["__ref__"]
        patches = patch_ref["__patches__"]
        
        # For now, we'll just return the base value
        # In a full implementation, you'd resolve the reference and apply patches
        # This would require access to the full configuration context
        return base_value
    
    def _apply_patch_list(self, base_list: List[Any], patch_list: List[Any]) -> List[Any]:
        """Apply patch-based list operations."""
        if not patch_list:
            return base_list.copy()
        
        metadata = patch_list[0]
        strategy = metadata.get("__merge_strategy__", "append")
        params = metadata.get("__merge_params__", {})
        
        # Remove metadata from the list
        clean_list = patch_list[1:] if len(patch_list) > 1 else []
        
        # Use the list merger for advanced operations
        return self.list_merger.merge_lists(base_list, clean_list, strategy, **params)
    
    def get_loaded_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded configurations for debugging."""
        return self.loaded_configs.copy()
    
    def clear_cache(self):
        """Clear the configuration cache."""
        self.loaded_configs.clear()
        self.loading_stack.clear()


def load_game_config(config_path: str = "game.yaml", base_path: str = "configs") -> Dict[str, Any]:
    """
    Convenience function to load a game configuration with includes.
    
    Args:
        config_path: Path to the main config file
        base_path: Base directory for config files
        
    Returns:
        Merged configuration dictionary
    """
    loader = ConfigLoader(base_path)
    return loader.load_config(config_path)


def load_and_validate_game_config(config_path: str = "game.yaml", base_path: str = "configs", validate: bool = True):
    """
    Load a game configuration with includes and optionally validate it.
    
    Args:
        config_path: Path to the main config file
        base_path: Base directory for config files
        validate: Whether to validate the merged config through Pydantic models
        
    Returns:
        If validate=True: Validated GameConfig object
        If validate=False: Merged configuration dictionary
        
    Raises:
        ConfigLoadError: If config loading fails
        ConfigValidationError: If validation fails (when validate=True)
    """
    # Load the merged configuration
    config_data = load_game_config(config_path, base_path)
    
    if validate:
        # Import here to avoid circular imports
        from .config_validator import validate_merged_config
        return validate_merged_config(config_data)
    else:
        return config_data
