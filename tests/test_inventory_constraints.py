"""Test comprehensive inventory constraint system."""

import pytest
from motive.inventory_constraints import check_inventory_constraints, validate_inventory_transfer
from motive.game_object import GameObject
from motive.character import Character


def test_immovable_constraint():
    """Test that immovable objects cannot be added to inventory."""
    # Create immovable object
    immovable_object = GameObject(
        obj_id="fountain",
        name="Fountain",
        description="A stone fountain",
        current_location_id="test_room",
        properties={},
        tags=["immovable"]
    )
    
    # Create test player
    player = Character(
        char_id="test_player",
        name="TestPlayer",
        backstory="A test character",
        motive="Test motive",
        current_room_id="test_room"
    )
    
    # Test constraint check
    can_add, error_msg, error_event = check_inventory_constraints(
        immovable_object, player, "pickup"
    )
    
    assert not can_add
    assert "immovable" in error_msg
    assert error_event is not None
    assert "immovable" in error_event.message


def test_size_constraint():
    """Test size-based inventory constraints."""
    # Create object requiring large size
    large_object = GameObject(
        obj_id="boulder",
        name="Massive Boulder",
        description="A massive boulder",
        current_location_id="test_room",
        properties={"required_size": "large"},
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
    
    # Create large player
    large_player = Character(
        char_id="large_player",
        name="LargePlayer",
        backstory="A large character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "large"}
    )
    
    # Test with small player (should fail)
    can_add, error_msg, error_event = check_inventory_constraints(
        large_object, small_player, "pickup"
    )
    
    assert not can_add
    assert "requires size large" in error_msg
    assert "SmallPlayer is small" in error_msg
    
    # Test with large player (should succeed)
    can_add, error_msg, error_event = check_inventory_constraints(
        large_object, large_player, "pickup"
    )
    
    assert can_add
    assert error_msg is None
    assert error_event is None


def test_class_constraint():
    """Test class-based inventory constraints."""
    # Create object requiring warrior class
    warrior_sword = GameObject(
        obj_id="warrior_sword",
        name="Warrior's Blade",
        description="A sword for warriors only",
        current_location_id="test_room",
        properties={"required_class": "warrior"},
        tags=["requires_class"]
    )
    
    # Create mage player
    mage_player = Character(
        char_id="mage_player",
        name="MagePlayer",
        backstory="A mage character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"class": "mage"}
    )
    
    # Create warrior player
    warrior_player = Character(
        char_id="warrior_player",
        name="WarriorPlayer",
        backstory="A warrior character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"class": "warrior"}
    )
    
    # Test with mage player (should fail)
    can_add, error_msg, error_event = check_inventory_constraints(
        warrior_sword, mage_player, "pickup"
    )
    
    assert not can_add
    assert "requires class warrior" in error_msg
    assert "MagePlayer is mage" in error_msg
    
    # Test with warrior player (should succeed)
    can_add, error_msg, error_event = check_inventory_constraints(
        warrior_sword, warrior_player, "pickup"
    )
    
    assert can_add
    assert error_msg is None
    assert error_event is None


def test_level_constraint():
    """Test level-based inventory constraints."""
    # Create object requiring level 10
    legendary_item = GameObject(
        obj_id="legendary_item",
        name="Legendary Artifact",
        description="A powerful artifact",
        current_location_id="test_room",
        properties={"required_level": 10},
        tags=["requires_level"]
    )
    
    # Create low-level player
    low_level_player = Character(
        char_id="low_player",
        name="LowPlayer",
        backstory="A low-level character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"level": 5}
    )
    
    # Create high-level player
    high_level_player = Character(
        char_id="high_player",
        name="HighPlayer",
        backstory="A high-level character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"level": 15}
    )
    
    # Test with low-level player (should fail)
    can_add, error_msg, error_event = check_inventory_constraints(
        legendary_item, low_level_player, "pickup"
    )
    
    assert not can_add
    assert "requires level 10" in error_msg
    assert "LowPlayer is level 5" in error_msg
    
    # Test with high-level player (should succeed)
    can_add, error_msg, error_event = check_inventory_constraints(
        legendary_item, high_level_player, "pickup"
    )
    
    assert can_add
    assert error_msg is None
    assert error_event is None


def test_custom_constraints():
    """Test custom constraint system."""
    # Create object with custom constraints
    custom_object = GameObject(
        obj_id="custom_item",
        name="Custom Item",
        description="An item with custom requirements",
        current_location_id="test_room",
        properties={
            "custom_constraints": [
                {"type": "alignment", "value": "good"},
                {"type": "race", "value": "elf"}
            ]
        },
        tags=[]
    )
    
    # Create player meeting requirements
    good_elf_player = Character(
        char_id="good_elf",
        name="GoodElf",
        backstory="A good elf character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"alignment": "good", "race": "elf"}
    )
    
    # Create player not meeting requirements
    evil_human_player = Character(
        char_id="evil_human",
        name="EvilHuman",
        backstory="An evil human character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"alignment": "evil", "race": "human"}
    )
    
    # Test with good elf (should succeed)
    can_add, error_msg, error_event = check_inventory_constraints(
        custom_object, good_elf_player, "pickup"
    )
    
    assert can_add
    assert error_msg is None
    assert error_event is None
    
    # Test with evil human (should fail)
    can_add, error_msg, error_event = check_inventory_constraints(
        custom_object, evil_human_player, "pickup"
    )
    
    assert not can_add
    assert "alignment" in error_msg
    assert "EvilHuman has alignment evil" in error_msg


def test_multiple_constraints():
    """Test objects with multiple constraint types."""
    # Create object with multiple constraints
    complex_object = GameObject(
        obj_id="complex_item",
        name="Complex Item",
        description="An item with multiple requirements",
        current_location_id="test_room",
        properties={
            "required_size": "large",
            "required_class": "warrior",
            "required_level": 5
        },
        tags=["requires_size", "requires_class", "requires_level"]
    )
    
    # Create player meeting all requirements
    qualified_player = Character(
        char_id="qualified_player",
        name="QualifiedPlayer",
        backstory="A qualified character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "large", "class": "warrior", "level": 10}
    )
    
    # Create player missing one requirement
    unqualified_player = Character(
        char_id="unqualified_player",
        name="UnqualifiedPlayer",
        backstory="An unqualified character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "small", "class": "warrior", "level": 10}  # Wrong size
    )
    
    # Test with qualified player (should succeed)
    can_add, error_msg, error_event = check_inventory_constraints(
        complex_object, qualified_player, "pickup"
    )
    
    assert can_add
    assert error_msg is None
    assert error_event is None
    
    # Test with unqualified player (should fail on first constraint)
    can_add, error_msg, error_event = check_inventory_constraints(
        complex_object, unqualified_player, "pickup"
    )
    
    assert not can_add
    assert "requires size large" in error_msg
    assert "UnqualifiedPlayer is small" in error_msg


def test_inventory_transfer_validation():
    """Test the inventory transfer validation function."""
    # Create object with constraints
    constrained_object = GameObject(
        obj_id="constrained_item",
        name="Constrained Item",
        description="An item with constraints",
        current_location_id="test_room",
        properties={"required_size": "medium"},
        tags=["requires_size"]
    )
    
    # Create players
    small_player = Character(
        char_id="small_player",
        name="SmallPlayer",
        backstory="A small character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "small"}
    )
    
    medium_player = Character(
        char_id="medium_player",
        name="MediumPlayer",
        backstory="A medium character",
        motive="Test motive",
        current_room_id="test_room",
        properties={"size": "medium"}
    )
    
    # Test transfer to small player (should fail)
    can_transfer, error_msg, error_event = validate_inventory_transfer(
        constrained_object, medium_player, small_player, "give"
    )
    
    assert not can_transfer
    assert "give" in error_msg
    assert "SmallPlayer is small" in error_msg
    
    # Test transfer to medium player (should succeed)
    can_transfer, error_msg, error_event = validate_inventory_transfer(
        constrained_object, small_player, medium_player, "give"
    )
    
    assert can_transfer
    assert error_msg is None
    assert error_event is None


def test_size_hierarchy():
    """Test that size hierarchy works correctly."""
    # Test all size combinations
    size_hierarchy = {
        "tiny": 1,
        "small": 2, 
        "medium": 3,
        "large": 4,
        "huge": 5,
        "gargantuan": 6
    }
    
    for size_name, size_value in size_hierarchy.items():
        # Create object requiring this size
        size_object = GameObject(
            obj_id=f"{size_name}_object",
            name=f"{size_name.title()} Object",
            description=f"An object requiring {size_name} size",
            current_location_id="test_room",
            properties={"required_size": size_name},
            tags=["requires_size"]
        )
        
        # Test with each player size
        for player_size_name, player_size_value in size_hierarchy.items():
            player = Character(
                char_id=f"{player_size_name}_player",
                name=f"{player_size_name.title()}Player",
                backstory="A test character",
                motive="Test motive",
                current_room_id="test_room",
                properties={"size": player_size_name}
            )
            
            can_add, error_msg, error_event = check_inventory_constraints(
                size_object, player, "pickup"
            )
            
            if player_size_value >= size_value:
                # Player should be able to carry the object
                assert can_add, f"{player_size_name} player should be able to carry {size_name} object"
            else:
                # Player should not be able to carry the object
                assert not can_add, f"{player_size_name} player should not be able to carry {size_name} object"
                assert "too small" in error_msg or "requires size" in error_msg
