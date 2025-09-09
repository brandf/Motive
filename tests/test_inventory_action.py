"""Test the look inventory functionality to view carried items."""

import pytest
from motive.game_objects import GameObject
from motive.player import PlayerCharacter
from motive.hooks.core_hooks import look_at_target


def test_inventory_action_empty():
    """Test inventory action when player has no items."""
    # Create a player character with empty inventory
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Mock game master (not used in this test)
    game_master = None
    
    # Mock action config (not used in this test)
    action_config = None
    
    # Call the look inventory action
    events, feedback = look_at_target(game_master, player_char, action_config, {"target": "inventory"})
    
    # Should return one event (inventory viewing is private to player)
    assert len(events) == 1
    assert events[0].event_type == "player_action"
    assert "looks at their empty inventory" in events[0].message
    assert events[0].observers == ["player"]
    
    # Should return feedback about empty inventory
    assert len(feedback) == 1
    assert "Your inventory is empty" in feedback[0]


def test_inventory_action_with_items():
    """Test inventory action when player has items."""
    # Create a player character
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Add some items to inventory
    torch = GameObject(
        obj_id="torch_1",
        name="Torch",
        description="A wooden torch",
        current_location_id="test_player"
    )
    sword = GameObject(
        obj_id="sword_1", 
        name="Iron Sword",
        description="A sharp iron sword",
        current_location_id="test_player"
    )
    potion = GameObject(
        obj_id="potion_1",
        name="Health Potion", 
        description="A red healing potion",
        current_location_id="test_player"
    )
    
    player_char.add_item_to_inventory(torch)
    player_char.add_item_to_inventory(sword)
    player_char.add_item_to_inventory(potion)
    
    # Mock game master (not used in this test)
    game_master = None
    
    # Mock action config (not used in this test)
    action_config = None
    
    # Call the look inventory action
    events, feedback = look_at_target(game_master, player_char, action_config, {"target": "inventory"})
    
    # Should return one event (inventory viewing is private to player)
    assert len(events) == 1
    assert events[0].event_type == "player_action"
    assert "looks at their inventory" in events[0].message
    assert events[0].observers == ["player"]
    
    # Should return feedback listing all items
    assert len(feedback) == 1
    feedback_text = feedback[0]
    
    # Should contain all item names
    assert "Torch" in feedback_text
    assert "Iron Sword" in feedback_text
    assert "Health Potion" in feedback_text
    
    # Should contain item descriptions
    assert "A wooden torch" in feedback_text
    assert "A sharp iron sword" in feedback_text
    assert "A red healing potion" in feedback_text


def test_inventory_action_single_item():
    """Test inventory action with a single item."""
    # Create a player character
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Add one item to inventory
    gem = GameObject(
        obj_id="gem_1",
        name="Ruby Gem",
        description="A sparkling red gem",
        current_location_id="test_player"
    )
    
    player_char.add_item_to_inventory(gem)
    
    # Mock game master (not used in this test)
    game_master = None
    
    # Mock action config (not used in this test)
    action_config = None
    
    # Call the look inventory action
    events, feedback = look_at_target(game_master, player_char, action_config, {"target": "inventory"})
    
    # Should return one event (inventory viewing is private to player)
    assert len(events) == 1
    assert events[0].event_type == "player_action"
    assert "looks at their inventory" in events[0].message
    assert events[0].observers == ["player"]
    
    # Should return feedback listing the item
    assert len(feedback) == 1
    feedback_text = feedback[0]
    
    # Should contain the item name and description
    assert "Ruby Gem" in feedback_text
    assert "A sparkling red gem" in feedback_text


def test_inventory_action_with_properties():
    """Test inventory action with items that have properties."""
    # Create a player character
    player_char = PlayerCharacter(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Add an item with properties
    magic_sword = GameObject(
        obj_id="magic_sword_1",
        name="Magic Sword",
        description="A sword imbued with magical energy",
        current_location_id="test_player"
    )
    magic_sword.properties = {
        "damage": 15,
        "magic_level": 3,
        "durability": 100
    }
    
    player_char.add_item_to_inventory(magic_sword)
    
    # Mock game master (not used in this test)
    game_master = None
    
    # Mock action config (not used in this test)
    action_config = None
    
    # Call the look inventory action
    events, feedback = look_at_target(game_master, player_char, action_config, {"target": "inventory"})
    
    # Should return one event (inventory viewing is private to player)
    assert len(events) == 1
    assert events[0].event_type == "player_action"
    assert "looks at their inventory" in events[0].message
    assert events[0].observers == ["player"]
    
    # Should return feedback listing the item
    assert len(feedback) == 1
    feedback_text = feedback[0]
    
    # Should contain the item name and description
    assert "Magic Sword" in feedback_text
    assert "A sword imbued with magical energy" in feedback_text
