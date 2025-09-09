import random
import time
import asyncio
import os
import logging
import sys # Added for stdout logging
import yaml # Added for YAML loading
from typing import List, Dict, Any, Optional, Tuple # Added for type hints
from pydantic import BaseModel, ValidationError # Added for Pydantic validation
from motive.player import Player, PlayerCharacter # Import PlayerCharacter
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
from motive.game_objects import GameObject # Import GameObject
from motive.game_rooms import Room # Import Room
from motive.action_parser import parse_player_response # Import the new action parser
from motive.exceptions import ConfigNotFoundError, ConfigParseError, ConfigValidationError # Import custom exceptions
from motive.game_initializer import GameInitializer # Import GameInitializer
from datetime import datetime # Added for datetime logging
import uuid # Added for UUID logging


class GameMaster:
    # Accept a pre-validated GameConfig object directly
    def __init__(self, game_config: GameConfig, game_id: str):
        self.players = []
        self.num_rounds = game_config.game_settings.num_rounds
        self.game_id = game_id
        # Resolve manual path relative to the configs directory (where game.yaml is located)
        import os
        configs_dir = os.path.dirname(os.path.abspath("configs/game.yaml"))
        self.manual_path = os.path.join(configs_dir, game_config.game_settings.manual)

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
        self.game_initializer = GameInitializer(game_config, game_id, self.game_logger, self.game_config.game_settings.initial_ap_per_turn)

        # Load Theme and Edition configurations
        self.game_initializer._load_configurations()
        self.theme = self.game_initializer.theme_cfg.id
        self.edition = self.game_initializer.edition_cfg.id

        # Now that theme and edition are known, set up the full logging
        self.log_dir = self._setup_logging()
        # Update the game initializer with the fully configured logger
        self.game_initializer.game_logger = self.game_logger

        self.manual_content = self._load_manual_content()

        # Store loaded configs in game_config for broader access
        game_config.theme_config = self.game_initializer.theme_cfg
        game_config.edition_config = self.game_initializer.edition_cfg
        # self.game_config = game_config # Store the full game config # Moved to earlier

        # Initialize game state collections - these will be populated by GameInitializer
        self.rooms: Dict[str, Room] = {}
        self.game_objects: Dict[str, GameObject] = {}
        self.player_characters: Dict[str, PlayerCharacter] = {}

        self.player_first_interaction_done: Dict[str, bool] = {} # Track if a player has had their first interaction

        # These will store the merged configurations
        self.game_object_types: Dict[str, ObjectTypeConfig] = {}
        self.game_actions: Dict[str, ActionConfig] = {}
        self.game_character_types: Dict[str, CharacterConfig] = {}

        # Event management
        self.event_queue: List[Event] = [] # All events generated during a turn
        self.player_observations: Dict[str, List[Event]] = {} # Events specific to each player

        self._initialize_players(game_config.players)
        
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
        self.game_initializer.initial_ap_per_turn = self.game_config.game_settings.initial_ap_per_turn

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
        base_log_dir = "logs"
        # Create a unique, sortable directory name for this game run
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hhr_%Mmin_%Ssec")
        unique_game_folder = f"({timestamp}) {self.game_id}"
        
        game_log_dir = os.path.join(base_log_dir, self.theme, self.edition, unique_game_folder)
        os.makedirs(game_log_dir, exist_ok=True)

        # Remove all existing handlers from the logger before reconfiguring
        for handler in list(self.game_logger.handlers):
            self.game_logger.removeHandler(handler)

        # Set the level for the game logger (now that it's the main logger)
        self.game_logger.setLevel(logging.INFO)

        # File handler for game.log
        game_narrative_file = os.path.join(game_log_dir, "game.log")
        game_file_handler = logging.FileHandler(game_narrative_file, encoding="utf-8")
        game_formatter = logging.Formatter('%(asctime)s - %(message)s') # Simpler format for narrative
        game_file_handler.setFormatter(game_formatter)
        self.game_logger.addHandler(game_file_handler)

        # Stream handler for stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_formatter = logging.Formatter('%(asctime)s - %(message)s')
        stdout_handler.setFormatter(stdout_formatter)
        self.game_logger.addHandler(stdout_handler)

        self.game_logger.info(f"Game narrative logging to {game_narrative_file} and stdout.")
        
        return game_log_dir

    def _initialize_players(self, player_configs: list[PlayerConfig]):
        """Initializes players based on the provided list of PlayerConfig objects."""
        self.game_logger.info("Initializing players from configuration...")
        for p_config in player_configs:
            player = Player(
                name=p_config.name,
                provider=p_config.provider,
                model=p_config.model,
                log_dir=self.log_dir  # Pass the log directory to the player
            )
            self.players.append(player)
            self.game_logger.info(f"  - Initialized player: {player.name} using {p_config.provider}/{p_config.model}")
            self.player_first_interaction_done[player.name] = False # Initialize for tracking

    async def run_game(self):
        """Main game loop."""
        self.game_logger.info("==================== GAME STARTING ====================")
        print("\n==================== GAME STARTING ====================") # Keep for console output

        # Removed: await self._send_initial_messages()

        for round_num in range(1, self.num_rounds + 1):
            self.game_logger.info(f"--- Starting Round {round_num} of {self.num_rounds} ---")
            print(f"\n--- Starting Round {round_num} of {self.num_rounds} ---") # Keep for console output
            
            # Filter out players who have quit
            active_players = [player for player in self.players if player.character.action_points != -1]
            
            if not active_players:
                self.game_logger.info("No active players remaining. Game ending early.")
                print("No active players remaining. Game ending early.")
                break
                
            for player in active_players:
                player.character.action_points = self.game_config.game_settings.initial_ap_per_turn # Reset AP from config
                await self._execute_player_turn(player, round_num)
                
                # Check if player quit during their turn
                if player.character.action_points == -1:
                    self.game_logger.info(f"Player {player.name} has quit the game.")
                    print(f"Player {player.name} has quit the game.")
                    
            self.game_logger.info(f"=== Round {round_num} Complete ===")
            print(f"=== Round {round_num} Complete ===") # Keep for console output

        self.game_logger.info("===================== GAME OVER ======================")
        print("\n===================== GAME OVER ======================") # Keep for console output
        
        # Check win conditions and provide game summary
        self._check_win_conditions_and_summarize()

    def _check_win_conditions_and_summarize(self):
        """Checks if any players achieved their motives and provides a game summary."""
        winners = []
        losers = []
        
        for player in self.players:
            if player.character.action_points == -1:  # Player quit
                losers.append(f"{player.name} (quit)")
                continue
                
            # For now, we'll implement a simple win condition check
            # In a real game, this would check if the player's motive was achieved
            # based on game state, objects collected, actions taken, etc.
            
            # Placeholder: Check if player has any items in inventory as a simple win condition
            if player.character.inventory:
                winners.append(f"{player.name} (achieved motive: {player.character.motive})")
            else:
                losers.append(f"{player.name} (failed to achieve motive: {player.character.motive})")
        
        # Log and display results
        if winners:
            winner_text = f"WINNERS: {', '.join(winners)}"
            self.game_logger.info(winner_text)
            print(f"\n{winner_text}")
        else:
            no_winners_text = "No players achieved their motives."
            self.game_logger.info(no_winners_text)
            print(f"\n{no_winners_text}")
        
        if losers:
            loser_text = f"LOSERS: {', '.join(losers)}"
            self.game_logger.info(loser_text)
            print(f"{loser_text}")
        
        # Game summary
        summary_text = f"\nGame Summary:\n- Total players: {len(self.players)}\n- Winners: {len(winners)}\n- Losers: {len(losers)}"
        self.game_logger.info(summary_text)
        print(summary_text)

    def _check_requirements(self, player_char: PlayerCharacter, action_config: ActionConfig, params: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Checks if all requirements for an action are met."""
        current_room = self.rooms.get(player_char.current_room_id)
        if not current_room:
            return False, f"Character is in an unknown room: {player_char.current_room_id}.", None

        found_exit_data: Optional[Dict[str, Any]] = None # To store exit data if found

        for req in action_config.requirements:
            if req.type == "player_has_tag":
                if not player_char.has_tag(req.tag):
                    return False, f"Player does not have tag '{req.tag}'.", None
            elif req.type == "object_in_room":
                object_name = params.get(req.object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{req.object_name_param}' for object_in_room requirement.", None
                
                obj_found = False
                for obj in current_room.objects.values():
                    if obj.name.lower() == object_name.lower():
                        obj_found = True
                        break
                if not obj_found:
                    return False, f"Object '{object_name}' not in room.", None
            elif req.type == "object_property_equals":
                object_name = params.get(req.object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{req.object_name_param}' for object_property_equals requirement.", None
                
                obj_found = player_char.get_item_in_inventory(object_name) # Check inventory first
                if not obj_found:
                    # Then check if it's in the current room
                    obj_found = current_room.get_object(object_name)

                if not obj_found:
                    return False, f"Object '{object_name}' not found for property check.", None
                
                if obj_found.get_property(req.property) != req.value:
                    return False, f"Object '{object_name}' property '{req.property}' is not '{req.value}'.", None
            elif req.type == "player_has_object_in_inventory":
                object_name = params.get(req.object_name_param)
                if object_name is None:
                    return False, f"Missing parameter '{req.object_name_param}' for player_has_object_in_inventory requirement.", None
                
                if not player_char.has_item_in_inventory(object_name):
                    return False, f"Player does not have '{object_name}' in inventory.", None
            elif req.type == "exit_exists":
                direction = params.get(req.direction_param)
                if not direction:
                    return False, f"Missing parameter '{req.direction_param}' for exit_exists requirement.", None
                
                found_exit = None
                for exit_id, exit_data in current_room.exits.items():
                    if exit_data['name'].lower() == direction.lower() and not exit_data.get('is_hidden', False):
                        found_exit = exit_data
                        break

                if not found_exit:
                    return False, f"No visible exit in the '{direction}' direction.", None
                found_exit_data = found_exit # Store for returning
            elif req.type == "player_in_room":
                player_name = params.get(req.target_player_param)
                if not player_name:
                    return False, f"Missing parameter '{req.target_player_param}' for player_in_room requirement.", None
                
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

    def _execute_effects(self, player_char: PlayerCharacter, action_config: ActionConfig, params: Dict[str, Any]) -> Tuple[List[Event], List[str]]:
        """Applies the effects of an action to the game state and generates feedback/events."""
        feedback_messages: List[str] = []
        events_generated: List[Event] = [] # Changed to list of Event objects

        current_room = self.rooms.get(player_char.current_room_id)
        if not current_room:
            feedback_messages.append(f"Error: Character is in an unknown room: {player_char.current_room_id}.")
            return [], feedback_messages

        for effect in action_config.effects:
            target_instance = None
            target_id_from_param = params.get(effect.target_id_param) if effect.target_id_param else None
            target_id = effect.target_id or target_id_from_param

            if effect.target_type == "player":
                # For player target, the instance is always the current player_char
                target_instance = player_char
            elif effect.target_type == "room":
                if target_id:
                    target_instance = self.rooms.get(target_id)
                elif player_char.current_room_id: # Default to current room if target_id not specified
                    target_instance = self.rooms.get(player_char.current_room_id)
            elif effect.target_type == "object":
                if target_id:
                    # Check player inventory first
                    target_instance = player_char.get_item_in_inventory(target_id)
                    if not target_instance:
                        # Then check current room
                        current_room = self.rooms.get(player_char.current_room_id)
                        if current_room:
                            target_instance = current_room.get_object(target_id)
            
            # Execute effects based on type
            if effect.type == "add_tag":
                if target_instance and effect.tag:
                    target_instance.add_tag(effect.tag)
                    feedback_messages.append(f"The {effect.target_type} '{target_instance.name}' gains the tag: '{effect.tag}'.")
                else:
                    self.game_logger.warning(f"add_tag effect missing target or tag for action '{action_config.name}'.")

            elif effect.type == "remove_tag":
                if target_instance and effect.tag:
                    target_instance.remove_tag(effect.tag)
                    feedback_messages.append(f"The {effect.target_type} '{target_instance.name}' loses the tag: '{effect.tag}'.")
                else:
                    self.game_logger.warning(f"remove_tag effect missing target or tag for action '{action_config.name}'.")

            elif effect.type == "set_property":
                if target_instance and effect.property and effect.value is not None:
                    target_instance.set_property(effect.property, effect.value)
                    feedback_messages.append(f"The {effect.target_type} '{target_instance.name}'s '{effect.property}' is now '{effect.value}'.")
                else:
                    self.game_logger.warning(f"set_property effect missing target, property, or value for action '{action_config.name}'.")

            elif effect.type == "generate_event":
                if effect.message and effect.observers:
                    event_message = effect.message.format(**params, player_name=player_char.name) # Add player_name to params for formatting
                    events_generated.append(Event(
                        message=event_message,
                        event_type="action_event", # A generic type for now
                        source_room_id=player_char.current_room_id,
                        timestamp=datetime.now().isoformat(),
                        related_player_id=player_char.id,
                        observers=effect.observers
                    ))
                    feedback_messages.append(event_message) # Player sees their own immediate events

            elif effect.type == "code_binding":
                if effect.function_name:
                    try:
                        # Use convention-based import: assume core_hooks for now
                        # TODO: Make this more flexible for different hook modules
                        import motive.hooks.core_hooks as core_hooks
                        hook_function = getattr(core_hooks, effect.function_name)
                        
                        hook_events_and_feedback = hook_function(self, player_char, params) # Expecting a tuple: (List[Event], List[str])
                        hook_events = hook_events_and_feedback[0]
                        hook_feedback = hook_events_and_feedback[1]
                        
                        feedback_messages.extend(hook_feedback)
                        events_generated.extend(hook_events) # Extend with actual Event objects

                    except (ImportError, AttributeError, KeyError, IndexError) as e: # Added KeyError for globals lookup
                        error_message = f"Error calling code binding for action '{action_config.name}': {e}"
                        self.game_logger.error(error_message)
                        feedback_messages.append(f"An error occurred while trying to process your action: {e}")
                    except Exception as e:
                        error_message = f"An unexpected error occurred in code binding for action '{action_config.name}': {e}"
                        self.game_logger.error(error_message)
                        feedback_messages.append(f"An unexpected error occurred: {e}")
                else:
                    self.game_logger.warning(f"code_binding effect for '{action_config.name}' missing function_name.")
                    feedback_messages.append(f"An error occurred due to missing code binding configuration.")

            else:
                self.game_logger.warning(f"Unsupported effect type: {effect.type}")

        # After processing all effects, add generated events to the main event queue
        return events_generated, feedback_messages

    def _calculate_action_cost(self, player_char: PlayerCharacter, action_config: Any, params: Dict[str, Any]) -> int:
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
        return action_config.cost

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
                        self.game_logger.info(f"OBSERVED - Player {player.name} in {player_char.current_room_id} observed event from {event.source_room_id}: '{event.message}' (Type: {event.event_type})")
        
        self.event_queue.clear() # Clear the queue after distributing all events

    async def _execute_player_turn(self, player: Player, round_num: int):
        """Executes a single player's turn, allowing multiple actions until AP are spent or turn ends."""
        player_char = player.character
        if not player_char:
            self.game_logger.error(f"Player {player.name} has no assigned character. Skipping turn.")
            return

        self.game_logger.info(f">>> It is {player.name}'s turn. (Round {round_num}) - AP: {player_char.action_points}")
        print(f"\n>>> It is {player.name}'s turn. (Round {round_num}) - AP: {player_char.action_points}") # Keep for console output

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
                observation_messages.append("**Recent Events:**")
                for event in player_observations:
                    observation_messages.append(f"• {event.message}")

            # Dynamically generate current room description and action prompt
            room_description_parts = [current_room.description]
            if current_room.objects:
                object_names = [obj.name for obj in current_room.objects.values()]
                room_description_parts.append(f"You also see: {', '.join(object_names)}.")
            if current_room.exits:
                exit_names = [exit_data['name'] for exit_data in current_room.exits.values() if not exit_data.get('is_hidden', False)]
                if exit_names:
                    room_description_parts.append(f"Exits: {', '.join(exit_names)}.")
            current_room_description = " ".join(room_description_parts)

            action_prompt = self._get_action_display(player_char, is_first_turn=False, round_num=round_num)

            # Handle the very first interaction differently
            if not self.player_first_interaction_done.get(player_char.id, False):
                # Include the full manual content in the system prompt for the LLM
                system_prompt = f"You are a player in a text-based adventure game. Below is the game manual. Read it carefully to understand the rules, your role, and how to interact with the game world.\n\n" \
                                f"--- GAME MANUAL START ---\n{self.manual_content}\n--- GAME MANUAL END ---\n\n" \
                                f"IMPORTANT: All actions must be on their own line and start with '>' (e.g., '> look', '> move west', '> say hello'). " \
                                f"Without the '>' prefix, your actions will be ignored and you'll receive a penalty.\n\n" \
                                f"Now, based on the manual and your character, respond with your actions."

                # Character Assignment and Motive
                char_type_id = player_char.id.split('_instance')[0]
                char_type_name = self.game_character_types[char_type_id].name
                article = "an" if char_type_name.lower().startswith(('a', 'e', 'i', 'o', 'u')) else "a"
                character_assignment = f"You are {player_char.name}, {article} {char_type_name}.\nYour motive is: {player_char.motive}"

                # Gather observations for the first interaction too
                player_observations = self.player_observations.get(player_char.id, [])
                observation_messages: List[str] = []
                if player_observations:
                    observation_messages.append("**Recent Events:**")
                    for event in player_observations:
                        observation_messages.append(f"• {event.message}")

                # Construct the first HumanMessage with character, motive, and initial room description
                first_action_prompt = self._get_action_display(player_char, is_first_turn=True, round_num=round_num)
                first_human_message_parts = [
                    character_assignment,
                    f"Initial location: {current_room_description}"
                ]
                
                if observation_messages:
                    first_human_message_parts.append("\n".join(observation_messages))
                    # Clear observations for this player after presenting them
                    self.player_observations[player_char.id] = []
                
                first_human_message_parts.extend([
                    f"{first_action_prompt}",
                    f"Action Points: {player_char.action_points} AP",
                    f"What do you do?"
                ])
                
                first_human_message_content = "\n\n".join(first_human_message_parts)

                system_msg = SystemMessage(content=system_prompt)
                human_msg = HumanMessage(content=first_human_message_content)

                player.add_message(system_msg)
                player.add_message(human_msg)
                self.game_logger.info(f"GM sent chat to {player.name} (SYSTEM, with manual: {self.manual_path}):\n{system_prompt[:50]}...")
                self.game_logger.info(f"GM sent chat to {player.name}:\n{first_human_message_content}")
                player.logger.info(f"GM sent chat to {player.name} (SYSTEM):\n{system_prompt}")
                player.logger.info(f"GM sent chat to {player.name}:\n{first_human_message_content}")

                start_time = time.time()
                response = await player.get_response_and_update_history(player.chat_history)
                duration = time.time() - start_time
                self.player_first_interaction_done[player_char.id] = True # Mark as done
            else:
                # Construct the GM message content for subsequent interactions, including observations
                gm_message_content_parts = []
                if observation_messages:
                    gm_message_content_parts.append("\n".join(observation_messages))
                
                gm_message_content_parts.extend([
                    f"{action_prompt}",
                    f"Action Points: {player_char.action_points} AP",
                    f"What do you do?"
                ])
                gm_message_content = "\n\n".join(gm_message_content_parts)
                
                gm_message = HumanMessage(content=gm_message_content)
                player.add_message(gm_message)
                player.logger.info(f"GM sent chat to {player.name}:\n{gm_message_content}")
                self.game_logger.info(f"GM sent chat to {player.name}:\n{gm_message_content}")
                
                # Clear observations for this player after presenting them
                if observation_messages:
                    self.player_observations[player_char.id] = []

                start_time = time.time()
                response = await player.get_response_and_update_history(player.chat_history)
                duration = time.time() - start_time
            
            response_len = len(response.content)

            player_input = response.content.strip().lower()
            self.game_logger.info(f"GM received chat from {player.name}:\n{player_input}")
            player.logger.info(f"GM received chat from {player.name}:\n{player_input}")
            print(f"    '{player.name}' responded in {duration:.2f}s ({response_len} chars): {player_input}")

            # Check for explicit "end turn" command first
            if player_input == "end turn":
                feedback = "You decide to end your turn."
                turn_in_progress = False
                feedback_message = HumanMessage(content=feedback)
                player.add_message(feedback_message)
                player.logger.info(f"GM sent chat to {player.name} (Feedback):\n{feedback}")
                self.game_logger.info(f"GM sent chat to {player.name} (Feedback):\n{feedback}")
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
                player.logger.info(f"GM sent chat to {player.name} (Feedback):\n{combined_feedback}")
                self.game_logger.info(f"GM sent chat to {player.name} (Feedback):\n{combined_feedback}")
                
                # Wait for player to confirm turn end
                await self._handle_turn_end_confirmation(player, player_char)
                turn_in_progress = False
                continue # Continue to the while loop condition to end the turn
            elif invalid_actions:
                # Penalty for providing invalid actions
                # Get valid action names for better feedback
                valid_action_names = [action.name for action, _ in parsed_actions] if parsed_actions else []
                core_actions = ["look", "move", "say", "pickup", "pass", "help"]
                
                feedback_parts = [
                    f"You provided invalid actions: {', '.join(invalid_actions)}",
                    "Your turn ends prematurely as a penalty."
                ]
                
                if valid_action_names:
                    feedback_parts.append(f"Valid actions in your response: {', '.join(valid_action_names)}")
                else:
                    feedback_parts.append(f"Available actions include: {', '.join(core_actions)}. Use 'help' for a complete list.")
                combined_feedback = "\n".join(feedback_parts)
                player_char.action_points = 0 # End turn as penalty
                
                # Log detailed information about what went wrong
                self.game_logger.error(f"{player.name} provided invalid actions. Turn ended.")
                self.game_logger.error(f"Invalid actions were: {invalid_actions}")
                if parsed_actions:
                    self.game_logger.error(f"Valid actions were: {[(action.name, params) for action, params in parsed_actions]}")

                feedback_message = HumanMessage(content=combined_feedback)
                player.add_message(feedback_message)
                player.logger.info(f"GM sent chat to {player.name} (Feedback):\n{combined_feedback}")
                self.game_logger.info(f"GM sent chat to {player.name} (Feedback):\n{combined_feedback}")
                
                # Wait for player to confirm turn end
                await self._handle_turn_end_confirmation(player, player_char)
                turn_in_progress = False
                continue # Continue to the while loop condition to end the turn

            else:
                all_actions_in_response_valid = True # Tracks if all actions in this specific response were valid and processed
                response_feedback_messages: List[str] = [] # Collect feedback for this response
                help_action_performed = False # Track if help action was performed to avoid duplicate action prompts

                for action_config, params in parsed_actions:
                    action_specific_feedback: List[str] = []
                    if player_char.action_points <= 0:
                        action_specific_feedback.append("You have run out of Action Points for this turn. Cannot perform further actions.")
                        # Don't set all_actions_in_response_valid = False for AP exhaustion - this is normal gameplay
                        break # Exit inner loop for actions

                    # Calculate actual cost using cost calculation function if available
                    actual_cost = self._calculate_action_cost(player_char, action_config, params)
                    
                    if actual_cost > player_char.action_points:
                        action_specific_feedback.append(f"Action '{action_config.name}' costs {actual_cost} AP, but you only have {player_char.action_points} AP. Skipping this action.")
                        self.game_logger.info(action_specific_feedback[-1])
                        # Don't set all_actions_in_response_valid = False for AP exhaustion - this is normal gameplay
                    else:
                        requirements_met, req_message, exit_data = self._check_requirements(player_char, action_config, params)
                        if requirements_met:
                            player_char.action_points -= actual_cost
                            action_events, action_specific_feedback_list = self._execute_effects(player_char, action_config, params)
                            action_specific_feedback.extend(action_specific_feedback_list)
                            
                            # Track if help action was performed
                            if action_config.name == "help":
                                help_action_performed = True
                            
                            # Add generated events to the main event queue
                            self.event_queue.extend(action_events)
                            
                            # Distribute events immediately after action execution
                            self._distribute_events()
                            
                            # Mark hint as executed if this action matches a hint
                            self._mark_hint_executed(player.name, action_config.name, params)
                            
                            self.game_logger.info(f"Action '{action_config.name}' executed by {player_char.name} (cost: {actual_cost} AP). Remaining AP: {player_char.action_points}")
                        else:
                            action_specific_feedback.append(f"Cannot perform '{action_config.name}': {req_message}. Skipping this action.")
                            self.game_logger.info(action_specific_feedback[-1])
                            all_actions_in_response_valid = False

                    if action_specific_feedback:
                        # Calculate AP info for this action
                        ap_before = player_char.action_points + actual_cost
                        ap_after = player_char.action_points
                        response_feedback_messages.append(f"- **{action_config.name.capitalize()} Action:** (Cost: {actual_cost} AP, Remaining: {ap_after} AP)")
                        response_feedback_messages.extend([f"  - {msg}" for msg in action_specific_feedback])

                # After processing all actions in the response
                if response_feedback_messages:
                    combined_feedback = "\n".join([
                        "**Your Actions for this turn:**",
                        "\n".join(response_feedback_messages)
                    ])
                else:
                    combined_feedback = "No specific feedback for actions performed this turn."

                feedback_message = HumanMessage(content=combined_feedback)
                player.add_message(feedback_message)
                player.logger.info(f"GM sent chat to {player.name} (Feedback):\n{combined_feedback}")
                self.game_logger.info(f"GM sent chat to {player.name} (Feedback):\n{combined_feedback}")

                if not all_actions_in_response_valid:
                    # If any action in the response was invalid or couldn't be performed, end the turn as a penalty.
                    feedback_parts = [
                        "One or more actions in your response were invalid or could not be performed.",
                        "Your turn ends prematurely as a penalty."
                    ]
                    penalty_feedback = "\n".join(feedback_parts)
                    player_char.action_points = 0 # End turn as penalty
                    
                    # Log detailed information about what went wrong
                    self.game_logger.error(f"{player.name} had invalid/unexecutable actions in response. Turn ended.")
                    self.game_logger.error(f"Parsed actions were: {[(action.name, params) for action, params in parsed_actions]}")
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
                    self.game_logger.info(f"{player.name} used all AP. Turn ended.")

                    # Wait for player to confirm turn end (no separate feedback needed)
                    await self._handle_turn_end_confirmation(player, player_char)
                    turn_in_progress = False
                    
                # If all actions were valid and AP remain, the loop continues automatically to re-prompt.
                # But if help action was performed, skip the next action prompt to avoid duplication
                if help_action_performed and player_char.action_points > 0:
                    # Help action already included the action prompt, so skip the next iteration
                    continue

        self.game_logger.info(f"End of action processing for {player.name}. Remaining AP: {player_char.action_points}")
        print(f"End of action processing for {player.name}. Remaining AP: {player_char.action_points}")

    async def _handle_turn_end_confirmation(self, player: Player, player_char: PlayerCharacter):
        """Handles the turn end confirmation process with the player."""
        self.game_logger.info(f"=== TURN END CONFIRMATION START for {player.name} ===")
        
        # Send turn end confirmation message
        confirmation_message = (
            "Your turn has ended. Please confirm how you'd like to proceed:\n\n"
            "Example actions: > continue, > quit (will count as failure to complete motive)\n\n"
            "What would you like to do?"
        )
        
        confirmation_msg = HumanMessage(content=confirmation_message)
        player.add_message(confirmation_msg)
        player.logger.info(f"GM sent chat to {player.name} (Turn End Confirmation):\n{confirmation_message}")
        self.game_logger.info(f"GM sent chat to {player.name} (Turn End Confirmation):\n{confirmation_message}")
        
        # Get player's response
        start_time = time.time()
        response = await player.get_response_and_update_history(player.chat_history)
        duration = time.time() - start_time
        response_len = len(response.content)
        
        player_input = response.content.strip().lower()
        self.game_logger.info(f"GM received chat from {player.name} (Turn End Response):\n{player_input}")
        player.logger.info(f"GM received chat from {player.name} (Turn End Response):\n{player_input}")
        print(f"    '{player.name}' responded in {duration:.2f}s ({response_len} chars): {player_input}")
        
        # Parse the response for turn end actions (only accept actions with > prefix)
        if "> quit" in response.content:
            self.game_logger.info(f"Player {player.name} chose to quit the game.")
            player.logger.info(f"Player {player.name} chose to quit the game.")
            # Mark player as quit (we'll handle this in the main game loop)
            player_char.action_points = -1  # Special marker for quit
            return False  # Player quit
        elif "> continue" in response.content:
            self.game_logger.info(f"Player {player.name} chose to continue.")
            player.logger.info(f"Player {player.name} chose to continue.")
            
            # Check for any other actions in the response and warn about them
            other_actions = []
            for line in response.content.strip().splitlines():
                trimmed_line = line.strip()
                if trimmed_line.startswith(">") and not trimmed_line.startswith("> continue") and not trimmed_line.startswith("> quit"):
                    other_actions.append(trimmed_line)
            
            if other_actions:
                warning_msg = f"Note: You submitted other actions ({', '.join(other_actions)}) during turn end confirmation. These were ignored. Actions can only be performed during your active turn."
                warning_message = HumanMessage(content=warning_msg)
                player.add_message(warning_message)
                player.logger.info(f"GM sent chat to {player.name} (Warning):\n{warning_msg}")
                self.game_logger.info(f"GM sent chat to {player.name} (Warning):\n{warning_msg}")
            
            return True  # Player continues
        else:
            # Default to continue if unclear response
            self.game_logger.info(f"Player {player.name} gave unclear response, defaulting to continue.")
            player.logger.info(f"Player {player.name} gave unclear response, defaulting to continue.")
            return True  # Player continues
        
        self.game_logger.info(f"=== TURN END CONFIRMATION COMPLETE for {player.name} ===")

    def _get_applicable_hints(self, player_name: str, round_num: int) -> List[str]:
        """Get hints that apply to the current player and round."""
        if not hasattr(self.game_config.game_settings, 'hints') or not self.game_config.game_settings.hints:
            return []
        
        applicable_hints = []
        for hint in self.game_config.game_settings.hints:
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
        if not hasattr(self.game_config.game_settings, 'hints') or not self.game_config.game_settings.hints:
            return
        
        for hint in self.game_config.game_settings.hints:
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

    def _get_action_display(self, player_char: PlayerCharacter, is_first_turn: bool = False, round_num: int = 1) -> str:
        """Get standardized action display text."""
        # Only show core actions from core.yaml
        core_actions = ["look", "move", "say", "pickup", "pass"]
        
        # Create action display without AP info (AP will be shown separately)
        action_display = f"Example actions: {', '.join(core_actions)}, help (for more available actions)."
        
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

