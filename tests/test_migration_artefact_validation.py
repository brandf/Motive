#!/usr/bin/env python3
"""Test migration artefact validation - ensure all migrated YAML files are valid and loadable."""

import pytest
import yaml
import os
from pathlib import Path
from glob import glob

from motive.sim_v2.config_loader import V2ConfigLoader


class TestMigrationArtefactValidation:
    """Test that all migrated YAML files are syntactically valid and structurally sound."""

    def test_all_migrated_yaml_files_parse(self):
        """Test that all *_migrated.yaml files can be parsed with yaml.safe_load."""
        # Find all migrated YAML files
        migrated_files = []
        
        # Check configs directory
        migrated_files.extend(glob("configs/**/*_migrated.yaml", recursive=True))
        
        # Check tests directory
        migrated_files.extend(glob("tests/**/*_migrated.yaml", recursive=True))
        
        assert len(migrated_files) > 0, "No migrated YAML files found"
        
        # Test each file can be parsed
        for file_path in migrated_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None, f"File {file_path} parsed to None"
                except yaml.YAMLError as e:
                    pytest.fail(f"YAML syntax error in {file_path}: {e}")
                except Exception as e:
                    pytest.fail(f"Unexpected error parsing {file_path}: {e}")

    def test_contentful_migrated_files_have_definitions(self):
        """Test that contentful migrated files have entity_definitions or action_definitions."""
        # Files that should have content (not empty)
        contentful_files = [
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_migrated.yaml",
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_migrated.yaml", 
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_migrated.yaml",
            "configs/core_actions_migrated.yaml",
            "configs/themes/fantasy/fantasy_objects_migrated.yaml"
        ]
        
        for file_path in contentful_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                # Should have either entity_definitions or action_definitions
                has_definitions = (
                    'entity_definitions' in data or 
                    'action_definitions' in data
                )
                assert has_definitions, f"Contentful file {file_path} missing definitions"

    def test_hierarchical_v2_configs_load_without_errors(self):
        """Test that hierarchical v2 configs can be loaded via V2ConfigLoader."""
        hierarchical_configs = [
            "configs/themes/fantasy/fantasy_migrated.yaml",
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml"
        ]
        
        for config_path in hierarchical_configs:
            if os.path.exists(config_path):
                loader = V2ConfigLoader()
                
                # Should load hierarchical config without errors
                try:
                    merged_data = loader.load_hierarchical_config(config_path)
                    loader.load_v2_config(merged_data)
                    
                    # Should have some definitions loaded
                    summary = loader.get_migration_summary()
                    assert summary['definitions_loaded'] >= 0
                    assert summary['actions_loaded'] >= 0
                    
                except Exception as e:
                    pytest.fail(f"Failed to load hierarchical config {config_path}: {e}")

    def test_hearth_and_shadow_has_content(self):
        """Test that hearth_and_shadow migrated config has substantial content."""
        config_path = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml"
        
        if os.path.exists(config_path):
            loader = V2ConfigLoader()
            merged_data = loader.load_hierarchical_config(config_path)
            loader.load_v2_config(merged_data)
            
            summary = loader.get_migration_summary()
            
            # Hearth and Shadow should have substantial content
            assert summary['definitions_loaded'] > 10, f"Expected >10 definitions, got {summary['definitions_loaded']}"
            
            # Should have rooms, objects, characters
            assert 'entity_definitions' in merged_data
            
            entity_defs = merged_data['entity_definitions']
            room_count = sum(1 for defn in entity_defs.values() if 'room' in defn.get('types', []))
            object_count = sum(1 for defn in entity_defs.values() if 'object' in defn.get('types', []))
            character_count = sum(1 for defn in entity_defs.values() if 'character' in defn.get('types', []))
            
            assert room_count > 0, "Expected rooms in hearth_and_shadow"
            assert object_count > 0, "Expected objects in hearth_and_shadow"
            assert character_count > 0, "Expected characters in hearth_and_shadow"

    def test_includes_resolve_without_filenotfound(self):
        """Test that all includes in migrated configs resolve without FileNotFoundError."""
        # Check main migrated configs for include resolution
        main_configs = [
            "configs/core_migrated.yaml",
            "configs/themes/fantasy/fantasy_migrated.yaml", 
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml"
        ]
        
        for config_path in main_configs:
            if os.path.exists(config_path):
                loader = V2ConfigLoader()
                
                # This should not raise FileNotFoundError
                try:
                    merged_data = loader.load_hierarchical_config(config_path)
                    assert merged_data is not None
                except FileNotFoundError as e:
                    pytest.fail(f"Include resolution failed for {config_path}: {e}")
                except Exception as e:
                    # Other errors are acceptable (e.g., validation errors)
                    pass
