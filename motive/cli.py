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
import subprocess
import threading
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv
from motive.game_master import GameMaster
# v1 config imports removed - v1 is DEAD
from motive.sim_v2.config_loader import V2ConfigLoader


class GameStatus(Enum):
    """Status of a parallel game instance."""
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GameProgress:
    """Progress information for a parallel game."""
    game_id: str
    status: GameStatus
    current_round: int = 0
    total_rounds: int = 0
    current_player: int = 0
    total_players: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    log_file: Optional[str] = None
    last_output_time: Optional[datetime] = None  # Track when we last received output
    completed_turns: int = 0  # Track completed turns for progress calculation
    current_turn_in_round: int = 0  # Track current turn within the current round


class ParallelGameRunner:
    """Manages multiple parallel game instances with progress monitoring."""
    
    def __init__(self, num_games: int, config_path: str, **game_args):
        self.num_games = num_games
        self.config_path = config_path
        self.game_args = game_args
        self.games: Dict[str, GameProgress] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.monitor_threads: Dict[str, threading.Thread] = {}
        self.running = True
        
        # Load config for progress tracking
        try:
            self._config_cache = load_config(config_path, validate=False)
        except Exception:
            self._config_cache = None
        
    def start_games(self):
        """Start all parallel game instances."""
        print(f"🚀 Starting {self.num_games} parallel games...")
        
        # Get base game ID from args, or generate one
        base_game_id = self.game_args.get('game_id')
        if not base_game_id:
            base_game_id = f"parallel_{uuid.uuid4().hex[:8]}"
        
        for i in range(self.num_games):
            # Create unique game ID for each parallel game
            if self.num_games == 1:
                game_id = base_game_id
            else:
                game_id = f"{base_game_id}_worker_{i+1}"
                
            self.games[game_id] = GameProgress(
                game_id=game_id,
                status=GameStatus.STARTING,
                start_time=datetime.now()
            )
            
            # Start the game process
            self._start_single_game(game_id)
            
        print(f"✅ Started {self.num_games} games")
    
    def _start_single_game(self, game_id: str):
        """Start a single game process."""
        # Use absolute path for config to ensure worker processes can find it
        import os
        abs_config_path = os.path.abspath(self.config_path)
        
        # Use the motive command directly with --worker flag for cleaner output
        cmd = ["motive", "-c", abs_config_path, "--game-id", game_id, "--worker"]
        
        # Add game arguments
        if self.game_args.get('rounds'):
            cmd.extend(["--rounds", str(self.game_args['rounds'])])
        if self.game_args.get('ap'):
            cmd.extend(["--ap", str(self.game_args['ap'])])
        if self.game_args.get('players'):
            cmd.extend(["--players", str(self.game_args['players'])])
        if self.game_args.get('hint'):
            cmd.extend(["--hint", self.game_args['hint']])
        if self.game_args.get('hint_character'):
            cmd.extend(["--hint-character", self.game_args['hint_character']])
        if self.game_args.get('character'):
            cmd.extend(["--character", self.game_args['character']])
        if self.game_args.get('deterministic'):
            cmd.append("--deterministic")
        if self.game_args.get('manual'):
            cmd.extend(["--manual", self.game_args['manual']])
        if self.game_args.get('no_validate'):
            cmd.append("--no-validate")
        if self.game_args.get('log_dir'):
            cmd.extend(["--log-dir", self.game_args['log_dir']])
        if self.game_args.get('no_file_logging'):
            cmd.append("--no-file-logging")
            
        try:
            # Set environment variables for unbuffered output
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            self.processes[game_id] = process
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_game,
                args=(game_id, process),
                daemon=True
            )
            monitor_thread.start()
            self.monitor_threads[game_id] = monitor_thread
            
        except Exception as e:
            self.games[game_id].status = GameStatus.FAILED
            self.games[game_id].error_message = str(e)
    
    def _monitor_game(self, game_id: str, process: subprocess.Popen):
        """Monitor a single game process and parse its output."""
        game = self.games[game_id]
        game.status = GameStatus.RUNNING
        
        def read_stdout():
            """Read from stdout in a separate thread."""
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        # Update last output time
                        game.last_output_time = datetime.now()
                        self._parse_game_output(game_id, line)
            except Exception as e:
                print(f"Error reading stdout for {game_id}: {e}")
        
        def read_stderr():
            """Read from stderr in a separate thread."""
            try:
                for line in iter(process.stderr.readline, ''):
                    if line:
                        # Store stderr for debugging
                        if not hasattr(game, 'stderr_output'):
                            game.stderr_output = []
                        game.stderr_output.append(line.strip())
                        
                        # Check for common error patterns
                        if "api_key" in line.lower() or "authentication" in line.lower():
                            game.status = GameStatus.FAILED
                            game.error_message = "API authentication error"
                        elif "error" in line.lower() and "exception" in line.lower():
                            game.status = GameStatus.FAILED
                            game.error_message = f"Error: {line.strip()}"
            except Exception as e:
                print(f"Error reading stderr for {game_id}: {e}")
        
        try:
            # Start threads to read stdout and stderr
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            
            stdout_thread.start()
            stderr_thread.start()
            
            start_time = time.time()
            hang_timeout_seconds = 120  # Increased timeout for LLM processing  # 30 seconds without output = hang
            
            while True:
                if not self.running:
                    break
                    
                # Check if process is still running
                if process.poll() is not None:
                    break
                
                # Check for hang based on last output time
                if game.last_output_time:
                    time_since_output = (datetime.now() - game.last_output_time).total_seconds()
                    if time_since_output > hang_timeout_seconds:
                        game.status = GameStatus.FAILED
                        game.error_message = f"Worker process hung - no output for {hang_timeout_seconds}s"
                        print(f"\n⚠️  Game {game_id} appears to have hung - no output for {hang_timeout_seconds}s")
                        break
                elif time.time() - start_time > 60:  # Initial startup timeout
                    game.status = GameStatus.FAILED
                    game.error_message = f"Worker process failed to start within 60s"
                    break
                
                # Small delay to prevent busy waiting
                time.sleep(0.1)
                
        except Exception as e:
            game.status = GameStatus.FAILED
            game.error_message = str(e)
        finally:
            # Wait for process to complete
            process.wait()
            if game.status == GameStatus.RUNNING:
                if process.returncode == 0:
                    game.status = GameStatus.COMPLETED
                else:
                    game.status = GameStatus.FAILED
                    if hasattr(game, 'stderr_output') and game.stderr_output:
                        # Use the last stderr line as error message
                        game.error_message = f"Process exited with code {process.returncode}: {game.stderr_output[-1]}"
                    else:
                        game.error_message = f"Process exited with code {process.returncode}"
            game.end_time = datetime.now()
    
    def _parse_game_output(self, game_id: str, line: str):
        """Parse game output to extract progress information."""
        game = self.games[game_id]
        
        # Update last output time for hang detection
        game.last_output_time = datetime.now()
        
        # Debug: Print raw worker output (uncomment for debugging)
        # print(f"DEBUG {game_id}: {line.strip()}")
        
        # Parse structured worker messages
        if line.startswith("WORKER_"):
            if line.startswith("WORKER_START:"):
                game.status = GameStatus.RUNNING
            elif line.startswith("WORKER_ROUNDS:"):
                game.total_rounds = int(line.split(":")[1].strip())
            elif line.startswith("WORKER_PLAYERS:"):
                game.total_players = int(line.split(":")[1].strip())
            elif line.startswith("WORKER_ROUND_START:"):
                game.current_round = int(line.split(":")[1].strip())
                game.current_turn_in_round = 0  # Reset turn counter for new round
            elif line.startswith("WORKER_PLAYER_TURN:"):
                player_name = line.split(":")[1].strip()
                # Extract player number from name like "Player_1" -> 1
                try:
                    if "_" in player_name:
                        game.current_player = int(player_name.split("_")[-1])
                    else:
                        game.current_player = 1
                except (ValueError, IndexError):
                    game.current_player = 1
                # Increment turn counter for current round
                game.current_turn_in_round += 1
            elif line.startswith("WORKER_TURN_COMPLETE:"):
                # Increment completed turns when a turn actually completes
                game.completed_turns += 1
            elif line.startswith("WORKER_ROUND_END:"):
                # Round completed, reset turn counter
                game.current_turn_in_round = 0
            elif line.startswith("WORKER_GAME_END:"):
                game.status = GameStatus.COMPLETED
                game.end_time = datetime.now()
                # Reset round and turn counters when game ends
                game.current_round = 0
                game.current_turn_in_round = 0
            return
        
        # Fallback to parsing regular game output (for non-worker mode)
        # Look for log file information - handle both Windows and Unix paths
        if "Game narrative logging to" in line and "and stdout" in line:
            # Extract log file path from lines like "Game narrative logging to logs/game_12345.log and stdout."
            try:
                # Find the log file path between "to " and " and"
                start_idx = line.find("to ") + 3
                end_idx = line.find(" and")
                if start_idx > 2 and end_idx > start_idx:
                    log_path = line[start_idx:end_idx].strip()
                    game.log_file = log_path
            except (ValueError, IndexError):
                pass
        
        # Look for game initialization info
        if "Game initialized" in line or "Starting game" in line or "GAME STARTING" in line:
            # Set total rounds and players from config
            if self._config_cache:
                if hasattr(self._config_cache, 'game_settings'):
                    game.total_rounds = getattr(self._config_cache.game_settings, 'num_rounds', 0)
                if hasattr(self._config_cache, 'players'):
                    game.total_players = len(self._config_cache.players)
        
        # Look for round information - be more flexible with patterns
        if "Round" in line:
            try:
                # Look for patterns like "🎯 Round 2 of 3" or "Round 2 starting" or "Round 2 begins"
                import re
                # Match "Round X of Y" or "Round X" patterns
                round_match = re.search(r'Round\s+(\d+)(?:\s+of\s+(\d+))?', line, re.IGNORECASE)
                if round_match:
                    game.current_round = int(round_match.group(1))
                    if round_match.group(2):  # If "of Y" is present, update total rounds
                        game.total_rounds = int(round_match.group(2))
            except (ValueError, IndexError, AttributeError):
                pass
        
        # Look for player information - be more flexible
        if "Player" in line and ("turn" in line.lower() or "starting" in line.lower() or "begins" in line.lower() or ">>>" in line):
            try:
                import re
                # Match "Player X" patterns
                player_match = re.search(r'Player\s+(\d+)', line, re.IGNORECASE)
                if player_match:
                    game.current_player = int(player_match.group(1))
            except (ValueError, IndexError, AttributeError):
                pass
        
        # Look for game completion
        if "Game completed" in line or "Game finished" in line or "Final results" in line or "GAME OVER" in line:
            game.status = GameStatus.COMPLETED
            game.end_time = datetime.now()
        
        # Look for errors
        if "Error:" in line or "Failed:" in line or "Exception:" in line:
            game.status = GameStatus.FAILED
            game.error_message = line.strip()
    
    def display_status(self, fancy_mode=False):
        """Display current status of all games."""
        if not self.running:
            return
            
        # Clear screen and move cursor to top (only in fancy mode)
        if fancy_mode and os.environ.get("MOTIVE_NO_CLEAR") != "1":
            print("\033[2J\033[H", end="")
        
        print("🎮 Motive Parallel Games Monitor")
        print("=" * 50)
        print(f"📊 Running {self.num_games} games")
        
        # Show log files section
        log_files = [game for game in self.games.values() if game.log_file]
        if log_files:
            print()
            print("📄 Log Files:")
            for i, (game_id, game) in enumerate(self.games.items(), 1):
                if game.log_file:
                    rel_log_path = os.path.relpath(game.log_file)
                    # Just show the clean path - most terminals don't handle file links well
                    print(f"Game {i:2d}: {rel_log_path}")
        
        print()
        print("📊 Progress:")
        
        # Display each game's progress
        for i, (game_id, game) in enumerate(self.games.items(), 1):
            self._display_game_progress(i, game)
        
        print()
        print("Press Ctrl+C to stop monitoring (games will continue running)")
    
    def _display_game_progress(self, game_num: int, game: GameProgress):
        """Display progress for a single game."""
        # Status indicator
        status_icons = {
            GameStatus.STARTING: "🔄",
            GameStatus.RUNNING: "▶️",
            GameStatus.COMPLETED: "✅",
            GameStatus.FAILED: "❌"
        }
        
        icon = status_icons.get(game.status, "❓")
        
        # Calculate total expected turns (players * rounds)
        total_expected_turns = game.total_rounds * game.total_players if game.total_rounds > 0 and game.total_players > 0 else 0
        
        # Overall game progress bar based on completed turns
        if total_expected_turns > 0:
            game_progress = min(game.completed_turns / total_expected_turns, 1.0)
            game_bar_length = 20
            game_filled_length = int(game_bar_length * game_progress)
            game_bar = "█" * game_filled_length + "░" * (game_bar_length - game_filled_length)
            game_progress_info = f"[{game_bar}] {game_progress:.1%}"
        else:
            game_progress_info = "[░░░░░░░░░░░░░░░░░░░░] 0.0%"
        
        # Round progress bar (current round only)
        if game.status == GameStatus.COMPLETED:
            # Game is completed, show 100% round progress
            round_progress_info = "[████████████] 100.0%"
        elif game.current_round > 0 and game.total_players > 0:
            # Calculate progress within current round based on completed turns
            # We need to calculate how many turns have been completed in the current round
            # Total completed turns - (completed rounds * players per round)
            completed_rounds = max(0, game.current_round - 1)  # Rounds that are fully completed
            completed_turns_in_current_round = max(0, game.completed_turns - (completed_rounds * game.total_players))
            round_progress = min(completed_turns_in_current_round / game.total_players, 1.0)
            round_bar_length = 12
            round_filled_length = int(round_bar_length * round_progress)
            round_bar = "█" * round_filled_length + "░" * (round_bar_length - round_filled_length)
            round_progress_info = f"[{round_bar}] {round_progress:.1%}"
        else:
            round_progress_info = "[░░░░░░░░░░░░] 0.0%"
        
        # Round and turn display
        if game.status == GameStatus.COMPLETED:
            # Game is completed, show final round and turn
            round_display = f"{game.total_rounds}/{game.total_rounds}"
            turn_display = f"{game.total_players}/{game.total_players}"
        else:
            round_display = f"{game.current_round}/{game.total_rounds}" if game.current_round > 0 else "-/-"
            turn_display = f"{game.current_turn_in_round}/{game.total_players}" if game.current_turn_in_round > 0 else "-/-"
        
        round_info = f"Round {round_display}, Turn {turn_display} {round_progress_info}"
        
        # Duration - stops when runner completes
        if game.start_time:
            if game.end_time:
                duration = game.end_time - game.start_time
                duration_str = f"{duration.total_seconds():.0f}s"
            else:
                duration = datetime.now() - game.start_time
                duration_str = f"{duration.total_seconds():.0f}s"
        else:
            duration_str = "0s"
        
        # Error message
        error_info = f" | Error: {game.error_message}" if game.error_message else ""
        
        # Combine all info with two progress bars
        main_info = f"Game {game_num:2d}: {icon} {game_progress_info} | {round_info} | {duration_str}"
        print(f"{main_info}{error_info}")
    
    def run(self, fancy_mode=False):
        """Run all games and monitor their progress."""
        self.start_games()
        
        try:
            while self.running:
                self.display_status(fancy_mode)
                time.sleep(1)  # Update every second
                
                # Check if all games are done
                if all(game.status in [GameStatus.COMPLETED, GameStatus.FAILED] for game in self.games.values()):
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor (games continue running)...")
            self.running = False
        
        # Final status
        self.display_status(fancy_mode)
        
        # Summary
        completed = sum(1 for game in self.games.values() if game.status == GameStatus.COMPLETED)
        failed = sum(1 for game in self.games.values() if game.status == GameStatus.FAILED)
        
        print(f"\n📈 Summary: {completed} completed, {failed} failed out of {self.num_games} games")
        
        # Cleanup
        for process in self.processes.values():
            if process.poll() is None:  # Still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


