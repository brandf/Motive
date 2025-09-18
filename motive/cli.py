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
from motive.config import GameConfig, PlayerConfig
from motive.config_loader import load_game_config, load_and_validate_game_config
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


def _convert_v2_to_v1_config(v2_config_data: Dict[str, Any]) -> GameConfig:
    """Convert v2 config data to v1 GameConfig format."""
    print(f"DEBUG: _convert_v2_to_v1_config called with type: {type(v2_config_data)}")
    print(f"DEBUG: v2_config_data keys: {list(v2_config_data.keys()) if isinstance(v2_config_data, dict) else 'Not a dict'}")
    
    # Extract basic game settings with defaults
    game_settings_data = v2_config_data.get('game_settings', {})
    if not game_settings_data:
        # Provide defaults for entity definition configs
        game_settings_data = {
            'num_rounds': 10,
            'initial_ap_per_turn': 30,
            'manual': 'docs/MANUAL.md'
        }
    
    players_data = v2_config_data.get('players', [])
    if not players_data:
        # Provide default players for entity definition configs
        players_data = [
            {'name': 'Player_1', 'provider': 'google', 'model': 'gemini-2.5-flash'},
            {'name': 'Player_2', 'provider': 'google', 'model': 'gemini-2.5-flash'}
        ]
    
    # Convert players
    players = [PlayerConfig(**player_data) for player_data in players_data]
    
    # Convert entity definitions to v1 format
    entity_definitions = v2_config_data.get('entity_definitions', {})
    print(f"DEBUG: entity_definitions type: {type(entity_definitions)}")
    print(f"DEBUG: entity_definitions keys: {list(entity_definitions.keys()) if isinstance(entity_definitions, dict) else 'Not a dict'}")
    
    # Separate entities by type
    rooms = {}
    object_types = {}
    character_types = {}
    characters = {}
    
    for entity_id, entity_def in entity_definitions.items():
        print(f"DEBUG: Processing entity {entity_id}, type: {type(entity_def)}")
        print(f"DEBUG: entity_def content: {entity_def}")
        entity_types = entity_def.get('types', [])
        
        if 'room' in entity_types:
            rooms[entity_id] = _convert_room_definition(entity_id, entity_def)
        elif 'object' in entity_types:
            object_types[entity_id] = _convert_object_definition(entity_id, entity_def)
        elif 'character' in entity_types:
            print(f"DEBUG: Converting character {entity_id}")
            character_types[entity_id] = _convert_character_definition(entity_id, entity_def)
    
    # Convert action definitions
    action_definitions = v2_config_data.get('action_definitions', {})
    actions = {}
    for action_id, action_def in action_definitions.items():
        actions[action_id] = _convert_action_definition(action_id, action_def)
    
    # Create GameConfig
    from motive.config import GameSettings
    game_settings = GameSettings(**game_settings_data)
    
    return GameConfig(
        game_settings=game_settings,
        players=players,
        rooms=rooms,
        object_types=object_types,
        character_types=character_types,
        characters=characters,
        actions=actions,
        # No theme/edition metadata needed - config includes handle organization
    )


def _convert_room_definition(room_id: str, entity_def: Dict[str, Any]) -> Dict[str, Any]:
    """Convert v2 room definition to v1 format."""
    from motive.config import RoomConfig
    properties = entity_def.get('properties', {})
    
    return RoomConfig(
        id=room_id,
        name=properties.get('name', room_id),
        description=properties.get('description', ''),
        exits={},  # TODO: Convert exits from v2 format
        objects={},  # TODO: Convert objects from v2 format
        tags=[],  # TODO: Convert tags from v2 format
        properties=_extract_property_values(properties)
    )


def _convert_object_definition(object_id: str, entity_def: Dict[str, Any]) -> Dict[str, Any]:
    """Convert v2 object definition to v1 format."""
    from motive.config import ObjectTypeConfig
    print(f"DEBUG: _convert_object_definition called with object_id={object_id}, entity_def type={type(entity_def)}")
    print(f"DEBUG: entity_def keys: {list(entity_def.keys()) if isinstance(entity_def, dict) else 'Not a dict'}")
    properties = entity_def.get('properties', {})
    
    return ObjectTypeConfig(
        id=object_id,
        name=properties.get('name', object_id),
        description=properties.get('description', ''),
        properties=_extract_property_values(properties)
    )


