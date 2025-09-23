#!/usr/bin/env python3
"""
Test the evidence operator fix to ensure >= operator works correctly.
"""

import pytest
from motive.character import Character
from motive.requirements_evaluator import evaluate_requirement


class TestEvidenceOperatorFix:
    """Test the evidence operator fix."""
    
    def setup_method(self):
        """Set up test environment."""
        self.character = Character(
            char_id="detective_thorne",
            name="Detective Thorne", 
            backstory="A seasoned detective",
            current_room_id="hidden_observatory"
        )
    
    def test_evidence_greater_than_equal_operator(self):
        """Test that >= operator works correctly for evidence_found."""
        # Set up 3 evidence flags
        self.character.set_property('partner_evidence_found', True)
        self.character.set_property('sacred_map_found', True)
        self.character.set_property('priest_diary_found', True)
        
        # Test >= 2 requirement (should pass with 3 evidence)
        requirement = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 2,
            'operator': '>='
        }
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        
        print(f"Evidence count: {self.character.evidence_found}")
        print(f"Handled: {handled}")
        print(f"Passed: {passed}")
        print(f"Error: {error}")
        
        assert handled == True, f"Requirement should be handled, got {handled}"
        assert passed == True, f"Requirement should pass with 3 evidence >= 2, got {passed}. Error: {error}"
    
    def test_evidence_greater_than_equal_operator_edge_cases(self):
        """Test edge cases for >= operator."""
        # Test with exactly 2 evidence (should pass)
        self.character.set_property('partner_evidence_found', True)
        self.character.set_property('sacred_map_found', True)
        
        requirement = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 2,
            'operator': '>='
        }
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == True, f"2 evidence should pass >= 2 requirement"
        
        # Test with 1 evidence (should fail)
        self.character.properties = {}  # Clear all
        self.character.set_property('partner_evidence_found', True)
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == False, f"1 evidence should fail >= 2 requirement"
        
        # Test with 0 evidence (should fail)
        self.character.properties = {}  # Clear all
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == False, f"0 evidence should fail >= 2 requirement"
    
    def test_evidence_equality_operator_still_works(self):
        """Test that == operator still works for backward compatibility."""
        # Set up exactly 2 evidence
        self.character.set_property('partner_evidence_found', True)
        self.character.set_property('sacred_map_found', True)
        
        # Test == 2 requirement (should pass)
        requirement = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 2,
            'operator': '=='
        }
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == True, f"2 evidence should pass == 2 requirement"
        
        # Test with 3 evidence (should fail)
        self.character.set_property('priest_diary_found', True)
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == False, f"3 evidence should fail == 2 requirement"
    
    def test_evidence_default_operator_is_equality(self):
        """Test that default operator is equality for backward compatibility."""
        # Set up exactly 2 evidence
        self.character.set_property('partner_evidence_found', True)
        self.character.set_property('sacred_map_found', True)
        
        # Test without operator (should default to ==)
        requirement = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 2
        }
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == True, f"2 evidence should pass == 2 requirement (default operator)"
        
        # Test with 3 evidence (should fail)
        self.character.set_property('priest_diary_found', True)
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == False, f"3 evidence should fail == 2 requirement (default operator)"
    
    def test_other_numeric_operators(self):
        """Test other numeric operators."""
        # Set up 3 evidence
        self.character.set_property('partner_evidence_found', True)
        self.character.set_property('sacred_map_found', True)
        self.character.set_property('priest_diary_found', True)
        
        # Test > 2 (should pass with 3)
        requirement = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 2,
            'operator': '>'
        }
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == True, f"3 evidence should pass > 2 requirement"
        
        # Test <= 3 (should pass with 3)
        requirement = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 3,
            'operator': '<='
        }
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == True, f"3 evidence should pass <= 3 requirement"
        
        # Test < 3 (should fail with 3)
        requirement = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 3,
            'operator': '<'
        }
        
        handled, passed, error = evaluate_requirement(self.character, None, requirement, {})
        assert handled == True and passed == False, f"3 evidence should fail < 3 requirement"
