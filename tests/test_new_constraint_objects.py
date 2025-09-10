"""Test the new constraint objects added to the game world."""

import pytest
from motive.hooks.core_hooks import handle_pickup_action
from motive.game_object import GameObject
from motive.room import Room
from motive.character import Character


def test_tiny_gem_pickup():
    """Test that tiny gems can be picked up by any size player."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create tiny gem object
    tiny_gem = GameObject(
        obj_id="tiny_gem",
        name="Tiny Gem",
        description="A small, precious gem that sparkles in the light.",
        current_location_id="test_room",
        properties={"required_size": "tiny"},
        tags=["requires_size"]
    )
    
    # Create small player
    small_player = Character(
        char_id="small_player",
        name="SmallPlayer",
        backstory="A small character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "small"}
    )
    small_player.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    test_room.objects = {"tiny_gem": tiny_gem}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test pickup action
    events, feedback = handle_pickup_action(game_master, small_player, action_config, {"object_name": "Tiny Gem"})
    
    # Should succeed (small >= tiny)
    assert len(events) == 3  # Success case generates 3 events
    assert "tiny_gem" in small_player.inventory
    assert "tiny_gem" not in test_room.objects


def test_large_sword_size_constraint():
    """Test that large swords require large or bigger players."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create large sword object
    large_sword = GameObject(
        obj_id="large_sword",
        name="Large Sword",
        description="A massive two-handed sword that requires great strength to wield.",
        current_location_id="test_room",
        properties={"required_size": "large"},
        tags=["requires_size"]
    )
    
    # Create small player (should fail)
    small_player = Character(
        char_id="small_player",
        name="SmallPlayer",
        backstory="A small character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "small"}
    )
    small_player.inventory = {}
    
    # Create large player (should succeed)
    large_player = Character(
        char_id="large_player",
        name="LargePlayer",
        backstory="A large character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "large"}
    )
    large_player.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    test_room.objects = {"large_sword": large_sword}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test with small player (should fail)
    events, feedback = handle_pickup_action(game_master, small_player, action_config, {"object_name": "Large Sword"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "large_sword" not in small_player.inventory
    assert "large_sword" in test_room.objects
    assert "requires size large" in feedback[0]
    
    # Test with large player (should succeed)
    events, feedback = handle_pickup_action(game_master, large_player, action_config, {"object_name": "Large Sword"})
    
    assert len(events) == 3  # Success case generates 3 events
    assert "large_sword" in large_player.inventory
    assert "large_sword" not in test_room.objects


def test_warrior_armor_class_constraint():
    """Test that warrior armor requires warrior class."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create warrior armor object
    warrior_armor = GameObject(
        obj_id="warrior_armor",
        name="Warrior's Armor",
        description="Heavy plate armor that only warriors can wear.",
        current_location_id="test_room",
        properties={"required_class": "warrior"},
        tags=["requires_class"]
    )
    
    # Create mage player (should fail)
    mage_player = Character(
        char_id="mage_player",
        name="MagePlayer",
        backstory="A mage character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"class": "mage"}
    )
    mage_player.inventory = {}
    
    # Create warrior player (should succeed)
    warrior_player = Character(
        char_id="warrior_player",
        name="WarriorPlayer",
        backstory="A warrior character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"class": "warrior"}
    )
    warrior_player.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    test_room.objects = {"warrior_armor": warrior_armor}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test with mage player (should fail)
    events, feedback = handle_pickup_action(game_master, mage_player, action_config, {"object_name": "Warrior's Armor"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "warrior_armor" not in mage_player.inventory
    assert "warrior_armor" in test_room.objects
    assert "requires class warrior" in feedback[0]
    
    # Test with warrior player (should succeed)
    events, feedback = handle_pickup_action(game_master, warrior_player, action_config, {"object_name": "Warrior's Armor"})
    
    assert len(events) == 3  # Success case generates 3 events
    assert "warrior_armor" in warrior_player.inventory
    assert "warrior_armor" not in test_room.objects


def test_legendary_sword_level_constraint():
    """Test that legendary swords require high level."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create legendary sword object
    legendary_sword = GameObject(
        obj_id="legendary_sword",
        name="Legendary Sword",
        description="A sword of immense power that only high-level heroes can wield.",
        current_location_id="test_room",
        properties={"required_level": 15},
        tags=["requires_level"]
    )
    
    # Create low-level player (should fail)
    low_level_player = Character(
        char_id="low_player",
        name="LowPlayer",
        backstory="A low-level character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"level": 5}
    )
    low_level_player.inventory = {}
    
    # Create high-level player (should succeed)
    high_level_player = Character(
        char_id="high_player",
        name="HighPlayer",
        backstory="A high-level character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"level": 20}
    )
    high_level_player.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    test_room.objects = {"legendary_sword": legendary_sword}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test with low-level player (should fail)
    events, feedback = handle_pickup_action(game_master, low_level_player, action_config, {"object_name": "Legendary Sword"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "legendary_sword" not in low_level_player.inventory
    assert "legendary_sword" in test_room.objects
    assert "requires level 15" in feedback[0]
    
    # Test with high-level player (should succeed)
    events, feedback = handle_pickup_action(game_master, high_level_player, action_config, {"object_name": "Legendary Sword"})
    
    assert len(events) == 3  # Success case generates 3 events
    assert "legendary_sword" in high_level_player.inventory
    assert "legendary_sword" not in test_room.objects


def test_paladin_sword_multi_constraint():
    """Test that paladin swords require both warrior class and high level."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create paladin sword object
    paladin_sword = GameObject(
        obj_id="paladin_sword",
        name="Paladin's Sword",
        description="A holy sword that requires both warrior class and high level.",
        current_location_id="test_room",
        properties={"required_class": "warrior", "required_level": 10},
        tags=["requires_class", "requires_level"]
    )
    
    # Create mage player (should fail on class)
    mage_player = Character(
        char_id="mage_player",
        name="MagePlayer",
        backstory="A mage character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"class": "mage", "level": 15}
    )
    mage_player.inventory = {}
    
    # Create low-level warrior (should fail on level)
    low_warrior_player = Character(
        char_id="low_warrior",
        name="LowWarrior",
        backstory="A low-level warrior",
        motive="Test motive",
        current_room_id="test_room",
        properties={"class": "warrior", "level": 5}
    )
    low_warrior_player.inventory = {}
    
    # Create qualified paladin (should succeed)
    paladin_player = Character(
        char_id="paladin_player",
        name="PaladinPlayer",
        backstory="A high-level warrior",
        motive="Test motive",
        current_room_id="test_room",
        properties={"class": "warrior", "level": 15}
    )
    paladin_player.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    test_room.objects = {"paladin_sword": paladin_sword}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test with mage player (should fail on class)
    events, feedback = handle_pickup_action(game_master, mage_player, action_config, {"object_name": "Paladin's Sword"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "paladin_sword" not in mage_player.inventory
    assert "paladin_sword" in test_room.objects
    assert "requires class warrior" in feedback[0]
    
    # Test with low-level warrior (should fail on level)
    events, feedback = handle_pickup_action(game_master, low_warrior_player, action_config, {"object_name": "Paladin's Sword"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "paladin_sword" not in low_warrior_player.inventory
    assert "paladin_sword" in test_room.objects
    assert "requires level 10" in feedback[0]
    
    # Test with qualified paladin (should succeed)
    events, feedback = handle_pickup_action(game_master, paladin_player, action_config, {"object_name": "Paladin's Sword"})
    
    assert len(events) == 3  # Success case generates 3 events
    assert "paladin_sword" in paladin_player.inventory
    assert "paladin_sword" not in test_room.objects


def test_elven_artifact_custom_constraints():
    """Test that elven artifacts require custom constraints (race and alignment)."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create elven artifact object
    elven_artifact = GameObject(
        obj_id="elven_artifact",
        name="Elven Artifact",
        description="An ancient elven artifact that only elves of good alignment can use.",
        current_location_id="test_room",
        properties={
            "custom_constraints": [
                {"type": "race", "value": "elf"},
                {"type": "alignment", "value": "good"}
            ]
        },
        tags=[]
    )
    
    # Create human player (should fail on race)
    human_player = Character(
        char_id="human_player",
        name="HumanPlayer",
        backstory="A human character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"race": "human", "alignment": "good"}
    )
    human_player.inventory = {}
    
    # Create evil elf (should fail on alignment)
    evil_elf_player = Character(
        char_id="evil_elf",
        name="EvilElf",
        backstory="An evil elf character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"race": "elf", "alignment": "evil"}
    )
    evil_elf_player.inventory = {}
    
    # Create good elf (should succeed)
    good_elf_player = Character(
        char_id="good_elf",
        name="GoodElf",
        backstory="A good elf character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"race": "elf", "alignment": "good"}
    )
    good_elf_player.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    test_room.objects = {"elven_artifact": elven_artifact}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test with human player (should fail on race)
    events, feedback = handle_pickup_action(game_master, human_player, action_config, {"object_name": "Elven Artifact"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "elven_artifact" not in human_player.inventory
    assert "elven_artifact" in test_room.objects
    assert "race" in feedback[0]
    
    # Test with evil elf (should fail on alignment)
    events, feedback = handle_pickup_action(game_master, evil_elf_player, action_config, {"object_name": "Elven Artifact"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "elven_artifact" not in evil_elf_player.inventory
    assert "elven_artifact" in test_room.objects
    assert "alignment" in feedback[0]
    
    # Test with good elf (should succeed)
    events, feedback = handle_pickup_action(game_master, good_elf_player, action_config, {"object_name": "Elven Artifact"})
    
    assert len(events) == 3  # Success case generates 3 events
    assert "elven_artifact" in good_elf_player.inventory
    assert "elven_artifact" not in test_room.objects


def test_immovable_objects():
    """Test that immovable objects cannot be picked up."""
    # Create mock game master
    class MockGameMaster:
        def __init__(self):
            self.rooms = {}
            self.game_id = "test_game"
    
    # Create test room
    test_room = Room(
        room_id="test_room",
        name="Test Room",
        description="A test room",
        exits={}
    )
    
    # Create ancient altar (immovable + magically bound)
    ancient_altar = GameObject(
        obj_id="ancient_altar",
        name="Ancient Altar",
        description="A sacred altar that has been in this place for centuries.",
        current_location_id="test_room",
        properties={},
        tags=["immovable", "magically_bound"]
    )
    
    # Create town statue (immovable + too heavy)
    town_statue = GameObject(
        obj_id="town_statue",
        name="Town Statue",
        description="A large statue of the town's founder, too heavy to move.",
        current_location_id="test_room",
        properties={},
        tags=["immovable", "too_heavy"]
    )
    
    # Create any player
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    player.inventory = {}
    
    # Create mock game master
    game_master = MockGameMaster()
    game_master.rooms = {"test_room": test_room}
    test_room.objects = {"ancient_altar": ancient_altar, "town_statue": town_statue}
    
    # Create mock action config
    class MockActionConfig:
        pass
    action_config = MockActionConfig()
    
    # Test ancient altar (should fail - immovable)
    events, feedback = handle_pickup_action(game_master, player, action_config, {"object_name": "Ancient Altar"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "ancient_altar" not in player.inventory
    assert "ancient_altar" in test_room.objects
    assert "immovable" in feedback[0]
    
    # Test town statue (should fail - immovable)
    events, feedback = handle_pickup_action(game_master, player, action_config, {"object_name": "Town Statue"})
    
    assert len(events) == 1  # Error case generates 1 event
    assert "town_statue" not in player.inventory
    assert "town_statue" in test_room.objects
    assert "immovable" in feedback[0]
