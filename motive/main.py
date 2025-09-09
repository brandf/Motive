import asyncio
import logging
import os
import sys
import yaml
from dotenv import load_dotenv
from motive.game_master import GameMaster
from motive.llm_factory import PROVIDER_API_KEYS
from motive.config import GameConfig # Only need GameConfig now
import uuid # Import for generating unique game IDs

# Setup basic logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """
    Main function to load environment variables, configure LangSmith,
    load game configuration with Pydantic, and run the game.
    """
    load_dotenv()

    # --- LangSmith Configuration (if enabled) ---
    # These environment variables will be picked up by LangChain/LangSmith automatically
    if os.getenv("LANGCHAIN_TRACING_V2") == "true":
        print("LangSmith tracing is enabled. Ensure LANGCHAIN_API_KEY is set in .env.")
    else:
        print("LangSmith tracing is disabled. Set LANGCHAIN_TRACING_V2='true' in .env to enable.")
    # --- End LangSmith Configuration ---

    game_id = os.getenv("MOTIVE_GAME_ID", str(uuid.uuid4()))

    # Load the main configs/game.yaml file
    try:
        with open("configs/game.yaml", "r", encoding="utf-8") as f:
            main_config_data = yaml.safe_load(f)
        game_config = GameConfig(**main_config_data)
    except FileNotFoundError:
        logging.critical("Main configuration file 'configs/game.yaml' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.critical(f"Error parsing main configuration file 'configs/game.yaml': {e}")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"An unexpected error occurred while loading main configuration: {e}")
        sys.exit(1)

    # The GameMaster now handles loading individual config files via GameInitializer
    try:
        gm = GameMaster(game_config=game_config, game_id=game_id)
        await gm.run_game()
    except Exception as e:
        logging.critical(f"An unexpected error occurred during game execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure LANGCHAIN_API_KEY is set if LangSmith tracing is enabled
    if os.getenv("LANGCHAIN_TRACING_V2") == "true" and not os.getenv("LANGCHAIN_API_KEY"):
        logging.warning("LangSmith tracing is enabled. Ensure LANGCHAIN_API_KEY is set in .env.")
    asyncio.run(main())

