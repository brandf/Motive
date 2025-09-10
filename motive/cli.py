#!/usr/bin/env python3
"""
Motive CLI - Command-line interface for running Motive games.
"""

import argparse
import asyncio
import logging
import os
import sys
import uuid
import yaml
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from motive.game_master import GameMaster
from motive.config import GameConfig
from motive.config_loader import load_game_config, load_and_validate_game_config


def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def load_config(config_path: str, validate: bool = True) -> GameConfig:
    """Load game configuration from file with optional validation."""
    try:
        # Check if it's a hierarchical config
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        if 'includes' in raw_config:
            # Use hierarchical config loader with validation
            base_path = str(Path(config_path).parent)
            config_file = Path(config_path).name
            return load_and_validate_game_config(config_file, base_path, validate=validate)
        else:
            # Traditional config loading
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            return GameConfig(**config_data)
        
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Check if it's a validation error
        if hasattr(e, 'validation_errors') and e.validation_errors:
            print(f"Configuration validation failed:", file=sys.stderr)
            for error in e.validation_errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)


async def run_game(config_path: str, game_id: str = None, validate: bool = True):
    """Run a Motive game with the specified configuration."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Generate game ID if not provided
    if not game_id:
        # Create a sortable game ID with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hhr_%Mmin_%Ssec")
        game_id = os.getenv("MOTIVE_GAME_ID", f"{timestamp}_{str(uuid.uuid4())[:8]}")
    
    # Load configuration
    print(f"Loading configuration from: {config_path}")
    game_config = load_config(config_path, validate=validate)
    
    # Check LangSmith configuration
    if os.getenv("LANGCHAIN_TRACING_V2") == "true":
        print("LangSmith tracing is enabled. Ensure LANGCHAIN_API_KEY is set in .env.")
    else:
        print("LangSmith tracing is disabled. Set LANGCHAIN_TRACING_V2='true' in .env to enable.")
    
    # Run the game
    try:
        gm = GameMaster(game_config=game_config, game_id=game_id)
        await gm.run_game()
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running game: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Motive - A platform for LLM benchmarking through turn-based games",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  motive                                    # Run with default config
  motive -c configs/game.yaml              # Run with specific config
  motive -c configs/game_test.yaml         # Run test configuration
  motive -c configs/game_new.yaml          # Run hierarchical config
  motive --game-id my-game-123             # Run with specific game ID
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='configs/game.yaml',
        help='Path to game configuration file (default: configs/game.yaml)'
    )
    
    parser.add_argument(
        '--game-id',
        help='Specific game ID to use (default: auto-generated)'
    )
    
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip Pydantic validation of merged configuration (for debugging)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.0.1'
    )
    
    args = parser.parse_args()
    
    # Validate config file exists
    if not Path(args.config).exists():
        print(f"Error: Configuration file '{args.config}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Run the game
    validate = not args.no_validate
    asyncio.run(run_game(args.config, args.game_id, validate=validate))


if __name__ == '__main__':
    main()
