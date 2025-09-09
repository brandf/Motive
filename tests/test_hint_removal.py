"""Test that hints are removed after the hinted action is executed."""

def test_hint_removal_logic():
    """Test the hint removal logic for executed hints."""
    # Mock hint data with IDs
    hints = [
        {
            "hint_id": "whisper_test",
            "hint_action": "> whisper Hero \"do you have the key?\"",
            "when": {
                "round": 1,
                "players": ["Lyra"]
            }
        },
        {
            "hint_id": "shout_test", 
            "hint_action": "> shout \"I'm looking for the amulet!\"",
            "when": {
                "round": 1,
                "players": ["Arion"]
            }
        }
    ]
    
    # Mock executed hints tracking
    executed_hints = {
        "shout_test": {"Arion"}  # Arion has executed the shout hint
    }
    
    # Test hint evaluation logic (same as in GameMaster._get_applicable_hints)
    def evaluate_hints(player_name: str, round_num: int):
        applicable_hints = []
        for hint in hints:
            # Check if hint has already been executed by this player
            hint_id = hint.get("hint_id", "")
            if hint_id and hint_id in executed_hints and player_name in executed_hints[hint_id]:
                continue  # Skip this hint as it's already been executed by this player
            
            # Check if hint applies to this player and round using structured when clause
            when_condition = hint.get("when", {})
            if not evaluate_when_condition(when_condition, player_name, round_num):
                continue
            
            hint_action = hint.get("hint_action", "")
            if hint_action:
                applicable_hints.append(hint_action)
        
        return applicable_hints
    
    def evaluate_when_condition(when_condition: dict, player_name: str, round_num: int) -> bool:
        """Evaluate a structured when condition to determine if a hint should be shown."""
        if not when_condition:
            return True  # No condition means always show
        
        # Check round condition
        if "round" in when_condition:
            required_round = when_condition["round"]
            if isinstance(required_round, int):
                if round_num < required_round:
                    return False
        
        # Check player condition
        if "players" in when_condition:
            target_players = when_condition["players"]
            if isinstance(target_players, list):
                if player_name not in target_players:
                    return False
            elif isinstance(target_players, str):
                if player_name != target_players:
                    return False
        
        return True
    
    # Test cases
    assert evaluate_hints("Lyra", 1) == ["> whisper Hero \"do you have the key?\""]  # Lyra hasn't executed whisper yet
    assert evaluate_hints("Arion", 1) == []  # Arion has already executed shout, so no hints
    assert evaluate_hints("UnknownPlayer", 1) == []  # Player not in any hints


def test_hint_marking_logic():
    """Test the logic for marking hints as executed."""
    # Mock hint data
    hints = [
        {
            "hint_id": "whisper_test",
            "hint_action": "> whisper Hero \"do you have the key?\"",
            "for_players": ["Lyra"]
        },
        {
            "hint_id": "shout_test",
            "hint_action": "> shout \"I'm looking for the amulet!\"", 
            "for_players": ["Arion"]
        }
    ]
    
    # Mock executed hints tracking
    executed_hints = {}
    
    # Test hint marking logic (same as in GameMaster._mark_hint_executed)
    def mark_hint_executed(player_name: str, action_name: str):
        for hint in hints:
            hint_id = hint.get("hint_id", "")
            if not hint_id:
                continue
                
            # Check if this player should have this hint
            if player_name not in hint.get("for_players", []):
                continue
            
            # Check if the action matches the hint
            hint_action = hint.get("hint_action", "")
            if not hint_action.startswith(">"):
                continue
                
            # Extract action from hint (e.g., "> whisper Hero" -> "whisper")
            hint_action_parts = hint_action[1:].strip().split()
            if not hint_action_parts:
                continue
                
            hint_action_name = hint_action_parts[0]
            
            # Check if the executed action matches the hint action
            if action_name == hint_action_name:
                # Mark this hint as executed by this player
                if hint_id not in executed_hints:
                    executed_hints[hint_id] = set()
                executed_hints[hint_id].add(player_name)
                return True  # Hint was marked as executed
        return False  # No hint was marked as executed
    
    # Test cases
    assert mark_hint_executed("Arion", "shout") == True  # Should mark shout_test as executed
    assert mark_hint_executed("Lyra", "whisper") == True  # Should mark whisper_test as executed
    assert mark_hint_executed("Arion", "whisper") == False  # Arion doesn't have whisper hint
    assert mark_hint_executed("Lyra", "look") == False  # look doesn't match any hint
    
    # Verify executed hints tracking
    assert executed_hints == {
        "shout_test": {"Arion"},
        "whisper_test": {"Lyra"}
    }
