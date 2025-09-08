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
from motive.game_objects import GameObject # Import GameObject
from motive.game_rooms import Room
from motive.player import Player, PlayerCharacter # Import Player and PlayerCharacter
from motive.exceptions import ConfigNotFoundError, ConfigParseError, ConfigValidationError

class GameInitializer:
    def __init__(self, game_config: GameConfig, game_id: str, game_logger: logging.Logger, initial_ap_per_turn: int = 20):
        self.game_config = game_config # This is the overall GameConfig loaded from config.yaml
        self.game_id = game_id
        self.game_logger = game_logger
        self.initial_ap_per_turn = initial_ap_per_turn # Store initial AP per turn

        self.rooms: Dict[str, Room] = {}
        self.game_objects: Dict[str, GameObject] = {}
        self.player_characters: Dict[str, PlayerCharacter] = {}

        # These will store the merged configurations
        self.game_object_types: Dict[str, ObjectTypeConfig] = {}
        self.game_actions: Dict[str, ActionConfig] = {}
        self.game_character_types: Dict[str, CharacterConfig] = {}

        # Store loaded configs for later merging
        self.core_cfg: Optional[CoreConfig] = None
        self.theme_cfg: Optional[ThemeConfig] = None
        self.edition_cfg: Optional[EditionConfig] = None

    def initialize_game_world(self, players: List[Player]):
        self._load_configurations()
        self._merge_configurations()
        self._instantiate_rooms_and_objects()
        self._instantiate_player_characters(players)

    def _load_configurations(self):
        """Loads theme and edition configurations and merges them."""
        self.game_logger.info("Loading game configurations...")

        # Load CoreConfig first
        try:
            self.core_cfg = self._load_yaml_config(self.game_config.game_settings.core_config_path, CoreConfig)
        except (ConfigNotFoundError, ConfigParseError, ConfigValidationError) as e:
            self.game_logger.critical(f"Critical configuration error for core config: {e}")
            raise # Re-raise to stop game initialization

        # Load ThemeConfig
        try:
            self.theme_cfg = self._load_yaml_config(self.game_config.game_settings.theme_config_path, ThemeConfig)
        except (ConfigNotFoundError, ConfigParseError, ConfigValidationError) as e:
            self.game_logger.critical(f"Critical configuration error for theme config: {e}")
            raise # Re-raise to stop game initialization

        # Load EditionConfig
        try:
            self.edition_cfg = self._load_yaml_config(self.game_config.game_settings.edition_config_path, EditionConfig)
        except (ConfigNotFoundError, ConfigParseError, ConfigValidationError) as e:
            self.game_logger.critical(f"Critical configuration error for edition config: {e}")
            raise # Re-raise to stop game initialization

        self.game_logger.info("Merging theme and edition configurations...")

        # Start with core actions if present
        if self.core_cfg and self.core_cfg.actions:
            self.game_actions.update(self.core_cfg.actions)
            self.game_logger.info(f"Merged {len(self.core_cfg.actions)} core actions.")

        # 1. Merge Object Types (Theme takes precedence, Edition can add)
        if self.theme_cfg:
            self.game_object_types.update(self.theme_cfg.object_types)

        if self.edition_cfg and self.edition_cfg.objects:
            # The edition defines ObjectInstanceConfig, not ObjectTypeConfig. 
            # This means the edition provides *instances* of objects, not new *types*.
            # The merging logic here needs to be revised if the edition is meant to define new object types.
            # For now, we will assume edition objects are instances and handled during world instantiation.
            pass # Object instances are handled in _instantiate_rooms_and_objects

        # 2. Merge Actions (Theme actions override core, Edition actions override theme)
        if self.theme_cfg and self.theme_cfg.actions:
            self.game_actions.update(self.theme_cfg.actions)
            self.game_logger.info(f"Merged {len(self.theme_cfg.actions)} theme actions.")

        # Edition can override/add actions
        # This block is incorrect as EditionConfig does not have an 'actions' attribute.
        # if self.edition_cfg and self.edition_cfg.actions: # Assuming edition can define actions now
        #     self.game_actions.update(self.edition_cfg.actions)
        #     self.game_logger.info(f"Merged {len(self.edition_cfg.actions)} edition actions.")

        # 3. Merge Character Types (Theme takes precedence, Edition can add)
        if self.theme_cfg and self.theme_cfg.character_types:
            self.game_character_types.update(self.theme_cfg.character_types)

        if self.edition_cfg and self.edition_cfg.characters:
            self.game_character_types.update(self.edition_cfg.characters)

        self.game_logger.info(f"Merged {len(self.game_object_types)} object types.")
        self.game_logger.info(f"Merged {len(self.game_actions)} actions.")
        self.game_logger.info(f"Merged {len(self.game_character_types)} character types.")

    def _load_yaml_config(self, file_path: str, config_model: BaseModel) -> BaseModel:
        """Loads and validates a YAML configuration file against a Pydantic model."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
            
            validated_config = config_model(**raw_config)
            self.game_logger.info(f"Successfully loaded and validated {file_path} as {config_model.__name__}")
            return validated_config
        except FileNotFoundError:
            self.game_logger.error(f"Configuration file not found: {file_path}")
            raise ConfigNotFoundError(f"Configuration file not found: {file_path}")
        except yaml.YAMLError as e:
            self.game_logger.error(f"Error parsing YAML file {file_path}: {e}")
            raise ConfigParseError(f"Error parsing YAML file {file_path}: {e}")
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
        self.game_logger.info("Instantiating rooms and objects...")
        for room_id, room_cfg in self.edition_cfg.rooms.items():
            room = Room(
                room_id=room_cfg.id,
                name=room_cfg.name,
                description=room_cfg.description,
                exits={exit_id: exit_cfg.model_dump() for exit_id, exit_cfg in room_cfg.exits.items()},
                tags=room_cfg.tags,
                properties=room_cfg.properties
            )
            self.rooms[room_id] = room
            self.game_logger.info(f"  - Created room: {room.name} ({room.id})")

            # Place objects defined within the room config
            if room_cfg.objects: # Corrected from objects_in_room
                for obj_id, obj_instance_cfg in room_cfg.objects.items(): # Corrected from objects_in_room
                    obj_type = self.game_object_types.get(obj_instance_cfg.object_type_id)
                    if obj_type:
                        final_tags = set(obj_type.tags).union(obj_instance_cfg.tags)
                        final_properties = {**obj_type.properties, **obj_instance_cfg.properties}

                        game_obj = GameObject(
                            obj_id=obj_instance_cfg.id,
                            name=obj_instance_cfg.name or obj_type.name,
                            description=obj_instance_cfg.description or obj_type.description,
                            current_location_id=room.id,
                            tags=list(final_tags),
                            properties=final_properties
                        )
                        room.add_object(game_obj)
                        self.game_objects[game_obj.id] = game_obj
                        self.game_logger.info(f"    - Placed object {game_obj.name} ({game_obj.id}) in {room.name}")
                    else:
                        self.game_logger.warning(f"Object type '{obj_instance_cfg.object_type_id}' not found for object '{obj_instance_cfg.id}' in room '{room.id}'. Skipping.")

    def _instantiate_player_characters(self, players: List[Player]):
        self.game_logger.info("Instantiating player characters and assigning to players...")
        # Use the merged game_character_types, not directly edition_cfg.characters
        available_character_type_ids = list(self.game_character_types.keys())
        if not available_character_type_ids:
            self.game_logger.error("No character types defined in merged configuration. Cannot assign characters to players.")
            return
        
        # Find a suitable starting room (e.g., the first room defined in the edition)
        start_room_id = next(iter(self.edition_cfg.rooms.keys()), None)
        if not start_room_id:
            self.game_logger.error(f"No rooms defined in edition configuration. Cannot assign starting room for players.")
            return

        for i, player in enumerate(players):
            char_type_id_to_assign = available_character_type_ids[i % len(available_character_type_ids)]
            char_cfg = self.game_character_types[char_type_id_to_assign] # Use merged config
            
            # For now, motive is directly from character config. Will be updated for GM-9.
            player_char = PlayerCharacter(
                char_id=f"{char_cfg.id}_instance_{i}", # Make character instance ID unique
                name=char_cfg.name,
                backstory=char_cfg.backstory,
                motive=char_cfg.motive,
                current_room_id=start_room_id,
                action_points=self.initial_ap_per_turn # Use configurable initial AP
            )
            player.character = player_char # Link player to character
            self.player_characters[player_char.id] = player_char
            self.rooms[start_room_id].add_player(player_char) # Add player to the room
            self.game_logger.info(f"  - Assigned {player_char.name} ({player_char.id}) to player {player.name} in room {start_room_id}.")
