#!/usr/bin/env python3
"""
V2 Smoke Test - Isolated test for v2 scenarios with mocked LLMs.

This test validates that v2 configs work end-to-end without v2→v1 conversion.
Following AGENT.md best practices for TDD and isolated testing.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from motive.game_master import GameMaster
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


class TestV2SmokeTest:
    """Test v2 config loading and basic game functionality."""
    
    def test_v2_config_loading_and_structure(self):
        """Test that v2 configs load correctly and have expected structure."""
        # Load v2 config
        config = load_and_validate_v2_config("game_v2.yaml", "configs")
        
        # Verify v2 structure
        assert hasattr(config, 'entity_definitions')
        assert hasattr(config, 'action_definitions')
        assert hasattr(config, 'game_settings')
        assert hasattr(config, 'players')
        
        # Verify content exists
        assert len(config.entity_definitions) > 0, "Should have entity definitions"
        assert len(config.action_definitions) > 0, "Should have action definitions"
        assert config.game_settings is not None, "Should have game settings"
        assert len(config.players) > 0, "Should have players"
        
        # Verify entity types
        entity_types = set()
        for entity_id, entity_def in config.entity_definitions.items():
            if hasattr(entity_def, 'behaviors'):
                entity_types.update(entity_def.behaviors)
            elif hasattr(entity_def, 'types'):
                entity_types.update(entity_def.types)
        
        assert 'character' in entity_types, "Should have character entities"
        assert 'object' in entity_types, "Should have object entities"
        assert 'room' in entity_types, "Should have room entities"
    
    @patch('motive.llm_factory.create_llm_client')
    def test_v2_config_with_game_master_initialization(self, mock_create_llm):
        """Test that GameMaster can initialize with v2 configs."""
        # Mock LLM client to avoid instantiation issues
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm
        
        # Use a simple temp directory approach
        temp_dir = "temp_test_logs"
        try:
            # Load v2 config
            config = load_and_validate_v2_config("game_v2.yaml", "configs")
            
            # Initialize GameMaster with v2 config
            game_master = GameMaster(
                game_config=config,
                game_id="test_v2_smoke",
                log_dir=temp_dir,
                deterministic=True,
                no_file_logging=True  # Disable file logging to avoid permission issues
            )
            
            # Verify GameMaster initialized successfully
            assert game_master.game_config is not None
            assert game_master.game_id == "test_v2_smoke"
            assert game_master.num_rounds > 0
            
            # Verify GameInitializer was created
            assert game_master.game_initializer is not None
        finally:
            # Clean up temp directory if it was created
            import shutil
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except PermissionError:
                    pass  # Ignore permission errors on cleanup
    
    @patch('motive.llm_factory.create_llm_client')
    def test_v2_config_minimal_game_run(self, mock_create_llm):
        """Test minimal game run with v2 configs and mocked LLMs."""
        # Mock LLM client
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "> look\n> move north\n> continue"
        mock_create_llm.return_value = mock_llm
        
        # Use a simple temp directory approach
        temp_dir = "temp_test_logs_minimal"
        try:
            # Load v2 config
            config = load_and_validate_v2_config("game_v2.yaml", "configs")
            
            # Initialize GameMaster with v2 config
            game_master = GameMaster(
                game_config=config,
                game_id="test_v2_minimal",
                log_dir=temp_dir,
                deterministic=True,
                no_file_logging=True  # Disable file logging to avoid permission issues
            )
            
            # Verify initialization report shows non-zero content
            init_data = game_master.game_initializer.initialize_game_world(game_master.players)
            
            # Check that we have content (not just dummy placeholders)
            assert init_data['rooms_created'] > 0, "Should have created rooms"
            assert init_data['objects_placed'] > 0, "Should have placed objects"
            assert len(init_data['characters_assigned']) > 0, "Should have assigned characters"
            
            # Verify no dummy motives
            for character in game_master.player_characters.values():
                if hasattr(character, 'motive') and character.motive:
                    # Check that motive conditions are not dummy placeholders
                    motive_str = str(character.motive)
                    assert "dummy" not in motive_str.lower(), f"Character {character.name} has dummy motive: {motive_str}"
        finally:
            # Clean up temp directory if it was created
            import shutil
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except PermissionError:
                    pass  # Ignore permission errors on cleanup
    
    def test_v2_config_motive_conditions_real(self):
        """Test that v2 configs produce real motive conditions, not dummy placeholders."""
        # Load v2 config
        config = load_and_validate_v2_config("game_v2.yaml", "configs")
        
        # Check character entities for real motives
        character_entities = []
        for entity_id, entity_def in config.entity_definitions.items():
            if hasattr(entity_def, 'behaviors') and 'character' in entity_def.behaviors:
                character_entities.append((entity_id, entity_def))
            elif hasattr(entity_def, 'types') and 'character' in entity_def.types:
                character_entities.append((entity_id, entity_def))
        
        assert len(character_entities) > 0, "Should have character entities"
        
        # Check that characters have real motives
        for entity_id, entity_def in character_entities:
            if hasattr(entity_def, 'config') and entity_def.config:
                motives = entity_def.config.get('motives', [])
                if motives:
                    for motive in motives:
                        if hasattr(motive, 'success_conditions'):
                            conditions = motive.success_conditions
                        elif isinstance(motive, dict):
                            conditions = motive.get('success_conditions', [])
                        else:
                            continue
                        
                        # Check that conditions are not dummy placeholders
                        for condition in conditions:
                            condition_str = str(condition)
                            assert "dummy" not in condition_str.lower(), f"Entity {entity_id} has dummy condition: {condition_str}"
    
    def test_v2_config_action_definitions_structure(self):
        """Test that v2 action definitions have proper structure."""
        # Load v2 config
        config = load_and_validate_v2_config("game_v2.yaml", "configs")
        
        # Check action definitions
        assert len(config.action_definitions) > 0, "Should have action definitions"
        
        # Check core actions exist
        core_actions = ['look', 'move', 'say', 'help', 'pickup', 'drop']
        for action_name in core_actions:
            assert action_name in config.action_definitions, f"Should have {action_name} action"
            
            action_def = config.action_definitions[action_name]
            assert hasattr(action_def, 'name') or 'name' in action_def, f"Action {action_name} should have name"
            assert hasattr(action_def, 'description') or 'description' in action_def, f"Action {action_name} should have description"
            assert hasattr(action_def, 'cost') or 'cost' in action_def, f"Action {action_name} should have cost"
    
    def test_v2_config_entity_definitions_structure(self):
        """Test that v2 entity definitions have proper structure."""
        # Load v2 config
        config = load_and_validate_v2_config("game_v2.yaml", "configs")
        
        # Check entity definitions
        assert len(config.entity_definitions) > 0, "Should have entity definitions"
        
        # Check that entities have proper structure
        for entity_id, entity_def in config.entity_definitions.items():
            # Should have behaviors or types
            has_behaviors = hasattr(entity_def, 'behaviors') and entity_def.behaviors
            has_types = hasattr(entity_def, 'types') and entity_def.types
            assert has_behaviors or has_types, f"Entity {entity_id} should have behaviors or types"
            
            # Should have name (either in properties or as direct attribute)
            has_name_in_properties = False
            has_name_direct = False
            
            # Check for name in properties
            if hasattr(entity_def, 'properties') and entity_def.properties:
                properties = entity_def.properties
                if hasattr(properties, 'get'):
                    name = properties.get('name')
                else:
                    name = getattr(properties, 'name', None)
                has_name_in_properties = name is not None
            
            # Check for name in config field (EntityDefinition structure)
            has_name_in_config = False
            if hasattr(entity_def, 'config') and entity_def.config:
                config = entity_def.config
                if hasattr(config, 'get'):
                    name = config.get('name')
                else:
                    name = getattr(config, 'name', None)
                has_name_in_config = name is not None
            
            # Check for name as direct attribute
            has_name_direct = hasattr(entity_def, 'name') and entity_def.name is not None
            
            # Also check if it's a dict-like object with name key
            if not has_name_direct and hasattr(entity_def, '__getitem__'):
                try:
                    has_name_direct = 'name' in entity_def and entity_def['name'] is not None
                except (KeyError, TypeError):
                    pass
            
            assert has_name_in_properties or has_name_in_config or has_name_direct, f"Entity {entity_id} should have name in properties, config, or as direct attribute"
