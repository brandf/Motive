"""
Test evidence collection system for Detective Thorne's motive.

This test verifies that examining evidence objects properly increments
the evidence_found property, which is required for motive completion.
"""

import pytest
from unittest.mock import Mock, patch
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
from motive.game_master import GameMaster
from motive.game_object import GameObject


class TestEvidenceCollectionSystem:
    """Test evidence collection mechanics for Detective Thorne's motive."""
    
    @pytest.mark.asyncio
    async def test_fresh_evidence_pickup_works(self):
        """Test that picking up Fresh Evidence works correctly."""
        # Load minimal test config
        config = load_and_validate_v2_config("minimal_game.yaml", "tests/configs/v2/evidence_test", validate=False)
        
        # Create game master
        game_master = GameMaster(config, "test_game", deterministic=True, no_file_logging=True)
        
        # Get Detective Thorne
        player = game_master.players[0]
        player_char = player.character
        
        # Move to Town Square where Fresh Evidence is located
        town_square = game_master.rooms['town_square']
        player_char.current_room_id = 'town_square'
        
        # Find Fresh Evidence object
        fresh_evidence = None
        for obj in town_square.objects.values():
            if obj.name == "Fresh Evidence":
                fresh_evidence = obj
                break
        
        assert fresh_evidence is not None, "Fresh Evidence object not found in Town Square"
        
        # Mock LLM response for pickup action
        from langchain_core.messages import AIMessage
        with patch.object(player, 'get_response_and_update_history') as mock_response:
            mock_response.side_effect = [
                AIMessage(content="> pickup Fresh Evidence"),
                AIMessage(content="> continue"),
                AIMessage(content="> continue")  # For turn end confirmation
            ]
            
            # Execute pickup action
            events, feedback = await game_master._execute_player_turn(player, round_num=1)
            
            # Verify the object was picked up (moved from room to inventory)
            assert fresh_evidence.id not in town_square.objects, "Fresh Evidence should be removed from room"
            assert fresh_evidence.id in player_char.inventory, "Fresh Evidence should be in player inventory"
    
    @pytest.mark.asyncio
    async def test_partner_evidence_pickup_increments_evidence_found(self):
        """Test that picking up Partner's Evidence automatically increments evidence_found property."""
        # Load minimal test config
        config = load_and_validate_v2_config("minimal_game.yaml", "tests/configs/v2/evidence_test", validate=False)
        
        # Create game master
        game_master = GameMaster(config, "test_game", deterministic=True, no_file_logging=True)
        
        # Get Detective Thorne
        player = game_master.players[0]
        player_char = player.character
        
        # Verify initial evidence_found is 0
        assert player_char.properties.get('evidence_found', 0) == 0
        
        # Move to Town Square where Partner's Evidence is located
        town_square = game_master.rooms['town_square']
        player_char.current_room_id = 'town_square'
        
        # Find Partner's Evidence object
        partner_evidence = None
        for obj in town_square.objects.values():
            if obj.name == "Partner's Evidence":
                partner_evidence = obj
                break
        
        assert partner_evidence is not None, "Partner's Evidence object not found in Town Square"
        
        # Mock LLM response for pickup action
        from langchain_core.messages import AIMessage
        with patch.object(player, 'get_response_and_update_history') as mock_response:
            mock_response.return_value = AIMessage(content="> pickup \"Partner's Evidence\"")
            
            # Execute pickup action
            events, feedback = await game_master._execute_player_turn(player, round_num=1)
            
            # Verify evidence_found was incremented automatically on pickup
            assert player_char.properties.get('evidence_found', 0) == 1, "evidence_found should be incremented to 1 after picking up Partner's Evidence"
    
    @pytest.mark.asyncio
    async def test_notice_board_look_increments_evidence_found(self):
        """Test that looking at Notice Board increments evidence_found property."""
        # Load minimal test config
        config = load_and_validate_v2_config("minimal_game.yaml", "tests/configs/v2/evidence_test", validate=False)
        
        # Create game master
        game_master = GameMaster(config, "test_game", deterministic=True, no_file_logging=True)
        
        # Get Detective Thorne
        player = game_master.players[0]
        player_char = player.character
        
        # Verify initial evidence_found is 0
        assert player_char.properties.get('evidence_found', 0) == 0
        
        # Move to Town Square where Notice Board is located
        town_square = game_master.rooms['town_square']
        player_char.current_room_id = 'town_square'
        
        # Find Notice Board object
        notice_board = None
        for obj in town_square.objects.values():
            if obj.name == "Notice Board":
                notice_board = obj
                break
        
        assert notice_board is not None, "Notice Board object not found in Town Square"
        
        # Mock LLM response for look action followed by pass
        from langchain_core.messages import AIMessage
        with patch.object(player, 'get_response_and_update_history') as mock_response:
            # First call: look action, then pass to end turn
            mock_response.side_effect = [
                AIMessage(content="> look \"Notice Board\""),
                AIMessage(content="> pass"),
                AIMessage(content="> continue"),  # For turn end confirmation
                AIMessage(content="> continue")   # For final turn end confirmation
            ]
            
            # Execute look action
            events, feedback = await game_master._execute_player_turn(player, round_num=1)
            
            # Verify evidence_found was incremented
            assert player_char.properties.get('evidence_found', 0) == 1, "evidence_found should be incremented to 1 after looking at Notice Board"
    
    @pytest.mark.asyncio
    async def test_evidence_found_property_tracking(self):      
        """Test that evidence_found property is properly tracked across multiple interactions."""                               
        # Load minimal test config
        config = load_and_validate_v2_config("minimal_game.yaml", "tests/configs/v2/evidence_test", validate=False)             

        # Create game master
        game_master = GameMaster(config, "test_game", deterministic=True, no_file_logging=True)                                 

        # Get Detective Thorne
        player = game_master.players[0]
        player_char = player.character

        # Move to Town Square
        town_square = game_master.rooms['town_square']
        player_char.current_room_id = 'town_square'
        
        # Mock LLM responses for all interactions in a single turn
        from langchain_core.messages import AIMessage
        with patch.object(player, 'get_response_and_update_history') as mock_response:                                          
            mock_response.side_effect = [
                # Multiple actions in one turn
                AIMessage(content="> pickup \"Fresh Evidence\"\n> pickup \"Partner's Evidence\"\n> look \"Notice Board\""),
                AIMessage(content="> continue"),  # For turn end confirmation
                AIMessage(content="> continue")   # For final turn end confirmation
            ]
            
            # Execute all interactions in one turn
            await game_master._execute_player_turn(player, round_num=1)                                                         
            assert player_char.properties.get('evidence_found', 0) == 3, "evidence_found should reach 3 after interacting with all three evidence objects"
