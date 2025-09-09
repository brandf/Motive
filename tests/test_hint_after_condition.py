"""Test the 'after' condition in hint when clauses."""

def test_hint_after_condition():
    """Test that hints with 'after' conditions only show after the referenced hint is executed."""
    # Mock hint data with after conditions
    hints = [
        {
            "hint_id": "first_hint",
            "hint_action": "> say \"Hello everyone!\"",
            "when": {
                "round": 1,
                "players": ["Lyra"]
            }
        },
        {
            "hint_id": "second_hint",
            "hint_action": "> whisper Arion \"Did you hear that?\"",
            "when": {
                "round": 1,
                "players": ["Arion"],
                "after": "first_hint"  # Only show after first_hint is executed
            }
        },
        {
            "hint_id": "third_hint",
            "hint_action": "> shout \"I heard it too!\"",
            "when": {
                "round": 1,
                "players": ["Arion"],
                "after": "second_hint"  # Only show after second_hint is executed
            }
        }
    ]
    
    # Mock executed hints tracking - start with no hints executed
    executed_hints = {}
    
    # Test hint evaluation logic with after conditions
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
        
        # Check after condition (hint should only show after another hint was executed)
        if "after" in when_condition:
            after_hint_id = when_condition["after"]
            if after_hint_id not in executed_hints:
                return False  # Required hint hasn't been executed by anyone yet
            # Note: We don't check if the current player executed the prerequisite hint
            # The hint just needs to be executed by someone
        
        return True
    
    # Test cases
    # Initially, only Lyra should see the first hint
    print("Lyra hints:", evaluate_hints("Lyra", 1))
    print("Arion hints:", evaluate_hints("Arion", 1))
    assert evaluate_hints("Lyra", 1) == ["> say \"Hello everyone!\""]
    assert evaluate_hints("Arion", 1) == []  # Arion shouldn't see second_hint yet because first_hint wasn't executed by anyone
    
    # After Lyra executes first_hint, Arion should see second_hint
    executed_hints["first_hint"] = {"Lyra"}  # Lyra executes first_hint
    assert evaluate_hints("Arion", 1) == ["> whisper Arion \"Did you hear that?\""]
    
    # Arion shouldn't see third_hint yet because second_hint hasn't been executed
    assert evaluate_hints("Arion", 1) == ["> whisper Arion \"Did you hear that?\""]
    
    # After Arion executes second_hint, he should see third_hint (but not second_hint since he already executed it)
    executed_hints["second_hint"] = {"Arion"}
    assert evaluate_hints("Arion", 1) == ["> shout \"I heard it too!\""]
    
    # Lyra should not see any hints now (she already executed the first hint, and she's not targeted by second/third hints)
    assert evaluate_hints("Lyra", 1) == []


def test_hint_after_condition_different_players():
    """Test that 'after' conditions work correctly when different players execute the prerequisite hint."""
    # Mock hint data where Player A's hint depends on Player B's hint
    hints = [
        {
            "hint_id": "player_b_hint",
            "hint_action": "> say \"I found something!\"",
            "when": {
                "round": 1,
                "players": ["PlayerB"]
            }
        },
        {
            "hint_id": "player_a_response",
            "hint_action": "> whisper PlayerB \"What did you find?\"",
            "when": {
                "round": 1,
                "players": ["PlayerA"],
                "after": "player_b_hint"  # PlayerA's hint depends on PlayerB's hint
            }
        }
    ]
    
    # Mock executed hints tracking
    executed_hints = {
        "player_b_hint": {"PlayerB"}  # Only PlayerB has executed their hint
    }
    
    def evaluate_when_condition(when_condition: dict, player_name: str, round_num: int) -> bool:
        """Evaluate a structured when condition to determine if a hint should be shown."""
        if not when_condition:
            return True
        
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
        
        # Check after condition
        if "after" in when_condition:
            after_hint_id = when_condition["after"]
            if after_hint_id not in executed_hints:
                return False  # Required hint hasn't been executed by anyone yet
            # Note: We don't check if the current player executed the prerequisite hint
            # The hint just needs to be executed by someone
        
        return True
    
    def evaluate_hints(player_name: str, round_num: int):
        applicable_hints = []
        for hint in hints:
            hint_id = hint.get("hint_id", "")
            if hint_id and hint_id in executed_hints and player_name in executed_hints[hint_id]:
                continue
            
            when_condition = hint.get("when", {})
            if not evaluate_when_condition(when_condition, player_name, round_num):
                continue
            
            hint_action = hint.get("hint_action", "")
            if hint_action:
                applicable_hints.append(hint_action)
        
        return applicable_hints
    
    # Test cases
    # PlayerB should not see their hint (they already executed it)
    assert evaluate_hints("PlayerB", 1) == []
    
    # PlayerA should see their response hint because PlayerB executed the prerequisite
    assert evaluate_hints("PlayerA", 1) == ["> whisper PlayerB \"What did you find?\""]
    
    # Unknown player should see nothing
    assert evaluate_hints("UnknownPlayer", 1) == []
