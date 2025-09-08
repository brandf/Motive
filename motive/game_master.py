import random
import time
import asyncio
import os
import logging
from motive.player import Player
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from motive.config import GameConfig, PlayerConfig # New import for Pydantic config


class GameMaster:
    # Accept a pre-validated GameConfig object directly
    def __init__(self, game_config: GameConfig, game_id: str):
        self.players = []
        self.num_rounds = game_config.game_settings.num_rounds
        self.game_id = game_id
        self.theme = game_config.game_settings.theme
        self.edition = game_config.game_settings.edition
        self.manual_path = game_config.game_settings.manual
        self.log_dir = self._setup_logging()
        self.manual_content = self._load_manual_content()
        self._initialize_players(game_config.players)

    def _load_manual_content(self) -> str:
        """Loads the content of the game manual from the specified path."""
        try:
            with open(self.manual_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.gm_logger.info(f"Loaded game manual from {self.manual_path}")
            return content
        except FileNotFoundError:
            self.gm_logger.error(f"Game manual file not found: {self.manual_path}")
            return ""
        except Exception as e:
            self.gm_logger.error(f"Error loading game manual from {self.manual_path}: {e}")
            return ""

    def _setup_logging(self):
        """Sets up the logging directory and configures the GM logger."""
        base_log_dir = "logs"
        game_log_dir = os.path.join(base_log_dir, self.theme, self.edition, self.game_id)
        os.makedirs(game_log_dir, exist_ok=True)

        # Configure GM logger
        self.gm_logger = logging.getLogger("GameMasterInternal")
        self.gm_logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to prevent duplicate logs
        if self.gm_logger.handlers:
            for handler in self.gm_logger.handlers:
                self.gm_logger.removeHandler(handler)

        gm_log_file = os.path.join(game_log_dir, "gm_log.log")
        gm_file_handler = logging.FileHandler(gm_log_file)
        gm_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        gm_file_handler.setFormatter(gm_formatter)
        self.gm_logger.addHandler(gm_file_handler)
        self.gm_logger.info(f"GameMaster internal logging to {gm_log_file}")
        
        # Configure Game logger for the combined game narrative
        self.game_logger = logging.getLogger("GameNarrative")
        self.game_logger.setLevel(logging.INFO)

        if self.game_logger.handlers:
            for handler in self.game_logger.handlers:
                self.game_logger.removeHandler(handler)

        game_narrative_file = os.path.join(game_log_dir, "game.log")
        game_file_handler = logging.FileHandler(game_narrative_file)
        game_formatter = logging.Formatter('%(asctime)s - %(message)s') # Simpler format for narrative
        game_file_handler.setFormatter(game_formatter)
        self.game_logger.addHandler(game_file_handler)
        self.gm_logger.info(f"Game narrative logging to {game_narrative_file}")
        
        return game_log_dir

    def _initialize_players(self, player_configs: list[PlayerConfig]):
        """Initializes players based on the provided list of PlayerConfig objects."""
        self.gm_logger.info("Initializing players from configuration...")
        for p_config in player_configs:
            player = Player(
                name=p_config.name,
                provider=p_config.provider,
                model=p_config.model,
                log_dir=self.log_dir  # Pass the log directory to the player
            )
            self.players.append(player)
            self.gm_logger.info(f"  - Initialized player: {player.name} using {p_config.provider}/{p_config.model}")

    async def run_game(self):
        """Main game loop."""
        self.game_logger.info("==================== GAME STARTING ====================")
        self.gm_logger.info("==================== GAME STARTING ====================") # Internal GM log
        print("\n==================== GAME STARTING ====================") # Keep for console output

        await self._send_initial_messages()

        for round_num in range(1, self.num_rounds + 1):
            self.game_logger.info(f"--- Starting Round {round_num} of {self.num_rounds} ---")
            self.gm_logger.info(f"--- Starting Round {round_num} of {self.num_rounds} ---") # Internal GM log
            print(f"\n--- Starting Round {round_num} of {self.num_rounds} ---") # Keep for console output
            for player in self.players:
                await self._execute_player_turn(player, round_num)
            self.game_logger.info(f"--- Round {round_num} Complete ---")
            self.gm_logger.info(f"--- Round {round_num} Complete ---") # Internal GM log
            print(f"--- Round {round_num} Complete ---") # Keep for console output

        self.game_logger.info("===================== GAME OVER ======================")
        self.gm_logger.info("===================== GAME OVER ======================") # Internal GM log
        print("\n===================== GAME OVER ======================") # Keep for console output

    async def _send_initial_messages(self):
        """Sends the initial game rules to all players."""
        self.game_logger.info("Sending initial game rules to all players...")
        print("\nSending initial game rules to all players...") # Keep for console output
        # Include the full manual content in the system prompt for the LLM
        system_prompt = f"You are a player in a text-based adventure game. Below is the game manual. Read it carefully to understand the rules, your role, and how to interact with the game world.\n\n" \
                        f"--- GAME MANUAL START ---\n{self.manual_content}\n--- GAME MANUAL END ---\n\n" \
                        f"Now, based on the manual and your character, respond with your actions."

        for player in self.players:
            # Hardcoded character/motive and initial observations for the first round
            character_assignment = f"You are {player.name}, a Brave Knight.\nYour motive is to find the Dragon's Hoard and escape the dungeon."
            initial_observations = "You are in a dimly lit antechamber. There is a rusty iron door to the north and a flickering torch on the wall."
            sample_actions = "Available actions (examples): 'look', 'move <direction>', 'help' (0 AP)."
            
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
            self.gm_logger.info(f"SYSTEM (with manual: {self.manual_path}): {system_prompt[:50]}...")
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


    async def _execute_player_turn(self, player: Player, round_num: int):
        """Executes a single player's turn, which may involve multiple messages."""
        self.game_logger.info(f">>> It is {player.name}'s turn. (Round {round_num})")
        print(f"\n>>> It is {player.name}'s turn. (Round {round_num})") # Keep for console output
        
        num_interactions = random.randint(1, 3)
        self.game_logger.info(f"({player.name} will have {num_interactions} interaction(s) this turn)")
        print(f"({player.name} will have {num_interactions} interaction(s) this turn)") # Keep for console output

        for i in range(num_interactions):
            gm_message_content = (
                f"This is interaction {i+1}/{num_interactions} of your turn. "
                f"The current state of the world is [placeholder for game state]. "
                f"What is your next action?"
            )
            
            gm_message = HumanMessage(content=gm_message_content)
            player.add_message(gm_message)
            player.logger.info(f"GM: {gm_message_content}")
            self.game_logger.info(f"GM to {player.name}: {gm_message_content}")

            start_time = time.time()
            response = await player.get_response_and_update_history(player.chat_history)
            
            duration = time.time() - start_time
            response_len = len(response.content)

            print(f"    '{player.name}' responded in {duration:.2f}s ({response_len} chars).")
            self.game_logger.info(f"{player.name}: {response.content}")
            player.logger.info(f"{player.name}: {response.content}")

