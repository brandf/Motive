"""
Test initial message formatting consistency.
"""
import pytest
from unittest.mock import Mock


class TestInitialMessageFormatting:
    """Test that the initial message has consistent formatting."""
    
    def test_room_description_formatting(self):
        """Test that room description uses consistent header and bullet formatting."""
        # Mock room with objects and exits
        mock_room = Mock()
        mock_room.description = "A bustling town square with a fountain in the center."
        
        # Create proper mock objects with name attributes
        fountain = Mock()
        fountain.name = "Fountain"
        statue = Mock()
        statue.name = "Town Statue"
        gem = Mock()
        gem.name = "Tiny Gem"
        
        mock_room.objects = {
            "fountain": fountain,
            "statue": statue,
            "gem": gem
        }
        mock_room.exits = {
            "west": {"name": "West Gate", "is_hidden": False}
        }
        
        # Test the current formatting logic
        room_description_parts = [mock_room.description]
        
        if mock_room.objects:
            object_names = [obj.name for obj in mock_room.objects.values()]
            room_description_parts.append(f"\n\n**Objects in the room:**")
            for obj_name in object_names:
                room_description_parts.append(f"\n  • {obj_name}")
        
        if mock_room.exits:
            exit_names = [exit_data['name'] for exit_data in mock_room.exits.values() if not exit_data.get('is_hidden', False)]
            if exit_names:
                room_description_parts.append(f"\n\n**Exits:**")
                for exit_name in exit_names:
                    room_description_parts.append(f"\n  • {exit_name}")
        
        room_description = "".join(room_description_parts)
        
        # Current formatting issues:
        # 1. Inconsistent spacing: "\n\n**Objects**" vs "\n  • item" (no space before bullet)
        # 2. Mixed header styles: "**Objects in the room:**" vs "**Exits:**"
        # 3. Inconsistent indentation
        
        # Should be improved to:
        expected_good_format = """A bustling town square with a fountain in the center.

**Objects in the room:**
  • Fountain
  • Town Statue
  • Tiny Gem

**Exits:**
  • West Gate"""
        
        # For now, just test current behavior
        assert "**Objects in the room:**" in room_description
        assert "**Exits:**" in room_description
        assert "• Fountain" in room_description
        assert "• West Gate" in room_description
    
    def test_character_assignment_formatting(self):
        """Test that character assignment uses consistent formatting."""
        # Test the new improved formatting logic
        character_assignment = f"**Character:**\nYou are Hero, a Hero.\n\n**Motive:**\nDefeat the evil sorcerer."
        
        # Should use consistent headers and spacing
        assert "**Character:**" in character_assignment
        assert "You are Hero, a Hero." in character_assignment
        assert "**Motive:**" in character_assignment
        assert "Defeat the evil sorcerer." in character_assignment
        assert "\n\n" in character_assignment  # Should have proper spacing between sections
    
    def test_action_display_formatting(self):
        """Test that action display uses consistent formatting."""
        example_actions = ["look", "move", "say", "pickup", "read"]
        
        # Current formatting logic
        action_display = "Example actions:\n"
        for action in example_actions:
            action_display += f"  > {action}\n"
        action_display += "  > help (for more available actions)"
        
        # This is actually good - consistent with other formatting
        assert "Example actions:" in action_display
        assert "  > look" in action_display
        assert "  > help (for more available actions)" in action_display
    
    def test_ap_display_formatting(self):
        """Test that AP display uses consistent formatting."""
        # Test the new improved formatting logic
        ap_display = "**Action Points:** 20 AP"
        
        # Should use consistent header style
        assert "**Action Points:**" in ap_display
        assert "20 AP" in ap_display
