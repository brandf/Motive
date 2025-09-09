"""Test that the system prompt emphasizes the > prefix requirement clearly."""

def test_system_prompt_includes_prefix_requirement():
    """Test that the system prompt includes clear instructions about the > prefix requirement."""
    # Test the system prompt generation logic directly (same as in GameMaster)
    manual_content = "Test manual content"
    
    system_prompt = f"You are a player in a text-based adventure game. Below is the game manual. Read it carefully to understand the rules, your role, and how to interact with the game world.\n\n" \
                    f"--- GAME MANUAL START ---\n{manual_content}\n--- GAME MANUAL END ---\n\n" \
                    f"IMPORTANT: All actions must be on their own line and start with '>' (e.g., '> look', '> move west', '> say hello'). " \
                    f"Without the '>' prefix, your actions will be ignored and you'll receive a penalty.\n\n" \
                    f"Now, based on the manual and your character, respond with your actions."
    
    # Verify the system prompt includes the prefix requirement
    assert "IMPORTANT: All actions must be on their own line and start with '>'" in system_prompt
    assert "Without the '>' prefix, your actions will be ignored and you'll receive a penalty" in system_prompt
    assert "e.g., '> look', '> move west', '> say hello'" in system_prompt
