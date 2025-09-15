#!/usr/bin/env python3
"""Adapter to convert v2 configs back to v1 format for CLI compatibility."""

import logging
from typing import Dict, Any, List, Optional
from ..config import GameConfig, PlayerConfig


class V2ToV1Adapter:
    """Converts v2 configs to v1 format for CLI compatibility."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def convert_v2_to_v1_config(self, v2_config_data: Dict[str, Any]) -> GameConfig:
        """Convert v2 config data to v1 GameConfig format."""
        
        # Extract basic game settings
        game_settings = v2_config_data.get('game_settings', {})
        players_data = v2_config_data.get('players', [])
        
        # Convert players
        players = []
        for player_data in players_data:
            players.append(PlayerConfig(**player_data))
        
        # Convert entity definitions to v1 format
        entity_definitions = v2_config_data.get('entity_definitions', {})
        
        # Separate entities by type
        rooms = {}
        object_types = {}
        character_types = {}
        characters = {}
        actions = {}
        
        for entity_id, entity_def in entity_definitions.items():
            entity_types = entity_def.get('types', [])
            
            if 'room' in entity_types:
                rooms[entity_id] = self._convert_room_definition(entity_id, entity_def)
            elif 'object' in entity_types:
                object_types[entity_id] = self._convert_object_definition(entity_id, entity_def)
            elif 'character' in entity_types:
                character_types[entity_id] = self._convert_character_definition(entity_id, entity_def)
        
        # Convert action definitions
        action_definitions = v2_config_data.get('action_definitions', {})
        for action_id, action_def in action_definitions.items():
            actions[action_id] = self._convert_action_definition(action_id, action_def)
        
        # Create GameConfig
        return GameConfig(
            game_settings=game_settings,
            players=players,
            rooms=rooms,
            object_types=object_types,
            character_types=character_types,
            characters=characters,
            actions=actions
        )
    
    def _convert_room_definition(self, room_id: str, entity_def: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v2 room definition to v1 format."""
        properties = entity_def.get('properties', {})
        
        return {
            'id': room_id,
            'name': properties.get('name', {}).get('default', room_id),
            'description': properties.get('description', {}).get('default', ''),
            'exits': {},  # TODO: Convert exits from v2 format
            'objects': {},  # TODO: Convert objects from v2 format
            'properties': self._extract_property_values(properties)
        }
    
    def _convert_object_definition(self, object_id: str, entity_def: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v2 object definition to v1 format."""
        properties = entity_def.get('properties', {})
        
        return {
            'id': object_id,
            'name': properties.get('name', {}).get('default', object_id),
            'description': properties.get('description', {}).get('default', ''),
            'properties': self._extract_property_values(properties)
        }
    
    def _convert_character_definition(self, character_id: str, entity_def: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v2 character definition to v1 format."""
        properties = entity_def.get('properties', {})
        
        return {
            'id': character_id,
            'name': properties.get('name', {}).get('default', character_id),
            'backstory': properties.get('backstory', {}).get('default', ''),
            'motive': properties.get('motive', {}).get('default', ''),
            'properties': self._extract_property_values(properties)
        }
    
    def _convert_action_definition(self, action_id: str, action_def: Dict[str, Any]) -> Dict[str, Any]:
        """Convert v2 action definition to v1 format."""
        return {
            'id': action_id,
            'name': action_def.get('name', action_id),
            'description': action_def.get('description', ''),
            'cost': action_def.get('cost', 10),
            'category': action_def.get('category', 'general'),
            'parameters': action_def.get('parameters', []),
            'requirements': action_def.get('requirements', []),
            'effects': action_def.get('effects', [])
        }
    
    def _extract_property_values(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Extract default values from v2 property schemas."""
        result = {}
        for prop_name, prop_schema in properties.items():
            if isinstance(prop_schema, dict) and 'default' in prop_schema:
                result[prop_name] = prop_schema['default']
            else:
                result[prop_name] = prop_schema
        return result
