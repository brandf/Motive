import random
import time
import asyncio
import os
import logging
import sys # Added for stdout logging
import yaml # Added for YAML loading
from typing import List, Dict, Any, Optional, Tuple # Added for type hints
from pydantic import BaseModel, ValidationError # Added for Pydantic validation
from motive.player import Player
from motive.character import Character
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from motive.config import (
    GameConfig,
    PlayerConfig,
    ThemeConfig,
    EditionConfig,
    ObjectTypeConfig, # Re-added for direct usage
    ActionConfig, # Re-added for direct usage
    ActionRequirementConfig,
    ActionEffectConfig,
    RoomConfig,
    ExitConfig,
    ObjectInstanceConfig,
    CharacterConfig, # Re-added for direct usage
    Event # Added for event handling
)
from motive.game_object import GameObject # Import GameObject
from motive.room import Room # Import Room
from motive.action_parser import parse_player_response # Import the new action parser
from motive.exceptions import ConfigNotFoundError, ConfigParseError, ConfigValidationError # Import custom exceptions
from motive.game_initializer import GameInitializer # Import GameInitializer
from datetime import datetime # Added for datetime logging
import uuid # Added for UUID logging


class GameMaster:
    # Accept a pre-validated GameConfig object directly
    def __init__(self, game_config: GameConfig, game_id: str, deterministic: bool = False):
        self.players = []
        
        # Resolve manual path relative to the configs directory (where game.yaml is located)
        import os
        configs_dir = os.path.dirname(os.path.abspath("configs/game.yaml"))
        
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(game_config, 'game_settings'):
            # Pydantic object
            self.num_rounds = game_config.game_settings.num_rounds
            self.manual_path = os.path.join(configs_dir, game_config.game_settings.manual)
        else:
            # Dictionary from merged config
            self.num_rounds = game_config['game_settings']['num_rounds']
            self.manual_path = os.path.join(configs_dir, game_config['game_settings']['manual'])
            
        self.game_id = game_id
        self.deterministic = deterministic

        self.game_config = game_config # Assign game_config earlier

        # Initialize theme and edition with temporary placeholders
        # These will be updated after configurations are loaded
        self.theme: str = ""
        self.edition: str = ""
        
        # Track which hints have been executed (hint_id -> set of player_names)
        self.executed_hints: Dict[str, set] = {}

        # Initialize a basic logger that logs to stdout before full setup
        self.game_logger = logging.getLogger("GameNarrative")
        self.game_logger.propagate = False # Prevent propagation to root logger to avoid duplicate output
        if not self.game_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.game_logger.addHandler(handler)
            self.game_logger.setLevel(logging.INFO)

        # Initialize GameInitializer with the basic logger
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(game_config, 'game_settings'):
            initial_ap = game_config.game_settings.initial_ap_per_turn
        else:
            initial_ap = game_config['game_settings']['initial_ap_per_turn']
        self.game_initializer = GameInitializer(game_config, game_id, self.game_logger, initial_ap, self.deterministic)

        # Load configurations from merged config
        self.game_initializer._load_configurations()
        
        # Extract theme and edition IDs from merged config
        if hasattr(game_config, 'theme_id') and game_config.theme_id:
            self.theme = game_config.theme_id
        elif 'theme_id' in game_config and game_config['theme_id']:
            self.theme = game_config['theme_id']
        else:
            self.theme = "unknown"
            
        if hasattr(game_config, 'edition_id') and game_config.edition_id:
            self.edition = game_config.edition_id
        elif 'edition_id' in game_config and game_config['edition_id']:
            self.edition = game_config['edition_id']
        else:
            self.edition = "unknown"

        # Now that theme and edition are known, set up the full logging
        self.log_dir = self._setup_logging()
        # Update the game initializer with the fully configured logger
        self.game_initializer.game_logger = self.game_logger

        self.manual_content = self._load_manual_content()

        # Configs are already merged in game_config via hierarchical loading
        # self.game_config = game_config # Store the full game config # Moved to earlier

        # Initialize game state collections - these will be populated by GameInitializer
        self.rooms: Dict[str, Room] = {}
        self.game_objects: Dict[str, GameObject] = {}
        self.player_characters: Dict[str, Character] = {}

        self.player_first_interaction_done: Dict[str, bool] = {} # Track if a player has had their first interaction

        # These will store the merged configurations
        self.game_object_types: Dict[str, ObjectTypeConfig] = {}
        self.game_actions: Dict[str, ActionConfig] = {}
        self.game_character_types: Dict[str, CharacterConfig] = {}

        # Event management
        self.event_queue: List[Event] = [] # All events generated during a turn
        self.player_observations: Dict[str, List[Event]] = {} # Events specific to each player

        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(game_config, 'players'):
            self._initialize_players(game_config.players)
        else:
            self._initialize_players(game_config['players'])
        
        # Now, use the initializer to set up the game world
        self.game_initializer.initialize_game_world(self.players)
        # Copy the initialized state from the initializer to GameMaster
        self.rooms = self.game_initializer.rooms
        self.game_objects = self.game_initializer.game_objects
        self.player_characters = self.game_initializer.player_characters
        self.game_object_types = self.game_initializer.game_object_types
        self.game_actions = self.game_initializer.game_actions
        self.game_character_types = self.game_initializer.game_character_types

        # Pass initial AP to GameInitializer for character instantiation
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(game_config, 'game_settings'):
            self.game_initializer.initial_ap_per_turn = game_config.game_settings.initial_ap_per_turn
        else:
            self.game_initializer.initial_ap_per_turn = game_config['game_settings']['initial_ap_per_turn']

        # Initialize player_observations for all players
        for player in self.players:
            if player.character:
                self.player_observations[player.character.id] = []
            else:
                self.game_logger.warning(f"Player {player.name} has no character, cannot initialize observation queue.")

        # Link PlayerCharacter instances to the actual Player objects
        # This section is no longer needed as GameInitializer already links PlayerCharacter to Player
        # for player in self.players:
        #     found_char = None
        #     for char_id, char_instance in self.player_characters.items():
        #         if char_instance.name == player.name:
        #             found_char = char_instance
        #             break
        #     if found_char:
        #         player.character = found_char
        #     else:
        #         self.game_logger.warning(f"Could not find PlayerCharacter for player {player.name}. Character not assigned.")

    def _load_manual_content(self) -> str:
        """Loads the content of the game manual from the specified path."""
        try:
            with open(self.manual_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.game_logger.info(f"Loaded game manual from {self.manual_path}")
            return content
        except FileNotFoundError:
            self.game_logger.error(f"Game manual file not found: {self.manual_path}")
            return ""
        except Exception as e:
            self.game_logger.error(f"Error loading game manual from {self.manual_path}: {e}")
            return ""

    def _setup_logging(self):
        """Sets up the logging directory and configures the GM logger."""
        import os
        disable_file_logging = os.environ.get("MOTIVE_DISABLE_FILE_LOGGING") == "1"
        base_log_dir = os.environ.get("MOTIVE_LOG_DIR", "logs")
        # Use game_id directly for folder name (should be sortable if game_id includes timestamp)
        game_log_dir = os.path.join(base_log_dir, self.theme, self.edition, self.game_id)
        if not disable_file_logging:
            os.makedirs(game_log_dir, exist_ok=True)

        # Remove all existing handlers from the logger before reconfiguring
        for handler in list(self.game_logger.handlers):
            self.game_logger.removeHandler(handler)

        # Set the level for the game logger (now that it's the main logger)
        self.game_logger.setLevel(logging.INFO)

        # File handler for game.log (skip in tests when disabled)
        log_targets = ["stdout"]
        if not disable_file_logging:
            game_narrative_file = os.path.join(game_log_dir, "game.log")
            game_file_handler = logging.FileHandler(game_narrative_file, encoding="utf-8")
            game_formatter = logging.Formatter('%(asctime)s - %(message)s') # Simpler format for narrative
            game_file_handler.setFormatter(game_formatter)
            self.game_logger.addHandler(game_file_handler)
            log_targets.insert(0, game_narrative_file)

        # Stream handler for stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_formatter = logging.Formatter('%(asctime)s - %(message)s')
        stdout_handler.setFormatter(stdout_formatter)
        self.game_logger.addHandler(stdout_handler)

        self.game_logger.info(f"Game narrative logging to {' and '.join(log_targets)}.")
        
        return game_log_dir

    def _initialize_players(self, player_configs: list[PlayerConfig]):
        """Initializes players based on the provided list of PlayerConfig objects."""
        for p_config in player_configs:
            player = Player(
                name=p_config.name,
                provider=p_config.provider,
                model=p_config.model,
                log_dir=self.log_dir  # Pass the log directory to the player
            )
            self.players.append(player)
            self.player_first_interaction_done[player.name] = False # Initialize for tracking

    async def run_game(self):
        """Main game loop."""
        self.game_logger.info("🚀 ==================== GAME STARTING ====================")
        
        # Log game settings for training data metadata
        if hasattr(self.game_config, 'game_settings'):
            self.game_logger.info(f"⚙️ Game Settings: {self.game_config.game_settings.num_rounds} rounds, {self.game_config.game_settings.initial_ap_per_turn} AP/turn")
        else:
            self.game_logger.info(f"⚙️ Game Settings: {self.game_config['game_settings']['num_rounds']} rounds, {self.game_config['game_settings']['initial_ap_per_turn']} AP/turn")

        # Removed: await self._send_initial_messages()

        for round_num in range(1, self.num_rounds + 1):
            self.game_logger.info(f"🎯 Round {round_num} of {self.num_rounds}")
            
            # Log character snapshot report before each round
            self.game_logger.info(self._generate_character_snapshot_report())
            
            # Filter out players who have quit
            active_players = [player for player in self.players if player.character.action_points != -1]
            
            if not active_players:
                self.game_logger.info("No active players remaining. Game ending early.")
                break
                
            for player in active_players:
                # Handle both Pydantic objects and dictionaries from merged config
                if hasattr(self.game_config, 'game_settings'):
                    player.character.action_points = self.game_config.game_settings.initial_ap_per_turn
                else:
                    player.character.action_points = self.game_config['game_settings']['initial_ap_per_turn']
                await self._execute_player_turn(player, round_num)
                
                # Check if player quit during their turn
                if player.character.action_points == -1:
                    self.game_logger.info(f"Player {player.name} has quit the game.")
                    
            self.game_logger.info(f"✅ Round {round_num} complete")

        self.game_logger.info("🏁 ===================== GAME OVER ======================")
        
        # Check win conditions and provide game summary
        self._check_win_conditions_and_summarize()

    def _generate_character_snapshot_report(self) -> str:
        """Generate a snapshot report of all characters' locations and inventories."""
        report_lines = ["📊 Character Snapshot Report:"]
        
        for player in self.players:
            char = player.character
            player_name = player.name
            char_name = char.name
            
            # Get room name
            room_name = "Unknown"
            if char.current_room_id in self.rooms:
                room = self.rooms[char.current_room_id]
                if hasattr(room, 'name'):
                    room_name = room.name
                else:
                    room_name = f"Unknown ({char.current_room_id})"
            else:
                room_name = f"Unknown ({char.current_room_id})"
            
            # Get inventory
            if char.inventory:
                inventory_str = ", ".join(item.name for item in char.inventory.values())
            else:
                inventory_str = "(empty)"
            
            report_lines.append(f"  👤 {player_name} ({char_name})")
            report_lines.append(f"    • Location: {room_name}")
            report_lines.append(f"    • Inventory: {inventory_str}")
        
        return "\n".join(report_lines)

    def _check_win_conditions_and_summarize(self):
        """Checks if any players achieved their motives and provides a detailed game summary."""
        winners = []
        losers = []
        
        for player in self.players:
            if player.character.action_points == -1:  # Player quit
                losers.append(f"{player.name} (quit)")
                continue
            
            # Get detailed motive information
            char = player.character
            motive_name = char.selected_motive.id if char.selected_motive else "legacy_motive"
            motive_desc = char.motive
            
            # Check motive success/failure using the new system
            success_result = char.check_motive_success(self)
            failure_result = char.check_motive_failure(self)
            
            # Success requires BOTH success conditions AND no failure conditions (redemption logic)
            if success_result and not failure_result:
                winners.append(f"{player.name} ({char.name}) - Motive '{motive_name}': {motive_desc}")
            elif failure_result:
                losers.append(f"{player.name} ({char.name}) - Motive '{motive_name}' FAILED: {motive_desc}")
            else:
                # Neither success nor failure conditions met - player didn't achieve motive
                losers.append(f"{player.name} ({char.name}) - Motive '{motive_name}' NOT ACHIEVED: {motive_desc}")
        
        # Log and display results with human-readable formatting
        self.game_logger.info("=" * 60)
        self.game_logger.info("🏆 GAME RESULTS")
        self.game_logger.info("=" * 60)
        
        if winners:
            self.game_logger.info("✅ WINNERS:")
            for winner in winners:
                self.game_logger.info(f"   🎉 {winner}")
        else:
            self.game_logger.info("❌ No players achieved their motives.")
        
        if losers:
            self.game_logger.info("\n❌ LOSERS:")
            for loser in losers:
                self.game_logger.info(f"   💔 {loser}")
        
        # Enhanced human-readable game summary
        self.game_logger.info("\n" + "=" * 60)
        self.game_logger.info("📊 GAME SUMMARY")
        self.game_logger.info("=" * 60)
        self.game_logger.info(f"👥 Total Players: {len(self.players)}")
        self.game_logger.info(f"🏆 Winners: {len(winners)}")
        self.game_logger.info(f"💔 Losers: {len(losers)}")
        self.game_logger.info("=" * 60)
        
        # Detailed motive condition trees for all players
        self.game_logger.info("\n" + "=" * 60)
        self.game_logger.info("🌳 DETAILED MOTIVE CONDITION TREES")
        self.game_logger.info("=" * 60)
        
        for player in self.players:
            if player.character.action_points == -1:  # Player quit
                continue
            
            char = player.character
            condition_tree = char.get_motive_condition_tree(self)
            self.game_logger.info(f"\n👤 {player.name} ({char.name}):")
            self.game_logger.info(condition_tree)
            self.game_logger.info("-" * 40)
        
        self.game_logger.info("=" * 60)

    def _check_requirements(self, player_char: Character, action_config: ActionConfig, params: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Checks if all requirements for an action are met."""
        current_room = self.rooms.get(player_char.current_room_id)
        if not current_room:
            return False, f"Character is in an unknown room: {player_char.current_room_id}.", None

        found_exit_data: Optional[Dict[str, Any]] = None # To store exit data if found

        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(action_config, 'requirements'):
            requirements = action_config.requirements
        else:
            requirements = action_config.get('requirements', [])
        
        for req in requirements:
            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(req, 'type'):
                req_type = req.type
            else:
                req_type = req.get('type', '')
                
            if req_type == "player_has_tag":
                tag = req.tag if hasattr(req, 'tag') else req.get('tag', '')
                if not player_char.has_tag(tag):
                    return False, f"Player does not have tag '{tag}'.", None
            elif req_type == "object_in_room":
                object_name_param = req.object_name_param if hasattr(req, 'object_name_param') else req.get('object_name_param', 'object_name')
                object_name = params.get(object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{object_name_param}' for object_in_room requirement.", None
                
                obj_found = False
                for obj in current_room.objects.values():
                    if obj.name.lower() == object_name.lower():
                        obj_found = True
                        break
                if not obj_found:
                    return False, f"Object '{object_name}' not in room.", None
            elif req_type == "object_in_inventory":
                object_name_param = req.object_name_param if hasattr(req, 'object_name_param') else req.get('object_name_param', 'object_name')
                object_name = params.get(object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{object_name_param}' for object_in_inventory requirement.", None
                
                obj_found = False
                for obj in player_char.inventory.values():
                    if obj.name.lower() == object_name.lower():
                        obj_found = True
                        break
                if not obj_found:
                    return False, f"Object '{object_name}' not in inventory.", None
            elif req_type == "object_possession_allowed":
                object_name_param = req.object_name_param if hasattr(req, 'object_name_param') else req.get('object_name_param', 'object_name')
                object_name = params.get(object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{object_name_param}' for object_possession_allowed requirement.", None
                
                # Find the object in the room
                target_object = None
                for obj in current_room.objects.values():
                    if obj.name.lower() == object_name.lower():
                        target_object = obj
                        break
                
                if not target_object:
                    return False, f"Object '{object_name}' not found for pickup check.", None
                
                # Check if object has pickup constraints
                if "immovable" in target_object.tags:
                    return False, f"Cannot pick up '{object_name}' - it is immovable.", None
                
                # Add other pickup constraints here (e.g., too_heavy, magically_bound, etc.)
                if "too_heavy" in target_object.tags:
                    return False, f"Cannot pick up '{object_name}' - it is too heavy.", None
                
                if "magically_bound" in target_object.tags:
                    return False, f"Cannot pick up '{object_name}' - it is magically bound to this location.", None
                
            elif req_type == "object_property_equals":
                object_name_param = req.object_name_param if hasattr(req, 'object_name_param') else req.get('object_name_param', 'object_name')
                object_name = params.get(object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{object_name_param}' for object_property_equals requirement.", None
                
                obj_found = player_char.get_item_in_inventory(object_name) # Check inventory first
                if not obj_found:
                    # Then check if it's in the current room
                    obj_found = current_room.get_object(object_name)

                if not obj_found:
                    return False, f"Object '{object_name}' not found for property check.", None
                
                property_name = req.property if hasattr(req, 'property') else req.get('property', '')
                property_value = req.value if hasattr(req, 'value') else req.get('value', '')
                if obj_found.get_property(property_name) != property_value:
                    return False, f"Object '{object_name}' property '{property_name}' is not '{property_value}'.", None
            elif req_type == "player_has_object_in_inventory":
                object_name_param = req.object_name_param if hasattr(req, 'object_name_param') else req.get('object_name_param', 'object_name')
                object_name = params.get(object_name_param)
                if object_name is None:
                    return False, f"Missing parameter '{object_name_param}' for player_has_object_in_inventory requirement.", None
                
                if not player_char.has_item_in_inventory(object_name):
                    return False, f"Player does not have '{object_name}' in inventory.", None
            elif req_type == "exit_exists":
                direction_param = req.direction_param if hasattr(req, 'direction_param') else req.get('direction_param', 'direction')
                direction = params.get(direction_param)
                if not direction:
                    return False, f"Missing parameter '{direction_param}' for exit_exists requirement.", None
                
                found_exit = None
                for exit_id, exit_data in current_room.exits.items():
                    if exit_data.get('is_hidden', False):
                        continue
                        
                    # Check if direction matches the exit name
                    if exit_data['name'].lower() == direction.lower():
                        found_exit = exit_data
                        break
                        
                    # Check if direction matches any of the exit aliases
                    aliases = exit_data.get('aliases', [])
                    if any(alias.lower() == direction.lower() for alias in aliases):
                        found_exit = exit_data
                        break

                if not found_exit:
                    return False, f"No visible exit in the '{direction}' direction.", None
                found_exit_data = found_exit # Store for returning
            elif req_type == "player_in_room":
                target_player_param = req.target_player_param if hasattr(req, 'target_player_param') else req.get('target_player_param', 'player')
                player_name = params.get(target_player_param)
                if not player_name:
                    return False, f"Missing parameter '{target_player_param}' for player_in_room requirement.", None
                
                # Check if the target player is in the same room
                target_player = None
                for player in self.players:
                    if hasattr(player, 'character') and player.character:
                        if player.character.name.lower() == player_name.lower():
                            target_player = player.character
                            break
                
                if not target_player:
                    return False, f"Player '{player_name}' not found.", None
                
                if target_player.current_room_id != player_char.current_room_id:
                    return False, f"Player '{player_name}' is not in the same room.", None
            # Add other requirement types here
            else:
                self.game_logger.warning(f"Unsupported requirement type: {req.type}")
                return False, f"Unsupported requirement type: {req.type}", None
        
        return True, "", found_exit_data

    def _execute_effects(self, player_char: Character, action_config: ActionConfig, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
        """Applies the effects of an action to the game state and generates feedback/events."""
        feedback_messages: List[str] = []
        events_generated: List[Event] = [] # Changed to list of Event objects

        current_room = self.rooms.get(player_char.current_room_id)
        if not current_room:
            feedback_messages.append(f"Error: Character is in an unknown room: {player_char.current_room_id}.")
            return [], feedback_messages

        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(action_config, 'effects'):
            effects = action_config.effects
        else:
            effects = action_config.get('effects', [])
        
        for effect in effects:
            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(effect, 'target_id_param'):
                target_id_param = effect.target_id_param
            else:
                target_id_param = effect.get('target_id_param', None)
                
            if hasattr(effect, 'target_id'):
                target_id = effect.target_id
            else:
                target_id = effect.get('target_id', None)
                
            if hasattr(effect, 'target_type'):
                target_type = effect.target_type
            else:
                target_type = effect.get('target_type', 'player')
                
            target_instance = None
            target_id_from_param = params.get(target_id_param) if target_id_param else None
            target_id = target_id or target_id_from_param

            if target_type == "player":
                # For player target, the instance is always the current player_char
                target_instance = player_char
            elif target_type == "room":
                if target_id:
                    target_instance = self.rooms.get(target_id)
                elif player_char.current_room_id: # Default to current room if target_id not specified
                    target_instance = self.rooms.get(player_char.current_room_id)
            elif target_type == "object":
                if target_id:
                    # Check player inventory first
                    target_instance = player_char.get_item_in_inventory(target_id)
                    if not target_instance:
                        # Then check current room
                        current_room = self.rooms.get(player_char.current_room_id)
                        if current_room:
                            target_instance = current_room.get_object(target_id)
            
            # Execute effects based on type
            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(effect, 'type'):
                effect_type = effect.type
            else:
                effect_type = effect.get('type', '')
                
            if hasattr(effect, 'tag'):
                effect_tag = effect.tag
            else:
                effect_tag = effect.get('tag', '')
                
            if hasattr(effect, 'target_type'):
                effect_target_type = effect.target_type
            else:
                effect_target_type = effect.get('target_type', 'player')
                
            if effect_type == "add_tag":
                if target_instance and effect_tag:
                    target_instance.add_tag(effect_tag)
                    feedback_messages.append(f"The {effect_target_type} '{target_instance.name}' gains the tag: '{effect_tag}'.")
                else:
                    # Handle both Pydantic objects and dictionaries from merged config
                    if hasattr(action_config, 'name'):
                        action_name = action_config.name
                    else:
                        action_name = action_config.get('name', 'unknown')
                    self.game_logger.warning(f"add_tag effect missing target or tag for action '{action_name}'.")

            elif effect_type == "remove_tag":
                if target_instance and effect_tag:
                    target_instance.remove_tag(effect_tag)
                    feedback_messages.append(f"The {effect_target_type} '{target_instance.name}' loses the tag: '{effect_tag}'.")
                else:
                    # Handle both Pydantic objects and dictionaries from merged config
                    if hasattr(action_config, 'name'):
                        action_name = action_config.name
                    else:
                        action_name = action_config.get('name', 'unknown')
                    self.game_logger.warning(f"remove_tag effect missing target or tag for action '{action_name}'.")

            elif effect_type == "set_property":
                # Handle both Pydantic objects and dictionaries from merged config
                if hasattr(effect, 'property'):
                    effect_property = effect.property
                else:
                    effect_property = effect.get('property', '')
                    
                if hasattr(effect, 'value'):
                    effect_value = effect.value
                else:
                    effect_value = effect.get('value', None)
                    
                if target_instance and effect_property and effect_value is not None:
                    target_instance.set_property(effect_property, effect_value)
                    feedback_messages.append(f"The {effect_target_type} '{target_instance.name}'s '{effect_property}' is now '{effect_value}'.")
                else:
                    # Handle both Pydantic objects and dictionaries from merged config
                    if hasattr(action_config, 'name'):
                        action_name = action_config.name
                    else:
                        action_name = action_config.get('name', 'unknown')
                    self.game_logger.warning(f"set_property effect missing target, property, or value for action '{action_name}'.")

            elif effect_type == "generate_event":
                # Handle both Pydantic objects and dictionaries from merged config
                if hasattr(effect, 'message'):
                    effect_message = effect.message
                else:
                    effect_message = effect.get('message', '')
                    
                if hasattr(effect, 'observers'):
                    effect_observers = effect.observers
                else:
                    effect_observers = effect.get('observers', [])
                    
                if effect_message and effect_observers:
                    event_message = effect_message.format(**params, player_name=player_char.name) # Add player_name to params for formatting
                    events_generated.append(Event(
                        message=event_message,
                        event_type="action_event", # A generic type for now
                        source_room_id=player_char.current_room_id,
                        timestamp=datetime.now().isoformat(),
                        related_player_id=player_char.id,
                        observers=effect_observers
                    ))
                    feedback_messages.append(event_message) # Player sees their own immediate events

            elif effect_type == "code_binding":
                # Handle both Pydantic objects and dictionaries from merged config
                if hasattr(effect, 'function_name'):
                    effect_function_name = effect.function_name
                else:
                    effect_function_name = effect.get('function_name', '')
                    
                if effect_function_name:
                    try:
                        # Use convention-based import: assume core_hooks for now
                        # TODO: Make this more flexible for different hook modules
                        import motive.hooks.core_hooks as core_hooks
                        hook_function = getattr(core_hooks, effect_function_name)
                        
                        hook_events_and_feedback = hook_function(self, player_char, action_config, params) # Expecting a tuple: (List[Event], List[str])
                        hook_events = hook_events_and_feedback[0]
                        hook_feedback = hook_events_and_feedback[1]
                        
                        feedback_messages.extend(hook_feedback)
                        events_generated.extend(hook_events) # Extend with actual Event objects

                    except (ImportError, AttributeError, KeyError, IndexError) as e: # Added KeyError for globals lookup
                        # Handle both Pydantic objects and dictionaries from merged config
                        if hasattr(action_config, 'name'):
                            action_name = action_config.name
                        else:
                            action_name = action_config.get('name', 'unknown')
                        error_message = f"Error calling code binding for action '{action_name}': {e}"
                        self.game_logger.error(error_message)
                        feedback_messages.append(f"An error occurred while trying to process your action: {e}")
                    except Exception as e:
                        # Handle both Pydantic objects and dictionaries from merged config
                        if hasattr(action_config, 'name'):
                            action_name = action_config.name
                        else:
                            action_name = action_config.get('name', 'unknown')
                        error_message = f"An unexpected error occurred in code binding for action '{action_name}': {e}"
                        self.game_logger.error(error_message)
                        feedback_messages.append(f"An unexpected error occurred: {e}")
                else:
                    # Handle both Pydantic objects and dictionaries from merged config
                    if hasattr(action_config, 'name'):
                        action_name = action_config.name
                    else:
                        action_name = action_config.get('name', 'unknown')
                    self.game_logger.warning(f"code_binding effect for '{action_name}' missing function_name.")
                    feedback_messages.append(f"An error occurred due to missing code binding configuration.")

            else:
                self.game_logger.warning(f"Unsupported effect type: {effect.type}")

        # After processing all effects, add generated events to the main event queue
        return events_generated, feedback_messages

    def _calculate_action_cost(self, player_char: Character, action_config: Any, params: Dict[str, Any]) -> int:
        """Calculate the actual cost for an action, using cost calculation function if available."""
        # Handle new cost configuration format
        if hasattr(action_config, 'cost') and isinstance(action_config.cost, dict):
            cost_config = action_config.cost
            if cost_config.get('type') == 'code_binding':
                function_name = cost_config.get('function_name')
                if function_name == "calculate_help_cost":
                    from motive.hooks.core_hooks import calculate_help_cost
                    return calculate_help_cost(self, player_char, action_config, params)
                # Add more cost calculation functions here as needed
            elif cost_config.get('type') == 'static':
                return cost_config.get('value', 0)
        
        # Handle CostConfig object (from Pydantic model)
        if hasattr(action_config, 'cost') and hasattr(action_config.cost, 'type'):
            if action_config.cost.type == 'code_binding':
                function_name = action_config.cost.function_name
                if function_name == "calculate_help_cost":
                    from motive.hooks.core_hooks import calculate_help_cost
                    return calculate_help_cost(self, player_char, action_config, params)
                # Add more cost calculation functions here as needed
            elif action_config.cost.type == 'static':
                return action_config.cost.value or 0
        
        # Default to static cost from config (backward compatibility for int)                                                             
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(action_config, 'cost'):
            cost_raw = action_config.cost
        else:
            cost_raw = action_config.get('cost', 0)
        
        # Handle cost as either integer or dictionary
        if isinstance(cost_raw, dict):
            return cost_raw.get('value', 0)  # Extract value from CostConfig dict
        else:
            return cost_raw

    def _distribute_events(self):
        """Distributes generated events to relevant players based on observer scopes."""
        if not self.event_queue:
            return  # No events to distribute
            
        for event in self.event_queue:
            # Ensure current_room exists for event distribution logic
            event_room = self.rooms.get(event.source_room_id)
            if not event_room:
                self.game_logger.warning(f"Event originated from unknown room ID: {event.source_room_id}. Cannot distribute to room-based observers.")
                continue # Skip room-based distribution for this event

            # Iterate through all players to determine who observes the event
            for player in self.players:
                player_char = player.character
                if not player_char:
                    continue
                
                observes = False
                # Determine if the player should observe this event based on scopes
                if "all_players" in event.observers:
                    observes = True
                elif "player" in event.observers and event.related_player_id == player_char.id:
                    observes = True
                elif "room_players" in event.observers and player_char.current_room_id == event.source_room_id:
                    observes = True
                elif "adjacent_rooms" in event.observers:
                    # Check if player's current room is adjacent to event_room
                    for exit_data in event_room.exits.values():
                        if exit_data['destination_room_id'] == player_char.current_room_id:
                            observes = True
                            break
                # Add more observer types here as needed (e.g., target_player, target_object_owner)

                if observes and player_char.id in self.player_observations:
                    # Don't let players observe their own events - they already get feedback
                    if event.related_player_id != player_char.id:
                        self.player_observations[player_char.id].append(event)
        
        self.event_queue.clear() # Clear the queue after distributing all events

    def _get_event_observation_details(self, event) -> List[str]:
        """Generate detailed observation breakdown for an event showing which players observed it and why others didn't."""
        details = []
        
        # Get the room where the event occurred
        event_room = self.rooms.get(event.source_room_id)
        if not event_room:
            details.append("    ⚠️ Event room not found - cannot determine observers")
            return details
        
        # Get all players in the event room
        players_in_room = []
        players_outside_room = []
        
        for player in self.players:
            player_char = player.character
            if not player_char:
                continue
                
            if player_char.current_room_id == event.source_room_id:
                players_in_room.append(player)
            else:
                players_outside_room.append(player)
        
        # Show players in the room and their observation status
        if players_in_room:
            for player in players_in_room:
                player_char = player.character
                observes, reason = self._determine_observation_status(event, player_char)
                checkbox = "☑️" if observes else "☐"
                details.append(f"    {checkbox} {player.name} ({player_char.name}) - {reason}")
        
        # Show players outside the room
        if players_outside_room:
            for player in players_outside_room:
                player_char = player.character
                details.append(f"    ☐ {player.name} ({player_char.name}) - Not in event room")
        
        return details

    def _determine_observation_status(self, event, player_char) -> Tuple[bool, str]:
        """Determine if a player observes an event and why."""
        # Check if player is the event originator (they don't observe their own events)
        if event.related_player_id == player_char.id:
            return False, "Event originator (gets direct feedback instead)"
        
        # Check observer scopes
        if "all_players" in event.observers:
            return True, "All players observer"
        elif "player" in event.observers and event.related_player_id == player_char.id:
            return True, "Target player observer"
        elif "room_players" in event.observers and player_char.current_room_id == event.source_room_id:
            return True, "Room players observer"
        elif "adjacent_rooms" in event.observers:
            # Check if player's current room is adjacent to event_room
            event_room = self.rooms.get(event.source_room_id)
            if event_room:
                for exit_data in event_room.exits.values():
                    if exit_data['destination_room_id'] == player_char.current_room_id:
                        return True, "Adjacent room observer"
            return False, "Not in adjacent room"
        else:
            return False, "No matching observer scope"

    async def _execute_player_turn(self, player: Player, round_num: int):
        """Executes a single player's turn, allowing multiple actions until AP are spent or turn ends."""
        player_char = player.character
        if not player_char:
            self.game_logger.error(f"Player {player.name} has no assigned character. Skipping turn.")
            return

        self.game_logger.info(f"🎮 >>> It is {player.name}'s turn. (Round {round_num}) - AP: {player_char.action_points}")

        turn_in_progress = True
        while turn_in_progress and player_char.action_points > 0:
            current_room = self.rooms.get(player_char.current_room_id)
            if not current_room:
                self.game_logger.error(f"Character {player_char.name} is in an unknown room: {player_char.current_room_id}. Ending turn.")
                break

            # Events are now distributed immediately after each action execution

            # Gather observations for the current player
            player_observations = self.player_observations.get(player_char.id, [])
            observation_messages: List[str] = []
            if player_observations:
                observation_messages.append("**📰 Recent Events:**")
                for event in player_observations:
                    observation_messages.append(f"• {event.message}")

            # Check motive status and add debug logging
            motive_status_message = player_char.get_motive_status_message(self)
            if motive_status_message:
                observation_messages.append(motive_status_message)
            
            # Log detailed motive condition tree (non-chat logging)
            condition_tree = player_char.get_motive_condition_tree(self)
            self.game_logger.info(f"Motive condition tree for {player.name} ({player_char.name}):\n{condition_tree}")

            # Get formatted room description from the Room object
            current_room_description = current_room.get_formatted_description()

            # Check if this is the first interaction for this player
            is_first_interaction = not self.player_first_interaction_done.get(player_char.id, False)
            action_prompt = self._get_action_display(player_char, is_first_turn=is_first_interaction, round_num=round_num)

            # Construct the message content
            message_content_parts = []
            
            # Add character assignment and initial location for first interaction
            if is_first_interaction:
                character_assignment = player_char.get_introduction_message()
                message_content_parts.append(character_assignment)
                
                # Add initial location with character's reason
                initial_location_text = f"**🏠 Initial location:**\n{current_room_description}"
                if hasattr(player_char, 'initial_room_reason') and player_char.initial_room_reason:
                    initial_location_text += f"\n\n{player_char.initial_room_reason}"
                message_content_parts.append(initial_location_text)
            
            # Add observations (if any)
            if observation_messages:
                message_content_parts.append("\n".join(observation_messages))
                # Clear observations for this player after presenting them
                self.player_observations[player_char.id] = []
            
            # Add action prompt and AP info
            message_content_parts.extend([
                f"{action_prompt}",
                f"**⚡ Action Points:**\n{player_char.action_points} AP",
                f"🤔 What do you do?"
            ])
            
            message_content = "\n\n".join(message_content_parts)
            
            # Send system message for first interaction only
            if is_first_interaction:
                system_prompt = f"You are a player in a text-based adventure game. Below is the game manual. Read it carefully to understand the rules, your role, and how to interact with the game world.\n\n" \
                                f"--- GAME MANUAL START ---\n{self.manual_content}\n--- GAME MANUAL END ---\n\n" \
                                f"IMPORTANT: All actions must be on their own line and start with '>' (e.g., '> look', '> move west', '> say hello'). " \
                                f"Without the '>' prefix, your actions will be ignored and you'll receive a penalty.\n\n" \
                                f"Now, based on the manual and your character, respond with your actions."
                
                system_msg = SystemMessage(content=system_prompt)
                player.add_message(system_msg)
                self.game_logger.info(f"GM ➡️ {player.name} (SYSTEM, with manual: {self.manual_path}):\n{system_prompt[:50]}...")
                player.logger.info(f"{player.name} ⬅️ GM (SYSTEM):\n{system_prompt}")
                self.player_first_interaction_done[player_char.id] = True
            
            # Send the main message
            human_msg = HumanMessage(content=message_content)
            player.add_message(human_msg)
            self.game_logger.info(f"GM ➡️ {player.name}:\n{message_content}")
            player.logger.info(f"{player.name} ⬅️ GM:\n{message_content}")

            start_time = time.time()
            response = await player.get_response_and_update_history(player.chat_history)
            duration = time.time() - start_time
            
            response_len = len(response.content)

            player_input = response.content.strip().lower()
            self.game_logger.info(f"GM ⬅️ {player.name}:\n{player_input}")
            player.logger.info(f"{player.name} ➡️ GM:\n{player_input}")

            # Check for explicit "end turn" command first
            if player_input == "end turn":
                feedback = "You decide to end your turn."
                turn_in_progress = False
                feedback_message = HumanMessage(content=feedback)
                player.add_message(feedback_message)
                player.logger.info(f"{player.name} ⬅️ GM (Feedback):\n{feedback}")
                self.game_logger.info(f"GM ➡️ {player.name} (Feedback):\n{feedback}")
                continue # Continue to the while loop condition to end the turn

            # Parse all actions from the player's response
            parsed_actions, invalid_actions = parse_player_response(response.content, self.game_actions)

            if not parsed_actions and not invalid_actions:
                # Penalty for not providing any actions at all
                feedback_parts = [
                    "You did not provide any actions.",
                    "",
                    "Remember: Actions must be on their own line and start with '>' (e.g., '> look', '> move west').",
                    "Your turn ends prematurely as a penalty."
                ]
                combined_feedback = "\n".join(feedback_parts)
                player_char.action_points = 0 # End turn as penalty
                self.game_logger.info(f"{player.name} failed to provide any actions. Turn ended.")

                feedback_message = HumanMessage(content=combined_feedback)
                player.add_message(feedback_message)
                player.logger.info(f"{player.name} ⬅️ GM (Feedback):\n{combined_feedback}")
                self.game_logger.info(f"GM ➡️ {player.name} (Feedback):\n{combined_feedback}")
                
                # Wait for player to confirm turn end
                await self._handle_turn_end_confirmation(player, player_char)
                turn_in_progress = False
                continue # Continue to the while loop condition to end the turn
            elif invalid_actions:
                # Penalty for providing invalid actions
                # Get valid action names for better feedback
                valid_action_names = []
                if parsed_actions:
                    for action, _ in parsed_actions:
                        if hasattr(action, 'name'):
                            valid_action_names.append(action.name)
                        else:
                            valid_action_names.append(action.get('name', ''))
                example_actions = self._get_example_actions()
                
                feedback_parts = [
                    f"You provided invalid actions: {', '.join(invalid_actions)}",
                    "Your turn ends prematurely as a penalty."
                ]
                
                if valid_action_names:
                    feedback_parts.append(f"Valid actions in your response: {', '.join(valid_action_names)}")
                else:
                    feedback_parts.append(f"Available actions include: {', '.join(example_actions)}. Use 'help' for a complete list.")
                combined_feedback = "\n".join(feedback_parts)
                player_char.action_points = 0 # End turn as penalty
                
                # Log detailed information about what went wrong
                self.game_logger.error(f"{player.name} provided invalid actions. Turn ended.")
                self.game_logger.error(f"Invalid actions were: {invalid_actions}")
                if parsed_actions:
                    valid_actions_log = []
                    for action, params in parsed_actions:
                        if hasattr(action, 'name'):
                            action_name = action.name
                        else:
                            action_name = action.get('name', '')
                        valid_actions_log.append((action_name, params))
                    self.game_logger.error(f"Valid actions were: {valid_actions_log}")

                feedback_message = HumanMessage(content=combined_feedback)
                player.add_message(feedback_message)
                player.logger.info(f"{player.name} ⬅️ GM (Feedback):\n{combined_feedback}")
                self.game_logger.info(f"GM ➡️ {player.name} (Feedback):\n{combined_feedback}")
                
                # Wait for player to confirm turn end
                await self._handle_turn_end_confirmation(player, player_char)
                turn_in_progress = False
                continue # Continue to the while loop condition to end the turn

            else:
                all_actions_in_response_valid = True # Tracks if all actions in this specific response were valid and processed
                response_feedback_messages: List[str] = [] # Collect feedback for this response
                help_action_performed = False # Track if help action was performed to avoid duplicate action prompts

                # Track actions that couldn't be executed due to AP exhaustion
                actions_skipped_due_to_ap = []
                
                # Collect all executed actions for logging
                executed_actions = []
                
                for action_config, params in parsed_actions:
                    # Handle both Pydantic objects and dictionaries from merged config
                    if hasattr(action_config, 'name'):
                        action_name = action_config.name
                    else:
                        action_name = action_config.get('name', '')
                        
                    action_specific_feedback: List[str] = []
                    if player_char.action_points <= 0:
                        # Track remaining actions that couldn't be processed due to AP exhaustion
                        remaining_actions = parsed_actions[parsed_actions.index((action_config, params)):]
                        for remaining_action_config, remaining_params in remaining_actions:
                            # Handle both Pydantic objects and dictionaries from merged config
                            if hasattr(remaining_action_config, 'name'):
                                remaining_action_name = remaining_action_config.name
                            else:
                                remaining_action_name = remaining_action_config.get('name', '')
                            actions_skipped_due_to_ap.append(f"{remaining_action_name} {remaining_params}")
                        break # Exit inner loop for actions

                    # Calculate actual cost using cost calculation function if available
                    actual_cost = self._calculate_action_cost(player_char, action_config, params)
                    
                    if actual_cost > player_char.action_points:
                        action_specific_feedback.append(f"Action '{action_name}' costs {actual_cost} AP, but you only have {player_char.action_points} AP. Skipping this action.")
                        actions_skipped_due_to_ap.append(f"{action_name} {params}")
                        # Don't set all_actions_in_response_valid = False for AP exhaustion - this is normal gameplay
                    else:
                        requirements_met, req_message, exit_data = self._check_requirements(player_char, action_config, params)
                        if requirements_met:
                            player_char.action_points -= actual_cost
                            action_events, action_specific_feedback_list = self._execute_effects(player_char, action_config, params)
                            action_specific_feedback.extend(action_specific_feedback_list)
                            
                            # Track if help action was performed     
                            if action_name == "help":
                                help_action_performed = True
                            
                            # Add generated events to the main event queue
                            self.event_queue.extend(action_events)
                            
                            # Mark hint as executed if this action matches a hint                                                         
                            self._mark_hint_executed(player.name, action_name, params)
                            
                            # Collect action info for batch logging
                            executed_actions.append({
                                'name': action_name,
                                'cost': actual_cost,
                                'remaining_ap': player_char.action_points,
                                'feedback': action_specific_feedback_list
                            })
                        else:
                            action_specific_feedback.append(f"Cannot perform '{action_name}': {req_message}. Skipping this action.")
                            all_actions_in_response_valid = False

                    if action_specific_feedback:
                        # Calculate AP info for this action
                        ap_before = player_char.action_points + actual_cost
                        ap_after = player_char.action_points
                        response_feedback_messages.append(f"- ⚔️ **{action_name.capitalize()} Action:** (Cost: {actual_cost} AP, Remaining: {ap_after} AP)")
                        response_feedback_messages.extend([f"  - {msg}" for msg in action_specific_feedback])
                
                # Log all executed actions in a single report
                if executed_actions:
                    action_report_lines = [f"🎬 Action Execution Report for {player_char.name}:"]
                    for action in executed_actions:
                        action_report_lines.append(f"  • {action['name']} (Cost: {action['cost']} AP, Remaining: {action['remaining_ap']} AP)")
                    self.game_logger.info("\n".join(action_report_lines))
                
                # Log detailed observation reports before distributing events (since _distribute_events clears the queue)
                if self.event_queue:
                    observation_report_lines = [f"👁️ Observation Report for {player_char.name}:"]
                    for event in self.event_queue:
                        observation_report_lines.append(f"  • {event.message} (Type: {event.event_type})")
                        # Add detailed observation breakdown for this event
                        observation_details = self._get_event_observation_details(event)
                        observation_report_lines.extend(observation_details)
                    self.game_logger.info("\n".join(observation_report_lines))
                
                # Distribute all events after all actions are processed
                self._distribute_events()

                # After processing all actions in the response
                if response_feedback_messages:
                    combined_feedback = "\n".join([
                        "📋 **Your Actions for this turn:**",
                        "\n".join(response_feedback_messages)
                    ])
                else:
                    combined_feedback = "ℹ️ No specific feedback for actions performed this turn."
                
                # Add feedback about actions skipped due to AP exhaustion
                if actions_skipped_due_to_ap:
                    skipped_actions_text = "\n".join([f"- {action}" for action in actions_skipped_due_to_ap])
                    combined_feedback += f"\n\n⚠️ **Actions skipped due to insufficient AP:**\n{skipped_actions_text}"

                feedback_message = HumanMessage(content=combined_feedback)
                player.add_message(feedback_message)
                player.logger.info(f"{player.name} ⬅️ GM (Feedback):\n{combined_feedback}")
                self.game_logger.info(f"GM ➡️ {player.name} (Feedback):\n{combined_feedback}")

                if not all_actions_in_response_valid:
                    # If any action in the response was invalid or couldn't be performed, end the turn as a penalty.
                    feedback_parts = [
                        "❌ One or more actions in your response were invalid or could not be performed.",
                        "⏰ Your turn ends prematurely as a penalty."
                    ]
                    penalty_feedback = "\n".join(feedback_parts)
                    player_char.action_points = 0 # End turn as penalty
                    
                    # Log detailed information about what went wrong
                    self.game_logger.error(f"❌ {player.name} had invalid/unexecutable actions in response. Turn ended.")
                    # Handle both Pydantic objects and dictionaries from merged config
                    action_names = []
                    for action, params in parsed_actions:
                        if hasattr(action, 'name'):
                            action_names.append(action.name)
                        else:
                            action_names.append(action.get('name', 'unknown'))
                    self.game_logger.error(f"Parsed actions were: {[(action_names[i], params) for i, (action, params) in enumerate(parsed_actions)]}")
                    self.game_logger.error(f"Action feedback that caused failure: {response_feedback_messages}")
                    
                    # Send final penalty feedback
                    feedback_message = HumanMessage(content=penalty_feedback)
                    player.add_message(feedback_message)
                    player.logger.info(f"GM sent chat to {player.name} (Feedback):\n{penalty_feedback}")
                    self.game_logger.info(f"GM sent chat to {player.name} (Feedback):\n{penalty_feedback}")
                    
                    # Wait for player to confirm turn end
                    await self._handle_turn_end_confirmation(player, player_char)
                    turn_in_progress = False
                    
                elif player_char.action_points <= 0:
                    # If all actions were valid but AP ran out, turn ends naturally.
                    feedback = "You have used all your Action Points for this turn. Your turn has ended."
                    self.game_logger.info(f"⚡ {player.name} used all AP. Turn ended.")

                    # Wait for player to confirm turn end (no separate feedback needed)
                    await self._handle_turn_end_confirmation(player, player_char)
                    turn_in_progress = False
                    
                # If all actions were valid and AP remain, the loop continues automatically to re-prompt.
                # But if help action was performed, skip the next action prompt to avoid duplication
                if help_action_performed and player_char.action_points > 0:
                    # Help action already included the action prompt, so skip the next iteration
                    continue

        self.game_logger.info(f"End of action processing for {player.name}. Remaining AP: {player_char.action_points}")

    async def _handle_turn_end_confirmation(self, player: Player, player_char: Character):
        """Handles the turn end confirmation process with the player."""
        self.game_logger.info(f"⏰ === TURN END CONFIRMATION START for {player.name} ===")
        
        # Send turn end confirmation message
        confirmation_message = (
            "Your turn has ended. Please confirm how you'd like to proceed:\n\n"
            "⚔️ Example actions:\n"
            "  > continue\n"
            "  > quit (will count as failure to complete motive)\n\n"
            "What would you like to do?"
        )
        
        confirmation_msg = HumanMessage(content=confirmation_message)
        player.add_message(confirmation_msg)
        player.logger.info(f"{player.name} ⬅️ GM (Turn End Confirmation):\n{confirmation_message}")
        self.game_logger.info(f"GM ➡️ {player.name} (Turn End Confirmation):\n{confirmation_message}")
        
        # Get player's response
        start_time = time.time()
        response = await player.get_response_and_update_history(player.chat_history)
        duration = time.time() - start_time
        response_len = len(response.content)
        
        player_input = response.content.strip().lower()
        self.game_logger.info(f"GM ⬅️ {player.name} (Turn End Response):\n{player_input}")
        player.logger.info(f"{player.name} ➡️ GM (Turn End Response):\n{player_input}")
        
        # Parse the response for turn end actions (only accept actions with > prefix)
        if "> quit" in response.content:
            self.game_logger.info(f"🚪 Player {player.name} chose to quit the game.")
            player.logger.info(f"🚪 Player {player.name} chose to quit the game.")
            # Mark player as quit (we'll handle this in the main game loop)
            player_char.action_points = -1  # Special marker for quit
            return False  # Player quit
        elif "> continue" in response.content:
            self.game_logger.info(f"✅ Player {player.name} chose to continue.")
            player.logger.info(f"✅ Player {player.name} chose to continue.")
            
            # Check for any other actions in the response and warn about them
            other_actions = []
            for line in response.content.strip().splitlines():
                trimmed_line = line.strip()
                if trimmed_line.startswith(">") and not trimmed_line.startswith("> continue") and not trimmed_line.startswith("> quit"):
                    other_actions.append(trimmed_line)
            
            if other_actions:
                # Format ignored actions with line breaks like AP exhaustion feedback
                ignored_actions_text = "\n".join([f"- {action}" for action in other_actions])
                warning_msg = f"Note: You submitted other actions during turn end confirmation. These were ignored. Actions can only be performed during your active turn.\n\n**Ignored actions:**\n{ignored_actions_text}"
                warning_message = HumanMessage(content=warning_msg)
                player.add_message(warning_message)
                player.logger.info(f"{player.name} ⬅️ GM (Warning):\n{warning_msg}")
                self.game_logger.info(f"GM ➡️ {player.name} (Warning):\n{warning_msg}")
            
            return True  # Player continues
        else:
            # Default to continue if unclear response
            self.game_logger.info(f"Player {player.name} gave unclear response, defaulting to continue.")
            player.logger.info(f"Player {player.name} gave unclear response, defaulting to continue.")
            return True  # Player continues
        
        self.game_logger.info(f"✅ === TURN END CONFIRMATION COMPLETE for {player.name} ===")

    def _get_applicable_hints(self, player_name: str, round_num: int) -> List[str]:
        """Get hints that apply to the current player and round."""
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(self.game_config, 'game_settings'):
            hints = getattr(self.game_config.game_settings, 'hints', None)
        else:
            hints = self.game_config.get('game_settings', {}).get('hints', None)
            
        if not hints:
            return []
        
        applicable_hints = []
        for hint in hints:
            # Check if hint has already been executed by this player
            hint_id = hint.get("hint_id", "")
            if hint_id and hint_id in self.executed_hints and player_name in self.executed_hints[hint_id]:
                continue  # Skip this hint as it's already been executed by this player
            
            # Check if hint applies to this player and round using structured when clause
            when_condition = hint.get("when", {})
            if not self._evaluate_when_condition(when_condition, player_name, round_num):
                continue
            
            hint_action = hint.get("hint_action", "")
            if hint_action:
                applicable_hints.append(hint_action)
        
        return applicable_hints

    def _evaluate_when_condition(self, when_condition: Dict[str, Any], player_name: str, round_num: int) -> bool:
        """Evaluate a structured when condition to determine if a hint should be shown."""
        if not when_condition:
            return True  # No condition means always show
        
        # Check round condition
        if "round" in when_condition:
            required_round = when_condition["round"]
            if isinstance(required_round, int):
                if round_num < required_round:
                    return False
            elif isinstance(required_round, dict):
                # Support range conditions like {"min": 1, "max": 3}
                if "min" in required_round and round_num < required_round["min"]:
                    return False
                if "max" in required_round and round_num > required_round["max"]:
                    return False
        
        # Check player condition
        if "players" in when_condition:
            target_players = when_condition["players"]
            if isinstance(target_players, list):
                if player_name not in target_players:
                    return False
            elif isinstance(target_players, str):
                if player_name != target_players:
                    return False
        
        # Check after condition (hint should only show after another hint was executed)
        if "after" in when_condition:
            after_hint_id = when_condition["after"]
            if after_hint_id not in self.executed_hints:
                return False  # Required hint hasn't been executed by anyone yet
            # Note: We don't check if the current player executed the prerequisite hint
            # The hint just needs to be executed by someone
        
        # Check room condition (for future expansion)
        if "room" in when_condition:
            # This could be expanded to check if player is in specific room
            pass
        
        # Check action condition (for future expansion)
        if "after_action" in when_condition:
            # This could be expanded to show hints after specific actions
            pass
        
        return True

    def _mark_hint_executed(self, player_name: str, action_name: str, params: Dict[str, Any]):
        """Mark a hint as executed if the action matches a hint."""
        # Handle both Pydantic objects and dictionaries from merged config
        if hasattr(self.game_config, 'game_settings'):
            hints = getattr(self.game_config.game_settings, 'hints', None)
        else:
            hints = self.game_config.get('game_settings', {}).get('hints', None)
            
        if not hints:
            return
        
        for hint in hints:
            hint_id = hint.get("hint_id", "")
            if not hint_id:
                continue
                
            # Check if this player should have this hint using the when condition
            when_condition = hint.get("when", {})
            if not self._evaluate_when_condition(when_condition, player_name, 1):  # Use round 1 for evaluation
                continue
            
            # Check if the action matches the hint
            hint_action = hint.get("hint_action", "")
            if not hint_action.startswith(">"):
                continue
                
            # Extract action from hint (e.g., "> whisper Hero" -> "whisper")
            hint_action_parts = hint_action[1:].strip().split()
            if not hint_action_parts:
                continue
                
            hint_action_name = hint_action_parts[0]
            
            # Check if the executed action matches the hint action
            if action_name == hint_action_name:
                # Mark this hint as executed by this player
                if hint_id not in self.executed_hints:
                    self.executed_hints[hint_id] = set()
                self.executed_hints[hint_id].add(player_name)
                self.game_logger.info(f"Marked hint '{hint_id}' as executed by {player_name}")

    def _get_example_actions(self) -> List[str]:
        """Generate example actions dynamically from available actions."""
        if not self.game_actions:
            return ["look", "help"]  # Fallback if no actions loaded
        
        # Define priority categories for example actions
        priority_categories = ["observation", "movement", "communication", "inventory", "interaction"]
        
        # Collect actions by category
        actions_by_category = {}
        for action_id, action_cfg in self.game_actions.items():      
            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(action_cfg, 'category'):
                category = action_cfg.category or "other"
            else:
                category = action_cfg.get('category', 'other')
            if category not in actions_by_category:
                actions_by_category[category] = []
            # Handle both Pydantic objects and dictionaries from merged config
            if hasattr(action_cfg, 'name'):
                action_name = action_cfg.name
            else:
                action_name = action_cfg.get('name', action_id)
            actions_by_category[category].append(action_name)
        
        # Build example actions list prioritizing core categories
        example_actions = []
        
        # Add actions from priority categories first
        for category in priority_categories:
            if category in actions_by_category:
                # Take the first action from each priority category
                example_actions.append(actions_by_category[category][0])
        
        # Add help action if available
        if "help" in self.game_actions:
            example_actions.append("help")
        
        # Ensure we have at least a few actions
        if len(example_actions) < 3:
            # Add more actions from any category
            for category, actions in actions_by_category.items():
                if category not in priority_categories:
                    example_actions.extend(actions[:2])  # Add up to 2 from each category
                    if len(example_actions) >= 5:  # Limit to reasonable number
                        break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_actions = []
        for action in example_actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        return unique_actions[:5]  # Limit to 5 example actions

    def _get_action_display(self, player_char: Character, is_first_turn: bool = False, round_num: int = 1) -> str:
        """Get standardized action display text."""
        # Generate example actions dynamically
        example_actions = self._get_example_actions()
        
        # Create action display without AP info (AP will be shown separately)
        action_display = "⚔️ Example actions:\n"
        for action in example_actions:
            action_display += f"  > {action}\n"
        action_display += "  > help (for more available actions)"
        
        # Add applicable hints
        player_name = None
        for player in self.players:
            if player.character and player.character.id == player_char.id:
                player_name = player.name
                break
        
        if player_name:
            hints = self._get_applicable_hints(player_name, round_num)
            if hints:
                action_display += "\n\nHint(s), try these actions please, we're testing game mechanics:\n" + "\n".join(hints)
        
        return action_display

    def _setup_game_world(self, theme_cfg: ThemeConfig, edition_cfg: EditionConfig):
        """Sets up the initial game world by merging configs and instantiating objects."""
        # This method is now handled by GameInitializer. This empty method can be removed after full refactor.
        pass

