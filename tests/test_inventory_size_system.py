"""
Test suite for the inventory size system.

This module tests the inventory size system including:
- Character inventory space calculations
- Object size properties
- Pickup constraints based on available space
- Inventory space display
- Edge cases and error handling

Following AGENT.md guidelines:
- Tests are completely isolated from external services
- Use real constructors and APIs
- Test both positive and negative cases
- Include boundary conditions and edge cases
"""

import pytest
from unittest.mock import Mock, patch
from motive.character import Character
from motive.game_object import GameObject
from motive.inventory_constraints import check_inventory_constraints, validate_inventory_transfer
from motive.hooks.core_hooks import handle_pickup_action, look_at_target
from motive.config import Event
from datetime import datetime


class TestCharacterInventorySpace:
    """Test the computed properties for inventory space management."""
    
    def test_empty_inventory_space_used(self):
        """Test that empty inventory shows 0 space used."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={}
        )
        assert char.inventory_space_used == 0
    
    def test_inventory_space_used_with_objects(self):
        """Test space calculation with objects of different sizes."""
        # Create objects with different sizes
        tiny_obj = GameObject(
            obj_id="tiny_item",
            name="Tiny Item",
            description="A tiny item",
            current_location_id="test_char",
            properties={"size": "tiny"}
        )
        medium_obj = GameObject(
            obj_id="medium_item", 
            name="Medium Item",
            description="A medium item",
            current_location_id="test_char",
            properties={"size": "medium"}
        )
        huge_obj = GameObject(
            obj_id="huge_item",
            name="Huge Item", 
            description="A huge item",
            current_location_id="test_char",
            properties={"size": "huge"}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character", 
            backstory="A test character",
            inventory={
                "tiny_item": tiny_obj,
                "medium_item": medium_obj,
                "huge_item": huge_obj
            }
        )
        
        # tiny=1, medium=3, huge=6 = 10 total
        assert char.inventory_space_used == 10
    
    def test_inventory_space_used_default_size(self):
        """Test that objects without size property default to medium (3 spaces)."""
        obj_no_size = GameObject(
            obj_id="no_size_item",
            name="No Size Item",
            description="An item without size property",
            current_location_id="test_char",
            properties={}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character", 
            inventory={"no_size_item": obj_no_size}
        )
        
        assert char.inventory_space_used == 3  # Default to medium
    
    def test_inventory_space_used_unknown_size(self):
        """Test that objects with unknown size default to medium (3 spaces)."""
        obj_unknown_size = GameObject(
            obj_id="unknown_size_item",
            name="Unknown Size Item",
            description="An item with unknown size",
            current_location_id="test_char",
            properties={"size": "unknown_size"}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={"unknown_size_item": obj_unknown_size}
        )
        
        assert char.inventory_space_used == 3  # Default to medium
    
    def test_inventory_space_available_default_capacity(self):
        """Test available space calculation with default capacity (12 spaces)."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={}
        )
        
        assert char.inventory_space_available == 12  # Default capacity
    
    def test_inventory_space_available_custom_capacity(self):
        """Test available space calculation with custom capacity."""
        char = Character(
            char_id="test_char",
            name="Test Character", 
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 20}
        )
        
        assert char.inventory_space_available == 20
    
    def test_inventory_space_available_with_items(self):
        """Test available space calculation with items in inventory."""
        medium_obj = GameObject(
            obj_id="medium_item",
            name="Medium Item",
            description="A medium item",
            current_location_id="test_char",
            properties={"size": "medium"}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={"medium_item": medium_obj},
            properties={"inventory_size": 15}
        )
        
        # 15 total - 3 used = 12 available
        assert char.inventory_space_available == 12
    
    def test_inventory_space_available_full_inventory(self):
        """Test available space when inventory is full."""
        large_obj = GameObject(
            obj_id="large_item",
            name="Large Item",
            description="A large item",
            current_location_id="test_char", 
            properties={"size": "large"}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={"large_item": large_obj},
            properties={"inventory_size": 4}  # Exactly fits the large item
        )
        
        assert char.inventory_space_available == 0
    
    def test_inventory_space_available_over_capacity(self):
        """Test available space when inventory exceeds capacity (should not happen in practice)."""
        huge_obj = GameObject(
            obj_id="huge_item",
            name="Huge Item",
            description="A huge item", 
            current_location_id="test_char",
            properties={"size": "huge"}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={"huge_item": huge_obj},
            properties={"inventory_size": 4}  # Less than the huge item (6 spaces)
        )
        
        # Should return negative available space
        assert char.inventory_space_available == -2


