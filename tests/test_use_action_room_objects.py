"""Test that use action works on both inventory and room objects."""

import pytest
from unittest.mock import Mock, patch
from motive.hooks.core_hooks import handle_use_action
from motive.game_object import GameObject
from motive.character import Character
from motive.room import Room


def test_use_action_works_on_inventory_objects():
    """Test that use action works on objects in player inventory (current behavior)."""
    # Create mock game master
    game_master = Mock()
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    game_master.rooms = {"test_room": test_room}
    
    # Create test player with object in inventory
    player = Character(
        char_id="test_player",
        name="TestPlayer", 
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Create object in inventory
    inventory_object = GameObject(
        obj_id="torch",
        name="Torch",
        description="A burning torch",
        current_location_id="test_player",
        properties={"is_lit": True}
    )
    player.inventory = {"torch": inventory_object}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action on inventory object
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Torch"})
    
    # Should succeed
    assert len(feedback) > 0
    assert any("You use the Torch" in msg or "You light the Torch" in msg for msg in feedback)


def test_use_action_now_works_on_room_objects():
    """Test that use action now works on room objects (after our fix)."""
    # Create mock game master
    game_master = Mock()
    
    # Create test room with object
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create object in room
    room_object = GameObject(
        obj_id="altar",
        name="Sacred Altar",
        description="A sacred altar",
        current_location_id="test_room",
        properties={"interactions": {"use": {"effects": [{"type": "generate_event", "message": "{{player_name}} uses the Sacred Altar", "observers": ["room_characters"]}]}}}
    )
    test_room.objects = {"altar": room_object}
    game_master.rooms = {"test_room": test_room}
    
    # Create test player
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character", 
        motive="Test motive",
        current_room_id="test_room"
    )
    player.inventory = {}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action on room object - should now work
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Sacred Altar"})
    
    # Should succeed after fix
    assert len(feedback) > 0
    assert any("You use the Sacred Altar" in msg for msg in feedback)


def test_use_action_should_work_on_room_objects_after_fix():
    """Test that use action should work on room objects after our fix."""
    # This test will pass after we implement the fix
    # Create mock game master
    game_master = Mock()
    
    # Create test room with object
    test_room = Room(
        room_id="test_room",
        name="Test Room", 
        description="A test room",
        exits={}
    )
    
    # Create object in room with use interaction
    room_object = GameObject(
        obj_id="altar",
        name="Sacred Altar",
        description="A sacred altar",
        current_location_id="test_room",
        properties={"interactions": {"use": {"effects": [{"type": "generate_event", "message": "{{player_name}} uses the Sacred Altar", "observers": ["room_characters"]}]}}}
    )
    test_room.objects = {"altar": room_object}
    game_master.rooms = {"test_room": test_room}
    
    # Create test player
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive", 
        current_room_id="test_room"
    )
    player.inventory = {}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action on room object - should work after fix
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Sacred Altar"})
    
    # Should succeed after fix
    assert len(feedback) > 0
    assert any("You use the Sacred Altar" in msg for msg in feedback)


def test_use_action_prioritizes_inventory_over_room():
    """Test that use action prioritizes inventory objects over room objects when both exist."""
    # Create mock game master
    game_master = Mock()
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room", 
        exits={}
    )
    
    # Create object in room
    room_object = GameObject(
        obj_id="torch_room",
        name="Torch",
        description="A torch on the wall",
        current_location_id="test_room",
        properties={"interactions": {"use": {"effects": [{"type": "generate_event", "message": "{{player_name}} uses the wall torch", "observers": ["room_characters"]}]}}}
    )
    test_room.objects = {"torch_room": room_object}
    game_master.rooms = {"test_room": test_room}
    
    # Create test player with same-named object in inventory
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Create object in inventory with same name
    inventory_object = GameObject(
        obj_id="torch_inv",
        name="Torch", 
        description="A torch in your hand",
        current_location_id="test_player",
        properties={"is_lit": True}
    )
    player.inventory = {"torch_inv": inventory_object}
    
    # Create mock action config
    action_config = Mock()
    
    # Test use action - should use inventory object, not room object
    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Torch"})
    
    # Should use inventory object (prioritized)
    assert len(feedback) > 0
    assert "You use the Torch" in feedback[0] or "You light the Torch" in feedback[0]
    # Should NOT use room object
    assert "wall torch" not in feedback[0]


