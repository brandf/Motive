#!/usr/bin/env python3
"""V2 configuration loader with v1 migration support."""

import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .definitions import EntityDefinition, DefinitionRegistry
from .properties import PropertySchema, PropertyType
from .adapters import V1ToV2Adapter
from .actions_pipeline import ActionDefinition, ActionParameter, ActionRequirement
from .effects import Effect, SetPropertyEffect, MoveEntityEffect, CodeBindingEffect, GenerateEventEffect, EffectEngine
from .conditions import ConditionAST, ConditionParser
from .relations import RelationsGraph


class V2ConfigLoader:
    """Loads and processes v2 configurations with v1 migration support."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.adapter = V1ToV2Adapter()
        self.condition_parser = ConditionParser()
        
        # Storage for loaded configurations
        self.definitions: DefinitionRegistry = DefinitionRegistry()
        self.actions: Dict[str, ActionDefinition] = {}
        self.entities: Dict[str, Any] = {}  # Will store MotiveEntity instances
        
        # V2 systems
        self.relations: RelationsGraph = RelationsGraph()
        self.effect_engine: EffectEngine = EffectEngine()
        
        # Migration tracking
        self.migration_stats = {
            'rooms_migrated': 0,
            'objects_migrated': 0,
            'characters_migrated': 0,
            'actions_migrated': 0,
            'warnings': []
        }
    
    def load_config_from_file(self, config_path: str) -> Dict[str, Any]:
        """Load a configuration file and return the parsed data."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            return config_data
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    def load_hierarchical_config(self, base_config_path: str) -> Dict[str, Any]:
        """Load a hierarchical configuration (core -> theme -> edition)."""
        config_data = self.load_config_from_file(base_config_path)
        
        # Process includes recursively
        if 'includes' in config_data:
            merged_data = {}
            for include_path in config_data['includes']:
                # Resolve relative paths
                if not include_path.startswith('/'):
                    include_path = str(Path(base_config_path).parent / include_path)
                
                # Recursively load included configs
                include_data = self.load_hierarchical_config(include_path)
                merged_data = self._merge_configs(merged_data, include_data)
            
            # Merge base config on top
            merged_data = self._merge_configs(merged_data, config_data)
            return merged_data
        
        return config_data
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key == 'includes':
                # Skip includes in merged configs
                continue
            elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = self._merge_configs(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # Merge lists (override takes precedence)
                result[key] = value
            else:
                # Override value
                result[key] = value
        
        return result
    
    def migrate_v1_to_v2(self, config_data: Dict[str, Any]) -> None:
        """Migrate v1 configuration data to v2 format."""
        self.logger.info("🔄 Starting v1 to v2 migration...")
        
        # Migrate rooms
        if 'rooms' in config_data:
            self._migrate_rooms(config_data['rooms'])
        
        # Migrate object types
        if 'object_types' in config_data:
            self._migrate_object_types(config_data['object_types'])
        
        # Migrate characters
        if 'characters' in config_data:
            self._migrate_characters(config_data['characters'])
        
        # Migrate actions
        if 'actions' in config_data:
            self._migrate_actions(config_data['actions'])
        
        # Log migration statistics
        self._log_migration_stats()
    
    def _migrate_rooms(self, rooms_data: Dict[str, Any]) -> None:
        """Migrate room configurations to v2 definitions."""
        for room_id, room_data in rooms_data.items():
            try:
                # Ensure room has an id
                if 'id' not in room_data:
                    room_data['id'] = room_id
                    self.migration_stats['warnings'].append(f"Room {room_id}: Missing 'id' field, using key as id")
                
                # Convert to v2 definition
                definition = self.adapter.room_to_definition(room_data)
                self.definitions.add(definition)
                self.migration_stats['rooms_migrated'] += 1
                
                self.logger.debug(f"Migrated room: {room_id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to migrate room {room_id}: {e}")
                self.migration_stats['warnings'].append(f"Room {room_id}: {e}")
    
    def _migrate_object_types(self, object_types_data: Dict[str, Any]) -> None:
        """Migrate object type configurations to v2 definitions."""
        for obj_type_id, obj_type_data in object_types_data.items():
            try:
                # Ensure object type has an id
                if 'id' not in obj_type_data:
                    obj_type_data['id'] = obj_type_id
                
                # Convert to v2 definition
                definition = self.adapter.object_type_to_definition(obj_type_data)
                self.definitions.add(definition)
                self.migration_stats['objects_migrated'] += 1
                
                self.logger.debug(f"Migrated object type: {obj_type_id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to migrate object type {obj_type_id}: {e}")
                self.migration_stats['warnings'].append(f"Object type {obj_type_id}: {e}")
    
    def _migrate_characters(self, characters_data: Dict[str, Any]) -> None:
        """Migrate character configurations to v2 definitions."""
        for char_id, char_data in characters_data.items():
            try:
                # Ensure character has an id
                if 'id' not in char_data:
                    char_data['id'] = char_id
                
                # Convert to v2 definition
                definition = self.adapter.character_to_definition(char_data)
                self.definitions.add(definition)
                self.migration_stats['characters_migrated'] += 1
                
                self.logger.debug(f"Migrated character: {char_id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to migrate character {char_id}: {e}")
                self.migration_stats['warnings'].append(f"Character {char_id}: {e}")
    
    def _migrate_actions(self, actions_data: Dict[str, Any]) -> None:
        """Migrate action configurations to v2 action definitions."""
        for action_id, action_data in actions_data.items():
            try:
                # Convert v1 action to v2 action definition
                action_def = self._convert_v1_action_to_v2(action_data, action_id)
                self.actions[action_id] = action_def
                self.migration_stats['actions_migrated'] += 1
                
                self.logger.debug(f"Migrated action: {action_id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to migrate action {action_id}: {e}")
                self.migration_stats['warnings'].append(f"Action {action_id}: {e}")
    
    def _convert_v1_action_to_v2(self, v1_action: Dict[str, Any], action_id: str) -> ActionDefinition:
        """Convert a v1 action to v2 action definition."""
        # Extract basic action properties
        name = v1_action.get('name', action_id)
        description = v1_action.get('description', f"Action: {name}")
        cost = v1_action.get('cost', 10)
        category = v1_action.get('category', 'general')  # CRITICAL: Preserve category
        
        # Convert parameters
        parameters = []
        if 'parameters' in v1_action:
            for param_data in v1_action['parameters']:
                param = ActionParameter(
                    name=param_data.get('name', ''),
                    type=param_data.get('type', 'string'),
                    description=param_data.get('description', ''),
                    required=param_data.get('required', True),
                    default_value=param_data.get('default_value')
                )
                parameters.append(param)
        
        # Convert requirements
        requirements = []
        if 'requirements' in v1_action:
            for req_data in v1_action['requirements']:
                # Convert v1 requirement to v2 requirement
                req = self._convert_v1_requirement_to_v2(req_data)
                requirements.append(req)
        
        # Convert effects
        effects = []
        if 'effects' in v1_action:
            for effect_data in v1_action['effects']:
                # Convert v1 effect to v2 effect
                effect = self._convert_v1_effect_to_v2(effect_data)
                effects.append(effect)
        
        return ActionDefinition(
            action_id=action_id,
            name=name,
            description=description,
            cost=cost,
            category=category,  # CRITICAL: Include category
            parameters=parameters,
            requirements=requirements,
            effects=effects
        )
    
    def _convert_v1_requirement_to_v2(self, v1_req: Dict[str, Any]) -> ActionRequirement:
        """Convert v1 requirement to v2 requirement."""
        req_type = v1_req.get('type', 'condition')
        description = v1_req.get('description', '')
        
        # For now, create a simple condition requirement
        # In a full implementation, this would parse v1 requirements into v2 conditions
        condition = None
        if req_type == 'condition' and 'condition' in v1_req:
            try:
                condition = self.condition_parser.parse(v1_req['condition'])
            except Exception as e:
                self.logger.warning(f"Failed to parse condition: {e}")
        
        return ActionRequirement(
            type=req_type,
            condition=condition,
            description=description,
            tag=v1_req.get('tag'),
            object_name_param=v1_req.get('object_name_param'),
            property=v1_req.get('property'),
            value=v1_req.get('value'),
            target_player_param=v1_req.get('target_player_param'),
            direction_param=v1_req.get('direction_param')
        )
    
    def _convert_v1_effect_to_v2(self, v1_effect: Dict[str, Any]) -> Effect:
        """Convert v1 effect to v2 effect."""
        effect_type = v1_effect.get('type', 'set_property')
        
        if effect_type == 'set_property':
            return SetPropertyEffect(
                target_entity=v1_effect.get('target', 'player'),
                property_name=v1_effect.get('property', ''),
                value=v1_effect.get('value', '')
            )
        elif effect_type == 'move_entity':
            return MoveEntityEffect(
                entity_id=v1_effect.get('entity_id', 'player'),
                new_container=v1_effect.get('new_container', '')
            )
        elif effect_type == 'code_binding':
            return CodeBindingEffect(
                function_name=v1_effect.get('function_name', ''),
                observers=v1_effect.get('observers', [])
            )
        elif effect_type == 'generate_event':
            return GenerateEventEffect(
                message=v1_effect.get('message', ''),
                observers=v1_effect.get('observers', [])
            )
        else:
            # Default to set_property effect
            return SetPropertyEffect(
                target_entity='player',
                property_name='unknown',
                value=''
            )
    
    def _log_migration_stats(self) -> None:
        """Log migration statistics."""
        self.logger.info("📊 Migration Statistics:")
        self.logger.info(f"  🏠 Rooms migrated: {self.migration_stats['rooms_migrated']}")
        self.logger.info(f"  📦 Objects migrated: {self.migration_stats['objects_migrated']}")
        self.logger.info(f"  👤 Characters migrated: {self.migration_stats['characters_migrated']}")
        self.logger.info(f"  ⚔️ Actions migrated: {self.migration_stats['actions_migrated']}")
        
        if self.migration_stats['warnings']:
            self.logger.warning(f"⚠️ Migration warnings ({len(self.migration_stats['warnings'])}):")
            for warning in self.migration_stats['warnings']:
                self.logger.warning(f"  - {warning}")
    
    def load_v2_config(self, config_data: Dict[str, Any]) -> None:
        """Load native v2 configuration data."""
        self.logger.info("🔧 Loading v2 configuration...")
        
        # Load entity definitions
        if 'entity_definitions' in config_data:
            self._load_entity_definitions(config_data['entity_definitions'])
        
        # Load action definitions
        if 'action_definitions' in config_data:
            self._load_action_definitions(config_data['action_definitions'])
        
        # Load entity instances
        if 'entity_instances' in config_data:
            self._load_entity_instances(config_data['entity_instances'])
    
    def _load_entity_definitions(self, definitions_data: Dict[str, Any]) -> None:
        """Load v2 entity definitions."""
        for def_id, def_data in definitions_data.items():
            try:
                definition = self._parse_entity_definition(def_data, def_id)
                self.definitions.add(definition)
                self.logger.debug(f"Loaded entity definition: {def_id}")
            except Exception as e:
                self.logger.warning(f"Failed to load entity definition {def_id}: {e}")
    
    def _load_action_definitions(self, actions_data: Dict[str, Any]) -> None:
        """Load v2 action definitions."""
        for action_id, action_data in actions_data.items():
            try:
                action_def = self._parse_action_definition(action_data, action_id)
                self.actions[action_id] = action_def
                self.logger.debug(f"Loaded action definition: {action_id}")
            except Exception as e:
                self.logger.warning(f"Failed to load action definition {action_id}: {e}")
    
    def _load_entity_instances(self, instances_data: Dict[str, Any]) -> None:
        """Load v2 entity instances."""
        for instance_id, instance_data in instances_data.items():
            try:
                entity = self._parse_entity_instance(instance_data, instance_id)
                self.entities[instance_id] = entity
                self.logger.debug(f"Loaded entity instance: {instance_id}")
            except Exception as e:
                self.logger.warning(f"Failed to load entity instance {instance_id}: {e}")
    
    def _parse_entity_definition(self, def_data: Dict[str, Any], def_id: str) -> EntityDefinition:
        """Parse v2 entity definition from data."""
        # This would parse the full v2 entity definition format
        # For now, create a basic definition
        properties = {}
        
        # Parse properties
        if 'properties' in def_data:
            for prop_name, prop_data in def_data['properties'].items():
                prop_type = PropertyType(prop_data.get('type', 'string'))
                default_value = prop_data.get('default', '')
                properties[prop_name] = PropertySchema(type=prop_type, default=default_value)
        
        return EntityDefinition(
            definition_id=def_id,
            types=def_data.get('types', ['entity']),
            properties=properties
        )
    
    def _parse_action_definition(self, action_data: Dict[str, Any], action_id: str) -> ActionDefinition:
        """Parse v2 action definition from data."""
        # This would parse the full v2 action definition format
        # For now, create a basic action definition
        return ActionDefinition(
            action_id=action_id,
            name=action_data.get('name', action_id),
            description=action_data.get('description', ''),
            cost=action_data.get('cost', 10),
            parameters=[],  # Would parse parameters
            requirements=[],  # Would parse requirements
            effects=[]  # Would parse effects
        )
    
    def _parse_entity_instance(self, instance_data: Dict[str, Any], instance_id: str) -> Any:
        """Parse v2 entity instance from data."""
        # This would create a MotiveEntity instance
        # For now, return the data as-is
        return instance_data
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """Get a summary of the migration process."""
        return {
            'definitions_loaded': len(self.definitions._defs),
            'actions_loaded': len(self.actions),
            'entities_loaded': len(self.entities),
            'migration_stats': self.migration_stats.copy()
        }