# All v1 conversion functions removed - v1 is DEAD


def _is_hierarchical_v2_config(config_data: Dict[str, Any], base_path: str) -> bool:
    """Check if a hierarchical config is v2 by examining included files."""
    includes = config_data.get('includes', [])
    for include_path in includes:
        full_path = Path(base_path) / include_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                included_data = yaml.safe_load(f)
            if 'entity_definitions' in included_data or 'action_definitions' in included_data:
                return True
            # Recursively check nested includes
            if 'includes' in included_data:
                if _is_hierarchical_v2_config(included_data, str(full_path.parent)):
                    return True
        except (FileNotFoundError, yaml.YAMLError):
            continue
    return False


def load_config(config_path: str, validate: bool = True) -> 'V2GameConfig':
    """Load game configuration from file with optional validation.
    Returns a V2GameConfig object - v1 is DEAD.
    """
    try:
        # Check if it's a v2 config or hierarchical config
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        if 'includes' in raw_config:
            # Check if this is a hierarchical v2 config by looking at included files
            base_path = str(Path(config_path).parent)
            is_v2_hierarchical = _is_hierarchical_v2_config(raw_config, base_path)
            
            if is_v2_hierarchical:
                # This is a hierarchical v2 config - use v2 pre-processor + Pydantic validation
                from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
                config_file = Path(config_path).name
                v2_config = load_and_validate_v2_config(config_file, base_path, validate=validate)
                print(f"DEBUG: v2_config type: {type(v2_config)}")
                # Return v2 config directly - GameMaster will be updated to work with v2
                return v2_config
            else:
                # This is a v1 hierarchical config - v1 is DEAD!
                print("ERROR: Found v1 hierarchical config - v1 is DEAD! Please use v2 configs only.", file=sys.stderr)
                raise ValueError("v1 configs are no longer supported. Please use v2 configs.")
        elif 'entity_definitions' in raw_config or 'action_definitions' in raw_config:
            # This is a standalone v2 config - use v2 pre-processor + Pydantic validation
            from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
            base_path = str(Path(config_path).parent)
            config_file = Path(config_path).name
            v2_config = load_and_validate_v2_config(config_file, base_path, validate=validate)
            print(f"DEBUG: v2_config type: {type(v2_config)}")
            # Return v2 config directly - GameMaster will be updated to work with v2
            return v2_config
        else:
            # This is a v1 config - v1 is DEAD!
            print("ERROR: Found v1 config - v1 is DEAD! Please use v2 configs only.", file=sys.stderr)
            raise ValueError("v1 configs are no longer supported. Please use v2 configs.")
        
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.", file=sys.stderr)
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
    except Exception as e:
        # Check if it's a validation error
        if hasattr(e, 'validation_errors') and e.validation_errors:
            print(f"Configuration validation failed:", file=sys.stderr)
            for error in e.validation_errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"Error loading configuration: {e}", file=sys.stderr)
        raise e


