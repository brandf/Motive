"""
Test suite for the use action working on room objects.

This module tests that the use action works on objects in the current room,
not just objects in the player's inventory.

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
from motive.hooks.core_hooks import handle_use_action
from motive.config import Event
from datetime import datetime


class TestUseActionOnRoomObjects:
    """Test that the use action works on objects in the current room."""
    
    def test_use_action_works_on_room_objects(self):
        """Test that use action succeeds when targeting objects in the current room."""
        # Create test objects
        room = Mock()
        room.objects = {
            "confrontation_manual": GameObject(
                obj_id="confrontation_manual",
                name="Confrontation Manual",
                description="A manual for confronting the cult",
                current_location_id="room",
                properties={"size": "medium", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "final_confrontation_ready",
                                "value": True
                            }
                        ]
                    }
                }
            )
        }
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action on room object
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Confrontation Manual", "target": ""}
        )
        
        # Verify success
        assert len(events) == 0  # No events when interactions are processed successfully
        assert len(feedback) == 1
        assert "You use the Confrontation Manual" in feedback[0]
        
        # Verify property was set
        assert char.properties.get("final_confrontation_ready") is True
    
    def test_use_action_works_on_inventory_objects(self):
        """Test that use action still works on objects in inventory (existing functionality)."""
        # Create test object in inventory
        manual_obj = GameObject(
            obj_id="confrontation_manual",
            name="Confrontation Manual",
            description="A manual for confronting the cult",
            current_location_id="test_char",
            properties={"size": "medium", "usable": True},
            interactions={
                "use": {
                    "effects": [
                        {
                            "type": "set_property",
                            "target": "player",
                            "property": "final_confrontation_ready",
                            "value": True
                        }
                    ]
                }
            }
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={"confrontation_manual": manual_obj},
            current_room_id="room"
        )
        
        room = Mock()
        room.objects = {}
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action on inventory object
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Confrontation Manual", "target": ""}
        )
        
        # Verify success
        assert len(events) == 0  # No events when interactions are processed successfully
        assert len(feedback) == 1
        assert "You use the Confrontation Manual" in feedback[0]
        
        # Verify property was set
        assert char.properties.get("final_confrontation_ready") is True
    
    def test_use_action_prioritizes_inventory_over_room(self):
        """Test that use action prioritizes inventory objects over room objects when both exist."""
        # Create same object in both inventory and room
        inventory_obj = GameObject(
            obj_id="confrontation_manual",
            name="Confrontation Manual",
            description="A manual for confronting the cult",
            current_location_id="test_char",
            properties={"size": "medium", "usable": True},
            interactions={
                "use": {
                    "effects": [
                        {
                            "type": "set_property",
                            "target": "player",
                            "property": "inventory_used",
                            "value": True
                        }
                    ]
                }
            }
        )
        
        room_obj = GameObject(
            obj_id="confrontation_manual",
            name="Confrontation Manual",
            description="A manual for confronting the cult",
            current_location_id="room",
            properties={"size": "medium", "usable": True},
            interactions={
                "use": {
                    "effects": [
                        {
                            "type": "set_property",
                            "target": "player",
                            "property": "room_used",
                            "value": True
                        }
                    ]
                }
            }
        )
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={"confrontation_manual": inventory_obj},
            current_room_id="room"
        )
        
        room = Mock()
        room.objects = {"confrontation_manual": room_obj}
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Confrontation Manual", "target": ""}
        )
        
        # Verify inventory object was used (not room object)
        assert char.properties.get("inventory_used") is True
        assert char.properties.get("room_used") is None
    
    def test_use_action_fails_when_object_not_found(self):
        """Test that use action fails when object is neither in inventory nor room."""
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        room = Mock()
        room.objects = {}
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action on non-existent object
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Non-existent Object", "target": ""}
        )
        
        # Verify failure
        assert len(events) == 0
        assert len(feedback) == 1
        assert "You don't see 'Non-existent Object' anywhere nearby." in feedback[0]
    
    def test_use_action_fails_when_object_not_usable(self):
        """Test that use action fails when object exists but is not usable."""
        room = Mock()
        room.objects = {
            "non_usable_object": GameObject(
                obj_id="non_usable_object",
                name="Non Usable Object",
                description="An object that cannot be used",
                current_location_id="room",
                properties={"size": "medium", "usable": False}
            )
        }
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action on non-usable object
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Non Usable Object", "target": ""}
        )
        
        # Verify failure
        assert len(events) == 0
        assert len(feedback) == 1
        assert "cannot be used" in feedback[0]
    
    def test_use_action_with_target_parameter(self):
        """Test that use action works with target parameter on room objects."""
        room = Mock()
        room.objects = {
            "holy_water": GameObject(
                obj_id="holy_water",
                name="Holy Water",
                description="Blessed water for purification",
                current_location_id="room",
                properties={"size": "small", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "purified",
                                "value": True
                            }
                        ]
                    }
                }
            )
        }
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action with target
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Holy Water", "target": "cult symbols"}
        )
        
        # Verify success
        assert len(events) == 0  # No events when interactions are processed successfully
        assert len(feedback) == 1
        assert "You use the Holy Water" in feedback[0]
        
        # Verify property was set
        assert char.properties.get("purified") is True


class TestUseActionEdgeCases:
    """Test edge cases for the use action."""
    
    def test_use_action_case_insensitive_object_name(self):
        """Test that use action works with case-insensitive object names."""
        room = Mock()
        room.objects = {
            "confrontation_manual": GameObject(
                obj_id="confrontation_manual",
                name="Confrontation Manual",
                description="A manual for confronting the cult",
                current_location_id="room",
                properties={"size": "medium", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "confrontation_ready",
                                "value": True
                            }
                        ]
                    }
                }
            )
        }
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action with different case
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "confrontation manual", "target": ""}
        )
        
        # Verify success
        assert len(events) == 0  # No events when interactions are processed successfully
        assert len(feedback) == 1
        assert "You use the Confrontation Manual" in feedback[0]
        assert char.properties.get("confrontation_ready") is True
    
    def test_use_action_with_quoted_object_name(self):
        """Test that use action works with quoted object names."""
        room = Mock()
        room.objects = {
            "confrontation_manual": GameObject(
                obj_id="confrontation_manual",
                name="Confrontation Manual",
                description="A manual for confronting the cult",
                current_location_id="room",
                properties={"size": "medium", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "confrontation_ready",
                                "value": True
                            }
                        ]
                    }
                }
            )
        }
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action with quoted name
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "\"Confrontation Manual\"", "target": ""}
        )
        
        # Verify success
        assert len(events) == 0  # No events when interactions are processed successfully
        assert len(feedback) == 1
        assert "You use the Confrontation Manual" in feedback[0]
        assert char.properties.get("confrontation_ready") is True
    
    def test_use_action_with_empty_target(self):
        """Test that use action works with empty target parameter."""
        room = Mock()
        room.objects = {
            "holy_water": GameObject(
                obj_id="holy_water",
                name="Holy Water",
                description="Blessed water for purification",
                current_location_id="room",
                properties={"size": "small", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "purified",
                                "value": True
                            }
                        ]
                    }
                }
            )
        }
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Execute use action with empty target
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Holy Water", "target": ""}
        )
        
        # Verify success
        assert len(events) == 0  # No events when interactions are processed successfully
        assert len(feedback) == 1
        assert "You use the Holy Water" in feedback[0]
        assert char.properties.get("purified") is True


class TestUseActionIntegration:
    """Integration tests for the use action system."""
    
    def test_use_action_complete_workflow(self):
        """Test complete workflow of using room objects."""
        # Create room with multiple objects
        room = Mock()
        room.objects = {
            "confrontation_manual": GameObject(
                obj_id="confrontation_manual",
                name="Confrontation Manual",
                description="A manual for confronting the cult",
                current_location_id="room",
                properties={"size": "medium", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "final_confrontation_ready",
                                "value": True
                            }
                        ]
                    }
                }
            ),
            "holy_water": GameObject(
                obj_id="holy_water",
                name="Holy Water",
                description="Blessed water for purification",
                current_location_id="room",
                properties={"size": "small", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "purified",
                                "value": True
                            }
                        ]
                    }
                }
            )
        }
        
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={},
            current_room_id="room"
        )
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Use first object
        events1, feedback1 = handle_use_action(
            game_master, char, Mock(), {"object_name": "Confrontation Manual", "target": ""}
        )
        
        # Use second object
        events2, feedback2 = handle_use_action(
            game_master, char, Mock(), {"object_name": "Holy Water", "target": ""}
        )
        
        # Verify both succeeded
        assert len(events1) == 0  # No events when interactions are processed successfully
        assert len(feedback1) == 1
        assert "You use the Confrontation Manual" in feedback1[0]
        assert char.properties.get("final_confrontation_ready") is True
        
        assert len(events2) == 0  # No events when interactions are processed successfully
        assert len(feedback2) == 1
        assert "You use the Holy Water" in feedback2[0]
        assert char.properties.get("purified") is True
    
    def test_use_action_with_inventory_space_constraints(self):
        """Test that use action works even when inventory is full."""
        # Create character with full inventory
        char = Character(
            char_id="test_char",
            name="Test Character",
            backstory="A test character",
            inventory={
                "item1": GameObject("item1", "Item 1", "First item", "test_char", properties={"size": "medium"}),
                "item2": GameObject("item2", "Item 2", "Second item", "test_char", properties={"size": "medium"}),
                "item3": GameObject("item3", "Item 3", "Third item", "test_char", properties={"size": "medium"}),
                "item4": GameObject("item4", "Item 4", "Fourth item", "test_char", properties={"size": "medium"})
            },
            current_room_id="room",
            properties={"inventory_size": 12}  # Full inventory
        )
        
        room = Mock()
        room.objects = {
            "confrontation_manual": GameObject(
                obj_id="confrontation_manual",
                name="Confrontation Manual",
                description="A manual for confronting the cult",
                current_location_id="room",
                properties={"size": "medium", "usable": True},
                interactions={
                    "use": {
                        "effects": [
                            {
                                "type": "set_property",
                                "target": "player",
                                "property": "final_confrontation_ready",
                                "value": True
                            }
                        ]
                    }
                }
            )
        }
        
        game_master = Mock()
        game_master.rooms = {"room": room}
        game_master.game_logger = Mock()
        
        # Use room object (should work even with full inventory)
        events, feedback = handle_use_action(
            game_master, char, Mock(), {"object_name": "Confrontation Manual", "target": ""}
        )
        
        # Verify success
        assert len(events) == 0  # No events when interactions are processed successfully
        assert len(feedback) == 1
        assert "You use the Confrontation Manual" in feedback[0]
        assert char.properties.get("final_confrontation_ready") is True