class TestInventoryConstraints:
    """Test the inventory constraint system for space limits."""
    
    def test_check_inventory_constraints_sufficient_space(self):
        """Test that objects can be added when there's sufficient space."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 12}
        )
        
        small_obj = GameObject(
            obj_id="small_item",
            name="Small Item",
            description="A small item",
            current_location_id="room",
            properties={"size": "small"}
        )
        
        can_add, error_msg, error_event = check_inventory_constraints(small_obj, char, "pickup")
        
        assert can_add is True
        assert error_msg is None
        assert error_event is None
    
    def test_check_inventory_constraints_insufficient_space(self):
        """Test that objects cannot be added when there's insufficient space."""
        # Fill inventory to near capacity
        large_obj = GameObject(
            obj_id="large_item",
            name="Large Item", 
            description="A large item",
            current_location_id="test_char",
            properties={"size": "large"}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={"large_item": large_obj},
            properties={"inventory_size": 5}  # Only 1 space left
        )
        
        medium_obj = GameObject(
            obj_id="medium_item",
            name="Medium Item",
            description="A medium item",
            current_location_id="room",
            properties={"size": "medium"}
        )
        
        can_add, error_msg, error_event = check_inventory_constraints(medium_obj, char, "pickup")
        
        assert can_add is False
        assert "not enough space" in error_msg
        assert "Need 3 space, but only 1 available" in error_msg
        assert error_event is not None
        assert error_event.event_type == "player_action"
        assert error_event.observers == ["room_characters"]
    
    def test_check_inventory_constraints_exact_space_fit(self):
        """Test that objects can be added when they exactly fit the remaining space."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 3}
        )
        
        medium_obj = GameObject(
            obj_id="medium_item",
            name="Medium Item",
            description="A medium item",
            current_location_id="room",
            properties={"size": "medium"}
        )
        
        can_add, error_msg, error_event = check_inventory_constraints(medium_obj, char, "pickup")
        
        assert can_add is True
        assert error_msg is None
        assert error_event is None
    
    def test_check_inventory_constraints_default_size(self):
        """Test space checking with objects that have no size property."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 3}
        )
        
        obj_no_size = GameObject(
            obj_id="no_size_item",
            name="No Size Item",
            description="An item without size property",
            current_location_id="room",
            properties={}
        )
        
        can_add, error_msg, error_event = check_inventory_constraints(obj_no_size, char, "pickup")
        
        assert can_add is True  # Should default to medium (3 spaces) and fit exactly
    
    def test_validate_inventory_transfer_sufficient_space(self):
        """Test inventory transfer validation with sufficient space."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 12}
        )
        
        small_obj = GameObject(
            obj_id="small_item",
            name="Small Item",
            description="A small item",
            current_location_id="room",
            properties={"size": "small"}
        )
        
        can_transfer, error_msg, error_event = validate_inventory_transfer(small_obj, None, char, "pickup")
        
        assert can_transfer is True
        assert error_msg is None
        assert error_event is None
    
    def test_validate_inventory_transfer_insufficient_space(self):
        """Test inventory transfer validation with insufficient space."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 1}  # Very small capacity
        )
        
        medium_obj = GameObject(
            obj_id="medium_item",
            name="Medium Item",
            description="A medium item",
            current_location_id="room",
            properties={"size": "medium"}
        )
        
        can_transfer, error_msg, error_event = validate_inventory_transfer(medium_obj, None, char, "pickup")
        
        assert can_transfer is False
        assert "not enough space" in error_msg
        assert error_event is not None


