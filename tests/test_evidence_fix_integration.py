"""Integration test to verify the evidence computed property fix works end-to-end."""

import pytest
from motive.character import Character


class TestEvidenceFixIntegration:
    """Test that the evidence computed property fix works in real scenarios."""
    
    def test_evidence_found_accessible_via_get_property(self):
        """Test that evidence_found computed property is accessible via get_property method."""
        # Create a character
        character = Character(
            char_id="detective_thorne",
            name="Detective Thorne",
            backstory="A seasoned detective",
            current_room_id="town_square"
        )
        
        # Set some evidence flags (simulating what happens when evidence is found)
        character.properties['partner_evidence_found'] = True
        character.properties['fresh_evidence_found'] = True
        character.properties['cult_history_found'] = True
        
        # Test direct access to computed property
        direct_count = character.evidence_found
        assert direct_count == 3, f"Direct access should return 3, got {direct_count}"
        
        # Test access via get_property (this is what the motive system uses)
        via_get_property = character.get_property('evidence_found', 0)
        assert via_get_property == 3, f"get_property should return 3, got {via_get_property}"
        
        # Test that both methods return the same value
        assert direct_count == via_get_property, "Direct access and get_property should return the same value"
    
    def test_evidence_found_updates_correctly(self):
        """Test that evidence_found updates correctly as more evidence is found."""
        character = Character(
            char_id="detective_thorne",
            name="Detective Thorne", 
            backstory="A seasoned detective",
            current_room_id="town_square"
        )
        
        # Initially no evidence
        assert character.evidence_found == 0
        assert character.get_property('evidence_found', 0) == 0
        
        # Add first piece of evidence
        character.properties['partner_evidence_found'] = True
        assert character.evidence_found == 1
        assert character.get_property('evidence_found', 0) == 1
        
        # Add second piece of evidence
        character.properties['fresh_evidence_found'] = True
        assert character.evidence_found == 2
        assert character.get_property('evidence_found', 0) == 2
        
        # Add third piece of evidence
        character.properties['cult_history_found'] = True
        assert character.evidence_found == 3
        assert character.get_property('evidence_found', 0) == 3
    
    def test_evidence_found_handles_duplicate_flags(self):
        """Test that evidence_found doesn't double-count if same flag is set multiple times."""
        character = Character(
            char_id="detective_thorne",
            name="Detective Thorne",
            backstory="A seasoned detective", 
            current_room_id="town_square"
        )
        
        # Set the same flag multiple times (shouldn't affect count)
        character.properties['partner_evidence_found'] = True
        character.properties['partner_evidence_found'] = True  # Set again
        character.properties['partner_evidence_found'] = True  # Set again
        
        # Should still only count as 1
        assert character.evidence_found == 1
        assert character.get_property('evidence_found', 0) == 1
        
        # Add another unique piece of evidence
        character.properties['fresh_evidence_found'] = True
        assert character.evidence_found == 2
        assert character.get_property('evidence_found', 0) == 2
    
    def test_evidence_found_handles_false_flags(self):
        """Test that evidence_found only counts True flags, not False ones."""
        character = Character(
            char_id="detective_thorne",
            name="Detective Thorne",
            backstory="A seasoned detective",
            current_room_id="town_square"
        )
        
        # Set some flags to True and some to False
        character.properties['partner_evidence_found'] = True
        character.properties['fresh_evidence_found'] = False  # Should not count
        character.properties['cult_history_found'] = True
        character.properties['church_records_found'] = False  # Should not count
        
        # Should only count the True flags
        assert character.evidence_found == 2
        assert character.get_property('evidence_found', 0) == 2


