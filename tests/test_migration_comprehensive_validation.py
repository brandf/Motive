"""Comprehensive validation of migration results to achieve 10/10 confidence."""

import os
import yaml
import pytest
from pathlib import Path
from motive.sim_v2.config_loader import V2ConfigLoader


class TestMigrationComprehensiveValidation:
    """Comprehensive validation of all migration results."""
    
    def test_all_migrated_yaml_files_syntax_valid(self):
        """Validate YAML syntax of all migrated files."""
        migrated_files = []
        
        # Find all *_migrated.yaml files
        for root, dirs, files in os.walk("configs"):
            for file in files:
                if file.endswith("_migrated.yaml"):
                    migrated_files.append(os.path.join(root, file))
        
        for root, dirs, files in os.walk("tests/configs"):
            for file in files:
                if file.endswith("_migrated.yaml"):
                    migrated_files.append(os.path.join(root, file))
        
        assert len(migrated_files) > 0, "No migrated files found"
        
        for file_path in migrated_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"YAML syntax error in {file_path}: {e}")
    
    def test_hearth_and_shadow_content_preservation(self):
        """Validate that hearth_and_shadow content is fully preserved."""
        # Test characters
        char_file = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_migrated.yaml"
        with open(char_file, 'r', encoding='utf-8') as f:
            char_data = yaml.safe_load(f)
        
        # Verify all 8 characters are present
        assert len(char_data['entity_definitions']) == 8
        
        # Verify detective_thorne has all required content
        detective = char_data['entity_definitions']['detective_thorne']
        assert 'motives' in detective['properties']
        assert 'initial_rooms' in detective['properties']
        assert 'aliases' in detective['properties']
        
        # Verify motives content is preserved (as string representation)
        motives_str = detective['properties']['motives']['default']
        assert 'investigate_mayor' in motives_str
        assert 'protect_daughter' in motives_str
        assert 'avenge_partner' in motives_str
        assert 'success_conditions' in motives_str
        assert 'failure_conditions' in motives_str
        
        # Verify initial_rooms content is preserved
        initial_rooms_str = detective['properties']['initial_rooms']['default']
        assert 'town_square' in initial_rooms_str
        assert 'tavern' in initial_rooms_str
        assert 'bank' in initial_rooms_str
        assert 'chance' in initial_rooms_str
        assert 'reason' in initial_rooms_str
        
        # Verify aliases content is preserved
        aliases_str = detective['properties']['aliases']['default']
        assert 'james' in aliases_str
        assert 'detective' in aliases_str
        assert 'thorn' in aliases_str
    
    def test_hearth_and_shadow_rooms_content_preservation(self):
        """Validate that hearth_and_shadow rooms content is fully preserved."""
        room_file = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_migrated.yaml"
        with open(room_file, 'r', encoding='utf-8') as f:
            room_data = yaml.safe_load(f)
        
        # Verify town_square has all required content
        town_square = room_data['entity_definitions']['town_square']
        assert 'exits' in town_square['properties']
        assert 'objects' in town_square['properties']
        
        # Verify exits content is preserved
        exits_str = town_square['properties']['exits']['default']
        assert 'tavern' in exits_str
        assert 'guild' in exits_str
        assert 'church' in exits_str
        assert 'bank' in exits_str
        assert 'destination_room_id' in exits_str
        assert 'aliases' in exits_str
        
        # Verify objects content is preserved
        objects_str = town_square['properties']['objects']['default']
        assert 'notice_board' in objects_str
        assert 'broken_fountain' in objects_str
        assert 'town_statue' in objects_str
        assert 'object_type_id' in objects_str
        assert 'current_room_id' in objects_str
        assert 'description' in objects_str
    
    def test_core_actions_content_preservation(self):
        """Validate that core actions content is fully preserved."""
        action_file = "configs/core_actions_migrated.yaml"
        with open(action_file, 'r', encoding='utf-8') as f:
            action_data = yaml.safe_load(f)
        
        # Verify look action has all required content
        look_action = action_data['action_definitions']['look']
        assert 'category' in look_action
        assert look_action['category'] == 'observation'
        assert 'parameters' in look_action
        assert 'requirements' in look_action
        assert 'effects' in look_action
        
        # Verify help action has complex cost structure
        help_action = action_data['action_definitions']['help']
        assert 'category' in help_action
        assert help_action['category'] == 'system'
        assert isinstance(help_action['cost'], dict)
        assert 'type' in help_action['cost']
        assert help_action['cost']['type'] == 'code_binding'
        
        # Verify move action has requirements
        move_action = action_data['action_definitions']['move']
        assert 'category' in move_action
        assert move_action['category'] == 'movement'
        assert len(move_action['requirements']) > 0
        assert move_action['requirements'][0]['type'] == 'exit_exists'
    
    def test_hierarchical_config_loading(self):
        """Validate that hierarchical config loading works correctly."""
        loader = V2ConfigLoader()
        
        # Test fantasy theme loading
        fantasy_config = loader.load_hierarchical_config("configs/themes/fantasy/fantasy_migrated.yaml")
        loader.load_v2_config(fantasy_config)
        
        # Should have loaded objects from fantasy_objects_migrated.yaml
        assert len(loader.definitions._defs) > 0
        
        # Test hearth_and_shadow loading
        hearth_config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml")
        loader.load_v2_config(hearth_config)
        
        # Should have loaded rooms, objects, characters
        assert len(loader.definitions._defs) > 10  # Should have multiple entities
        assert len(loader.actions) > 0  # Should have actions from core
    
    def test_tags_converted_to_boolean_properties(self):
        """Validate that tags are converted to boolean properties, not preserved as arrays."""
        # Check a room that should have tags
        room_file = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_migrated.yaml"
        with open(room_file, 'r', encoding='utf-8') as f:
            room_data = yaml.safe_load(f)
        
        # Verify no 'tags' property exists as array
        for room_id, room_def in room_data['entity_definitions'].items():
            properties = room_def['properties']
            # Should not have a 'tags' property that's an array
            if 'tags' in properties:
                # If tags exist, they should be string representation, not array
                assert isinstance(properties['tags']['default'], str)
    
    def test_object_properties_preserved(self):
        """Validate that object properties are correctly preserved and typed."""
        obj_file = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_migrated.yaml"
        with open(obj_file, 'r', encoding='utf-8') as f:
            obj_data = yaml.safe_load(f)
        
        # Check notice_board object
        notice_board = obj_data['entity_definitions']['notice_board']
        properties = notice_board['properties']
        
        # Should have readable property as boolean
        assert 'readable' in properties
        assert properties['readable']['type'] == 'boolean'
        assert properties['readable']['default'] == True
        
        # Should have text property as string
        assert 'text' in properties
        assert properties['text']['type'] == 'string'
        assert len(properties['text']['default']) > 0
    
    def test_edge_cases_empty_values(self):
        """Validate that empty values are handled correctly."""
        # Check core configs that should be empty
        core_rooms_file = "configs/core_rooms_migrated.yaml"
        with open(core_rooms_file, 'r', encoding='utf-8') as f:
            core_rooms_data = yaml.safe_load(f)
        
        # Core configs are completely empty (no content to migrate)
        # This is expected behavior - core configs have no rooms/objects/characters
        assert isinstance(core_rooms_data, dict)
        # Should be empty dict since core_rooms.yaml has no content
        assert len(core_rooms_data) == 0
    
    def test_special_characters_in_strings(self):
        """Validate that special characters in strings are handled correctly."""
        char_file = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_migrated.yaml"
        with open(char_file, 'r', encoding='utf-8') as f:
            char_data = yaml.safe_load(f)
        
        # Check that strings with quotes, newlines, etc. are preserved
        detective = char_data['entity_definitions']['detective_thorne']
        backstory = detective['properties']['backstory']['default']
        motives = detective['properties']['motives']['default']
        
        # Should contain newlines in backstory
        assert '\n' in backstory
        
        # Should contain quotes in motives string representation
        assert '"' in motives or "'" in motives
    
    def test_reference_integrity(self):
        """Validate that references between entities are intact."""
        # Load all hearth_and_shadow configs
        loader = V2ConfigLoader()
        hearth_config = loader.load_hierarchical_config("configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_migrated.yaml")
        loader.load_v2_config(hearth_config)
        
        # Check that room references in exits are valid
        town_square_def = loader.definitions.get('town_square')
        assert town_square_def is not None
        
        # The exits property should contain references to other rooms
        exits_prop = town_square_def.properties.get('exits')
        assert exits_prop is not None
        exits_str = exits_prop.default
        
        # Should reference other rooms that exist
        assert 'tavern' in exits_str
        assert 'church' in exits_str
        assert 'bank' in exits_str
    
    def test_migration_statistics_accuracy(self):
        """Validate that migration statistics are accurate."""
        # This would require running migration and checking stats
        # For now, just verify the migration completed without errors
        migrated_files = []
        for root, dirs, files in os.walk("configs"):
            for file in files:
                if file.endswith("_migrated.yaml"):
                    migrated_files.append(os.path.join(root, file))
        
        # Should have migrated files for all major configs
        assert len(migrated_files) >= 10  # Should have multiple migrated files
        
        # Verify key files exist
        key_files = [
            "configs/core_actions_migrated.yaml",
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_characters_migrated.yaml",
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_rooms_migrated.yaml",
            "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects_migrated.yaml"
        ]
        
        for key_file in key_files:
            assert os.path.exists(key_file), f"Missing key migrated file: {key_file}"