def test_evidence_compiler_requires_documents():
    game_master = Mock()

    test_room = Room("test_room", "Test Room", "", {})
    compiler = GameObject(
        "evidence_compiler",
        "Evidence Compiler",
        "",
        "test_room",
        properties={
            'requires_player_properties': [
                {'property': 'town_records_found', 'label': 'Town Records'},
                {'property': 'witness_testimony_found', 'label': 'Witness Testimony'},
                {'property': 'editor_notes_found', 'label': 'Gazette roster'},
            ]
        }
    )
    test_room.objects = {"compiler": compiler}
    game_master.rooms = {"test_room": test_room}

    player = Character("test_player", "TestPlayer", "", "", current_room_id="test_room")
    player.inventory = {}

    action_config = Mock()

    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Evidence Compiler"})

    assert events == []
    assert any("Town Records" in msg for msg in feedback)


def test_evidence_compiler_allows_use_when_documents_present():
    game_master = Mock()

    test_room = Room("test_room", "Test Room", "", {})
    compiler = GameObject(
        "evidence_compiler",
        "Evidence Compiler",
        "",
        "test_room",
        properties={
            'requires_player_properties': [
                {'property': 'town_records_found', 'label': 'Town Records'},
                {'property': 'witness_testimony_found', 'label': 'Witness Testimony'},
                {'property': 'editor_notes_found', 'label': 'Gazette roster'},
            ]
        }
    )
    test_room.objects = {"compiler": compiler}
    game_master.rooms = {"test_room": test_room}

    player = Character("test_player", "TestPlayer", "", "", current_room_id="test_room")
    player.inventory = {}
    player.set_property('town_records_found', True)
    player.set_property('witness_testimony_found', True)
    player.set_property('editor_notes_found', True)

    action_config = Mock()

    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Evidence Compiler"})

    assert any("You use" in msg for msg in feedback)


def test_quest_board_use_trains_recruits():
    game_master = Mock()

    room = Room("guild", "Guild Hall", "", {})
    board = GameObject(
        "quest_board",
        "Quest Board",
        "",
        "guild",
        properties={
            'quest_workflows': {
                'train_property': 'adventurers_trained',
                'train_feedback': "You coordinate guild recruits in drills.",
                'train_event': "{{player_name}} drills the guild recruits.",
                'defend_property': 'town_defended',
                'defend_feedback': "You redeploy patrols to defend Blackwater.",
                'defend_event': "{{player_name}} posts guild patrols across the town.",
                'completed_feedback': "The board lists no new assignments."
            }
        }
    )
    room.objects = {"board": board}
    game_master.rooms = {"guild": room}

    player = Character("guild_master", "Guild Master", "", "", current_room_id="guild")
    player.inventory = {}

    action_config = Mock()

    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Quest Board"})

    assert player.get_property('adventurers_trained') is True
    assert any("drill" in msg.lower() for msg in feedback)
    assert events


def test_quest_board_use_secures_town_after_training():
    game_master = Mock()

    room = Room("guild", "Guild Hall", "", {})
    board = GameObject(
        "quest_board",
        "Quest Board",
        "",
        "guild",
        properties={
            'quest_workflows': {
                'train_property': 'adventurers_trained',
                'train_feedback': "You coordinate guild recruits in drills.",
                'train_event': "{{player_name}} drills the guild recruits.",
                'defend_property': 'town_defended',
                'defend_feedback': "You redeploy patrols to defend Blackwater.",
                'defend_event': "{{player_name}} posts guild patrols across the town.",
                'completed_feedback': "The board lists no new assignments."
            }
        }
    )
    room.objects = {"board": board}
    game_master.rooms = {"guild": room}

    player = Character("guild_master", "Guild Master", "", "", current_room_id="guild")
    player.inventory = {}
    player.set_property('adventurers_trained', True)

    action_config = Mock()

    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Quest Board"})

    assert player.get_property('town_defended') is True
    assert any("patrols" in msg.lower() for msg in feedback)
    assert events


def test_quest_board_use_after_completion():
    game_master = Mock()

    room = Room("guild", "Guild Hall", "", {})
    board = GameObject(
        "quest_board",
        "Quest Board",
        "",
        "guild",
        properties={
            'quest_workflows': {
                'train_property': 'adventurers_trained',
                'train_feedback': "You coordinate guild recruits in drills.",
                'train_event': "{{player_name}} drills the guild recruits.",
                'defend_property': 'town_defended',
                'defend_feedback': "You redeploy patrols to defend Blackwater.",
                'defend_event': "{{player_name}} posts guild patrols across the town.",
                'completed_feedback': "The board lists no new assignments."
            }
        }
    )
    room.objects = {"board": board}
    game_master.rooms = {"guild": room}

    player = Character("guild_master", "Guild Master", "", "", current_room_id="guild")
    player.inventory = {}
    player.set_property('adventurers_trained', True)
    player.set_property('town_defended', True)

    action_config = Mock()

    events, feedback = handle_use_action(game_master, player, action_config, {"object_name": "Quest Board"})

    assert events == []
    assert any("no new assignments" in msg.lower() for msg in feedback)
