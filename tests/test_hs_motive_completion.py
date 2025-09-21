"""
Integration tests for Hearth and Shadow motive completion.

Tests that all character motives can be achieved with the current H&S configuration.
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from motive.cli import run_game
from tests.utils.llm_mock import llm_script


class TestHSMotiveCompletion:
    """Test that H&S motives are achievable with current configuration."""
    
    @pytest.fixture
    def objects_config(self):
        """Load H&S objects configuration."""
        config_path = "configs/themes/fantasy/editions/hearth_and_shadow/hearth_and_shadow_objects.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_detective_thorne_motive_objects_exist(self, objects_config):
        """Test that objects needed for Detective Thorne's motive exist."""
        entity_definitions = objects_config.get('entity_definitions', {})
        
        # Objects that should exist for Detective Thorne's motive
        required_objects = [
            'partner_evidence',  # For evidence_found
            'cult_history',      # For evidence_found  
            'decoder_ring',      # For mystery_solved
            'justice_scales',    # For justice_served
            'ritual_candle',     # For ritual_materials_gathered
            'secret_map'         # For secret_passages_discovered
        ]
        
        for obj_name in required_objects:
            assert obj_name in entity_definitions, f"Required object '{obj_name}' not found for Detective Thorne's motive"
    
    def test_father_marcus_motive_objects_exist(self, objects_config):
        """Test that objects needed for Father Marcus's motive exist."""
        entity_definitions = objects_config.get('entity_definitions', {})
        
        # Objects that should exist for Father Marcus's motive
        required_objects = [
            'ancient_tome',      # For secrets_uncovered
            'cult_confession',   # For secrets_uncovered, courage_found
            'faith_restoration', # For faith_restored
            'ancient_scroll',   # For ritual_knowledge_gained
            'holy_symbol',      # For divine_protection_gained, family_protected
            'binding_chain'     # For binding_power_acquired, congregation_protected
        ]
        
        for obj_name in required_objects:
            assert obj_name in entity_definitions, f"Required object '{obj_name}' not found for Father Marcus's motive"
    
    def test_captain_omalley_motive_objects_exist(self, objects_config):
        """Test that objects needed for Captain O'Malley's motive exist."""
        entity_definitions = objects_config.get('entity_definitions', {})
        
        # Objects that should exist for Captain O'Malley's motive
        required_objects = [
            'corruption_documents', # For corruption_evidence, secrets_exposed
            'meeting_table',        # For corruption_evidence
            'justice_scales',       # For justice_served
            'ritual_candle',        # For ritual_materials_gathered
            'secret_map',          # For secret_passages_discovered
            'holy_symbol'          # For family_protected
        ]
        
        for obj_name in required_objects:
            assert obj_name in entity_definitions, f"Required object '{obj_name}' not found for Captain O'Malley's motive"
    
    def test_key_object_interactions_exist(self, objects_config):
        """Test that key objects have the required interactions."""
        entity_definitions = objects_config.get('entity_definitions', {})
        
        # Test specific objects that should have key interactions
        key_objects = {
            'partner_evidence': ['look', 'use'],  # Should increment evidence_found and set mystery_solved
            'decoder_ring': ['use'],              # Should set mystery_solved
            'justice_scales': ['use'],            # Should set justice_served
            'cult_confession': ['look', 'use'],   # Should increment secrets_uncovered and set courage_found
            'faith_restoration': ['use'],         # Should set faith_restored
            'holy_symbol': ['use'],              # Should set divine_protection_gained and family_protected
            'binding_chain': ['use'],            # Should set binding_power_acquired and congregation_protected
            'corruption_documents': ['look', 'use'], # Should increment corruption_evidence and set secrets_exposed
            'secret_map': ['look'],              # Should set secret_passages_discovered
            'ritual_candle': ['use']             # Should set ritual_materials_gathered
        }
        
        for obj_name, expected_interactions in key_objects.items():
            assert obj_name in entity_definitions, f"Object '{obj_name}' not found"
            
            obj_def = entity_definitions[obj_name]
            interactions = obj_def.get('interactions', {})
            
            for interaction in expected_interactions:
                assert interaction in interactions, f"Object '{obj_name}' missing '{interaction}' interaction"


class TestHSMotiveIntegration:
    """Integration tests for H&S motive completion with mocked LLM responses."""
    
    @pytest.mark.asyncio
    async def test_detective_thorne_motive_path(self, tmp_path):
        """Test Detective Thorne's motive completion path with mocked LLM."""
        scripts = {
            "Player_1": (
                "> look\n"
                "> pickup \"Partner's Evidence\"\n"
                "> look \"Partner's Evidence\"\n"
                "> move old_library\n"
                "> look \"Cult History\"\n"
                "> pickup \"Decoder Ring\"\n"
                "> use \"Decoder Ring\"\n"
                "> move church\n"
                "> use \"Scales of Justice\"\n"
                "> pickup \"Ritual Candle\"\n"
                "> use \"Ritual Candle\"\n"
                "> look \"Secret Map\"\n"
                "> use \"Secret Map\"\n"
                "> pass"
            )
        }

        with llm_script(scripts, manual="Test Manual"):
            await run_game(
                config_path="configs/game.yaml",
                game_id="test_detective_thorne_motive",
                validate=True,
                rounds=1,
                deterministic=True,
                players=1,
                character_motives=["detective_thorne:avenge_partner"],
                log_dir=str(tmp_path / "logs"),
                no_file_logging=True,
            )
    
    @pytest.mark.asyncio
    async def test_father_marcus_motive_path(self, tmp_path):
        """Test Father Marcus's motive completion path with mocked LLM."""
        scripts = {
            "Player_1": (
                "> look\n"
                "> move old_library\n"
                "> look \"Ancient Tome\"\n"
                "> move church\n"
                "> look \"Cult Confession\"\n"
                "> use \"Cult Confession\"\n"
                "> use \"Sacred Relic\"\n"
                "> look \"Ancient Scroll\"\n"
                "> use \"Ancient Scroll\"\n"
                "> use \"Holy Symbol\"\n"
                "> use \"Binding Chain\"\n"
                "> pass"
            )
        }

        with llm_script(scripts, manual="Test Manual"):
            await run_game(
                config_path="configs/game.yaml",
                game_id="test_father_marcus_motive",
                validate=True,
                rounds=1,
                deterministic=True,
                players=1,
                character_motives=["father_marcus:restore_divine_connection"],
                log_dir=str(tmp_path / "logs"),
                no_file_logging=True,
            )
    
    @pytest.mark.asyncio
    async def test_captain_omalley_motive_path(self, tmp_path):
        """Test Captain O'Malley's motive completion path with mocked LLM."""
        scripts = {
            "Player_1": (
                "> look\n"
                "> move abandoned_warehouse\n"
                "> look \"Corruption Documents\"\n"
                "> look \"Meeting Table\"\n"
                "> use \"Corruption Documents\"\n"
                "> move church\n"
                "> use \"Scales of Justice\"\n"
                "> pickup \"Ritual Candle\"\n"
                "> use \"Ritual Candle\"\n"
                "> look \"Secret Map\"\n"
                "> use \"Secret Map\"\n"
                "> use \"Holy Symbol\"\n"
                "> pass"
            )
        }

        with llm_script(scripts, manual="Test Manual"):
            await run_game(
                config_path="configs/game.yaml",
                game_id="test_captain_omalley_motive",
                validate=True,
                rounds=1,
                deterministic=True,
                players=1,
                character_motives=["captain_marcus_omalley:break_free_from_cult"],
                log_dir=str(tmp_path / "logs"),
                no_file_logging=True,
            )
