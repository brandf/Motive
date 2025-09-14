"""
Critical path tests for motive/util.py

These tests focus on the most important utility functionality that could break user experience:
- Configuration loading and analysis
- Display functions
- Error handling and edge cases
"""

import pytest
import tempfile
import os
import json
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from motive.util import (
    load_config, show_raw_config, show_summary, show_actions, show_objects,
    show_rooms, show_characters, show_includes, find_latest_log_directory,
    extract_game_config_from_log
)


class TestConfigLoading:
    """Test configuration loading functionality."""
    
    def test_load_config_traditional_yaml(self):
        """Test loading a traditional YAML config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
game_settings:
  num_rounds: 10
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
actions:
  move:
    cost: 1
    description: Move to another room
""")
            config_path = f.name
        
        try:
            config = load_config(config_path)
            assert config['theme'] == 'fantasy'
            assert config['edition'] == 'hearth_and_shadow'
            assert config['game_settings']['num_rounds'] == 10
            assert len(config['players']) == 1
            assert config['players'][0]['name'] == 'Player_1'
            assert 'move' in config['actions']
        finally:
            os.unlink(config_path)
    
    def test_load_config_hierarchical_with_includes(self):
        """Test loading a hierarchical config with includes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
theme: fantasy
edition: hearth_and_shadow
includes:
  - core.yaml
  - fantasy.yaml
game_settings:
  num_rounds: 10
  manual: test_manual.md
  initial_ap_per_turn: 3
players:
  - name: Player_1
    provider: google
    model: gemini-2.5-flash
""")
            config_path = f.name
        
        try:
            with patch('motive.util.load_game_config') as mock_load_game_config:
                mock_config = {
                    'theme': 'fantasy',
                    'edition': 'hearth_and_shadow',
                    'game_settings': {'num_rounds': 10},
                    'players': [{'name': 'Player_1', 'provider': 'google', 'model': 'gemini-2.5-flash'}]
                }
                mock_load_game_config.return_value = mock_config
                
                config = load_config(config_path)
                
                # Verify hierarchical loader was called
                mock_load_game_config.assert_called_once()
                assert config == mock_config
        finally:
            os.unlink(config_path)
    
    def test_load_config_invalid_file(self):
        """Test loading an invalid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with patch('sys.exit') as mock_exit:
                load_config(config_path)
                mock_exit.assert_called_once_with(1)
        finally:
            os.unlink(config_path)
    
    def test_load_config_nonexistent_file(self):
        """Test loading a nonexistent config file."""
        with patch('sys.exit') as mock_exit:
            load_config("nonexistent_config.yaml")
            mock_exit.assert_called_once_with(1)


class TestConfigDisplay:
    """Test configuration display functions."""
    
    def test_show_raw_config_yaml(self):
        """Test showing raw config in YAML format."""
        config = {
            'theme': 'fantasy',
            'game_settings': {'num_rounds': 10}
        }
        
        with patch('builtins.print') as mock_print:
            show_raw_config(config, 'yaml')
            
            # Verify output was printed
            assert mock_print.call_count >= 3  # Header, content, empty line
    
    def test_show_raw_config_json(self):
        """Test showing raw config in JSON format."""
        config = {
            'theme': 'fantasy',
            'game_settings': {'num_rounds': 10}
        }
        
        with patch('builtins.print') as mock_print:
            show_raw_config(config, 'json')
            
            # Verify output was printed
            assert mock_print.call_count >= 3  # Header, content, empty line
    
    def test_show_summary(self):
        """Test showing configuration summary."""
        config = {
            'actions': {'move': {}, 'say': {}},
            'object_types': {'sword': {}, 'potion': {}},
            'rooms': {'tavern': {}, 'forest': {}},
            'characters': {'warrior': {}, 'mage': {}}
        }
        
        with patch('builtins.print') as mock_print:
            show_summary(config)
            
            # Verify summary was printed
            assert mock_print.call_count >= 6  # Header, counts, empty line
    
    def test_show_summary_with_character_types(self):
        """Test showing summary with character_types instead of characters."""
        config = {
            'actions': {'move': {}},
            'object_types': {'sword': {}},
            'rooms': {'tavern': {}},
            'character_types': {'warrior': {}, 'mage': {}}  # Note: character_types not characters
        }
        
        with patch('builtins.print') as mock_print:
            show_summary(config)
            
            # Verify summary was printed
            assert mock_print.call_count >= 6  # Header, counts, empty line
    
    def test_show_actions(self):
        """Test showing available actions."""
        config = {
            'actions': {
                'move': {'cost': 1, 'description': 'Move to another room'},
                'say': {'cost': 0, 'description': 'Speak to other players'}
            }
        }
        
        with patch('builtins.print') as mock_print:
            show_actions(config)
            
            # Verify actions were printed
            assert mock_print.call_count >= 3  # Header, actions, empty line
    
    def test_show_actions_empty(self):
        """Test showing actions when none exist."""
        config = {'actions': {}}
        
        with patch('builtins.print') as mock_print:
            show_actions(config)
            
            # Verify "No actions found" message was printed
            assert mock_print.call_count >= 2  # Header, message
    
    def test_show_objects(self):
        """Test showing available objects."""
        config = {
            'object_types': {
                'sword': {'description': 'A sharp blade'},
                'potion': {'description': 'A healing potion'}
            }
        }
        
        with patch('builtins.print') as mock_print:
            show_objects(config)
            
            # Verify objects were printed
            assert mock_print.call_count >= 3  # Header, objects, empty line
    
    def test_show_rooms(self):
        """Test showing available rooms."""
        config = {
            'rooms': {
                'tavern': {'description': 'A cozy tavern'},
                'forest': {'description': 'A dark forest'}
            }
        }
        
        with patch('builtins.print') as mock_print:
            show_rooms(config)
            
            # Verify rooms were printed
            assert mock_print.call_count >= 3  # Header, rooms, empty line
    
    def test_show_characters(self):
        """Test showing available characters."""
        config = {
            'characters': {
                'warrior': {'description': 'A brave warrior'},
                'mage': {'description': 'A wise mage'}
            }
        }
        
        with patch('builtins.print') as mock_print:
            show_characters(config)
            
            # Verify characters were printed
            assert mock_print.call_count >= 3  # Header, characters, empty line


class TestLogProcessing:
    """Test log processing functionality."""
    
    def test_find_latest_log_directory_no_logs(self):
        """Test finding latest log directory when none exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = find_latest_log_directory()
            assert result is None
    
    def test_find_latest_log_directory_with_logs(self):
        """Test finding latest log directory when logs exist."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('os.walk') as mock_walk:
                mock_walk.return_value = [
                    ('logs/fantasy/hearth_and_shadow/game1', [], ['game.log']),
                    ('logs/fantasy/hearth_and_shadow/game2', [], ['game.log'])
                ]
                
                with patch('pathlib.Path.stat') as mock_stat:
                    # Mock stat to return different modification times
                    mock_stat.side_effect = [
                        Mock(st_mtime=1000),  # game1
                        Mock(st_mtime=2000)   # game2 (newer)
                    ]
                    
                    result = find_latest_log_directory()
                    assert result == 'logs/fantasy/hearth_and_shadow/game2'
    
    def test_extract_game_config_from_log(self):
        """Test extracting game configuration from log file."""
        log_content = """
