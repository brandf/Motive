"""
Test utilities for proper isolation and sandboxing.

This module provides utilities to ensure tests are properly isolated from external services
and don't make real API calls or create persistent side effects.
"""

import os
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

# Import GameMaster for the utility function
try:
    from motive.game_master import GameMaster
except ImportError:
    # Handle case where GameMaster might not be available during test discovery
    GameMaster = None


class Sandbox:
    """
    A comprehensive test sandbox that ensures complete isolation from external services.
    
    This class provides:
    - LLM client mocking
    - Temporary directory management
    - Log file cleanup
    - Environment variable isolation
    - Network call prevention
    """
    
    def __init__(self):
        self.temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.original_env: Dict[str, str] = {}
        self.patches: list = []
        
    def __enter__(self):
        """Enter the sandbox context."""
        # Store original environment variables
        self.original_env = os.environ.copy()
        
        # Create temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Mock LLM factory to prevent real API calls
        self._mock_llm_factory()
        
        # Mock network calls
        self._mock_network_calls()
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the sandbox context and clean up."""
        # Stop all patches
        for patcher in self.patches:
            patcher.stop()
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clean up temporary directory
        if self.temp_dir:
            self.temp_dir.cleanup()
    
    def _mock_llm_factory(self):
        """Mock the LLM factory to prevent real API calls."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = MagicMock(return_value=MagicMock(content="Mocked response"))
        
        patcher = patch('motive.llm_factory.create_llm_client', return_value=mock_llm)
        patcher.start()
        self.patches.append(patcher)
    
    def _mock_network_calls(self):
        """Mock network calls to prevent external requests."""
        # Mock requests library
        try:
            patcher = patch('requests.get')
            patcher.start()
            self.patches.append(patcher)
        except ImportError:
            pass
        
        # Mock urllib
        try:
            patcher = patch('urllib.request.urlopen')
            patcher.start()
            self.patches.append(patcher)
        except ImportError:
            pass
    
    def get_temp_dir(self) -> str:
        """Get the temporary directory path."""
        if not self.temp_dir:
            raise RuntimeError("Sandbox not entered")
        return self.temp_dir.name
    
    def create_mock_config(self, **overrides) -> MagicMock:
        """Create a properly configured mock config for testing."""
        mock_config = MagicMock()
        mock_config.theme_id = overrides.get('theme_id', 'fantasy')
        mock_config.edition_id = overrides.get('edition_id', 'hearth_and_shadow')
        mock_config.game_settings = MagicMock()
        mock_config.game_settings.num_rounds = overrides.get('num_rounds', 1)
        mock_config.game_settings.manual = overrides.get('manual', 'manual.md')
        mock_config.game_settings.initial_ap_per_turn = overrides.get('initial_ap_per_turn', 10)
        return mock_config


@contextmanager
def isolated_test_environment():
    """
    Context manager for isolated test environment.
    
    Usage:
        with isolated_test_environment() as sandbox:
            # Your test code here
            temp_dir = sandbox.get_temp_dir()
            mock_config = sandbox.create_mock_config()
    """
    with Sandbox() as sandbox:
        yield sandbox


def mock_game_master_creation():
    """
    Decorator to mock GameMaster creation to prevent LLM calls.
    
    Usage:
        @mock_game_master_creation()
        def test_something():
            # Test code that creates GameMaster instances
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with isolated_test_environment() as sandbox:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def cleanup_log_handlers(game_master_instance):
    """
    Clean up log handlers to prevent file locking issues on Windows.
    
    Args:
        game_master_instance: GameMaster instance with log handlers to clean up
    """
    if hasattr(game_master_instance, 'game_logger'):
        for handler in game_master_instance.game_logger.handlers[:]:
            handler.close()
            game_master_instance.game_logger.removeHandler(handler)


def create_isolated_game_master(game_config, game_id="test_game", **kwargs):
    """
    Create a GameMaster instance with proper test isolation.
    
    This function ensures that:
    - Log files are created in a temporary directory
    - LLM clients are mocked
    - No persistent side effects are created
    
    Args:
        game_config: Game configuration (Pydantic or dict)
        game_id: Game identifier (default: "test_game")
        **kwargs: Additional arguments to pass to GameMaster constructor
        
    Returns:
        tuple: (GameMaster instance, temporary directory context manager)
    """
    if GameMaster is None:
        raise ImportError("GameMaster not available. Make sure motive.game_master is importable.")
    
    temp_dir = tempfile.TemporaryDirectory()
    
    # Mock LLM factory to prevent real API calls
    with patch('motive.llm_factory.create_llm_client') as mock_create_llm:
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm
        
        # Create GameMaster with temporary log directory
        gm = GameMaster(game_config, game_id, log_dir=temp_dir.name, **kwargs)
        
        return gm, temp_dir


class IsolationError(Exception):
    """Raised when test isolation is violated."""
    pass


def check_test_isolation():
    """
    Check if tests are properly isolated from external services.
    
    This function can be called at the start of tests to ensure proper isolation.
    """
    # Check for real API keys in environment
    api_key_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
    for var in api_key_vars:
        if os.environ.get(var):
            raise IsolationError(
                f"Test isolation violated: {var} is set in environment. "
                "Tests should not use real API keys."
            )
    
    # Check for network connectivity (optional)
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        # If we can connect to internet, warn but don't fail
        print("WARNING: Network connectivity detected. Ensure tests are properly mocked.")
    except OSError:
        # No network connectivity is good for test isolation
        pass


# Test configuration constants
TEST_CONFIG = {
    'theme_id': 'fantasy',
    'edition_id': 'hearth_and_shadow',
    'num_rounds': 1,
    'players': 1,
    'initial_ap_per_turn': 10,
    'manual': 'manual.md'
}
