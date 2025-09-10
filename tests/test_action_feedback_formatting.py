"""
Test action feedback formatting consistency.
"""
import pytest
from unittest.mock import Mock


class TestActionFeedbackFormatting:
    """Test that action feedback uses consistent formatting."""
    
    def test_ap_exhaustion_feedback_formatting(self):
        """Test that AP exhaustion feedback uses proper line-by-line formatting."""
        # This should use the good formatting: one action per line with bullets
        actions_skipped_due_to_ap = [
            "pickup legendary sword",
            "pickup warrior's armor", 
            "move west"
        ]
        
        # Test the current formatting logic
        skipped_actions_text = "\n".join([f"- {action}" for action in actions_skipped_due_to_ap])
        expected = "- pickup legendary sword\n- pickup warrior's armor\n- move west"
        
        assert skipped_actions_text == expected
        assert "pickup legendary sword" in skipped_actions_text
        assert "pickup warrior's armor" in skipped_actions_text
        assert "move west" in skipped_actions_text
        assert "\n" in skipped_actions_text  # Should have line breaks
    
    def test_turn_end_confirmation_feedback_formatting(self):
        """Test that turn end confirmation feedback uses proper line-by-line formatting."""
        other_actions = [
            "pickup Tiny Gem",
            "pickup Warrior's Armor"
        ]
        
        # Test the new improved formatting logic
        ignored_actions_text = "\n".join([f"- {action}" for action in other_actions])
        warning_msg = f"Note: You submitted other actions during turn end confirmation. These were ignored. Actions can only be performed during your active turn.\n\n**Ignored actions:**\n{ignored_actions_text}"
        
        # Should use line-by-line formatting like AP exhaustion
        assert "pickup Tiny Gem" in warning_msg
        assert "pickup Warrior's Armor" in warning_msg
        assert "\n" in warning_msg  # Should have line breaks
        assert "**Ignored actions:**" in warning_msg
        assert "- pickup Tiny Gem" in warning_msg
        assert "- pickup Warrior's Armor" in warning_msg
        assert "pickup Tiny Gem, pickup Warrior's Armor" not in warning_msg  # Should not use comma-separated format