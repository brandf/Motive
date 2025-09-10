"""Test whisper action with player_in_room requirement."""

import pytest
from motive.game_master import GameMaster
from motive.character import Character
from motive.room import Room
from motive.config import GameConfig, ActionConfig, ActionRequirementConfig
import yaml


def test_player_in_room_requirement_implementation():
    """Test the actual player_in_room requirement implementation."""
    from motive.room import Room
    from motive.config import ActionConfig, ActionRequirementConfig
    from motive.character import Character
    
    # Create a mock GameMaster class that only has the _check_requirements method
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.players = {}
        
        def _check_requirements(self, player_char, action_config, params):
            """Test the actual _check_requirements method from GameMaster."""
            current_room = self.rooms.get(player_char.current_room_id)
            if not current_room:
                return False, f"Character is in an unknown room: {player_char.current_room_id}.", None

            found_exit_data = None

            for req in action_config.requirements:
                if req.type == "player_in_room":
                    player_name = params.get(req.target_player_param)
                    if not player_name:
                        return False, f"Missing parameter '{req.target_player_param}' for player_in_room requirement.", None
                    
                    # Check if the target player is in the same room
                    target_player = None
                    for player in self.players.values():
                        if hasattr(player, 'character') and player.character:
                            if player.character.name.lower() == player_name.lower():
                                target_player = player.character
                                break
                    
                    if not target_player:
                        return False, f"Player '{player_name}' not found.", None
                    
                    if target_player.current_room_id != player_char.current_room_id:
                        return False, f"Player '{player_name}' is not in the same room.", None
                else:
                    return False, f"Unsupported requirement type: {req.type}", None
            
            return True, "", found_exit_data
    
    # Create test room
    room = Room(
        room_id="test_room",
        name="Test Room", 
        description="A test room",
        exits={},
        objects={}
    )
    
    # Create test player characters
    player1_char = Character(
        char_id="player1",
        name="Player1",
        backstory="Test player 1",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    player2_char = Character(
        char_id="player2", 
        name="Player2",
        backstory="Test player 2",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Create mock players
    class MockPlayer:
        def __init__(self, character):
            self.character = character
    
    mock_player1 = MockPlayer(player1_char)
    mock_player2 = MockPlayer(player2_char)
    
    # Create GameMaster and set up test data
    gm = MockGameMaster()
    gm.rooms["test_room"] = room
    gm.players["Player1"] = mock_player1
    gm.players["Player2"] = mock_player2
    
    # Create whisper action config with player_in_room requirement
    whisper_action = ActionConfig(
        id="whisper",
        name="whisper", 
        cost=10,
        description="Whisper privately to a specific player in the same room.",
        category="communication",
        parameters=[],
        requirements=[
            ActionRequirementConfig(
                type="player_in_room",
                target_player_param="player"
            )
        ],
        effects=[]
    )
    
    # Test case 1: Player exists in room - should pass
    params_valid = {"player": "Player2", "phrase": "Hello"}
    requirements_met, message, data = gm._check_requirements(player1_char, whisper_action, params_valid)
    assert requirements_met, f"Should pass when target player is in room: {message}"
    
    # Test case 2: Player doesn't exist - should fail
    params_invalid = {"player": "NonExistentPlayer", "phrase": "Hello"}
    requirements_met, message, data = gm._check_requirements(player1_char, whisper_action, params_invalid)
    assert not requirements_met, f"Should fail when target player doesn't exist: {message}"
    assert "not found" in message.lower()
    
    # Test case 3: Missing player parameter - should fail
    params_missing = {"phrase": "Hello"}
    requirements_met, message, data = gm._check_requirements(player1_char, whisper_action, params_missing)
    assert not requirements_met, f"Should fail when player parameter is missing: {message}"
    assert "missing parameter" in message.lower()
    
    # Test case 4: Player in different room - should fail
    player3_char = Character(
        char_id="player3",
        name="Player3", 
        backstory="Test player 3",
        motive="Test motive",
        current_room_id="other_room"
    )
    mock_player3 = MockPlayer(player3_char)
    gm.players["Player3"] = mock_player3
    
    params_different_room = {"player": "Player3", "phrase": "Hello"}
    requirements_met, message, data = gm._check_requirements(player1_char, whisper_action, params_different_room)
    assert not requirements_met, f"Should fail when target player is in different room: {message}"
    assert "not in the same room" in message.lower()