Game settings:
  num_rounds: 10
  initial_ap_per_turn: 3
  manual: test_manual.md
  - Initialized player: Player_1 using google/gemini-2.5-flash
  - Initialized player: Player_2 using anthropic/claude-3-sonnet
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            log_path = f.name
        
        try:
            config = extract_game_config_from_log(Path(log_path))
            
            assert config['total_rounds'] == 10
            assert config['ap_per_turn'] == 3
            assert config['game_settings']['num_rounds'] == 10
            assert config['game_settings']['initial_ap_per_turn'] == 3
            assert config['game_settings']['manual'] == 'test_manual.md'
            assert len(config['players']) == 2
            assert config['players'][0]['name'] == 'Player_1'
            assert config['players'][0]['provider'] == 'google'
            assert config['players'][0]['model'] == 'gemini-2.5-flash'
            assert config['players'][1]['name'] == 'Player_2'
            assert config['players'][1]['provider'] == 'anthropic'
            assert config['players'][1]['model'] == 'claude-3-sonnet'
        finally:
            os.unlink(log_path)
    
    def test_extract_game_config_from_log_invalid_file(self):
        """Test extracting config from invalid log file."""
        with patch('builtins.print') as mock_print:
            config = extract_game_config_from_log(Path("nonexistent.log"))
            
            # Should return default config structure
            assert config['total_rounds'] == 'unknown'
            assert config['ap_per_turn'] == 'unknown'
            assert config['players'] == []
            assert config['game_settings'] == {}


class TestShowIncludes:
    """Test show_includes functionality."""
    
    def test_show_includes_with_includes(self):
        """Test showing includes when config has includes."""
        config = {
            'includes': ['core.yaml', 'fantasy.yaml']
        }
        
        with patch('builtins.print') as mock_print:
            show_includes(config, 'test.yaml')
            
            # Verify includes were printed
            assert mock_print.call_count >= 3  # Header, includes, empty line
    
    def test_show_includes_without_includes(self):
        """Test showing includes when config has no includes."""
        config = {}
        
        with patch('builtins.print') as mock_print:
            show_includes(config, 'test.yaml')
            
            # Verify "No includes found" message was printed
            assert mock_print.call_count >= 2  # Header, message


if __name__ == '__main__':
    pytest.main([__file__])
