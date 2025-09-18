import pytest
from motive.action_parser import parse_player_response
from motive.config import ActionConfig, ParameterConfig

def test_action_aliases_basic():
    """Test that action aliases redirect to the correct action."""
    # Mock available actions
    available_actions = {
        'look': ActionConfig(
            id='look',
            name='look',
            description='Look around',
            cost=10,
            category='observation',
            parameters=[ParameterConfig(name='target', type='string', description='Target to look at', required=True)],
            requirements=[],
            effects=[]
        )
    }
    
    # Mock room objects with aliases
    room_objects = {
        'quest_board': {
            'action_aliases': {
                'read': 'look',
                'investigate': 'look'
            }
        }
    }
    
    # Test that 'read' gets redirected to 'look'
    parsed_actions, invalid_actions = parse_player_response(
        "> read \"Quest Board\"", 
        available_actions, 
        room_objects
    )
    
    assert len(parsed_actions) == 1
    assert len(invalid_actions) == 0
    action_config, params = parsed_actions[0]
    assert action_config.name == 'look'
    assert params['target'] == 'Quest Board'
    
    # Test that 'investigate' gets redirected to 'look'
    parsed_actions, invalid_actions = parse_player_response(
        "> investigate \"Quest Board\"", 
        available_actions, 
        room_objects
    )
    
    assert len(parsed_actions) == 1
    assert len(invalid_actions) == 0
    action_config, params = parsed_actions[0]
    assert action_config.name == 'look'
    assert params['target'] == 'Quest Board'

def test_action_aliases_no_match():
    """Test that actions without aliases still work normally."""
    available_actions = {
        'look': ActionConfig(
            id='look',
            name='look',
            description='Look around',
            cost=10,
            category='observation',
            parameters=[ParameterConfig(name='target', type='string', description='Target to look at', required=True)],
            requirements=[],
            effects=[]
        )
    }
    
    room_objects = {
        'quest_board': {
            'action_aliases': {
                'read': 'look'
            }
        }
    }
    
    # Test that 'look' works normally
    parsed_actions, invalid_actions = parse_player_response(
        "> look \"Quest Board\"", 
        available_actions, 
        room_objects
    )
    
    assert len(parsed_actions) == 1
    assert len(invalid_actions) == 0
    action_config, params = parsed_actions[0]
    assert action_config.name == 'look'
    assert params['target'] == 'Quest Board'
    
    # Test that unknown action fails
    parsed_actions, invalid_actions = parse_player_response(
        "> unknown \"Quest Board\"", 
        available_actions, 
        room_objects
    )
    
    assert len(parsed_actions) == 0
    assert len(invalid_actions) == 1
    assert "unknown" in invalid_actions[0]

def test_action_aliases_no_room_objects():
    """Test that action aliases don't interfere when no room objects are provided."""
    available_actions = {
        'look': ActionConfig(
            id='look',
            name='look',
            description='Look around',
            cost=10,
            category='observation',
            parameters=[ParameterConfig(name='target', type='string', description='Target to look at', required=True)],
            requirements=[],
            effects=[]
        )
    }
    
    # Test without room objects
    parsed_actions, invalid_actions = parse_player_response(
        "> read \"Quest Board\"", 
        available_actions, 
        None
    )
    
    assert len(parsed_actions) == 0
    assert len(invalid_actions) == 1
    assert "read" in invalid_actions[0]

def test_action_aliases_multiple_objects():
    """Test that aliases work with multiple objects in a room."""
    available_actions = {
        'look': ActionConfig(
            id='look',
            name='look',
            description='Look around',
            cost=10,
            category='observation',
            parameters=[ParameterConfig(name='target', type='string', description='Target to look at', required=True)],
            requirements=[],
            effects=[]
        )
    }
    
    room_objects = {
        'quest_board': {
            'action_aliases': {
                'read': 'look'
            }
        },
        'fresh_evidence': {
            'action_aliases': {
                'investigate': 'look',
                'examine': 'look'
            }
        }
    }
    
    # Test read alias on quest board
    parsed_actions, invalid_actions = parse_player_response(
        "> read \"Quest Board\"", 
        available_actions, 
        room_objects
    )
    
    assert len(parsed_actions) == 1
    assert len(invalid_actions) == 0
    action_config, params = parsed_actions[0]
    assert action_config.name == 'look'
    assert params['target'] == 'Quest Board'
    
    # Test investigate alias on fresh evidence
    parsed_actions, invalid_actions = parse_player_response(
        "> investigate \"Fresh Evidence\"", 
        available_actions, 
        room_objects
    )
    
    assert len(parsed_actions) == 1
    assert len(invalid_actions) == 0
    action_config, params = parsed_actions[0]
    assert action_config.name == 'look'
    assert params['target'] == 'Fresh Evidence'
    
    # Test examine alias on fresh evidence
    parsed_actions, invalid_actions = parse_player_response(
        "> examine \"Fresh Evidence\"", 
        available_actions, 
        room_objects
    )
    
    assert len(parsed_actions) == 1
    assert len(invalid_actions) == 0
    action_config, params = parsed_actions[0]
    assert action_config.name == 'look'
    assert params['target'] == 'Fresh Evidence'