class TestPickupActionWithSpaceConstraints:
    """Test the pickup action with inventory space constraints."""
    
    @patch('motive.inventory_constraints.validate_inventory_transfer')
    def test_pickup_action_sufficient_space(self, mock_validate):
        """Test pickup action succeeds when there's sufficient space."""
        # Mock successful validation
        mock_validate.return_value = (True, None, None)
        
        # Create test objects
        room = Mock()
        room.objects = {
            "small_item": GameObject(
                obj_id="small_item",
                name="Small Item",
                description="A small item",
                current_location_id="room",
                properties={"size": "small"}
            )
        }
        room.remove_object = Mock()
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 12},
            current_room_id="room"
        )

        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()

        # Execute pickup action
        events, feedback = handle_pickup_action(
            game_master, char, Mock(), {"object_name": "Small Item"}
        )
        
        # Verify success and inventory messaging
        assert len(feedback) == 2
        assert "You pick up the Small Item" in feedback[0]
        assert "Inventory space:" in feedback[1]
        assert mock_validate.called
        room.remove_object.assert_called_once_with("small_item")
    
    @patch('motive.inventory_constraints.validate_inventory_transfer')
    def test_pickup_action_insufficient_space(self, mock_validate):
        """Test pickup action fails when there's insufficient space."""
        # Mock failed validation
        error_event = Event(
            message="Test character attempts to add the Medium Item to their inventory, but they don't have enough space (1/12 available, need 3).",
            event_type="player_action",
            source_room_id="room",
            timestamp=datetime.now().isoformat(),
            related_object_id="medium_item",
            related_player_id="test_char",
            observers=["room_characters"]
        )
        mock_validate.return_value = (False, "Cannot perform 'pickup': Cannot add 'Medium Item' to inventory - not enough space. Need 3 space, but only 1 available.", error_event)
        
        # Create test objects
        room = Mock()
        room.objects = {
            "medium_item": GameObject(
                obj_id="medium_item",
                name="Medium Item",
                description="A medium item",
                current_location_id="room",
                properties={"size": "medium"}
            )
        }
        room.remove_object = Mock()
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 1},  # Very small capacity
            current_room_id="room"
        )

        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()

        # Execute pickup action
        events, feedback = handle_pickup_action(
            game_master, char, Mock(), {"object_name": "Medium Item"}
        )
        
        # Verify failure
        assert len(events) == 1
        assert events[0] == error_event
        assert len(feedback) == 1
        assert "not enough space" in feedback[0]
        assert not room.remove_object.called  # Object should not be removed from room


