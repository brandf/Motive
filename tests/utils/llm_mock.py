from contextlib import contextmanager
from unittest.mock import patch, MagicMock


@contextmanager
def llm_script(scripts_by_player_name: dict[str, str], default: str = "> pass", manual: str = "Test Manual"):
    # Track turn counts per player
    turn_counts = {}
    
    async def fake_get_response_and_update_history(self, messages_for_llm):
        # Get the full script for this player
        full_script = scripts_by_player_name.get(self.name, default)
        
        # Split the script into individual actions
        actions = [line.strip() for line in full_script.split('\n') if line.strip()]
        
        # Get current turn count for this player
        turn_counts[self.name] = turn_counts.get(self.name, 0)
        current_turn = turn_counts[self.name]
        
        # Return the action for this turn, or pass if we're out of actions
        if current_turn < len(actions):
            action = actions[current_turn]
        else:
            action = "> pass"
        
        # Increment turn count for next time
        turn_counts[self.name] += 1
        
        return type("_AI", (), {"content": action})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value=manual),
    ):
        yield