def _convert_character_definition(character_id: str, entity_def: Dict[str, Any]) -> Dict[str, Any]:
    """Convert v2 character definition to v1 format.

    Ensures motives are converted into proper MotiveConfig objects with parsed
    success/failure conditions (no placeholder 'dummy' fallbacks).
    """
    from motive.config import (
        CharacterConfig,
        MotiveConfig,
        ActionRequirementConfig,
        MotiveConditionGroup,
    )
    properties = entity_def.get('properties', {})
    
    # Helpers to build typed condition objects
    def _build_condition(cond_data: Any):
        # Single dict condition
        if isinstance(cond_data, dict) and 'type' in cond_data:
            return ActionRequirementConfig(**cond_data)
        # List form: [ {operator: AND|OR}, {cond1}, {cond2}, ... ] or [ {cond} ] or [ {operator: AND, conditions: [...]} ]
        if isinstance(cond_data, list):
            if len(cond_data) == 1 and isinstance(cond_data[0], dict) and 'type' in cond_data[0]:
                return ActionRequirementConfig(**cond_data[0])
            if len(cond_data) == 1 and isinstance(cond_data[0], dict) and 'operator' in cond_data[0] and 'conditions' in cond_data[0]:
                # Handle nested structure in list: [{operator: AND, conditions: [...]}]
                operator = cond_data[0]['operator']
                conditions = []
                for item in cond_data[0]['conditions']:
                    if isinstance(item, dict) and 'type' in item:
                        conditions.append(ActionRequirementConfig(**item))
                return MotiveConditionGroup(operator=operator, conditions=conditions)
            if len(cond_data) >= 2 and isinstance(cond_data[0], dict) and 'operator' in cond_data[0]:
                operator = cond_data[0]['operator']
                conditions = []
                for item in cond_data[1:]:
                    if isinstance(item, dict):
                        conditions.append(ActionRequirementConfig(**item))
                return MotiveConditionGroup(operator=operator, conditions=conditions)
        # Handle nested structure: {operator: AND, conditions: [{cond1}, {cond2}]}
        if isinstance(cond_data, dict) and 'operator' in cond_data and 'conditions' in cond_data:
            operator = cond_data['operator']
            conditions = []
            for item in cond_data['conditions']:
                if isinstance(item, dict) and 'type' in item:
                    conditions.append(ActionRequirementConfig(**item))
            return MotiveConditionGroup(operator=operator, conditions=conditions)
        # Unknown/empty
        return None

    # Convert complex fields from string representations back to typed objects
    motive_objs = None
    
    # Check for motives in config field (v2 format)
    config_data = entity_def.get('config', {})
    if 'motives' in config_data:
        motives_data = config_data['motives']
    elif 'config' in config_data and 'motives' in config_data['config']:
        # Handle nested config structure
        motives_data = config_data['config']['motives']
    elif 'motives' in entity_def:
        motives_data = entity_def['motives']
    else:
        motives_data = None
    
    if motives_data is not None:
        if isinstance(motives_data, list):
            # Direct list of motive objects (v2 format)
            motive_objs = []
            for m in motives_data:
                if isinstance(m, dict) and 'id' in m and 'description' in m:
                    sc = _build_condition(m.get('success_conditions', []))
                    fc = _build_condition(m.get('failure_conditions', []))
                    motive_objs.append(
                        MotiveConfig(
                            id=m['id'],
                            description=m['description'],
                            success_conditions=sc,
                            failure_conditions=fc,
                        )
                    )
        elif isinstance(motives_data, str):
            # String representation (legacy format)
            try:
                import ast
                # Fix single quotes to double quotes for valid Python syntax
                motives_str_fixed = motives_data.replace("''", '"')
                motives_list = ast.literal_eval(motives_str_fixed)
                if isinstance(motives_list, list):
                    motive_objs = []
                    for m in motives_list:
                        if isinstance(m, dict) and 'id' in m and 'description' in m:
                            sc = _build_condition(m.get('success_conditions', []))
                            fc = _build_condition(m.get('failure_conditions', []))
                            motive_objs.append(
                                MotiveConfig(
                                    id=m['id'],
                                    description=m['description'],
                                    success_conditions=sc,
                                    failure_conditions=fc,
                                )
                            )
            except (ValueError, SyntaxError):
                motive_objs = None
    
    aliases = []
    if 'aliases' in config_data:
        aliases_data = config_data['aliases']
    elif 'config' in config_data and 'aliases' in config_data['config']:
        # Handle nested config structure
        aliases_data = config_data['config']['aliases']
    elif 'aliases' in entity_def:
        aliases_data = entity_def['aliases']
    else:
        aliases_data = None
    
    if aliases_data is not None:
        if isinstance(aliases_data, list):
            # Direct list (v2 format)
            aliases = aliases_data
        elif isinstance(aliases_data, str):
            # String representation (legacy format)
            try:
                import ast
                # Fix single quotes to double quotes for valid Python syntax
                aliases_str_fixed = aliases_data.replace("''", '"')
                aliases = ast.literal_eval(aliases_str_fixed)
            except (ValueError, SyntaxError):
                # If parsing fails, keep as empty list
                aliases = []
    
    initial_rooms = []
    if 'initial_rooms' in config_data:
        initial_rooms_data = config_data['initial_rooms']
    elif 'config' in config_data and 'initial_rooms' in config_data['config']:
        # Handle nested config structure
        initial_rooms_data = config_data['config']['initial_rooms']
    elif 'initial_rooms' in entity_def:
        initial_rooms_data = entity_def['initial_rooms']
    else:
        initial_rooms_data = None
    
    if initial_rooms_data is not None:
        if isinstance(initial_rooms_data, list):
            # Direct list (v2 format) - convert strings to InitialRoomConfig objects
            initial_rooms = []
            for room_data in initial_rooms_data:
                if isinstance(room_data, str):
                    # Simple string format - create InitialRoomConfig with defaults
                    from motive.config import InitialRoomConfig
                    initial_rooms.append(InitialRoomConfig(
                        room_id=room_data,
                        chance=100,
                        reason="Default starting location"
                    ))
                elif isinstance(room_data, dict):
                    # Already in InitialRoomConfig format
                    from motive.config import InitialRoomConfig
                    initial_rooms.append(InitialRoomConfig(**room_data))
        elif isinstance(initial_rooms_data, str):
            # String representation (legacy format)
            try:
                import ast
                # Fix single quotes to double quotes for valid Python syntax
                initial_rooms_str_fixed = initial_rooms_data.replace("''", '"')
                initial_rooms_list = ast.literal_eval(initial_rooms_str_fixed)
                if isinstance(initial_rooms_list, list):
                    initial_rooms = []
                    for room_data in initial_rooms_list:
                        if isinstance(room_data, str):
                            from motive.config import InitialRoomConfig
                            initial_rooms.append(InitialRoomConfig(
                                room_id=room_data,
                                chance=100,
                                reason="Default starting location"
                            ))
                        elif isinstance(room_data, dict):
                            from motive.config import InitialRoomConfig
                            initial_rooms.append(InitialRoomConfig(**room_data))
            except (ValueError, SyntaxError):
                # If parsing fails, keep as empty list
                initial_rooms = []
    
    # Extract name and backstory from nested config structure
    name = character_id  # default
    backstory = ''
    motive = ''
    
    if 'name' in config_data:
        name = config_data['name']
    elif 'config' in config_data and 'name' in config_data['config']:
        name = config_data['config']['name']
    elif 'name' in entity_def:
        name = entity_def['name']
    
    if 'backstory' in config_data:
        backstory = config_data['backstory']
    elif 'config' in config_data and 'backstory' in config_data['config']:
        backstory = config_data['config']['backstory']
    elif 'backstory' in entity_def:
        backstory = entity_def['backstory']
    
    if 'motive' in config_data:
        motive = config_data['motive']
    elif 'config' in config_data and 'motive' in config_data['config']:
        motive = config_data['config']['motive']
    elif 'motive' in entity_def:
        motive = entity_def['motive']
    
    char_config = CharacterConfig(
        id=character_id,
        name=name,
        backstory=backstory,
        motive=motive,
        motives=motive_objs,
        aliases=aliases,
        initial_rooms=initial_rooms
    )
    return char_config