class TestInventoryDisplay:
    """Test the inventory display with space information."""
    
    @patch('motive.hooks.core_hooks.Event')
    def test_look_inventory_empty_with_space_display(self, mock_event):
        """Test inventory display for empty inventory shows space information."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 12}
        )
        
        game_master = Mock()
        game_master.game_logger = Mock()
        
        # Execute look inventory action
        events, feedback = look_at_target(
            game_master, char, Mock(), {"target": "inventory"}
        )
        
        # Verify empty inventory message includes space info
        assert len(feedback) == 1
        assert "Your inventory is empty" in feedback[0]
    
    @patch('motive.hooks.core_hooks.Event')
    def test_look_inventory_with_items_and_space_display(self, mock_event):
        """Test inventory display with items shows space information."""
        # Create test objects
        small_obj = GameObject(
            obj_id="small_item",
            name="Small Item",
            description="A small item",
            current_location_id="test_char",
            properties={"size": "small"}
        )
        
        medium_obj = GameObject(
            obj_id="medium_item",
            name="Medium Item", 
            description="A medium item",
            current_location_id="test_char",
            properties={"size": "medium"}
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={
                "small_item": small_obj,
                "medium_item": medium_obj
            },
            properties={"inventory_size": 12}
        )
        
        game_master = Mock()
        game_master.game_logger = Mock()
        
        # Execute look inventory action
        events, feedback = look_at_target(
            game_master, char, Mock(), {"target": "inventory"}
        )
        
        # Verify inventory display includes space information
        assert len(feedback) == 1
        inventory_text = feedback[0]
        assert "You are carrying:" in inventory_text
        assert "Small Item" in inventory_text
        assert "Medium Item" in inventory_text
        assert "**Inventory Space:** 5/12 used (7 available)" in inventory_text


class TestInventorySizeEdgeCases:
    """Test edge cases and boundary conditions for the inventory size system."""
    
    def test_size_mapping_all_sizes(self):
        """Test that all defined sizes map to correct numeric values."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={}
        )
        
        # Test all size mappings
        size_tests = [
            ("tiny", 1),
            ("small", 2),
            ("medium", 3),
            ("large", 4),
            ("huge", 6)
        ]
        
        for size_name, expected_value in size_tests:
            obj = GameObject(
                obj_id=f"{size_name}_item",
                name=f"{size_name.title()} Item",
                description=f"A {size_name} item",
                current_location_id="test_char",
                properties={"size": size_name}
            )
            
            char.inventory = {f"{size_name}_item": obj}
            assert char.inventory_space_used == expected_value, f"Size '{size_name}' should map to {expected_value}"
    
    def test_character_without_inventory_size_property(self):
        """Test that characters without inventory_size property use default (12)."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={}
            # No properties dict, so no inventory_size
        )
        
        assert char.inventory_space_available == 12  # Should default to 12
    
    def test_character_with_zero_inventory_size(self):
        """Test behavior with zero inventory capacity."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 0}
        )
        
        assert char.inventory_space_available == 0
        
        # Should not be able to pick up anything
        tiny_obj = GameObject(
            obj_id="tiny_item",
            name="Tiny Item",
            description="A tiny item",
            current_location_id="room",
            properties={"size": "tiny"}
        )
        
        can_add, error_msg, error_event = check_inventory_constraints(tiny_obj, char, "pickup")
        
        assert can_add is False
        assert "not enough space" in error_msg
    
    def test_character_with_negative_inventory_size(self):
        """Test behavior with negative inventory capacity (edge case)."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": -5}
        )
        
        # Should return negative available space
        assert char.inventory_space_available == -5
        
        # Should not be able to pick up anything
        tiny_obj = GameObject(
            obj_id="tiny_item",
            name="Tiny Item",
            description="A tiny item",
            current_location_id="room",
            properties={"size": "tiny"}
        )
        
        can_add, error_msg, error_event = check_inventory_constraints(tiny_obj, char, "pickup")
        
        assert can_add is False
        assert "not enough space" in error_msg
    
    def test_object_with_empty_string_size(self):
        """Test behavior with empty string size property."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={}
        )
        
        obj_empty_size = GameObject(
            obj_id="empty_size_item",
            name="Empty Size Item",
            description="An item with empty string size",
            current_location_id="test_char",
            properties={"size": ""}
        )
        
        char.inventory = {"empty_size_item": obj_empty_size}
        
        # Should default to medium (3 spaces) for empty string
        assert char.inventory_space_used == 3
    
    def test_object_with_none_size(self):
        """Test behavior with None size property."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={}
        )
        
        obj_none_size = GameObject(
            obj_id="none_size_item",
            name="None Size Item",
            description="An item with None size",
            current_location_id="test_char",
            properties={"size": None}
        )
        
        char.inventory = {"none_size_item": obj_none_size}
        
        # Should default to medium (3 spaces) for None
        assert char.inventory_space_used == 3


class TestInventorySizeIntegration:
    """Integration tests for the inventory size system."""
    
    def test_full_pickup_workflow_with_space_constraints(self):
        """Test complete pickup workflow with space constraints."""
        # Create character with limited capacity
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 5},
            current_room_id="room"
        )
        
        # Create room with objects
        room = Mock()
        room.objects = {
            "small_item": GameObject(
                obj_id="small_item",
                name="Small Item",
                description="A small item",
                current_location_id="room",
                properties={"size": "small"}
            ),
            "large_item": GameObject(
                obj_id="large_item",
                name="Large Item",
                description="A large item",
                current_location_id="room",
                properties={"size": "large"}
            )
        }
        room.remove_object = Mock()
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # First pickup should succeed (small item = 2 spaces, fits in 5)
        events, feedback = handle_pickup_action(
            game_master, char, Mock(), {"object_name": "Small Item"}
        )

        assert len(feedback) == 2
        assert "You pick up the Small Item" in feedback[0]
        assert "Inventory space:" in feedback[1]
        assert "small_item" in char.inventory
        room.remove_object.assert_called_once_with("small_item")
        
        # Reset room mock
        room.remove_object.reset_mock()
        
        # Second pickup should fail (large item = 4 spaces, but only 3 left)
        events, feedback = handle_pickup_action(
            game_master, char, Mock(), {"object_name": "Large Item"}
        )
        
        assert len(events) == 1
        assert "not enough space" in feedback[0]
        assert "large_item" not in char.inventory
        assert not room.remove_object.called
    
    def test_inventory_space_calculation_accuracy(self):
        """Test that inventory space calculations are accurate across multiple operations."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            properties={"inventory_size": 15}
        )
        
        # Add items one by one and verify space calculations
        items_to_add = [
            ("tiny_item", "tiny", 1),
            ("small_item", "small", 2),
            ("medium_item", "medium", 3),
            ("large_item", "large", 4),
            ("huge_item", "huge", 6)
        ]
        
        total_expected_space = 0
        
        for item_id, size, expected_space in items_to_add:
            obj = GameObject(
                obj_id=item_id,
                name=f"{size.title()} Item",
                description=f"A {size} item",
                current_location_id="test_char",
                properties={"size": size}
            )
            
            char.inventory[item_id] = obj
            total_expected_space += expected_space
            
            assert char.inventory_space_used == total_expected_space
            assert char.inventory_space_available == 15 - total_expected_space
        
        # Final verification
        assert char.inventory_space_used == 16  # 1+2+3+4+6 = 16
        assert char.inventory_space_available == -1  # 15 - 16 = -1 (over capacity)
