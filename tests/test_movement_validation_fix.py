#!/usr/bin/env python3
"""
Test to verify that movement validation and exit alias resolution work correctly.
"""

import pytest
from motive.game_initializer import GameInitializer
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config


class TestMovementValidationFix:
    """Test that movement validation works correctly with v2 configs."""
    
    def test_exit_parsing_from_v2_config(self):
        """Test that exits are parsed correctly from v2 config string format."""
        # Load v2 config
        config = load_and_validate_v2_config("game_v2.yaml", "configs")
        
        # Create GameInitializer
        import logging
        logger = logging.getLogger("test")
        initializer = GameInitializer(config, "test_game", logger)
        
        # Load configurations
        initializer._load_configurations()
        
        # Debug: Check what rooms are loaded
        print(f"DEBUG: Available rooms: {list(initializer.game_rooms.keys())}")
        
        # Check that town_square room has exits parsed correctly
        town_square_room = initializer.game_rooms.get('town_square')
        assert town_square_room is not None, f"town_square room should exist. Available rooms: {list(initializer.game_rooms.keys())}"
        
        print(f"DEBUG: town_square_room keys: {list(town_square_room.keys())}")
        print(f"DEBUG: town_square_room exits type: {type(town_square_room.get('exits'))}")
        print(f"DEBUG: town_square_room exits value: {town_square_room.get('exits')}")
        
        exits = town_square_room.get('exits', {})
        assert isinstance(exits, dict), "exits should be parsed as a dictionary"
        assert len(exits) > 0, "town_square should have exits"
        
        # Check specific exit
        tavern_exit = exits.get('tavern')
        assert tavern_exit is not None, "tavern exit should exist"
        assert tavern_exit['name'] == 'Rusty Anchor Tavern', "exit name should be correct"
        assert tavern_exit['destination_room_id'] == 'tavern', "destination should be correct"
        assert 'tavern' in tavern_exit['aliases'], "aliases should include tavern"
        assert 'bar' in tavern_exit['aliases'], "aliases should include bar"
        
        print(f"✅ Exit parsing test passed. Found {len(exits)} exits in town_square")
        for exit_id, exit_data in exits.items():
            print(f"  - {exit_id}: {exit_data['name']} -> {exit_data['destination_room_id']}")
    
    def test_room_creation_with_exits(self):
        """Test that rooms are created with proper exit structure."""
        # Load v2 config
        config = load_and_validate_v2_config("game_v2.yaml", "configs")
        
        # Create GameInitializer
        import logging
        logger = logging.getLogger("test")
        initializer = GameInitializer(config, "test_game", logger)
        
        # Load configurations
        initializer._load_configurations()
        
        # Create rooms
        initializer._instantiate_rooms_and_objects()
        
        # Check that town_square room was created
        town_square_room = initializer.rooms.get('town_square')
        assert town_square_room is not None, "town_square room should be created"
        
        # Check that exits are accessible
        exits = town_square_room.exits
        assert isinstance(exits, dict), "room.exits should be a dictionary"
        assert len(exits) > 0, "room should have exits"
        
        # Check specific exit structure
        tavern_exit = exits.get('tavern')
        assert tavern_exit is not None, "tavern exit should exist in room"
        assert tavern_exit['name'] == 'Rusty Anchor Tavern', "exit name should be correct"
        assert tavern_exit['destination_room_id'] == 'tavern', "destination should be correct"
        
        print(f"✅ Room creation test passed. town_square has {len(exits)} exits")
        for exit_id, exit_data in exits.items():
            print(f"  - {exit_id}: {exit_data['name']} -> {exit_data['destination_room_id']}")
