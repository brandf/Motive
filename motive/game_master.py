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
    ObjectTypeConfig,
    ActionConfig,
    ActionRequirementConfig,
    ActionEffectConfig,
    RoomConfig,
    ExitConfig,
    ObjectInstanceConfig,
    CharacterConfig
)
from motive.game_objects import GameObject # Import GameObject
from motive.game_rooms import Room # Import Room
from motive.action_parser import parse_player_response # Import the new action parser


class GameMaster:
    # Accept a pre-validated GameConfig object directly
    def __init__(self, game_config: GameConfig, game_id: str):
        self.players = []
        self.num_rounds = game_config.game_settings.num_rounds
        self.game_id = game_id
        self.manual_path = game_config.game_settings.manual

        # Initialize theme and edition with temporary placeholders for logging setup
        self.theme = "initial_theme" 
        self.edition = "initial_edition"

        self.log_dir = self._setup_logging() # Setup logging first

        # Load Theme and Edition configurations
        theme_cfg = self._load_yaml_config(game_config.game_settings.theme_config_path, ThemeConfig)
        edition_cfg = self._load_yaml_config(game_config.game_settings.edition_config_path, EditionConfig)

        if not theme_cfg:
            self.game_logger.error(f"Failed to load theme configuration from {game_config.game_settings.theme_config_path}. Exiting.")
            return # Or raise an exception
        if not edition_cfg:
            self.game_logger.error(f"Failed to load edition configuration from {game_config.game_settings.edition_config_path}. Exiting.")
            return # Or raise an exception

        # Update actual theme and edition IDs from loaded configs
        self.theme = theme_cfg.id
        self.edition = edition_cfg.id

        self.manual_content = self._load_manual_content()

        # Store loaded configs in game_config for broader access
        game_config.theme_config = theme_cfg
        game_config.edition_config = edition_cfg
        self.game_config = game_config # Store the full game config

        # Initialize game state collections
        self.rooms: Dict[str, Room] = {}
        self.game_objects: Dict[str, GameObject] = {}
        self.player_characters: Dict[str, PlayerCharacter] = {}

        # These will store the merged configurations
        self.game_object_types: Dict[str, ObjectTypeConfig] = {}
        self.game_actions: Dict[str, ActionConfig] = {}
        self.game_character_types: Dict[str, CharacterConfig] = {}

        self._initialize_players(game_config.players)
        self._setup_game_world(theme_cfg, edition_cfg)

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

    def _load_yaml_config(self, file_path: str, config_model: BaseModel) -> Optional[BaseModel]:
        """Loads and validates a YAML configuration file against a Pydantic model."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
            validated_config = config_model(**raw_config)
            self.game_logger.info(f"Successfully loaded and validated {file_path} as {config_model.__name__}")
            return validated_config
        except FileNotFoundError:
            self.game_logger.error(f"Configuration file not found: {file_path}")
            return None
        except yaml.YAMLError as e:
            self.game_logger.error(f"Error parsing YAML file {file_path}: {e}")
            return None
        except ValidationError as e:
            self.game_logger.error(f"Validation error in {file_path} for {config_model.__name__}: {e}")
            return None
        except Exception as e:
            self.game_logger.error(f"An unexpected error occurred while loading {file_path}: {e}")
            return None

    def _setup_logging(self):
        """Sets up the logging directory and configures the GM logger."""
        base_log_dir = "logs"
        game_log_dir = os.path.join(base_log_dir, self.theme, self.edition, self.game_id)
        os.makedirs(game_log_dir, exist_ok=True)

        # Configure Game logger for the combined game narrative and stdout
        self.game_logger = logging.getLogger("GameNarrative")
        self.game_logger.setLevel(logging.INFO)

        if self.game_logger.handlers:
            for handler in self.game_logger.handlers:
                self.game_logger.removeHandler(handler)

        # File handler for game.log
        game_narrative_file = os.path.join(game_log_dir, "game.log")
        game_file_handler = logging.FileHandler(game_narrative_file)
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

    async def run_game(self):
        """Main game loop."""
        self.game_logger.info("==================== GAME STARTING ====================")
        print("\n==================== GAME STARTING ====================") # Keep for console output

        await self._send_initial_messages()

        for round_num in range(1, self.num_rounds + 1):
            self.game_logger.info(f"--- Starting Round {round_num} of {self.num_rounds} ---")
            print(f"\n--- Starting Round {round_num} of {self.num_rounds} ---") # Keep for console output
            for player in self.players:
                await self._execute_player_turn(player, round_num)
            self.game_logger.info(f"--- Round {round_num} Complete ---")
            print(f"--- Round {round_num} Complete ---") # Keep for console output

        self.game_logger.info("===================== GAME OVER ======================")
        print("\n===================== GAME OVER ======================") # Keep for console output

    async def _send_initial_messages(self):
        """Sends the initial game rules and character/world info to all players."""
        self.game_logger.info("Sending initial game rules and world state to all players...")
        print("\nSending initial game rules and world state to all players...") # Keep for console output
        
        # Include the full manual content in the system prompt for the LLM
        system_prompt = f"You are a player in a text-based adventure game. Below is the game manual. Read it carefully to understand the rules, your role, and how to interact with the game world.\n\n" \
                        f"--- GAME MANUAL START ---\n{self.manual_content}\n--- GAME MANUAL END ---\n\n" \
                        f"Now, based on the manual and your character, respond with your actions."

        for player in self.players:
            player_char = player.character
            if not player_char:
                self.game_logger.error(f"Player {player.name} has no assigned character. Skipping initial message.")
                continue

            # Character Assignment and Motive
            character_assignment = f"You are {player_char.name}, a {self.game_character_types[player_char.id.replace('_instance','')].name}.\nYour motive is: {player_char.motive}"

            # Room Description and Objects
            current_room = self.rooms.get(player_char.current_room_id)
            if not current_room:
                self.game_logger.error(f"Character {player_char.name} is in an unknown room: {player_char.current_room_id}. Skipping initial message.")
                continue

            room_description_parts = [current_room.description]
            if current_room.objects:
                object_names = [obj.name for obj in current_room.objects.values()]
                room_description_parts.append(f"You also see: {', '.join(object_names)}.")
            
            # Visible exits
            if current_room.exits:
                exit_names = [exit_data['name'] for exit_data in current_room.exits.values() if not exit_data.get('is_hidden', False)]
                if exit_names:
                    room_description_parts.append(f"Exits: {', '.join(exit_names)}.")

            initial_observations = " ".join(room_description_parts)

            # Available Actions (simplified for now)
            available_action_names = [action.name for action in self.game_actions.values()]
            sample_actions = f"Available actions: {', '.join(available_action_names)}. (Costs {player_char.action_points} AP per turn.)"
            
            # Construct the first HumanMessage with character, motive, and observations
            first_human_message_content = (
                f"{character_assignment}\n\n"
                f"Observations: {initial_observations}\n\n"
                f"{sample_actions}\n\n"
                f"What do you do?"
            )

            system_msg = SystemMessage(content=system_prompt)
            human_msg = HumanMessage(content=first_human_message_content)

            messages_for_llm = [system_msg, human_msg]

            player.add_message(system_msg)
            player.add_message(human_msg)
            # Log a placeholder for the manual in GM and game logs
            self.game_logger.info(f"SYSTEM (with manual: {self.manual_path}): {system_prompt[:50]}...")
            self.game_logger.info(f"GM to {player.name} (SYSTEM, with manual: {self.manual_path}): {system_prompt[:50]}...")

            player.logger.info(f"SYSTEM: {system_prompt}") # Player's log gets full manual
            player.logger.info(f"GM: {first_human_message_content}") # Player's log gets full first message
            self.game_logger.info(f"GM to {player.name}: {first_human_message_content}")

            start_time = time.time()
            response = await player.get_response_and_update_history(messages_for_llm)
            duration = time.time() - start_time
            response_len = len(response.content)

            print(f"    '{player.name}' initial response in {duration:.2f}s ({response_len} chars).")
            self.game_logger.info(f"{player.name}: {response.content}")
            player.logger.info(f"{player.name}: {response.content}")

    def _check_requirements(self, player_char: PlayerCharacter, action_config: ActionConfig, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Checks if all requirements for an action are met."""
        current_room = self.rooms.get(player_char.current_room_id)
        if not current_room:
            return False, f"Character is in an unknown room: {player_char.current_room_id}."

        for req in action_config.requirements:
            if req.type == "player_has_tag":
                if not player_char.has_tag(req.tag):
                    return False, f"Player does not have tag '{req.tag}'."
            elif req.type == "object_in_room":
                object_name = params.get(req.object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{req.object_name_param}' for object_in_room requirement."
                
                obj_found = False
                for obj in current_room.objects.values():
                    if obj.name.lower() == object_name.lower():
                        obj_found = True
                        break
                if not obj_found:
                    return False, f"Object '{object_name}' not in room."
            elif req.type == "object_property_equals":
                object_name = params.get(req.object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{req.object_name_param}' for object_property_equals requirement."
                
                obj_found = player_char.get_item_in_inventory(object_name) # Check inventory first
                if not obj_found:
                    # Then check if it's in the current room
                    obj_found = current_room.get_object(object_name)

                if not obj_found:
                    return False, f"Object '{object_name}' not found for property check."
                
                if obj_found.get_property(req.property) != req.value:
                    return False, f"Object '{object_name}' property '{req.property}' is not '{req.value}'."
            elif req.type == "player_has_object_in_inventory":
                object_name = params.get(req.object_name_param)
                if not object_name:
                    return False, f"Missing parameter '{req.object_name_param}' for player_has_object_in_inventory requirement."
                if not player_char.has_item_in_inventory(object_name):
                    return False, f"Player does not have '{object_name}' in inventory."
            elif req.type == "exit_exists":
                direction = params.get(req.direction_param)
                if not direction:
                    return False, f"Missing parameter '{req.direction_param}' for exit_exists requirement."
                
                exit_data = current_room.exits.get(direction.lower())
                if not exit_data or exit_data.get('is_hidden', False):
                    return False, f"No visible exit in the '{direction}' direction."
            # Add other requirement types here
            else:
                self.game_logger.warning(f"Unsupported requirement type: {req.type}")
                return False, f"Unsupported requirement type: {req.type}"
        
        return True, ""

    def _execute_effects(self, player_char: PlayerCharacter, action_config: ActionConfig, params: Dict[str, Any]) -> str:
        """Applies the effects of an action to the game state and generates feedback/events."""
        feedback_messages: List[str] = []
        events_generated: List[Dict[str, Any]] = []

        current_room = self.rooms.get(player_char.current_room_id)
        if not current_room:
            return f"Error: Character is in an unknown room: {player_char.current_room_id}."

        for effect in action_config.effects:
            if effect.type == "add_tag":
                target_obj = None
                if effect.target == "player":
                    player_char.add_tag(effect.tag)
                    feedback_messages.append(f"You gain the tag: '{effect.tag}'.")
                elif effect.target == "object" and effect.object_name_param:
                    object_name = params.get(effect.object_name_param)
                    target_obj = player_char.get_item_in_inventory(object_name) or current_room.get_object(object_name)
                    if target_obj:
                        target_obj.add_tag(effect.tag)
                        feedback_messages.append(f"The {target_obj.name} gains the tag: '{effect.tag}'.")
                # Add other targets (room, other players) later
                
            elif effect.type == "remove_tag":
                target_obj = None
                if effect.target == "player":
                    player_char.remove_tag(effect.tag)
                    feedback_messages.append(f"You lose the tag: '{effect.tag}'.")
                elif effect.target == "object" and effect.object_name_param:
                    object_name = params.get(effect.object_name_param)
                    target_obj = player_char.get_item_in_inventory(object_name) or current_room.get_object(object_name)
                    if target_obj:
                        target_obj.remove_tag(effect.tag)
                        feedback_messages.append(f"The {target_obj.name} loses the tag: '{effect.tag}'.")
            
            elif effect.type == "set_object_property":
                object_name = params.get(effect.object_name_param)
                if object_name and effect.property is not None and effect.value is not None:
                    target_obj = player_char.get_item_in_inventory(object_name) or current_room.get_object(object_name)
                    if target_obj:
                        target_obj.set_property(effect.property, effect.value)
                        feedback_messages.append(f"The {target_obj.name}'s {effect.property} is now '{effect.value}'.")
                    else:
                        self.game_logger.warning(f"Object '{object_name}' not found for property setting.")

            elif effect.type == "move_object":
                object_name = params.get(effect.object_name_param)
                if object_name:
                    obj_to_move = None
                    if player_char.has_item_in_inventory(object_name):
                        obj_to_move = player_char.remove_item_from_inventory(object_name)
                    else: # Assume it's in the current room
                        obj_to_move = current_room.remove_object(object_name)
                    
                    if obj_to_move:
                        if effect.destination_type == "player_inventory":
                            player_char.add_item_to_inventory(obj_to_move)
                            feedback_messages.append(f"You pick up the {obj_to_move.name}.")
                        elif effect.destination_type == "room" and effect.destination_id:
                            destination_room = self.rooms.get(effect.destination_id)
                            if destination_room:
                                destination_room.add_object(obj_to_move)
                                feedback_messages.append(f"You move the {obj_to_move.name} to {destination_room.name}.")
                            else:
                                self.game_logger.warning(f"Destination room '{effect.destination_id}' not found for move_object effect.")
                                # If destination not found, put it back where it came from
                                if obj_to_move.current_location_id == player_char.id:
                                    player_char.add_item_to_inventory(obj_to_move)
                                else:
                                    current_room.add_object(obj_to_move)
                        else:
                            self.game_logger.warning(f"Unsupported destination type '{effect.destination_type}' or missing destination_id for move_object effect.")
                    else:
                        self.game_logger.warning(f"Object '{object_name}' not found for move_object effect.")

            elif effect.type == "generate_event":
                # Events will be processed for observability later
                event_message = effect.message.format(**params, player_name=player_char.name) # Add player_name to params for formatting
                events_generated.append({"message": event_message, "observers": effect.observers, "source_room": player_char.current_room_id})
                feedback_messages.append(event_message) # Player sees their own immediate events

            elif effect.type == "move_player":
                direction = params.get(effect.direction_param)
                if direction:
                    exit_data = current_room.exits.get(direction.lower())
                    if exit_data and not exit_data.get('is_hidden', False):
                        destination_room_id = exit_data['destination_room_id']
                        player_char.current_room_id = destination_room_id
                        feedback_messages.append(f"You move to the '{self.rooms[destination_room_id].name}'.")
                    else:
                        self.game_logger.warning(f"Cannot move '{player_char.name}' in direction '{direction}'. Exit not found or hidden.")
                else:
                    self.game_logger.warning(f"Missing direction parameter for move_player effect for {player_char.name}.")

            # Add other effect types here (e.g., deal_damage, tele_port)
            else:
                self.game_logger.warning(f"Unsupported effect type: {effect.type}")

        # TODO: Process events_generated for observability and distribute to relevant players

        return ". ".join(feedback_messages)

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

            # Dynamically generate current observations and action prompt for each iteration
            room_description_parts = [current_room.description]
            if current_room.objects:
                object_names = [obj.name for obj in current_room.objects.values()]
                room_description_parts.append(f"You also see: {', '.join(object_names)}.")
            if current_room.exits:
                exit_names = [exit_data['name'] for exit_data in current_room.exits.values() if not exit_data.get('is_hidden', False)]
                if exit_names:
                    room_description_parts.append(f"Exits: {', '.join(exit_names)}.")
            current_observations = " ".join(room_description_parts)

            available_action_names = [action.name for action in self.game_actions.values()]
            action_prompt = f"Available actions: {', '.join(available_action_names)}. (You have {player_char.action_points} AP remaining.)"

            gm_message_content = (
                f"Current situation: {current_observations}\n\n"
                f"{action_prompt}\n\n"
                f"What do you do? (You can also type 'end turn' to finish.)"
            )
            
            gm_message = HumanMessage(content=gm_message_content)
            player.add_message(gm_message)
            player.logger.info(f"GM: {gm_message_content}")
            self.game_logger.info(f"GM to {player.name}: {gm_message_content}")

            start_time = time.time()
            response = await player.get_response_and_update_history(player.chat_history)
            duration = time.time() - start_time
            response_len = len(response.content)

            player_input = response.content.strip().lower()
            self.game_logger.info(f"{player.name}: {player_input}")
            player.logger.info(f"{player.name}: {player_input}")
            print(f"    '{player.name}' responded in {duration:.2f}s ({response_len} chars): {player_input}")

            # Check for explicit "end turn" command first
            if player_input == "end turn":
                feedback = "You decide to end your turn."
                turn_in_progress = False
                feedback_message = HumanMessage(content=feedback)
                player.add_message(feedback_message)
                player.logger.info(f"GM (Feedback): {feedback}")
                self.game_logger.info(f"GM to {player.name} (Feedback): {feedback}")
                continue # Continue to the while loop condition to end the turn

            # Parse all actions from the player's response
            parsed_actions = parse_player_response(response.content, self.game_actions)

            if not parsed_actions:
                # Penalty for not providing any valid actions
                feedback = "You did not provide any valid actions. Your turn ends prematurely as a penalty."
                player_char.action_points = 0 # End turn as penalty
                turn_in_progress = False
                self.game_logger.info(f"{player.name} failed to provide valid actions. Turn ended.")

                feedback_message = HumanMessage(content=feedback)
                player.add_message(feedback_message)
                player.logger.info(f"GM (Feedback): {feedback}")
                self.game_logger.info(f"GM to {player.name} (Feedback): {feedback}")
                continue # Continue to the while loop condition to end the turn

            else:
                all_actions_in_response_valid = True # Tracks if all actions in this specific response were valid and processed
                response_feedback_messages = [] # Collect feedback for this response

                for action_config, params in parsed_actions:
                    action_feedback = ""
                    if player_char.action_points <= 0:
                        action_feedback = "You have run out of Action Points for this turn. Cannot perform further actions."
                        all_actions_in_response_valid = False # No more actions can be processed
                        break # Exit inner loop for actions

                    if action_config.cost > player_char.action_points:
                        action_feedback = f"Action '{action_config.name}' costs {action_config.cost} AP, but you only have {player_char.action_points} AP. Skipping this action."
                        self.game_logger.info(action_feedback)
                        all_actions_in_response_valid = False
                    else:
                        requirements_met, req_message = self._check_requirements(player_char, action_config, params)
                        if requirements_met:
                            player_char.action_points -= action_config.cost
                            action_feedback = self._execute_effects(player_char, action_config, params)
                            self.game_logger.info(f"Action '{action_config.name}' executed. Remaining AP: {player_char.action_points}")
                            self.game_logger.info(f"Action '{action_config.name}' executed by {player_char.name}. Remaining AP: {player_char.action_points}")
                        else:
                            action_feedback = f"Cannot perform '{action_config.name}': {req_message}. Skipping this action."
                            self.game_logger.info(action_feedback)
                            all_actions_in_response_valid = False

                    response_feedback_messages.append(action_feedback)

                # After processing all actions in the response
                combined_feedback = ". ".join(response_feedback_messages)

                feedback_message = HumanMessage(content=combined_feedback)
                player.add_message(feedback_message)
                player.logger.info(f"GM (Feedback): {combined_feedback}")
                self.game_logger.info(f"GM to {player.name} (Feedback): {combined_feedback}")

                if not all_actions_in_response_valid:
                    # If any action in the response was invalid or couldn't be performed, end the turn as a penalty.
                    feedback = "One or more actions in your response were invalid or could not be performed. Your turn ends prematurely as a penalty."
                    player_char.action_points = 0 # End turn as penalty
                    turn_in_progress = False
                    self.game_logger.info(f"{player.name} had invalid/unexecutable actions in response. Turn ended.")

                    # Send final penalty feedback
                    feedback_message = HumanMessage(content=feedback)
                    player.add_message(feedback_message)
                    player.logger.info(f"GM (Feedback): {feedback}")
                    self.game_logger.info(f"GM to {player.name} (Feedback): {feedback}")
                    
                elif player_char.action_points <= 0:
                    # If all actions were valid but AP ran out, turn ends naturally.
                    feedback = "You have used all your Action Points for this turn. Your turn has ended."
                    turn_in_progress = False
                    self.game_logger.info(f"{player.name} used all AP. Turn ended.")

                    # Send final AP exhaustion feedback
                    feedback_message = HumanMessage(content=feedback)
                    player.add_message(feedback_message)
                    player.logger.info(f"GM (Feedback): {feedback}")
                    self.game_logger.info(f"GM to {player.name} (Feedback): {feedback}")
                    
                # If all actions were valid and AP remain, the loop continues automatically to re-prompt.

            self.game_logger.info(f"<<< {player.name}'s turn ended. Remaining AP: {player_char.action_points}")
            print(f"<<< {player.name}'s turn ended. Remaining AP: {player_char.action_points}")

    def _setup_game_world(self, theme_cfg: ThemeConfig, edition_cfg: EditionConfig):
        """Sets up the initial game world by merging configs and instantiating objects."""
        self.game_logger.info("Setting up game world...")

        # 1. Merge Object Types
        self.game_object_types.update(theme_cfg.object_types)
        self.game_object_types.update(edition_cfg.objects) # Edition objects can override or add to theme object types
        self.game_logger.info(f"Merged {len(self.game_object_types)} object types.")

        # 2. Merge Actions
        self.game_actions.update(theme_cfg.actions)
        # self.game_actions.update(edition_cfg.actions) # Edition actions can override or add
        self.game_logger.info(f"Merged {len(self.game_actions)} actions.")

        # 3. Merge Character Types
        self.game_character_types.update(theme_cfg.character_types)
        self.game_character_types.update(edition_cfg.characters) # Edition characters can override or add
        self.game_logger.info(f"Merged {len(self.game_character_types)} character types.")

        # 4. Instantiate Rooms
        for room_id, room_cfg in edition_cfg.rooms.items():
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
            for obj_id, obj_instance_cfg in room_cfg.objects.items():
                obj_type = self.game_object_types.get(obj_instance_cfg.object_type_id)
                if obj_type:
                    # Merge object instance config with object type config
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

        # 5. Instantiate Global Objects (from edition_cfg.objects not explicitly placed in rooms)
        for obj_id, obj_instance_cfg in edition_cfg.objects.items():
            # Only create if not already placed in a room above
            if obj_id not in self.game_objects:
                obj_type = self.game_object_types.get(obj_instance_cfg.object_type_id)
                if obj_type:
                    final_tags = set(obj_type.tags).union(obj_instance_cfg.tags)
                    final_properties = {**obj_type.properties, **obj_instance_cfg.properties}

                    game_obj = GameObject(
                        obj_id=obj_instance_cfg.id,
                        name=obj_instance_cfg.name or obj_type.name,
                        description=obj_instance_cfg.description or obj_type.description,
                        current_location_id="world_spawn", # A default location if not specified
                        tags=list(final_tags),
                        properties=final_properties
                    )
                    self.game_objects[game_obj.id] = game_obj
                    self.game_logger.info(f"  - Created global object: {game_obj.name} ({game_obj.id}) at {game_obj.current_location_id}")
                else:
                    self.game_logger.warning(f"Object type '{obj_instance_cfg.object_type_id}' not found for global object '{obj_instance_cfg.id}'. Skipping.")

        # 6. Instantiate Player Characters and link to Players
        available_character_ids = list(edition_cfg.characters.keys())
        if not available_character_ids:
            self.game_logger.error("No character types defined in edition configuration. Cannot assign characters to players.")
            return
        
        # Assign characters to players in a round-robin fashion for now
        for i, player in enumerate(self.players):
            char_id_to_assign = available_character_ids[i % len(available_character_ids)]
            char_cfg = edition_cfg.characters[char_id_to_assign]
            
            # Find a suitable starting room (e.g., the first room defined in the edition)
            start_room_id = next(iter(edition_cfg.rooms.keys()), None)
            if not start_room_id:
                self.game_logger.error(f"No rooms defined in edition configuration. Cannot assign starting room for {player.name}.")
                return

            player_char = PlayerCharacter(
                char_id=char_cfg.id + "_instance", # Make character instance ID unique
                name=char_cfg.name,
                backstory=char_cfg.backstory,
                motive=char_cfg.motive,
                current_room_id=start_room_id,
                action_points=3 # Default AP per turn for now
            )
            player.character = player_char # Link player to character
            self.player_characters[player_char.id] = player_char
            self.game_logger.info(f"  - Assigned {player_char.name} ({player_char.id}) to player {player.name} in room {start_room_id}.")

        self.game_logger.info("Game world setup complete.")

