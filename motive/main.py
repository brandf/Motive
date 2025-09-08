import os
import asyncio
import yaml
from dotenv import load_dotenv
from motive.game_master import GameMaster
from motive.llm_factory import PROVIDER_API_KEYS
from motive.config import GameConfig # New import for Pydantic config
import uuid # Import for generating unique game IDs


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


    # --- Load & Validate Game Configuration with Pydantic ---
    print("\nLoading and validating game configuration...")
    game_config: GameConfig
    try:
        with open("config.yaml", "r") as f:
            raw_config = yaml.safe_load(f)
        game_config = GameConfig(**raw_config) # Validate with Pydantic
        print("Game configuration loaded and validated successfully.")
    except FileNotFoundError:
        print("Error: config.yaml not found. Please ensure the file exists.")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        return
    except Exception as e: # Catch Pydantic validation errors
        print(f"Error validating config.yaml with Pydantic: {e}")
        return
    # --- End Pydantic Config Loading ---


    # --- Dynamic API Key Validation ---
    used_providers = {player.provider for player in game_config.players} # Use Pydantic object
    
    missing_keys = []
    for provider in used_providers:
        env_var_name = PROVIDER_API_KEYS.get(provider)
        if env_var_name and not os.getenv(env_var_name):
            missing_keys.append(env_var_name)
        elif not env_var_name:
            print(f"Warning: No API key environment variable defined in llm_factory.py for provider '{provider}'. "
                  "Assuming it does not require an explicit environment variable or will be handled internally by LangChain.")

    if missing_keys:
        print("\nError: The following API keys are missing from your .env file or environment variables:")
        for key in missing_keys:
            print(f" - {key}")
        print("Please ensure they are set for the providers specified in config.yaml.")
        return
    # --- End Dynamic API Key Validation ---

    # Generate a unique game ID
    game_id = str(uuid.uuid4())
    print(f"\nStarting game session: {game_id}")

    try:
        # Pass the validated GameConfig object directly
        gm = GameMaster(game_config=game_config, game_id=game_id) 
        await gm.run_game()
    except Exception as e:
        print(f"An unexpected error occurred during game execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

