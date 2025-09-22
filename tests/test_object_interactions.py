"""
Test object interactions for Detective Thorne's motive.

This test verifies that objects properly set the required properties
when interacted with, enabling motive completion.
"""

import pytest
from unittest.mock import Mock, patch
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from motive.game_master import GameMaster
from motive.game_object import GameObject


class TestObjectInteractions:
    """Test object interaction mechanics for Detective Thorne's motive."""
    
    @pytest.mark.asyncio
    async def test_cult_roster_look_sets_cult_hierarchy_discovered(self):
        """Test that looking at Cult Roster sets cult_hierarchy_discovered to true."""
        # Load minimal test config
        config = load_and_validate_v2_config("minimal_game.yaml", "tests/configs/v2/object_interaction_test", validate=False)
        
        # Create game master
        game_master = GameMaster(config, "test_game", deterministic=True, no_file_logging=True)
        
        # Get Detective Thorne
        player = game_master.players[0]
        player_char = player.character
        
        # Verify initial cult_hierarchy_discovered is false
        assert player_char.properties.get('cult_hierarchy_discovered', False) == False
        
        # Move to Abandoned Warehouse where Cult Roster is located
        abandoned_warehouse = game_master.rooms['abandoned_warehouse']
        player_char.current_room_id = 'abandoned_warehouse'
        
        # Find Cult Roster object
        cult_roster = None
        for obj in abandoned_warehouse.objects.values():
            if obj.name == "Cult Roster":
                cult_roster = obj
                break
        
        assert cult_roster is not None, "Cult Roster object not found in Abandoned Warehouse"                                   
        
        # Debug: Check if object has interactions field
        print(f"Object interactions: {getattr(cult_roster, 'interactions', 'NO INTERACTIONS FIELD')}")
        print(f"Object attributes: {dir(cult_roster)}")
        
        # Debug: Check if room can find the object by name
        found_object = abandoned_warehouse.get_object("Cult Roster")
        print(f"Found object by name 'Cult Roster': {found_object}")
        print(f"Found object by ID 'cult_roster': {abandoned_warehouse.get_object('cult_roster')}")

        # Mock LLM response for look action
        from langchain_core.messages import AIMessage
        with patch.object(player, 'get_response_and_update_history') as mock_response:
            mock_response.return_value = AIMessage(content="> look \"Cult Roster\"")
            
            # Execute look action
            events, feedback = await game_master._execute_player_turn(player, round_num=1)
            
            # Verify cult_hierarchy_discovered was set to true
            assert player_char.properties.get('cult_hierarchy_discovered', False) == True, "cult_hierarchy_discovered should be set to true after looking at Cult Roster"
    
