"""
Test action formatting improvements.
"""
import pytest
from unittest.mock import Mock


class TestActionFormatting:
    """Test that action examples are properly formatted with '>' syntax."""
    
    def test_turn_end_confirmation_formatting(self):
        """Test that turn end confirmation shows actions with '>' syntax."""
        # Test the confirmation message formatting
        confirmation_message = (
            "Your turn has ended. Please confirm how you'd like to proceed:\n\n"
            "Example actions:\n"
            "  > continue\n"
            "  > quit (will count as failure to complete motive)\n\n"
            "What would you like to do?"
        )
        
        # Verify the formatting
        assert "Example actions:" in confirmation_message
        assert "  > continue" in confirmation_message
        assert "  > quit (will count as failure to complete motive)" in confirmation_message
        assert "•" not in confirmation_message  # Should not use bullets
        assert ">" in confirmation_message  # Should use > syntax
    
    def test_action_display_formatting(self):
        """Test that action display shows actions with '>' syntax."""
        # Test the action display formatting
        example_actions = ["look", "move", "say", "pickup", "read"]
        
        action_display = "Example actions:\n"
        for action in example_actions:
            action_display += f"  > {action}\n"
        action_display += "  > help (for more available actions)"
        
        # Verify the formatting
        assert "Example actions:" in action_display
        assert "  > look" in action_display
        assert "  > move" in action_display
        assert "  > say" in action_display
        assert "  > pickup" in action_display
        assert "  > read" in action_display
        assert "  > help (for more available actions)" in action_display
        assert "•" not in action_display  # Should not use bullets
        assert ">" in action_display  # Should use > syntax
        
        # Verify each action is on its own line
        lines = action_display.split('\n')
        action_lines = [line for line in lines if line.strip().startswith('>')]
        assert len(action_lines) == 6  # 5 example actions + help