def _convert_action_definition(action_id: str, action_def: Dict[str, Any]) -> Dict[str, Any]:
    """Convert v2 action definition to v1 format."""
    from motive.config import CostConfig, ParameterConfig, ActionRequirementConfig, ActionEffectConfig
    
    # Handle cost - can be a number or a complex object
    cost = action_def.get('cost', 10)
    if isinstance(cost, dict):
        # Complex cost object (e.g., code_binding) - convert to CostConfig
        converted_cost = CostConfig(**cost)
    else:
        # Simple numeric cost
        converted_cost = cost
    
    # Convert parameters to ParameterConfig objects
    parameters = []
    for param_data in action_def.get('parameters', []):
        parameters.append(ParameterConfig(**param_data))
    
    # Convert requirements to ActionRequirementConfig objects
    requirements = []
    for req_data in action_def.get('requirements', []):
        requirements.append(ActionRequirementConfig(**req_data))
    
    # Convert effects to ActionEffectConfig objects
    effects = []
    for effect_data in action_def.get('effects', []):
        effects.append(ActionEffectConfig(**effect_data))
    
    # Create ActionConfig object
    from motive.config import ActionConfig
    return ActionConfig(
        id=action_id,
        name=action_def.get('name', action_id),
        description=action_def.get('description', ''),
        cost=converted_cost,
        category=action_def.get('category', 'general'),
        parameters=parameters,
        requirements=requirements,
        effects=effects
    )


