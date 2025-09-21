import ast
import logging
import warnings
import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError

from motive.config import (
    GameConfig,
    ThemeConfig,
    EditionConfig,
    ObjectTypeConfig,
    ActionConfig,
    CharacterConfig,
    RoomConfig,
    ExitConfig,
    ObjectInstanceConfig,
    # CharacterInstanceConfig # Removed this as it does not exist
    CoreConfig, # Added CoreConfig
)
from motive.game_object import GameObject # Import GameObject
from motive.room import Room
from motive.player import Player
from motive.character import Character
from motive.exceptions import ConfigNotFoundError, ConfigParseError, ConfigValidationError

class GameInitializer:
    def __init__(self, game_config, game_id: str, game_logger: logging.Logger, initial_ap_per_turn: int = 20, deterministic: bool = False, character_override: str = None, motive_override: str = None, characters_override: List[str] = None, motives_override: List[str] = None, character_motives_override: List[str] = None):
        self.game_config = game_config # This is the overall GameConfig loaded from config.yaml
        self.game_id = game_id
        self.game_logger = game_logger
        self.initial_ap_per_turn = initial_ap_per_turn # Store initial AP per turn
        self.deterministic = deterministic # Store deterministic flag
        self.character_override = character_override # Store character override for first player
        self.motive_override = motive_override # Store motive override for character assignment
        self.characters_override = characters_override # Store characters override for multiple players
        self.motives_override = motives_override # Store motives override for multiple players
        self.character_motives_override = character_motives_override # Store character-motives override
        # GameInitializer now works with v2 configs directly - no conversion needed

        self.rooms: Dict[str, Room] = {}
        self.game_objects: Dict[str, GameObject] = {}
        self.player_characters: Dict[str, Character] = {}

        # These will store the merged configurations
        self.game_object_types: Dict[str, ObjectTypeConfig] = {}
        self.game_actions: Dict[str, ActionConfig] = {}
        self.game_character_types: Dict[str, CharacterConfig] = {}
        self.game_characters: Dict[str, CharacterConfig] = {}
        self.game_rooms: Dict[str, Any] = {}

        # Store loaded configs for later merging
        self.core_cfg: Optional[CoreConfig] = None
        self.theme_cfg: Optional[ThemeConfig] = None
        self.edition_cfg: Optional[EditionConfig] = None

    def initialize_game_world(self, players: List[Player]):
        # Collect initialization data for consolidated reporting
        init_data = {
            'config_loaded': False,
            'rooms_created': 0,
            'objects_placed': 0,
            'characters_assigned': [],
            'warnings': []
        }
        
        # Load configurations
        self._load_configurations_silent(init_data)
        
        # Instantiate rooms and objects
        self._instantiate_rooms_and_objects_silent(init_data)
        
        # Instantiate player characters
        self._instantiate_player_characters_silent(players, init_data)
        
        # Log consolidated initialization report
        self._log_initialization_report(init_data)

    def _load_configurations(self):
        """Loads configurations from the already-merged game config."""
        self.game_logger.info("🔧 Loading game configurations...")

        # With hierarchical configs, everything is already merged into game_config
        # We need to extract the merged data from the raw config dict
        
        # Get the raw merged config data
        if hasattr(self.game_config, 'model_dump'):
            # Avoid Pydantic serializer warnings by silencing during export
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="Pydantic serializer warnings:",
                        category=UserWarning,
                    )
                    raw_config = self.game_config.model_dump()
            except Exception:
                raw_config = self.game_config.dict() if hasattr(self.game_config, 'dict') else self.game_config
        elif hasattr(self.game_config, '__dict__'):
            raw_config = self.game_config.__dict__
        else:
            # If it's already a dictionary, use it directly
            raw_config = self.game_config
        
        # Handle v2 configs (action_definitions, entity_definitions)
        if 'action_definitions' in raw_config and raw_config['action_definitions']:
            # Store v2 ActionDefinition objects directly - no conversion needed
            self.game_actions = raw_config['action_definitions']
        
        # Handle v1 configs (actions) - legacy support
        elif 'actions' in raw_config and raw_config['actions']:
            self.game_actions.update(raw_config['actions'])
        
        # Handle v2 configs (entity_definitions)
        if 'entity_definitions' in raw_config and raw_config['entity_definitions']:
            self.game_logger.info(f"Processing v2 entity_definitions with {len(raw_config['entity_definitions'])} entities")
            # Convert v2 entity definitions to v1 format for compatibility
            for entity_id, entity_def in raw_config['entity_definitions'].items():
                if hasattr(entity_def, 'dict'):
                    # Pydantic object
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message="Pydantic serializer warnings:",
                            category=UserWarning,
                        )
                        entity_data = entity_def.dict()
                else:
                    # Dictionary
                    entity_data = entity_def
                
                # Check entity types/behaviors (v2 uses 'behaviors', v1 uses 'types')
                # The v2 pre-processor may convert 'behaviors' to 'types' during merge
                entity_types = entity_data.get('behaviors', entity_data.get('types', []))
                self.game_logger.info(f"Processing entity {entity_id} with types {entity_types}")
                if 'object' in entity_types:
                    # Convert to ObjectTypeConfig - map entity_id to id field and extract name/description from attributes/properties
                    config_data = {}
                    config_data['id'] = entity_id
                    
                    # Prefer attributes over legacy properties
                    attributes = entity_data.get('attributes', {})
                    properties = entity_data.get('properties', {})
                    name_source = attributes if attributes else properties
                    config_data['name'] = name_source.get('name', entity_id)
                    config_data['description'] = name_source.get('description', f"A {entity_id} object")
                    # Preserve object type properties (e.g., interactions, defaults)
                    if properties:
                        config_data['properties'] = properties
                    # Preserve tags if present (v2 discourages tags, but keep for backward compat in types)
                    if 'tags' in entity_data:
                        config_data['tags'] = entity_data.get('tags', [])
                    
                    # Preserve action aliases from attributes
                    if 'action_aliases' in attributes:
                        config_data['action_aliases'] = attributes['action_aliases']
                    
                    # Preserve interactions from attributes
                    if 'interactions' in attributes:
                        config_data['interactions'] = attributes['interactions']
                    
                    # Copy other properties that might be relevant
                    for key, value in entity_data.items():
                        if key not in ['behaviors', 'types', 'properties']:
                            config_data[key] = value
                    
                    self.game_object_types[entity_id] = ObjectTypeConfig(**config_data)
                elif 'character' in entity_types:
                    # Convert to CharacterConfig - map entity_id to id field and extract name from attributes (preferred)
                    self.game_logger.info(f"Processing character entity {entity_id}, checking for converted character type")
                    config_data = {}
                    config_data['id'] = entity_id
                    
                    # Extract name/backstory from attributes (preferred) or properties
                    attributes = entity_data.get('attributes', {})
                    properties = entity_data.get('properties', {})
                    attr_source = attributes if attributes else properties
                    config_data['name'] = attr_source.get('name', entity_id)
                    # Add required backstory field
                    config_data['backstory'] = attr_source.get('backstory', f"A character with the role of {config_data['name']}")
                    
                    # Copy motives if present (v2 stores motives in config field)
                    converted_motives = None
                    # Prefer attributes.motives, support legacy config.motives
                    motives_data = None
                    if 'attributes' in entity_data and 'motives' in entity_data['attributes']:
                        motives_data = entity_data['attributes']['motives']
                    elif 'properties' in entity_data and 'motives' in entity_data['properties']:
                        motives_data = entity_data['properties']['motives']
                    # drop legacy entity-level 'config' fallback
                    
                    if motives_data is not None:
                        # Convert motives from dict format to MotiveConfig objects
                        self.game_logger.info(f"Converting motives for {entity_id}: {len(motives_data)} motives found")
                        if motives_data:
                            from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
                            converted_motives = []
                            for motive_item in motives_data:
                                if isinstance(motive_item, dict):
                                    # Convert success_conditions
                                    success_conditions = self._convert_conditions(motive_item.get('success_conditions', []))
                                    # Convert failure_conditions
                                    failure_conditions = self._convert_conditions(motive_item.get('failure_conditions', []))
                                    # Create MotiveConfig object
                                    converted_motives.append(MotiveConfig(
                                        id=motive_item['id'],
                                        description=motive_item['description'],
                                        success_conditions=success_conditions,
                                        failure_conditions=failure_conditions
                                    ))
                                else:
                                    # Already a MotiveConfig object
                                    converted_motives.append(motive_item)
                            config_data['motives'] = converted_motives
                    elif 'motives' in entity_data:
                        # Handle string-encoded motives from v2 config
                        motives_data = entity_data['motives']
                        if isinstance(motives_data, str):
                            # Parse string representation of motives list
                            import ast
                            try:
                                # Replace single quotes with double quotes for proper JSON parsing
                                motives_str = motives_data.replace("'", '"')
                                motives_list = ast.literal_eval(motives_str)
                                self.game_logger.info(f"Parsed string motives for {entity_id}: {len(motives_list)} motives")
                                
                                # Convert to MotiveConfig objects
                                from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
                                converted_motives = []
                                for motive_item in motives_list:
                                    if isinstance(motive_item, dict):
                                        # Convert success_conditions
                                        success_conditions = self._convert_conditions(motive_item.get('success_conditions', []))
                                        # Convert failure_conditions
                                        failure_conditions = self._convert_conditions(motive_item.get('failure_conditions', []))
                                        # Create MotiveConfig object
                                        converted_motives.append(MotiveConfig(
                                            id=motive_item['id'],
                                            description=motive_item['description'],
                                            success_conditions=success_conditions,
                                            failure_conditions=failure_conditions
                                        ))
                                    else:
                                        # Already a MotiveConfig object
                                        converted_motives.append(motive_item)
                                config_data['motives'] = converted_motives
                            except Exception as e:
                                self.game_logger.error(f"Failed to parse motives for {entity_id}: {e}")
                                config_data['motives'] = []
                        else:
                            # Already a structured list of motive dicts
                            config_data['motives'] = motives_data
                    
                    # Copy other fields that might be relevant
                    for key, value in entity_data.items():
                        if key not in ['behaviors', 'types', 'properties', 'attributes', 'motives']:
                            config_data[key] = value
                    
                    # Store a mutated v2 entity def that includes a 'config' section so downstream code can read motives
                    stored_def = entity_data.copy()
                    # Ensure attributes exist and include name/backstory when available
                    stored_def.setdefault('attributes', {})
                    if 'name' in config_data:
                        stored_def['attributes']['name'] = config_data['name']
                    if 'backstory' in config_data:
                        stored_def['attributes']['backstory'] = config_data['backstory']
                    # Move motives under attributes for v2 schema clarity
                    if 'motives' in config_data and config_data['motives'] is not None:
                        stored_def['attributes']['motives'] = config_data['motives']
                    self.game_character_types[entity_id] = stored_def
                    self.game_logger.info(f"Stored v2 character entity {entity_id} with attributes.motives: {bool(stored_def.get('attributes', {}).get('motives'))}")
                elif 'room' in entity_types:
                    # Convert to room data - extract properties and store in game_rooms
                    attributes = entity_data.get('attributes', {})
                    properties = entity_data.get('properties', {})

                    # Parse exits from properties (fallback to attributes) and normalize
                    exits = properties.get('exits', {}) if properties else {}
                    if not exits and attributes:
                        exits = attributes.get('exits', {})
                    if isinstance(exits, str):
                        try:
                            # Handle YAML double-single-quote format ('' -> ')
                            cleaned_exits = exits.replace("''", "'")
                            exits = ast.literal_eval(cleaned_exits)
                        except:
                            # Fallback: try to parse as JSON-like format
                            try:
                                import json
                                exits = json.loads(exits.replace("'", '"'))
                            except:
                                exits = {}

                    # Parse objects from properties (fallback to attributes) and normalize
                    objects = properties.get('objects', {}) if properties else {}
                    if not objects and attributes:
                        objects = attributes.get('objects', {})
                    if isinstance(objects, str):
                        try:
                            # Handle YAML double-single-quote format ('' -> ')
                            cleaned_objects = objects.replace("''", "'")
                            objects = ast.literal_eval(cleaned_objects)
                        except:
                            # Fallback: try to parse as JSON-like format
                            try:
                                import json
                                objects = json.loads(objects.replace("'", '"'))
                            except:
                                objects = {}
                    
                    # Carry through additional room properties (e.g., dark, hidden)
                    filtered_properties = {}
                    if isinstance(properties, dict):
                        for k, v in properties.items():
                            if k not in ('exits', 'objects'):
                                filtered_properties[k] = v

                    room_data = {
                        'id': entity_id,  # Add required id field
                        'name': attributes.get('name', properties.get('name', entity_id)),
                        'description': attributes.get('description', properties.get('description', f"A room called {entity_id}")),
                        'exits': exits,
                        'objects': objects,
                        'properties': filtered_properties
                    }
                    self.game_rooms[entity_id] = room_data
        
        # Handle v1 configs (object_types, character_types)
        else:
            if 'object_types' in raw_config and raw_config['object_types']:
                self.game_object_types.update(raw_config['object_types'])
        
            if 'character_types' in raw_config and raw_config['character_types']:
                # Handle v1 character_types - legacy support
                self.game_character_types.update(raw_config['character_types'])
        
            # Extract characters from merged config
            if 'characters' in raw_config and raw_config['characters']:
                self.game_characters.update(raw_config['characters'])
        
        # Extract rooms from merged config (only if not already populated from v2 entity_definitions)
        if 'rooms' in raw_config and raw_config['rooms']:
            self.game_rooms = raw_config['rooms']
        elif not self.game_rooms:
            # Initialize empty rooms if none defined and none loaded from entity_definitions
            self.game_rooms = {}
            self.game_logger.warning("No rooms defined in config.")
        
        self.game_logger.info(f"📊 Configuration Summary: {len(self.game_object_types)} object types, {len(self.game_actions)} actions, {len(self.game_character_types)} character types, {len(self.game_characters)} characters, {len(self.game_rooms)} rooms.")

    def _load_configurations_silent(self, init_data):
        """Loads configurations silently, collecting data for consolidated reporting."""
        # With hierarchical configs, everything is already merged into game_config
        # We need to extract the merged data from the raw config dict
        
        # Get the raw merged config data
        if hasattr(self.game_config, 'model_dump'):
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="Pydantic serializer warnings:",
                        category=UserWarning,
                    )
                    raw_config = self.game_config.model_dump()
            except Exception:
                raw_config = self.game_config.dict() if hasattr(self.game_config, 'dict') else self.game_config
        elif hasattr(self.game_config, '__dict__'):
            raw_config = self.game_config.__dict__
        else:
            # If it's already a dictionary, use it directly
            raw_config = self.game_config
        
        # Handle v2 configs (action_definitions, entity_definitions)
        if 'action_definitions' in raw_config and raw_config['action_definitions']:
            # Convert v2 action definitions to v1 format for compatibility
            for action_id, action_def in raw_config['action_definitions'].items():
                if hasattr(action_def, 'dict'):
                    # Pydantic object
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message="Pydantic serializer warnings:",
                            category=UserWarning,
                        )
                        action_data = action_def.dict()
                else:
                    # Dictionary
                    action_data = action_def

                # Map v2 action_id to v1 id field
                if 'action_id' in action_data and 'id' not in action_data:
                    action_data = action_data.copy()
                    action_data['id'] = action_data.pop('action_id')
                # Ensure id exists for dict-based actions
                if 'id' not in action_data:
                    action_data = action_data.copy()
                    action_data['id'] = action_id

                self.game_actions[action_id] = ActionConfig(**action_data)

        # Handle v1 configs (actions)
        elif 'actions' in raw_config and raw_config['actions']:
            self.game_actions.update(raw_config['actions'])

        # Handle v2 configs (entity_definitions)
        self.game_logger.info(f"Raw config keys: {list(raw_config.keys())}")
        if 'entity_definitions' in raw_config and raw_config['entity_definitions']:
            self.game_logger.info(f"Found {len(raw_config['entity_definitions'])} entity definitions")
            for entity_id, entity_def in raw_config['entity_definitions'].items():
                if hasattr(entity_def, 'dict'):
                    # Pydantic object
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            message="Pydantic serializer warnings:",
                            category=UserWarning,
                        )
                        entity_data = entity_def.dict()
                else:
                    # Dictionary
                    entity_data = entity_def
                
                # Check entity types/behaviors (v2 uses 'behaviors', v1 uses 'types')
                entity_types = entity_data.get('behaviors', entity_data.get('types', []))
                self.game_logger.info(f"Processing entity {entity_id}: types = {entity_types}")
                if 'object' in entity_types:
                    # Convert to ObjectTypeConfig - map entity_id to id field and extract name/description from attributes/properties
                    config_data = {}
                    config_data['id'] = entity_id
                    # Prefer attributes over legacy properties
                    attributes = entity_data.get('attributes', {})
                    properties = entity_data.get('properties', {})
                    name_source = attributes if attributes else properties
                    config_data['name'] = name_source.get('name', entity_id)
                    config_data['description'] = name_source.get('description', f"A {entity_id} object")
                    # Preserve object type properties (e.g., interactions, defaults)
                    if properties:
                        config_data['properties'] = properties
                    # Preserve tags if present (v2 discourages tags, but keep for backward compat in types)
                    if 'tags' in entity_data:
                        config_data['tags'] = entity_data.get('tags', [])
                    
                    # Preserve action aliases from attributes
                    if 'action_aliases' in attributes:
                        config_data['action_aliases'] = attributes['action_aliases']
                    
                    # Preserve interactions from attributes
                    if 'interactions' in attributes:
                        config_data['interactions'] = attributes['interactions']
                    
                    # Copy other properties that might be relevant
                    for key, value in entity_data.items():
                        if key not in ['behaviors', 'types', 'properties']:
                            config_data[key] = value
                    
                    self.game_object_types[entity_id] = ObjectTypeConfig(**config_data)
                elif 'character' in entity_types:
                    # Convert to CharacterConfig - map entity_id to id field and extract from attributes
                    self.game_logger.info(f"Processing character entity {entity_id}, checking for converted character type")
                    config_data = {}
                    config_data['id'] = entity_id
                    # Extract name/backstory from attributes (preferred) or properties
                    attributes = entity_data.get('attributes', {})
                    properties = entity_data.get('properties', {})
                    attr_source = attributes if attributes else properties
                    config_data['name'] = attr_source.get('name', entity_id)
                    # Add required backstory field
                    config_data['backstory'] = attr_source.get('backstory', f"A character with the role of {config_data['name']}")
                    
                    # Copy motives if present (prefer attributes, then properties; no legacy 'config')
                    motives_data = None
                    if 'attributes' in entity_data and 'motives' in entity_data['attributes']:
                        motives_data = entity_data['attributes']['motives']
                    elif 'properties' in entity_data and 'motives' in entity_data['properties']:
                        motives_data = entity_data['properties']['motives']
                    if motives_data is not None:
                        # Convert motives from dict format to MotiveConfig objects
                        self.game_logger.info(f"Converting motives for {entity_id}: {len(motives_data)} motives found")
                        if motives_data:
                            from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
                            converted_motives = []
                            for motive_item in motives_data:
                                if isinstance(motive_item, dict):
                                    # Convert success_conditions
                                    success_conditions = self._convert_conditions(motive_item.get('success_conditions', []))
                                    # Convert failure_conditions
                                    failure_conditions = self._convert_conditions(motive_item.get('failure_conditions', []))
                                    # Create MotiveConfig object
                                    converted_motives.append(MotiveConfig(
                                        id=motive_item['id'],
                                        description=motive_item['description'],
                                        success_conditions=success_conditions,
                                        failure_conditions=failure_conditions
                                    ))
                                else:
                                    # Already a MotiveConfig object
                                    converted_motives.append(motive_item)
                            config_data['motives'] = converted_motives
                    elif 'motives' in entity_data:
                        # Handle string-encoded motives from v2 config
                        motives_data = entity_data['motives']
                        if isinstance(motives_data, str):
                            # Parse string representation of motives list
                            import ast
                            try:
                                # Replace single quotes with double quotes for proper JSON parsing
                                motives_str = motives_data.replace("'", '"')
                                motives_list = ast.literal_eval(motives_str)
                                self.game_logger.info(f"Parsed string motives for {entity_id}: {len(motives_list)} motives")
                                
                                # Convert to MotiveConfig objects
                                from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
                                converted_motives = []
                                for motive_item in motives_list:
                                    if isinstance(motive_item, dict):
                                        # Convert success_conditions
                                        success_conditions = self._convert_conditions(motive_item.get('success_conditions', []))
                                        # Convert failure_conditions
                                        failure_conditions = self._convert_conditions(motive_item.get('failure_conditions', []))
                                        # Create MotiveConfig object
                                        converted_motives.append(MotiveConfig(
                                            id=motive_item['id'],
                                            description=motive_item['description'],
                                            success_conditions=success_conditions,
                                            failure_conditions=failure_conditions
                                        ))
                                    else:
                                        # Already a MotiveConfig object
                                        converted_motives.append(motive_item)
                                config_data['motives'] = converted_motives
                            except Exception as e:
                                self.game_logger.error(f"Failed to parse motives for {entity_id}: {e}")
                                config_data['motives'] = []
                        else:
                            config_data['motives'] = motives_data
                    
                    # Copy other fields that might be relevant
                    for key, value in entity_data.items():
                        if key not in ['behaviors', 'types', 'properties', 'attributes', 'motives']:
                            config_data[key] = value
                    
                    # Store a mutated v2 entity def that includes an attributes section for downstream code
                    stored_def = entity_data.copy()
                    stored_def.setdefault('attributes', {})
                    if 'name' in config_data:
                        stored_def['attributes']['name'] = config_data['name']
                    if 'backstory' in config_data:
                        stored_def['attributes']['backstory'] = config_data['backstory']
                    if 'motives' in config_data and config_data['motives'] is not None:
                        stored_def['attributes']['motives'] = config_data['motives']
                    self.game_character_types[entity_id] = stored_def
                    self.game_logger.info(f"Stored v2 character entity {entity_id} with attributes.motives: {bool(stored_def.get('attributes', {}).get('motives'))}")
                elif 'room' in entity_types:
                    # Convert to room data - extract properties/attributes and store in game_rooms
                    attributes = entity_data.get('attributes', {})
                    properties = entity_data.get('properties', {})

                    # Parse exits from properties (fallback to attributes) and normalize
                    exits = properties.get('exits', {}) if properties else {}
                    if not exits and attributes:
                        exits = attributes.get('exits', {})
                    if isinstance(exits, str):
                        try:
                            # Handle YAML double-single-quote format ('' -> ')
                            cleaned_exits = exits.replace("''", "'")
                            exits = ast.literal_eval(cleaned_exits)
                        except Exception:
                            # Try YAML-safe load
                            try:
                                exits = yaml.safe_load(exits)
                            except Exception:
                                # Fallback: try to parse as JSON-like format
                                try:
                                    import json
                                    exits = json.loads(exits.replace("'", '"'))
                                except Exception:
                                    exits = {}

                    # Parse objects from properties (fallback to attributes) and normalize
                    objects = properties.get('objects', {}) if properties else {}
                    if not objects and attributes:
                        objects = attributes.get('objects', {})
                    if isinstance(objects, str):
                        try:
                            # Handle YAML double-single-quote format ('' -> ')
                            cleaned_objects = objects.replace("''", "'")
                            objects = ast.literal_eval(cleaned_objects)
                        except Exception:
                            # Try YAML-safe load
                            try:
                                objects = yaml.safe_load(objects)
                            except Exception:
                                # Fallback: try to parse as JSON-like format
                                try:
                                    import json
                                    objects = json.loads(objects.replace("'", '"'))
                                except Exception:
                                    objects = {}

                    # Carry through additional room properties (e.g., dark, hidden)
                    filtered_properties = {}
                    if isinstance(properties, dict):
                        for k, v in properties.items():
                            if k not in ('exits', 'objects'):
                                filtered_properties[k] = v

                    room_data = {
                        'id': entity_id,  # Add required id field
                        'name': attributes.get('name', properties.get('name', entity_id)),
                        'description': attributes.get('description', properties.get('description', f"A room called {entity_id}")),
                        'exits': exits,
                        'objects': objects,
                        'properties': filtered_properties
                    }
                    self.game_rooms[entity_id] = room_data
        
        # Handle v1 configs (object_types, character_types)
        else:
            if 'object_types' in raw_config and raw_config['object_types']:
                self.game_object_types.update(raw_config['object_types'])
        
            if 'character_types' in raw_config and raw_config['character_types']:
                # Handle v1 character_types - legacy support
                self.game_character_types.update(raw_config['character_types'])
        
            # Extract characters from merged config
            if 'characters' in raw_config and raw_config['characters']:
                self.game_characters.update(raw_config['characters'])
        
        # Extract rooms from merged config (only if not already populated from v2 entity_definitions)
        if not self.game_rooms and 'rooms' in raw_config and raw_config['rooms']:
            self.game_rooms = raw_config['rooms']
        elif not self.game_rooms:
            # Initialize empty rooms if none defined and none loaded from entity_definitions
            self.game_rooms = {}
            init_data['warnings'].append("No rooms defined in config.")
        
        init_data['config_loaded'] = True

    def _instantiate_rooms_and_objects_silent(self, init_data):
        """Instantiates rooms and objects silently, collecting data for consolidated reporting."""
        for room_id, room_cfg in self.game_rooms.items():
            # Handle both v1 (room_cfg['id']) and v2 (room_id as key) formats
            actual_room_id = room_cfg.get('id', room_id)
            room = Room(
                room_id=actual_room_id,
                name=room_cfg['name'],
                description=room_cfg['description'],
                exits=room_cfg.get('exits', {}),
                tags=room_cfg.get('tags', []),
                properties=room_cfg.get('properties', {})
            )
            self.rooms[room_id] = room
            # Debug: log exits/objects parsed for each room
            try:
                num_exits = len(room.exits) if isinstance(room.exits, dict) else 0
                num_objects = len(room_cfg.get('objects', {}) or {})
                init_data['warnings'].append(f"Room '{room_id}' initialized with {num_exits} exits and {num_objects} object specs")
            except Exception:
                pass
            init_data['rooms_created'] += 1

            # Place objects defined within the room config
            if room_cfg.get('objects'):
                for obj_id, obj_instance_cfg in room_cfg['objects'].items():
                    obj_type = self.game_object_types.get(obj_instance_cfg['object_type_id'])
                    if obj_type:
                        # Handle both ObjectTypeConfig objects and dictionaries
                        if hasattr(obj_type, 'tags'):
                            obj_type_tags = obj_type.tags if obj_type.tags else []
                        else:
                            obj_type_tags = obj_type.get('tags', [])
                        
                        if hasattr(obj_type, 'properties'):
                            obj_type_properties = obj_type.properties if obj_type.properties else {}
                        else:
                            obj_type_properties = obj_type.get('properties', {})
                        
                        if hasattr(obj_type, 'name'):
                            obj_type_name = obj_type.name
                        else:
                            obj_type_name = obj_type.get('name')
                        
                        if hasattr(obj_type, 'description'):
                            obj_type_description = obj_type.description
                        else:
                            obj_type_description = obj_type.get('description')
                        
                        # Extract action_aliases from entity definition
                        obj_type_aliases = {}
                        if hasattr(obj_type, 'action_aliases') and obj_type.action_aliases:
                            obj_type_aliases = obj_type.action_aliases
                        elif hasattr(obj_type, 'attributes') and obj_type.attributes and 'action_aliases' in obj_type.attributes:
                            obj_type_aliases = obj_type.attributes['action_aliases']
                        
                        final_tags = set(obj_type_tags).union(obj_instance_cfg.get('tags', []))
                        final_properties = {**obj_type_properties, **obj_instance_cfg.get('properties', {})}
                        final_aliases = {**obj_type_aliases, **obj_instance_cfg.get('action_aliases', {})}
                        
                        # Extract interactions from entity definition
                        obj_type_interactions = {}
                        if hasattr(obj_type, 'interactions'):
                            obj_type_interactions = obj_type.interactions
                        elif hasattr(obj_type, 'attributes') and obj_type.attributes and 'interactions' in obj_type.attributes:
                            obj_type_interactions = obj_type.attributes['interactions']
                        final_interactions = {**obj_type_interactions, **obj_instance_cfg.get('interactions', {})}

                        game_obj = GameObject(
                            obj_id=obj_instance_cfg['id'],
                            name=obj_instance_cfg.get('name') or obj_type_name,
                            description=obj_instance_cfg.get('description') or obj_type_description,
                            current_location_id=room.id,
                            tags=list(final_tags),
                            properties=final_properties,
                            action_aliases=final_aliases,
                            interactions=final_interactions
                        )
                        room.add_object(game_obj)
                        self.game_objects[game_obj.id] = game_obj
                        init_data['objects_placed'] += 1
                    else:
                        init_data['warnings'].append(f"Object type '{obj_instance_cfg['object_type_id']}' not found for object '{obj_instance_cfg['id']}' in room '{room.id}'. Skipping.")

    def _instantiate_player_characters_silent(self, players: List[Player], init_data):
        """Instantiates player characters silently, collecting data for consolidated reporting."""
        # Use characters if available, otherwise fall back to character_types
        available_character_ids = []
        if hasattr(self, 'game_characters') and self.game_characters:
            available_character_ids = list(self.game_characters.keys())
        elif self.game_character_types:
            available_character_ids = list(self.game_character_types.keys())

        if not available_character_ids:
            init_data['warnings'].append("No characters defined in merged configuration. Cannot assign characters to players.")
            return
        
        # Find a suitable starting room (e.g., the first room defined in the merged config)
        start_room_id = next(iter(self.game_rooms.keys()), None)
        if not start_room_id:
            init_data['warnings'].append("No rooms defined in merged configuration. Cannot assign starting room for players.")
            return

        # Handle character assignment with override support
        import random
        
        # Assign characters to players based on override parameters
        char_assignments = []
        
        # Handle character-motives override (highest priority)
        if self.character_motives_override:
            self.game_logger.info(f"Using character-motives override: {self.character_motives_override}")
            for pair in self.character_motives_override:
                if ':' in pair:
                    char_id, motive_id = pair.split(':', 1)
                    char_id = char_id.strip()
                    if char_id in available_character_ids:
                        char_assignments.append(char_id)
                        self.game_logger.info(f"Assigned character '{char_id}' with motive '{motive_id.strip()}'")
                    else:
                        self.game_logger.warning(f"Character '{char_id}' not found in available characters. Available: {available_character_ids}")
                else:
                    self.game_logger.warning(f"Invalid character-motive pair format '{pair}'. Expected 'character:motive'")
        
        # Handle separate characters and motives lists
        elif self.characters_override and self.motives_override:
            self.game_logger.info(f"Using characters override: {self.characters_override}")
            self.game_logger.info(f"Using motives override: {self.motives_override}")
            for char_id in self.characters_override:
                if char_id in available_character_ids:
                    char_assignments.append(char_id)
                else:
                    self.game_logger.warning(f"Character '{char_id}' not found in available characters. Available: {available_character_ids}")
        
        # Handle characters only override
        elif self.characters_override:
            self.game_logger.info(f"Using characters override: {self.characters_override}")
            for char_id in self.characters_override:
                if char_id in available_character_ids:
                    char_assignments.append(char_id)
                else:
                    self.game_logger.warning(f"Character '{char_id}' not found in available characters. Available: {available_character_ids}")
        
        # Handle motives only override (assign random characters with specified motives)
        elif self.motives_override:
            self.game_logger.info(f"Using motives override: {self.motives_override}")
            # For now, just assign random characters - motive assignment happens later
            if not self.deterministic:
                char_assignments = random.sample(available_character_ids, len(players))
            else:
                char_assignments = available_character_ids[:len(players)]
        
        # Handle single character override (legacy)
        elif self.character_override:
            if self.character_override in available_character_ids:
                char_assignments.append(self.character_override)
                # Fill remaining slots with random characters
                remaining_characters = [c for c in available_character_ids if c != self.character_override]
                if not self.deterministic:
                    additional_chars = random.sample(remaining_characters, min(len(players) - 1, len(remaining_characters)))
                else:
                    additional_chars = remaining_characters[:len(players) - 1]
                char_assignments.extend(additional_chars)
                self.game_logger.info(f"Assigned override character '{self.character_override}' to first player")
            else:
                self.game_logger.warning(f"Character override '{self.character_override}' not found in available characters. Available: {available_character_ids}")
                # Fall back to random assignment
                if not self.deterministic:
                    char_assignments = random.sample(available_character_ids, len(players))
                else:
                    char_assignments = available_character_ids[:len(players)]
        
        # Default random assignment if no overrides
        else:
            if not self.deterministic:
                # Random assignment in normal mode
                char_assignments = random.sample(available_character_ids, len(players))
            else:
                # Deterministic assignment (first N characters in order)
                char_assignments = available_character_ids[:len(players)]

        for i, player in enumerate(players):
            # Use the character from char_assignments list
            if i < len(char_assignments):
                char_id_to_assign = char_assignments[i]
            else:
                # Fallback if we don't have enough characters assigned
                char_id_to_assign = available_character_ids[i % len(available_character_ids)]
            # Use characters if available, otherwise fall back to character_types
            if hasattr(self, 'game_characters') and self.game_characters:
                char_cfg = self.game_characters[char_id_to_assign]
            else:
                char_cfg = self.game_character_types[char_id_to_assign]

            # Debug: Log character config
            self.game_logger.info(f"Character config for {char_id_to_assign}: {type(char_cfg)}")
            if hasattr(char_cfg, 'motives'):
                self.game_logger.info(f"  Has motives attribute: {char_cfg.motives}")
            elif isinstance(char_cfg, dict) and 'motives' in char_cfg:
                self.game_logger.info(f"  Has motives in dict: {char_cfg['motives']}")
            else:
                self.game_logger.info(f"  No motives found")

            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(char_cfg, 'id'):
                # v1 CharacterConfig object
                char_id = char_cfg.id
                char_name = char_cfg.name
                char_backstory = char_cfg.backstory
                char_motive = getattr(char_cfg, 'motive', None)  # Legacy single motive
                char_motives = getattr(char_cfg, 'motives', None)  # New multiple motives
                char_aliases = getattr(char_cfg, 'aliases', [])
            elif 'id' in char_cfg:
                # v1 dictionary format
                char_id = char_cfg['id']
                char_name = char_cfg['name']
                char_backstory = char_cfg['backstory']
                char_motive = char_cfg.get('motive', None)  # Legacy single motive
                char_motives = char_cfg.get('motives', None)  # New multiple motives
                char_aliases = char_cfg.get('aliases', [])
            else:
                # v2 EntityDefinition format - entity_id is the key, character data is in attributes (preferred) or legacy config
                char_id = char_id_to_assign  # Use the entity_id as the character id
                attributes = char_cfg.get('attributes', {})
                legacy_config = {}
                properties = char_cfg.get('properties', {})
                # Prefer attributes, then legacy config; keep properties for fallback of motives only
                config_data = attributes if attributes else legacy_config
                char_name = config_data.get('name', char_id)
                char_backstory = config_data.get('backstory', '')
                char_motive = config_data.get('motive', None)  # Legacy single motive
                char_motives = config_data.get('motives', None)  # New multiple motives
                if not char_motives and properties and 'motives' in properties:
                    char_motives = properties.get('motives')
                char_aliases = config_data.get('aliases', [])

            # Convert motives dictionaries to MotiveConfig objects if needed
            converted_motives = None
            selected_motive = None
            if char_motives and len(char_motives) > 0:
                from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
                converted_motives = []
                for motive_item in char_motives:
                    if isinstance(motive_item, MotiveConfig):
                        # Already a MotiveConfig object (from v2→v1 conversion)
                        converted_motives.append(motive_item)
                    elif isinstance(motive_item, dict):
                        # Convert success_conditions
                        success_conditions = self._convert_conditions(motive_item.get('success_conditions', []))

                        # Convert failure_conditions
                        failure_conditions = self._convert_conditions(motive_item.get('failure_conditions', []))

                        # Create MotiveConfig object
                        converted_motives.append(MotiveConfig(
                            id=motive_item['id'],
                            description=motive_item['description'],
                            success_conditions=success_conditions,
                            failure_conditions=failure_conditions
                        ))
                    else:
                        # Already a MotiveConfig object
                        converted_motives.append(motive_item)
                
                # Handle motive override - check multiple override sources
                motive_to_assign = None
                
                # Check character-motives override first
                if self.character_motives_override and i < len(self.character_motives_override):
                    pair = self.character_motives_override[i]
                    if ':' in pair:
                        _, motive_id = pair.split(':', 1)
                        motive_to_assign = motive_id.strip()
                
                # Check motives list override
                elif self.motives_override and i < len(self.motives_override):
                    motive_to_assign = self.motives_override[i]
                
                # Check single motive override (legacy)
                elif self.motive_override:
                    motive_to_assign = self.motive_override
                
                # Apply the selected motive
                if motive_to_assign:
                    # Find the specified motive
                    selected_motive = None
                    for motive in converted_motives:
                        if motive.id == motive_to_assign:
                            selected_motive = motive
                            break
                    
                    if selected_motive:
                        self.game_logger.info(f"Assigned override motive '{motive_to_assign}' to character '{char_name}'")
                    else:
                        self.game_logger.warning(f"Motive override '{motive_to_assign}' not found in available motives for character '{char_name}'. Available: {[m.id for m in converted_motives]}")
                        # Don't clear the override here as it might be used for other players
                else:
                    # No motive override, select first available motive
                    if converted_motives:
                        selected_motive = converted_motives[0]
                        self.game_logger.info(f"Assigned default motive '{selected_motive.id}' to character '{char_name}'")
            else:
                # Character has no motives
                self.game_logger.warning(f"Character '{char_name}' has no motives defined")
                selected_motive = None

            # Select initial room based on character configuration
            selected_room_id = self._select_initial_room(char_cfg, start_room_id)
            
            # Find the reason for the selected room
            initial_room_reason = None
            if hasattr(char_cfg, 'initial_rooms') and char_cfg.initial_rooms:
                for room_config in char_cfg.initial_rooms:
                    if room_config.room_id == selected_room_id:
                        initial_room_reason = room_config.reason
                        break
            elif isinstance(char_cfg, dict) and 'initial_rooms' in char_cfg:
                for room_config in char_cfg['initial_rooms']:
                    if room_config['room_id'] == selected_room_id:
                        initial_room_reason = room_config['reason']
                        break
            
            # Create character with new motives system support
            player_char = Character(
                char_id=f"{char_id}_instance_{i}", # Make character instance ID unique                                                
                name=char_name,
                backstory=char_backstory,
                motive=char_motive,  # Legacy single motive
                motives=converted_motives,  # New multiple motives (converted)
                selected_motive=selected_motive,  # Override motive if specified
                current_room_id=selected_room_id,
                action_points=self.initial_ap_per_turn, # Use configurable initial AP
                aliases=char_aliases,
                deterministic=self.deterministic,  # Pass deterministic flag
                short_name=getattr(char_cfg, 'short_name', None) if hasattr(char_cfg, 'short_name') else char_cfg.get('short_name', None) if isinstance(char_cfg, dict) else None
            )
            
            # Store the initial room reason for use in initial turn message
            player_char.initial_room_reason = initial_room_reason
            
            player.character = player_char # Link player to character
            self.player_characters[player_char.id] = player_char
            self.rooms[selected_room_id].add_player(player_char) # Add player to the room
            init_data['characters_assigned'].append(f"{player_char.name} to {player.name}")

    def _log_initialization_report(self, init_data):
        """Logs a consolidated initialization report."""
        report_lines = ["🏗️ Game Initialization Report:"]
        
        if init_data['config_loaded']:
            report_lines.append(f"  📊 Configuration: {len(self.game_object_types)} object types, {len(self.game_actions)} actions, {len(self.game_character_types)} character types, {len(self.game_characters)} characters, {len(self.game_rooms)} rooms")
        
        report_lines.append(f"  🏠 Rooms: Created {init_data['rooms_created']} rooms and placed {init_data['objects_placed']} objects")
        
        if init_data['characters_assigned']:
            report_lines.append(f"  🎭 Characters: Assigned {len(init_data['characters_assigned'])} characters")
            for assignment in init_data['characters_assigned']:
                report_lines.append(f"    • {assignment}")
        
        if init_data['warnings']:
            report_lines.append(f"  ⚠️ Warnings: {len(init_data['warnings'])} issues")
            for warning in init_data['warnings']:
                report_lines.append(f"    • {warning}")
        
        self.game_logger.info("\n".join(report_lines))

    def _convert_conditions(self, conditions_data):
        """Convert conditions from YAML dict format to MotiveConfig format."""
        from motive.config import ActionRequirementConfig, MotiveConditionGroup
        
        if not conditions_data:
            return ActionRequirementConfig(type="character_has_property", property="dummy", value=True)  # Default empty condition
        
        # If it's a single condition (dict with 'type')
        if isinstance(conditions_data, dict) and 'type' in conditions_data:
            return ActionRequirementConfig(**conditions_data)
        
        # If it's a list of conditions
        if isinstance(conditions_data, list):
            if len(conditions_data) == 1:
                # Single condition in a list
                return ActionRequirementConfig(**conditions_data[0])
            else:
                # Handle v2 format where operator is a separate list item
                # Format: [{'operator': 'AND'}, {'type': '...', 'property': '...', 'value': '...'}, ...]
                if len(conditions_data) >= 2 and isinstance(conditions_data[0], dict) and 'operator' in conditions_data[0]:
                    operator = conditions_data[0]['operator']
                    conditions = []
                    for condition_dict in conditions_data[1:]:
                        if isinstance(condition_dict, dict) and 'type' in condition_dict:
                            conditions.append(ActionRequirementConfig(**condition_dict))
                    
                    if conditions:
                        return MotiveConditionGroup(operator=operator, conditions=conditions)
                
                # Fallback: try to find operator in first condition
                if isinstance(conditions_data[0], dict) and 'operator' in conditions_data[0]:
                    operator = conditions_data[0]['operator']
                    conditions = []
                    for condition_dict in conditions_data[1:]:
                        conditions.append(ActionRequirementConfig(**condition_dict))
                    
                    return MotiveConditionGroup(operator=operator, conditions=conditions)
                
                # If no operator found, treat as single condition
                return ActionRequirementConfig(**conditions_data[0])
        
        return ActionRequirementConfig(type="character_has_property", property="dummy", value=True)  # Default fallback

    def _load_yaml_config(self, file_path: str, config_model: BaseModel) -> BaseModel:
        """Loads and validates a YAML configuration file against a Pydantic model."""
        try:
            # Resolve path relative to the configs directory (where game.yaml is located)
            import os
            configs_dir = os.path.dirname(os.path.abspath("configs/game.yaml"))
            resolved_path = os.path.join(configs_dir, file_path)
            
            with open(resolved_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
            
            validated_config = config_model(**raw_config)
            self.game_logger.info(f"Successfully loaded and validated {resolved_path} as {config_model.__name__}")
            return validated_config
        except FileNotFoundError:
            self.game_logger.error(f"Configuration file not found: {resolved_path}")
            raise ConfigNotFoundError(f"Configuration file not found: {resolved_path}")
        except yaml.YAMLError as e:
            self.game_logger.error(f"Error parsing YAML file {resolved_path}: {e}")
            raise ConfigParseError(f"Error parsing YAML file {resolved_path}: {e}")
        except ValidationError as e:
            self.game_logger.error(f"Validation error in {file_path} for {config_model.__name__}: {e}")
            raise ConfigValidationError(f"Validation error in {file_path} for {config_model.__name__}: {e}")
        except Exception as e:
            self.game_logger.error(f"An unexpected error occurred while loading {file_path}: {e}")
            raise e # Re-raise unexpected exceptions

    def _merge_configurations(self):
        self.game_logger.info("Merging theme and edition configurations...")
        
        # 1. Merge Object Types
        self.game_object_types.update(self.theme_cfg.object_types)
        # Edition objects config are ObjectInstanceConfig, not ObjectTypeConfig. 
        # This line should be removed or logic adjusted if edition can define new object *types*
        # For now, adhering to GM-10, edition objects are instances not types.
        # self.game_object_types.update(self.edition_cfg.objects) 
        self.game_logger.info(f"Merged {len(self.game_object_types)} object types.")

        # 2. Merge Actions
        self.game_actions.update(self.theme_cfg.actions)
        # self.game_actions.update(self.edition_cfg.actions) # Edition actions can override or add
        self.game_logger.info(f"Merged {len(self.game_actions)} actions.")

        # 3. Merge Character Types
        self.game_character_types.update(self.theme_cfg.character_types)
        # Edition characters config are CharacterConfig (types), not character instances.
        if self.edition_cfg.characters: # Use 'characters' from EditionConfig
            self.game_character_types.update(self.edition_cfg.characters) # Edition characters can override or add
        self.game_logger.info(f"Merged {len(self.game_character_types)} character types.")

    def _instantiate_rooms_and_objects(self):
        self.game_logger.info("🏗️ Instantiating rooms and objects...")
        rooms_created = 0
        objects_placed = 0
        
        for room_id, room_cfg in self.game_rooms.items():
            room = Room(
                room_id=room_cfg['id'],
                name=room_cfg['name'],
                description=room_cfg['description'],
                exits=room_cfg.get('exits', {}),
                tags=room_cfg.get('tags', []),
                properties=room_cfg.get('properties', {})
            )
            self.rooms[room_id] = room
            rooms_created += 1

            # Place objects defined within the room config
            if room_cfg.get('objects'):
                for obj_id, obj_instance_cfg in room_cfg['objects'].items():
                    obj_type = self.game_object_types.get(obj_instance_cfg['object_type_id'])
                    if obj_type:
                        # Handle both ObjectTypeConfig objects and dictionaries
                        if hasattr(obj_type, 'tags'):
                            obj_type_tags = obj_type.tags if obj_type.tags else []
                        else:
                            obj_type_tags = obj_type.get('tags', [])
                        
                        if hasattr(obj_type, 'properties'):
                            obj_type_properties = obj_type.properties if obj_type.properties else {}
                        else:
                            obj_type_properties = obj_type.get('properties', {})
                        
                        if hasattr(obj_type, 'name'):
                            obj_type_name = obj_type.name
                        else:
                            obj_type_name = obj_type.get('name')
                        
                        if hasattr(obj_type, 'description'):
                            obj_type_description = obj_type.description
                        else:
                            obj_type_description = obj_type.get('description')
                        
                        # Extract action_aliases from entity definition
                        obj_type_aliases = {}
                        if hasattr(obj_type, 'action_aliases') and obj_type.action_aliases:
                            obj_type_aliases = obj_type.action_aliases
                        elif hasattr(obj_type, 'attributes') and obj_type.attributes and 'action_aliases' in obj_type.attributes:
                            obj_type_aliases = obj_type.attributes['action_aliases']
                        
                        final_tags = set(obj_type_tags).union(obj_instance_cfg.get('tags', []))
                        final_properties = {**obj_type_properties, **obj_instance_cfg.get('properties', {})}
                        final_aliases = {**obj_type_aliases, **obj_instance_cfg.get('action_aliases', {})}
                        
                        # Extract interactions from entity definition
                        obj_type_interactions = {}
                        if hasattr(obj_type, 'interactions'):
                            obj_type_interactions = obj_type.interactions
                        elif hasattr(obj_type, 'attributes') and obj_type.attributes and 'interactions' in obj_type.attributes:
                            obj_type_interactions = obj_type.attributes['interactions']
                        final_interactions = {**obj_type_interactions, **obj_instance_cfg.get('interactions', {})}

                        game_obj = GameObject(
                            obj_id=obj_instance_cfg['id'],
                            name=obj_instance_cfg.get('name') or obj_type_name,
                            description=obj_instance_cfg.get('description') or obj_type_description,
                            current_location_id=room.id,
                            tags=list(final_tags),
                            properties=final_properties,
                            action_aliases=final_aliases,
                            interactions=final_interactions
                        )
                        room.add_object(game_obj)
                        self.game_objects[game_obj.id] = game_obj
                        objects_placed += 1
                    else:
                        self.game_logger.warning(f"Object type '{obj_instance_cfg['object_type_id']}' not found for object '{obj_instance_cfg['id']}' in room '{room.id}'. Skipping.")
        
        self.game_logger.info(f"Created {rooms_created} rooms and placed {objects_placed} objects.")

    def _select_initial_room(self, char_config, default_room_id: str) -> str:
        """Select an initial room for a character based on their configuration."""
        import random
        
        # Check if character has initial_rooms configured
        initial_rooms = None
        if hasattr(char_config, 'initial_rooms') and char_config.initial_rooms:
            initial_rooms = char_config.initial_rooms
        elif isinstance(char_config, dict) and 'initial_rooms' in char_config:
            initial_rooms = char_config['initial_rooms']
        
        if not initial_rooms:
            # No custom initial rooms, use default
            return default_room_id
        
        # Convert to list if it's a dict (from merged config)
        if isinstance(initial_rooms, dict):
            initial_rooms = list(initial_rooms.values())
        
        # Select room based on weighted random choice
        rooms = []
        weights = []
        
        for room_config in initial_rooms:
            room_id = room_config.room_id if hasattr(room_config, 'room_id') else room_config['room_id']
            chance = room_config.chance if hasattr(room_config, 'chance') else room_config['chance']
            
            # Only include rooms that exist in the game
            if room_id in self.game_rooms:
                rooms.append(room_id)
                weights.append(chance)
        
        if not rooms:
            # No valid rooms found, use default
            return default_room_id
        
        # Normalize weights if they exceed 100% (user-friendly for story writers)
        total_weight = sum(weights)
        if total_weight > 100:
            # Normalize proportionally to sum to 100
            weights = [int(weight * 100 / total_weight) for weight in weights]
            # Ensure we don't have any zero weights (minimum 1%)
            weights = [max(1, weight) for weight in weights]
            # Re-normalize to ensure they sum to 100
            total_weight = sum(weights)
            if total_weight != 100:
                # Adjust the largest weight to make it exactly 100
                max_idx = weights.index(max(weights))
                weights[max_idx] += (100 - total_weight)
        
        # Use weighted random choice
        if self.deterministic:
            # In deterministic mode, always pick the first room
            return rooms[0]
        else:
            # Use random.choices for weighted selection
            return random.choices(rooms, weights=weights, k=1)[0]

    def _instantiate_player_characters(self, players: List[Player]):
        self.game_logger.info("🎭 Instantiating player characters and assigning to players...")
        # Use characters if available, otherwise fall back to character_types
        available_character_ids = []
        if hasattr(self, 'game_characters') and self.game_characters:
            available_character_ids = list(self.game_characters.keys())
        elif self.game_character_types:
            available_character_ids = list(self.game_character_types.keys())
        
        # Filter out characters without motives - only characters with motives should be playable
        playable_character_ids = []
        for char_id in available_character_ids:
            char_cfg = None
            if hasattr(self, 'game_characters') and self.game_characters:
                char_cfg = self.game_characters[char_id]
            else:
                char_cfg = self.game_character_types[char_id]
            
            # Check if character has motives
            has_motives = False
            if hasattr(char_cfg, 'motives') and char_cfg.motives and len(char_cfg.motives) > 0:
                has_motives = True
            elif isinstance(char_cfg, dict) and char_cfg.get('motives') and len(char_cfg.get('motives', [])) > 0:
                has_motives = True
            elif hasattr(char_cfg, 'motive') and char_cfg.motive:
                has_motives = True
            elif isinstance(char_cfg, dict) and char_cfg.get('motive'):
                has_motives = True
            
            if has_motives:
                playable_character_ids.append(char_id)
            else:
                self.game_logger.warning(f"Character '{char_id}' has no motives - excluding from playable characters")
        
        available_character_ids = playable_character_ids
        
        if not available_character_ids:
            self.game_logger.error("No playable characters (with motives) defined in merged configuration. Cannot assign characters to players.")
            return
        
        # Check if we have enough characters for all players
        if len(players) > len(available_character_ids):
            self.game_logger.warning(f"More players ({len(players)}) than characters ({len(available_character_ids)}). Will duplicate characters as needed.")
            # Allow character duplication - we'll handle this in the assignment logic below
        
        # Find a suitable starting room (e.g., the first room defined in the merged config)
        default_start_room_id = next(iter(self.game_rooms.keys()), None)
        if not default_start_room_id:
            self.game_logger.error("No rooms defined in merged configuration. Cannot assign starting room for players.")
            return

        # Handle character assignment with override support
        import random
        
        # Assign characters to players based on override parameters
        char_assignments = []
        
        # Handle character-motives override (highest priority)
        if self.character_motives_override:
            self.game_logger.info(f"Using character-motives override: {self.character_motives_override}")
            for pair in self.character_motives_override:
                if ':' in pair:
                    char_id, motive_id = pair.split(':', 1)
                    char_id = char_id.strip()
                    if char_id in available_character_ids:
                        char_assignments.append(char_id)
                        self.game_logger.info(f"Assigned character '{char_id}' with motive '{motive_id.strip()}'")
                    else:
                        self.game_logger.warning(f"Character '{char_id}' not found in available characters. Available: {available_character_ids}")
                else:
                    self.game_logger.warning(f"Invalid character-motive pair format '{pair}'. Expected 'character:motive'")
        
        # Handle separate characters and motives lists
        elif self.characters_override and self.motives_override:
            self.game_logger.info(f"Using characters override: {self.characters_override}")
            self.game_logger.info(f"Using motives override: {self.motives_override}")
            for char_id in self.characters_override:
                if char_id in available_character_ids:
                    char_assignments.append(char_id)
                    self.game_logger.info(f"Assigned character '{char_id}'")
                else:
                    self.game_logger.warning(f"Character '{char_id}' not found in available characters. Available: {available_character_ids}")
        
        # Handle characters only override
        elif self.characters_override:
            self.game_logger.info(f"Using characters override: {self.characters_override}")
            for char_id in self.characters_override:
                if char_id in available_character_ids:
                    char_assignments.append(char_id)
                    self.game_logger.info(f"Assigned character '{char_id}'")
                else:
                    self.game_logger.warning(f"Character '{char_id}' not found in available characters. Available: {available_character_ids}")
        
        # Handle motives only override (assign random characters with specified motives)
        elif self.motives_override:
            self.game_logger.info(f"Using motives override: {self.motives_override}")
            # For motives-only override, we'll assign random characters but the motive assignment will be handled later
            remaining_characters = available_character_ids.copy()
            for i in range(len(players)):
                if remaining_characters:
                    char_assignments.append(remaining_characters.pop(0))
                else:
                    # Duplicate characters if needed
                    char_assignments.append(available_character_ids[i % len(available_character_ids)])
        
        # Handle single character override (legacy)
        elif self.character_override:
            if self.character_override in available_character_ids:
                char_assignments.append(self.character_override)
                remaining_characters = available_character_ids.copy()
                remaining_characters.remove(self.character_override)
                self.game_logger.info(f"Assigned override character '{self.character_override}' to first player")
                
                # Assign remaining characters to remaining players (with duplication if needed)
                remaining_players = len(players) - len(char_assignments)
                if remaining_players > 0:
                    if not self.deterministic:
                        # Random assignment for remaining characters (with duplication if needed)
                        if remaining_players <= len(remaining_characters):
                            remaining_assignments = random.sample(remaining_characters, remaining_players)
                        else:
                            # Need to duplicate characters
                            remaining_assignments = []
                            for i in range(remaining_players):
                                remaining_assignments.append(random.choice(remaining_characters))
                    else:
                        # Deterministic assignment (cycle through characters if needed)
                        remaining_assignments = []
                        for i in range(remaining_players):
                            remaining_assignments.append(remaining_characters[i % len(remaining_characters)])
                    char_assignments.extend(remaining_assignments)
            else:
                self.game_logger.warning(f"Character override '{self.character_override}' not found in available characters. Available: {available_character_ids}")
                # Fall through to default assignment
        
        # Default assignment (no overrides)
        if not char_assignments:
            if not self.deterministic:
                # Random assignment in normal mode
                char_assignments = random.sample(available_character_ids, len(players))
            else:
                # Deterministic assignment (cycle through characters if needed)
                char_assignments = []
                for i in range(len(players)):
                    char_assignments.append(available_character_ids[i % len(available_character_ids)])

        for i, player in enumerate(players):
            char_id_to_assign = char_assignments[i]
            # Use characters if available, otherwise fall back to character_types
            if hasattr(self, 'game_characters') and self.game_characters:
                char_cfg = self.game_characters[char_id_to_assign]
            else:
                char_cfg = self.game_character_types[char_id_to_assign]                                              

            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(char_cfg, 'id'):
                # v1 CharacterConfig object
                char_id = char_cfg.id
                char_name = char_cfg.name
                char_backstory = char_cfg.backstory
                char_motive = getattr(char_cfg, 'motive', None)  # Legacy single motive
                char_motives = getattr(char_cfg, 'motives', None)  # New multiple motives
                char_aliases = getattr(char_cfg, 'aliases', [])
            elif 'id' in char_cfg:
                # v1 dictionary format
                char_id = char_cfg['id']
                char_name = char_cfg['name']
                char_backstory = char_cfg['backstory']
                char_motive = char_cfg.get('motive', None)  # Legacy single motive
                char_motives = char_cfg.get('motives', None)  # New multiple motives
                char_aliases = char_cfg.get('aliases', [])
            else:
                # v2 EntityDefinition format - entity_id is the key, character data is in config
                char_id = char_id_to_assign  # Use the entity_id as the character id
                config_data = {}
                char_name = config_data.get('name', char_id)
                char_backstory = config_data.get('backstory', '')
                char_motive = config_data.get('motive', None)  # Legacy single motive
                char_motives = config_data.get('motives', None)  # New multiple motives
                char_aliases = config_data.get('aliases', [])

            # Convert motives dictionaries to MotiveConfig objects if needed
            converted_motives = None
            selected_motive = None
            if char_motives and len(char_motives) > 0:
                from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
                converted_motives = []
                for motive_item in char_motives:
                    if isinstance(motive_item, MotiveConfig):
                        # Already a MotiveConfig object (from v2→v1 conversion)
                        converted_motives.append(motive_item)
                    elif isinstance(motive_item, dict):
                        # Convert success_conditions
                        success_conditions = self._convert_conditions(motive_item.get('success_conditions', []))

                        # Convert failure_conditions
                        failure_conditions = self._convert_conditions(motive_item.get('failure_conditions', []))

                        # Create MotiveConfig object
                        converted_motives.append(MotiveConfig(
                            id=motive_item['id'],
                            description=motive_item['description'],
                            success_conditions=success_conditions,
                            failure_conditions=failure_conditions
                        ))
                    else:
                        # Already a MotiveConfig object
                        converted_motives.append(motive_item)
                
                # Handle motive override - check multiple override sources
                motive_to_assign = None
                
                # Check character-motives override first
                if self.character_motives_override and i < len(self.character_motives_override):
                    pair = self.character_motives_override[i]
                    if ':' in pair:
                        _, motive_id = pair.split(':', 1)
                        motive_to_assign = motive_id.strip()
                
                # Check motives list override
                elif self.motives_override and i < len(self.motives_override):
                    motive_to_assign = self.motives_override[i]
                
                # Check single motive override (legacy)
                elif self.motive_override:
                    motive_to_assign = self.motive_override
                
                # Apply the selected motive
                if motive_to_assign:
                    # Find the specified motive
                    selected_motive = None
                    for motive in converted_motives:
                        if motive.id == motive_to_assign:
                            selected_motive = motive
                            break
                    
                    if selected_motive:
                        self.game_logger.info(f"Assigned override motive '{motive_to_assign}' to character '{char_name}'")
                    else:
                        self.game_logger.warning(f"Motive override '{motive_to_assign}' not found in available motives for character '{char_name}'. Available: {[m.id for m in converted_motives]}")
                        # Don't clear the override here as it might be used for other players
                else:
                    # No motive override, select first available motive
                    if converted_motives:
                        selected_motive = converted_motives[0]
                        self.game_logger.info(f"Assigned default motive '{selected_motive.id}' to character '{char_name}'")
            else:
                # Character has no motives
                self.game_logger.warning(f"Character '{char_name}' has no motives defined")
                selected_motive = None

            # Select initial room based on character configuration
            selected_room_id = self._select_initial_room(char_cfg, default_start_room_id)
            
            # Find the reason for the selected room
            initial_room_reason = None
            if hasattr(char_cfg, 'initial_rooms') and char_cfg.initial_rooms:
                for room_config in char_cfg.initial_rooms:
                    if room_config.room_id == selected_room_id:
                        initial_room_reason = room_config.reason
                        break
            elif isinstance(char_cfg, dict) and 'initial_rooms' in char_cfg:
                for room_config in char_cfg['initial_rooms']:
                    if room_config['room_id'] == selected_room_id:
                        initial_room_reason = room_config['reason']
                        break
            
            # Create character with new motives system support
            player_char = Character(
                char_id=f"{char_id}_instance_{i}", # Make character instance ID unique                                                
                name=char_name,
                backstory=char_backstory,
                motive=char_motive,  # Legacy single motive
                motives=converted_motives,  # New multiple motives (converted)
                selected_motive=selected_motive,  # Override motive if specified
                current_room_id=selected_room_id,
                action_points=self.initial_ap_per_turn, # Use configurable initial AP
                aliases=char_aliases,
                deterministic=self.deterministic,  # Pass deterministic flag
                short_name=getattr(char_cfg, 'short_name', None) if hasattr(char_cfg, 'short_name') else char_cfg.get('short_name', None) if isinstance(char_cfg, dict) else None
            )
            
            # Store the initial room reason for use in initial turn message
            player_char.initial_room_reason = initial_room_reason
            
            player.character = player_char # Link player to character
            self.player_characters[player_char.id] = player_char
            self.rooms[selected_room_id].add_player(player_char) # Add player to the room
            self.game_logger.info(f"Assigned {player_char.name} to {player.name}")
