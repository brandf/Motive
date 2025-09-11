import logging
import yaml
from typing import Dict, List, Optional
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
    def __init__(self, game_config: GameConfig, game_id: str, game_logger: logging.Logger, initial_ap_per_turn: int = 20):
        self.game_config = game_config # This is the overall GameConfig loaded from config.yaml
        self.game_id = game_id
        self.game_logger = game_logger
        self.initial_ap_per_turn = initial_ap_per_turn # Store initial AP per turn

        self.rooms: Dict[str, Room] = {}
        self.game_objects: Dict[str, GameObject] = {}
        self.player_characters: Dict[str, Character] = {}

        # These will store the merged configurations
        self.game_object_types: Dict[str, ObjectTypeConfig] = {}
        self.game_actions: Dict[str, ActionConfig] = {}
        self.game_character_types: Dict[str, CharacterConfig] = {}
        self.game_characters: Dict[str, CharacterConfig] = {}

        # Store loaded configs for later merging
        self.core_cfg: Optional[CoreConfig] = None
        self.theme_cfg: Optional[ThemeConfig] = None
        self.edition_cfg: Optional[EditionConfig] = None

    def initialize_game_world(self, players: List[Player]):
        # Load configurations from the merged game config
        self._load_configurations()
        self._instantiate_rooms_and_objects()
        self._instantiate_player_characters(players)

    def _load_configurations(self):
        """Loads configurations from the already-merged game config."""
        self.game_logger.info("🔧 Loading game configurations...")

        # With hierarchical configs, everything is already merged into game_config
        # We need to extract the merged data from the raw config dict
        
        # Get the raw merged config data
        if hasattr(self.game_config, 'model_dump'):
            raw_config = self.game_config.model_dump()
        elif hasattr(self.game_config, '__dict__'):
            raw_config = self.game_config.__dict__
        else:
            # If it's already a dictionary, use it directly
            raw_config = self.game_config
        
        # Extract actions from merged config
        if 'actions' in raw_config and raw_config['actions']:
            self.game_actions.update(raw_config['actions'])
            self.game_logger.info(f"⚔️ Loaded {len(raw_config['actions'])} actions from merged config.")
        
        # Extract object types from merged config
        if 'object_types' in raw_config and raw_config['object_types']:
            self.game_object_types.update(raw_config['object_types'])
            self.game_logger.info(f"📦 Loaded {len(raw_config['object_types'])} object types from merged config.")
        
        # Extract character types from merged config
        if 'character_types' in raw_config and raw_config['character_types']:
            self.game_character_types.update(raw_config['character_types'])
            self.game_logger.info(f"👥 Loaded {len(raw_config['character_types'])} character types from merged config.")
        
        # Extract characters from merged config
        if 'characters' in raw_config and raw_config['characters']:
            self.game_characters.update(raw_config['characters'])
            self.game_logger.info(f"🎭 Loaded {len(raw_config['characters'])} characters from merged config.")
        
        # Extract rooms from merged config
        if 'rooms' in raw_config and raw_config['rooms']:
            self.game_rooms = raw_config['rooms']
            self.game_logger.info(f"🏠 Loaded {len(raw_config['rooms'])} rooms from merged config.")
        else:
            # Initialize empty rooms if none defined
            self.game_rooms = {}
            self.game_logger.info("⚠️ No rooms defined in config.")
        
        self.game_logger.info(f"📊 Total loaded: {len(self.game_object_types)} object types, {len(self.game_actions)} actions, {len(self.game_character_types)} character types, {len(self.game_characters)} characters.")

    def _convert_conditions(self, conditions_data):
        """Convert conditions from YAML dict format to MotiveConfig format."""
        from motive.config import ActionRequirementConfig, MotiveConditionGroup
        
        if not conditions_data:
            return ActionRequirementConfig(type="player_has_tag", tag="dummy")  # Default empty condition
        
        # If it's a single condition (dict with 'type')
        if isinstance(conditions_data, dict) and 'type' in conditions_data:
            return ActionRequirementConfig(**conditions_data)
        
        # If it's a list of conditions
        if isinstance(conditions_data, list):
            if len(conditions_data) == 1:
                # Single condition in a list
                return ActionRequirementConfig(**conditions_data[0])
            else:
                # Multiple conditions - require explicit operator
                if not isinstance(conditions_data[0], dict) or 'operator' not in conditions_data[0]:
                    raise ValueError("Multiple conditions require explicit 'operator' field (AND or OR)")
                
                operator = conditions_data[0]['operator']
                conditions = []
                for condition_dict in conditions_data[1:]:
                    conditions.append(ActionRequirementConfig(**condition_dict))
                
                return MotiveConditionGroup(operator=operator, conditions=conditions)
        
        return ActionRequirementConfig(type="player_has_tag", tag="dummy")  # Default fallback

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
            self.game_logger.info(f"  🏠 Created room: {room.name} ({room.id})")

            # Place objects defined within the room config
            if room_cfg.get('objects'):
                for obj_id, obj_instance_cfg in room_cfg['objects'].items():
                    obj_type = self.game_object_types.get(obj_instance_cfg['object_type_id'])
                    if obj_type:
                        final_tags = set(obj_type.get('tags', [])).union(obj_instance_cfg.get('tags', []))
                        final_properties = {**obj_type.get('properties', {}), **obj_instance_cfg.get('properties', {})}

                        game_obj = GameObject(
                            obj_id=obj_instance_cfg['id'],
                            name=obj_instance_cfg.get('name') or obj_type.get('name'),
                            description=obj_instance_cfg.get('description') or obj_type.get('description'),
                            current_location_id=room.id,
                            tags=list(final_tags),
                            properties=final_properties
                        )
                        room.add_object(game_obj)
                        self.game_objects[game_obj.id] = game_obj
                        self.game_logger.info(f"    📦 Placed object {game_obj.name} ({game_obj.id}) in {room.name}")
                    else:
                        self.game_logger.warning(f"⚠️ Object type '{obj_instance_cfg['object_type_id']}' not found for object '{obj_instance_cfg['id']}' in room '{room.id}'. Skipping.")

    def _instantiate_player_characters(self, players: List[Player]):
        self.game_logger.info("🎭 Instantiating player characters and assigning to players...")
        # Use characters if available, otherwise fall back to character_types
        available_character_ids = []
        if hasattr(self, 'game_characters') and self.game_characters:
            available_character_ids = list(self.game_characters.keys())
            self.game_logger.info(f"🎯 Using {len(available_character_ids)} characters from characters section")
        elif self.game_character_types:
            available_character_ids = list(self.game_character_types.keys())
            self.game_logger.info(f"🎯 Using {len(available_character_ids)} characters from character_types section")
        
        if not available_character_ids:
            self.game_logger.error("❌ No characters defined in merged configuration. Cannot assign characters to players.")
            return
        
        # Find a suitable starting room (e.g., the first room defined in the merged config)
        start_room_id = next(iter(self.game_rooms.keys()), None)
        if not start_room_id:
            self.game_logger.error(f"❌ No rooms defined in merged configuration. Cannot assign starting room for players.")
            return

        for i, player in enumerate(players):
            char_id_to_assign = available_character_ids[i % len(available_character_ids)]
            # Use characters if available, otherwise fall back to character_types
            if hasattr(self, 'game_characters') and self.game_characters:
                char_cfg = self.game_characters[char_id_to_assign]
            else:
                char_cfg = self.game_character_types[char_id_to_assign]                                              

            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(char_cfg, 'id'):
                char_id = char_cfg.id
                char_name = char_cfg.name
                char_backstory = char_cfg.backstory
                char_motive = getattr(char_cfg, 'motive', None)  # Legacy single motive
                char_motives = getattr(char_cfg, 'motives', None)  # New multiple motives
                char_aliases = getattr(char_cfg, 'aliases', [])
            else:
                # Handle dictionary from merged config
                char_id = char_cfg['id']
                char_name = char_cfg['name']
                char_backstory = char_cfg['backstory']
                char_motive = char_cfg.get('motive', None)  # Legacy single motive
                char_motives = char_cfg.get('motives', None)  # New multiple motives
                char_aliases = char_cfg.get('aliases', [])

            # Convert motives dictionaries to MotiveConfig objects if needed
            converted_motives = None
            if char_motives:
                from motive.config import MotiveConfig, ActionRequirementConfig, MotiveConditionGroup
                converted_motives = []
                for motive_dict in char_motives:
                    if isinstance(motive_dict, dict):
                        # Convert success_conditions
                        success_conditions = self._convert_conditions(motive_dict.get('success_conditions', []))
                        
                        # Convert failure_conditions  
                        failure_conditions = self._convert_conditions(motive_dict.get('failure_conditions', []))
                        
                        # Create MotiveConfig object
                        converted_motives.append(MotiveConfig(
                            id=motive_dict['id'],
                            description=motive_dict['description'],
                            success_conditions=success_conditions,
                            failure_conditions=failure_conditions
                        ))
                    else:
                        # Already a MotiveConfig object
                        converted_motives.append(motive_dict)

            # Create character with new motives system support
            player_char = Character(
                char_id=f"{char_id}_instance_{i}", # Make character instance ID unique                                                
                name=char_name,
                backstory=char_backstory,
                motive=char_motive,  # Legacy single motive
                motives=converted_motives,  # New multiple motives (converted)
                current_room_id=start_room_id,
                action_points=self.initial_ap_per_turn, # Use configurable initial AP
                aliases=char_aliases
            )
            player.character = player_char # Link player to character
            self.player_characters[player_char.id] = player_char
            self.rooms[start_room_id].add_player(player_char) # Add player to the room
            self.game_logger.info(f"  👤 Assigned {player_char.name} ({player_char.id}) to player {player.name} in room {start_room_id}.")