def _extract_property_values(properties: Dict[str, Any]) -> Dict[str, Any]:
    """Extract default values from v2 property schemas."""
    result = {}
    for prop_name, prop_schema in properties.items():
        if isinstance(prop_schema, dict) and 'default' in prop_schema:
            result[prop_name] = prop_schema['default']
        else:
            result[prop_name] = prop_schema
    return result


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


def load_config(config_path: str, validate: bool = True) -> Union[GameConfig, 'V2GameConfig']:
    """Load game configuration from file with optional validation.
    Returns a GameConfig (v1) or V2GameConfig (v2) object.
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
                # Use hierarchical config loader with validation (v1)
                config_file = Path(config_path).name
                return load_and_validate_game_config(config_file, base_path, validate=validate)
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
            # Traditional config loading (v1)
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
    game_config = load_config(config_path, validate=validate)
    
    # Apply command line overrides
    if rounds is not None:
        # Handle both v1 and v2 configs
        if hasattr(game_config, 'game_settings'):
            print(f"Overriding rounds: {game_config.game_settings.num_rounds} -> {rounds}")
            game_config.game_settings.num_rounds = rounds
        else:
            # v2 config - modify the dict directly
            if 'game_settings' not in game_config:
                game_config['game_settings'] = {}
            print(f"Overriding rounds: {game_config['game_settings'].get('num_rounds', 'default')} -> {rounds}")
            game_config['game_settings']['num_rounds'] = rounds
    
    if ap is not None:
        if hasattr(game_config, 'game_settings'):
            print(f"Overriding action points: {game_config.game_settings.initial_ap_per_turn} -> {ap}")
            game_config.game_settings.initial_ap_per_turn = ap
        else:
            if 'game_settings' not in game_config:
                game_config['game_settings'] = {}
            print(f"Overriding action points: {game_config['game_settings'].get('initial_ap_per_turn', 'default')} -> {ap}")
            game_config['game_settings']['initial_ap_per_turn'] = ap
    
    if manual is not None:
        if hasattr(game_config, 'game_settings'):
            print(f"Overriding manual: {game_config.game_settings.manual} -> {manual}")
            game_config.game_settings.manual = manual
        else:
            if 'game_settings' not in game_config:
                game_config['game_settings'] = {}
            print(f"Overriding manual: {game_config['game_settings'].get('manual', 'default')} -> {manual}")
            game_config['game_settings']['manual'] = manual
    if hint is not None:
        print(f"Adding hint: {hint}")
        # Add hint to game settings
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
        # Add character-specific hint to game settings
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
    
    # Handle players count override
    if players is not None:
        print(f"Overriding player count: {len(game_config.players)} -> {players}")
        if players <= 0:
            # Handle zero or negative players
            game_config.players = []
        elif players < len(game_config.players):
            # Use first N players
            game_config.players = game_config.players[:players]
        elif players > len(game_config.players):
            # Create additional players by duplicating existing ones
            original_players = game_config.players.copy()
            additional_needed = players - len(game_config.players)
            
            for i in range(additional_needed):
                # Pick a random player to duplicate (or cycle through if deterministic)
                if deterministic:
                    source_player = original_players[i % len(original_players)]
                else:
                    import random
                    source_player = random.choice(original_players)
                
                # Create a new player with modified name
                new_player = source_player.model_copy()
                new_player.name = f"{source_player.name}_{i + 1}"
                game_config.players.append(new_player)
    
    # Check LangSmith configuration
    if os.getenv("LANGCHAIN_TRACING_V2") == "true":
        print("LangSmith tracing is enabled. Ensure LANGCHAIN_API_KEY is set in .env.")
    else:
        print("LangSmith tracing is disabled. Set LANGCHAIN_TRACING_V2='true' in .env to enable.")
    
    # Run the game
    try:
        # Use the same GameMaster for both v1 and v2 configs
        gm = GameMaster(game_config=game_config, game_id=game_id, deterministic=deterministic,
                        log_dir=log_dir, no_file_logging=no_file_logging, character=character, motive=motive)
        if worker:
            # In worker mode, suppress most stdout output and use structured progress reporting
            await gm.run_game_worker()
        else:
            await gm.run_game()
        
        # Return the GameMaster object for testing
        return gm
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
  motive -c tests/configs/integration/game_test.yaml         # Run test configuration
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
    
    # Game settings overrides
    parser.add_argument(
        '--rounds',
        type=int,
        help='Number of rounds to run (overrides config)'
    )
    parser.add_argument(
        '--ap',
        type=int,
        help='Initial action points per turn (overrides config)'
    )
    parser.add_argument(
        '--manual',
        type=str,
        help='Path to game manual (overrides config)'
    )
    parser.add_argument(
        '--hint',
        type=str,
        help='Add a hint that will be shown to all players every round'
    )
    parser.add_argument(
        '--hint-character',
        type=str,
        help='Add a hint shown only to a specific character. Format: "character_id:hint_text"'
    )
    parser.add_argument(
        '--deterministic',
        action='store_true',
        help='Run in deterministic mode with fixed random seed for reproducible results'
    )
    parser.add_argument(
        '--players',
        type=int,
        help='Number of players to use (overrides config). If more than config players, creates additional players by duplicating existing ones. If more than available characters, will error.'
    )
    parser.add_argument(
        '--character',
        type=str,
        help='Force assignment of a specific character ID to the first player (for testing specific characters)'
    )
    parser.add_argument(
        '--motive',
        type=str,
        help='Force assignment of a specific motive ID to the character (for testing specific motives)'
    )
    
    # Parallel execution
    parser.add_argument(
        '--parallel',
        type=int,
        metavar='N',
        help='Run N games in parallel with progress monitoring. Does not run a game itself, just monitors parallel instances.'
    )
    
    # Worker mode (internal use)
    parser.add_argument(
        '--worker',
        action='store_true',
        help=argparse.SUPPRESS  # Hide from help since it's internal
    )
    
    # Fancy terminal mode
    parser.add_argument(
        '--fancy',
        action='store_true',
        help='Enable fancy terminal UI with live progress updates (may not work in all terminals)'
    )
    
    # Logging configuration
    parser.add_argument(
        '--log-dir',
        type=str,
        default='logs',
        help='Base directory for log files (default: logs)'
    )
    parser.add_argument(
        '--no-file-logging',
        action='store_true',
        help='Disable file logging (logs only to stdout)'
    )
    
    args = parser.parse_args()
    
    # Validate config file exists
    if not Path(args.config).exists():
        print(f"Error: Configuration file '{args.config}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Handle parallel mode
    if args.parallel:
        if args.parallel < 1:
            print("Error: --parallel must specify at least 1 game", file=sys.stderr)
            sys.exit(1)
        
        # Prepare game arguments
        game_args = {
            'game_id': args.game_id,
            'rounds': args.rounds,
            'ap': args.ap,
            'players': args.players,
            'hint': args.hint,
            'hint_character': args.hint_character,
            'character': args.character,
            'motive': args.motive,
            'deterministic': args.deterministic,
            'manual': args.manual,
            'no_validate': args.no_validate,
            'log_dir': args.log_dir,
            'no_file_logging': args.no_file_logging
        }
        
        # Remove None values
        game_args = {k: v for k, v in game_args.items() if v is not None}
        
        # Run parallel games
        runner = ParallelGameRunner(args.parallel, args.config, **game_args)
        runner.run(fancy_mode=args.fancy)
    else:
        # Run single game
        validate = not args.no_validate
        asyncio.run(run_game(args.config, args.game_id, validate=validate, 
                            rounds=args.rounds, ap=args.ap, manual=args.manual, hint=args.hint,
                            hint_character=args.hint_character, deterministic=args.deterministic, 
                            players=args.players, character=args.character, motive=args.motive, worker=args.worker,
                            log_dir=args.log_dir, no_file_logging=args.no_file_logging))


if __name__ == '__main__':
    main()