async def run_game(config_path: str, game_id: str = None, validate: bool = True,
                   rounds: int = None, ap: int = None, manual: str = None, hint: str = None,
                   hint_character: str = None, deterministic: bool = False, players: int = None,
                   character: str = None, motive: str = None, worker: bool = False, log_dir: str = "logs", 
                   no_file_logging: bool = False):
    """Run a Motive game with the specified configuration."""
    # Load environment variables
    load_dotenv()
    
    # Setup deterministic mode if requested
    if deterministic:
        import random
        random.seed(42)  # Fixed seed for reproducibility
        print("Running in deterministic mode with fixed random seed (42)")
    
    # Setup logging
    setup_logging()
    
    # Generate game ID if not provided
    if not game_id:
        # Create a sortable game ID with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hhr_%Mmin_%Ssec")
        game_id = os.getenv("MOTIVE_GAME_ID", f"{timestamp}_{str(uuid.uuid4())[:8]}")
    
    # Load configuration
    print(f"Loading configuration from: {config_path}")
    try:
        game_config = load_config(config_path, validate=validate)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
        return  # Ensure function exits even when sys.exit is mocked
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)
        return  # Ensure function exits even when sys.exit is mocked
    
    # Apply command line overrides - v2 config only
    if rounds is not None:
        # v2 config - modify the Pydantic object
        if not hasattr(game_config, 'game_settings') or game_config.game_settings is None:
            # Create a new game_settings object
            from motive.sim_v2.v2_config_validator import GameSettings
            game_config.game_settings = GameSettings()
        print(f"Overriding rounds: {game_config.game_settings.num_rounds} -> {rounds}")
        game_config.game_settings.num_rounds = rounds
    
    if ap is not None:
        # v2 config - modify the Pydantic object
        if not hasattr(game_config, 'game_settings') or game_config.game_settings is None:
            # Create a new game_settings object
            from motive.sim_v2.v2_config_validator import GameSettings
            game_config.game_settings = GameSettings()
        print(f"Overriding action points: {game_config.game_settings.initial_ap_per_turn} -> {ap}")
        game_config.game_settings.initial_ap_per_turn = ap
    
    if manual is not None:
        # v2 config - modify the Pydantic object
        if not hasattr(game_config, 'game_settings') or game_config.game_settings is None:
            # Create a new game_settings object
            from motive.sim_v2.v2_config_validator import GameSettings
            game_config.game_settings = GameSettings()
        print(f"Overriding manual: {game_config.game_settings.manual} -> {manual}")
        game_config.game_settings.manual = manual
    
    if hint is not None:
        print(f"Adding hint: {hint}")
        # Add hint to game settings - v2 config only
        if not hasattr(game_config, 'game_settings') or game_config.game_settings is None:
            # Create a new game_settings object
            from motive.sim_v2.v2_config_validator import GameSettings
            game_config.game_settings = GameSettings()
        if game_config.game_settings.hints is None:
            game_config.game_settings.hints = []
        # Create a simple hint that shows every round for all players
        game_config.game_settings.hints.append({
            "hint_id": "cli_hint",
            "hint_action": f"> {hint}",
            "when": {}  # Empty when condition means always show
        })
    
    if hint_character is not None:
        print(f"Adding character-specific hint for character: {hint_character}")
        # Add character-specific hint to game settings - v2 config only
        if not hasattr(game_config, 'game_settings') or game_config.game_settings is None:
            # Create a new game_settings object
            from motive.sim_v2.v2_config_validator import GameSettings
            game_config.game_settings = GameSettings()
        if game_config.game_settings.hints is None:
            game_config.game_settings.hints = []
        # Create a hint that shows only for the specified character
        # Note: We need to parse the hint_character format "character_id:hint_text"
        if ':' in hint_character:
            char_id, hint_text = hint_character.split(':', 1)
            game_config.game_settings.hints.append({
                "hint_id": "cli_hint_character",
                "hint_action": f"> {hint_text}",
                "when": {
                    "character_id": char_id
                }
            })
        else:
            print("Warning: --hint-character format should be 'character_id:hint_text'")
    
    # Handle players count override - v2 config only
    if players is not None:
        current_players = game_config.players if hasattr(game_config, 'players') else []
        
        print(f"Overriding player count: {len(current_players)} -> {players}")
        if players <= 0:
            # Handle zero or negative players
            game_config.players = []
        elif players < len(current_players):
            # Use first N players
            game_config.players = current_players[:players]
        elif players > len(current_players):
            # Create additional players by duplicating existing ones
            original_players = current_players.copy()
            additional_needed = players - len(current_players)
            
            for i in range(additional_needed):
                # Pick a random player to duplicate (or cycle through if deterministic)
                if deterministic:
                    source_player = original_players[i % len(original_players)]
                else:
                    import random
                    source_player = random.choice(original_players)
                
                # Create a new player with modified name
                new_player = source_player.copy()
                new_player['name'] = f"{source_player['name']}_{i + 1}"
                game_config.players.append(new_player)
    
    # Initialize and run the game
    print(f"Initializing game with ID: {game_id}")
    
    # Create GameMaster with v2 config
    game_master = GameMaster(game_config, game_id=game_id, deterministic=deterministic, log_dir=log_dir, no_file_logging=no_file_logging, character=character, motive=motive)
    
    # Run the game
    try:
        if worker:
            # In worker mode, suppress most stdout output and use structured progress reporting
            await game_master.run_game_worker()
        else:
            await game_master.run_game()
        
        # Return the GameMaster object for testing
        return game_master
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running game: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Motive - Interactive LLM Game Platform")
    
    # Configuration
    parser.add_argument("-c", "--config", default="configs/game.yaml", 
                       help="Path to game configuration file")
    
    # Game settings
    parser.add_argument("--rounds", type=int, help="Number of rounds to play")
    parser.add_argument("--ap", type=int, help="Action points per turn")
    parser.add_argument("--players", type=int, help="Number of players")
    parser.add_argument("--manual", help="Path to manual file")
    parser.add_argument("--hint", help="Add a hint for all players")
    parser.add_argument("--hint-character", help="Add a character-specific hint (format: character_id:hint_text)")
    parser.add_argument("--character", help="Character to play as")
    parser.add_argument("--motive", help="Motive to pursue")
    
    # Game behavior
    parser.add_argument("--deterministic", action="store_true", 
                       help="Run in deterministic mode with fixed random seed")
    parser.add_argument("--worker", action="store_true", 
                       help="Run in worker mode (for parallel games)")
    parser.add_argument("--no-validate", action="store_true", 
                       help="Skip configuration validation")
    
    # Logging
    parser.add_argument("--log-dir", default="logs", help="Directory for log files")
    parser.add_argument("--no-file-logging", action="store_true", 
                       help="Disable file logging")
    
    # Game ID
    parser.add_argument("--game-id", help="Custom game ID")
    
    # Parallel games
    parser.add_argument("--parallel", type=int, metavar="N", 
                       help="Run N parallel games")
    parser.add_argument("--fancy", action="store_true", 
                       help="Use fancy progress display for parallel games")
    
    args = parser.parse_args()
    
    # Handle parallel games
    if args.parallel:
        runner = ParallelGameRunner(
            num_games=args.parallel,
            config_path=args.config,
            rounds=args.rounds,
            ap=args.ap,
            players=args.players,
            manual=args.manual,
            hint=args.hint,
            hint_character=args.hint_character,
            character=args.character,
            deterministic=args.deterministic,
            no_validate=args.no_validate,
            log_dir=args.log_dir,
            no_file_logging=args.no_file_logging,
            game_id=args.game_id
        )
        runner.run(fancy_mode=args.fancy)
        return
    
    # Run single game
    asyncio.run(run_game(
        config_path=args.config,
        game_id=args.game_id,
        validate=not args.no_validate,
        rounds=args.rounds,
        ap=args.ap,
        manual=args.manual,
        hint=args.hint,
        hint_character=args.hint_character,
        deterministic=args.deterministic,
        players=args.players,
        character=args.character,
        motive=args.motive,
        worker=args.worker,
        log_dir=args.log_dir,
        no_file_logging=args.no_file_logging
    ))


if __name__ == "__main__":
    main()
