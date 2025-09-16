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
    def __init__(self, game_config: GameConfig, game_id: str, game_logger: logging.Logger, initial_ap_per_turn: int = 20, deterministic: bool = False, character_override: str = None, motive_override: str = None):
        self.game_config = game_config # This is the overall GameConfig loaded from config.yaml
        self.game_id = game_id
        self.game_logger = game_logger
        self.initial_ap_per_turn = initial_ap_per_turn # Store initial AP per turn
        self.deterministic = deterministic # Store deterministic flag
        self.character_override = character_override # Store character override for first player
        self.motive_override = motive_override # Store motive override for character assignment

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
            raw_config = self.game_config.model_dump()
        elif hasattr(self.game_config, '__dict__'):
            raw_config = self.game_config.__dict__
        else:
            # If it's already a dictionary, use it directly
            raw_config = self.game_config
        
        # Extract actions from merged config
        if 'actions' in raw_config and raw_config['actions']:
            self.game_actions.update(raw_config['actions'])
        
        # Extract object types from merged config
        if 'object_types' in raw_config and raw_config['object_types']:
            self.game_object_types.update(raw_config['object_types'])
        
        # Extract character types from merged config
        if 'character_types' in raw_config and raw_config['character_types']:
            self.game_character_types.update(raw_config['character_types'])
        
        # Extract characters from merged config
        if 'characters' in raw_config and raw_config['characters']:
            self.game_characters.update(raw_config['characters'])
        
        # Extract rooms from merged config
        if 'rooms' in raw_config and raw_config['rooms']:
            self.game_rooms = raw_config['rooms']
        else:
            # Initialize empty rooms if none defined
            self.game_rooms = {}
            self.game_logger.warning("No rooms defined in config.")
        
        self.game_logger.info(f"📊 Configuration Summary: {len(self.game_object_types)} object types, {len(self.game_actions)} actions, {len(self.game_character_types)} character types, {len(self.game_characters)} characters, {len(self.game_rooms)} rooms.")

    def _load_configurations_silent(self, init_data):
        """Loads configurations silently, collecting data for consolidated reporting."""
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
        
        # Extract object types from merged config
        if 'object_types' in raw_config and raw_config['object_types']:
            self.game_object_types.update(raw_config['object_types'])
        
        # Extract character types from merged config
        if 'character_types' in raw_config and raw_config['character_types']:
            self.game_character_types.update(raw_config['character_types'])
        
        # Extract characters from merged config
        if 'characters' in raw_config and raw_config['characters']:
            self.game_characters.update(raw_config['characters'])
        
        # Extract rooms from merged config
        if 'rooms' in raw_config and raw_config['rooms']:
            self.game_rooms = raw_config['rooms']
        else:
            # Initialize empty rooms if none defined
            self.game_rooms = {}
            init_data['warnings'].append("No rooms defined in config.")
        
        init_data['config_loaded'] = True

    def _instantiate_rooms_and_objects_silent(self, init_data):
        """Instantiates rooms and objects silently, collecting data for consolidated reporting."""
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
            init_data['rooms_created'] += 1

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

        # Randomly assign characters to players (no duplicates)
        import random
        if not self.deterministic:
            # Random assignment in normal mode
            char_assignments = random.sample(available_character_ids, len(players))
        else:
            # Deterministic assignment (first N characters in order)
            char_assignments = available_character_ids[:len(players)]

        for i, player in enumerate(players):
            # Apply character override for first player if specified
            if i == 0 and self.character_override:
                if self.character_override in available_character_ids:
                    char_id_to_assign = self.character_override
                    self.game_logger.info(f"Assigned override character '{self.character_override}' to Player_1")
                else:
                    self.game_logger.warning(f"Character override '{self.character_override}' not found in available characters. Available: {available_character_ids}")
                    char_id_to_assign = char_assignments[i]
            else:
                char_id_to_assign = char_assignments[i]
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
                
                # Handle motive override
                if self.motive_override:
                    # Find the specified motive
                    selected_motive = None
                    for motive in converted_motives:
                        if motive.id == self.motive_override:
                            selected_motive = motive
                            break
                    
                    if selected_motive:
                        self.game_logger.info(f"Assigned override motive '{self.motive_override}' to character '{char_name}'")
                    else:
                        self.game_logger.warning(f"Motive override '{self.motive_override}' not found in available motives for character '{char_name}'. Available: {[m.id for m in converted_motives]}")
                        self.motive_override = None
            elif self.motive_override:
                # Character has no motives but motive override was requested
                self.game_logger.warning(f"Motive override '{self.motive_override}' requested but character '{char_name}' has no motives defined")
                self.motive_override = None

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
                deterministic=self.deterministic  # Pass deterministic flag
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
        
        if not available_character_ids:
            self.game_logger.error("No characters defined in merged configuration. Cannot assign characters to players.")
            return
        
        # Check if we have enough characters for all players
        if len(players) > len(available_character_ids):
            self.game_logger.error(f"Not enough characters for all players. Need {len(players)} characters but only have {len(available_character_ids)} available.")
            return
        
        # Find a suitable starting room (e.g., the first room defined in the merged config)
        default_start_room_id = next(iter(self.game_rooms.keys()), None)
        if not default_start_room_id:
            self.game_logger.error("No rooms defined in merged configuration. Cannot assign starting room for players.")
            return

        # Handle character assignment with override support
        import random
        
        # Check if character override is valid
        if self.character_override and self.character_override not in available_character_ids:
            self.game_logger.warning(f"Character override '{self.character_override}' not found in available characters. Available: {available_character_ids}")
            self.character_override = None
        
        # Assign characters to players
        char_assignments = []
        remaining_characters = available_character_ids.copy()
        
        # First player gets the override character if specified
        if self.character_override and len(players) > 0:
            char_assignments.append(self.character_override)
            remaining_characters.remove(self.character_override)
            self.game_logger.info(f"Assigned override character '{self.character_override}' to first player")
        
        # Assign remaining characters to remaining players
        remaining_players = len(players) - len(char_assignments)
        if remaining_players > 0:
            if not self.deterministic:
                # Random assignment for remaining characters
                remaining_assignments = random.sample(remaining_characters, remaining_players)
            else:
                # Deterministic assignment (first N characters in order)
                remaining_assignments = remaining_characters[:remaining_players]
            char_assignments.extend(remaining_assignments)

        for i, player in enumerate(players):
            char_id_to_assign = char_assignments[i]
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
                
                # Handle motive override
                if self.motive_override:
                    # Find the specified motive
                    selected_motive = None
                    for motive in converted_motives:
                        if motive.id == self.motive_override:
                            selected_motive = motive
                            break
                    
                    if selected_motive:
                        self.game_logger.info(f"Assigned override motive '{self.motive_override}' to character '{char_name}'")
                    else:
                        self.game_logger.warning(f"Motive override '{self.motive_override}' not found in available motives for character '{char_name}'. Available: {[m.id for m in converted_motives]}")
                        self.motive_override = None
            elif self.motive_override:
                # Character has no motives but motive override was requested
                self.game_logger.warning(f"Motive override '{self.motive_override}' requested but character '{char_name}' has no motives defined")
                self.motive_override = None

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
                deterministic=self.deterministic  # Pass deterministic flag
            )
            
            # Store the initial room reason for use in initial turn message
            player_char.initial_room_reason = initial_room_reason
            
            player.character = player_char # Link player to character
            self.player_characters[player_char.id] = player_char
            self.rooms[selected_room_id].add_player(player_char) # Add player to the room
            self.game_logger.info(f"Assigned {player_char.name} to {player.name}")
