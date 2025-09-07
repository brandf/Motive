import random
import time
import asyncio
from motive.player import Player
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from motive.config import GameConfig, PlayerConfig # New import for Pydantic config


class GameMaster:
    # Accept a pre-validated GameConfig object directly
    def __init__(self, game_config: GameConfig):
        self.players = []
        self.num_rounds = game_config.game_settings.num_rounds
        self._initialize_players(game_config.players)

    def _initialize_players(self, player_configs: list[PlayerConfig]):
        """Initializes players based on the provided list of PlayerConfig objects."""
        print("Initializing players from configuration...")
        for p_config in player_configs:
            player = Player(
                name=p_config.name,
                provider=p_config.provider,
                model=p_config.model,
            )
            self.players.append(player)
            print(f"  - Initialized player: {player.name} using {p_config.provider}/{p_config.model}")

    async def run_game(self):
        """Main game loop."""
        print("\n==================== GAME STARTING ====================")
        await self._send_initial_messages()

        for round_num in range(1, self.num_rounds + 1):
            print(f"\n--- Starting Round {round_num} of {self.num_rounds} ---")
            for player in self.players:
                await self._execute_player_turn(player, round_num)
            print(f"--- Round {round_num} Complete ---")

        print("\n===================== GAME OVER =====================")

    async def _send_initial_messages(self):
        """Sends the initial game rules to all players."""
        print("\nSending initial game rules to all players...")
        system_prompt = "You are a player in a text-based adventure game. Respond with your actions."
        rules_message = "Welcome to the game! Here are the rules: [Placeholder for game rules]. You are in a dark room. What do you do?"

        for player in self.players:
            system_msg = SystemMessage(content=system_prompt)
            human_msg = HumanMessage(content=rules_message)

            messages_for_llm = [system_msg, human_msg]

            player.add_message(system_msg)
            player.add_message(human_msg)
            player.logger.info(f"SYSTEM: {system_prompt}")
            player.logger.info(f"GM: {rules_message}")

            start_time = time.time()
            response = await player.get_response_and_update_history(messages_for_llm)
            duration = time.time() - start_time
            response_len = len(response.content)

            print(f"    '{player.name}' initial response in {duration:.2f}s ({response_len} chars).")

            player.logger.info(f"{player.name}: {response.content}")


    async def _execute_player_turn(self, player: Player, round_num: int):
        """Executes a single player's turn, which may involve multiple messages."""
        print(f"\n>>> It is {player.name}'s turn. (Round {round_num})")
        
        num_interactions = random.randint(1, 3)
        print(f"({player.name} will have {num_interactions} interaction(s) this turn)")

        for i in range(num_interactions):
            gm_message_content = (
                f"This is interaction {i+1}/{num_interactions} of your turn. "
                f"The current state of the world is [placeholder for game state]. "
                f"What is your next action?"
            )
            
            gm_message = HumanMessage(content=gm_message_content)
            player.add_message(gm_message)
            player.logger.info(f"GM: {gm_message_content}")

            start_time = time.time()
            response = await player.get_response_and_update_history(player.chat_history)
            
            duration = time.time() - start_time
            response_len = len(response.content)

            print(f"    '{player.name}' responded in {duration:.2f}s ({response_len} chars).")

            player.logger.info(f"{player.name}: {response.content}")

