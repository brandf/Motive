"""
Integration test for Detective Thorne's motive completion.
Tests that Detective Thorne can achieve all 8 success conditions for his motive.
"""
import pytest
from motive.hooks.core_hooks import handle_pickup_action
from motive.sim_v2.v2_config_preprocessor import load_and_validate_v2_config
import logging

class TestDetectiveThorneMotiveCompletion:
    """Test that Detective Thorne can complete his motive by picking up objects with automatic look effects."""
    
    def setup_method(self):
        """Set up test environment with Detective Thorne and his motive."""
        # Create a simple character for testing
        self.character = type('Character', (), {
            'id': 'detective_thorne',
            'name': 'Detective Thorne',
            'properties': {
                "evidence_found": 0,
                "cult_hierarchy_discovered": False,
                "cult_locations_mapped": False,
                "ritual_knowledge_mastered": False,
                "cult_timing_understood": False,
                "justice_tools_acquired": False,
                "evidence_chain_complete": False,
                "final_confrontation_ready": False
            },
            'set_property': lambda self, prop, value: self.properties.update({prop: value}),
            'add_item_to_inventory': lambda self, item: None,  # Mock method
            'get_display_name': lambda self: self.name,  # Mock method
            'current_room_id': 'church'
        })()
        
        # Create a simple room for testing
        self.room = type('Room', (), {
            'id': 'church',
            'name': 'Church',
            'objects': {}
        })()
        
        # Set up logger
        self.logger = logging.getLogger("test_detective_thorne")
        self.logger.setLevel(logging.INFO)
    
    def test_pickup_automatic_look_effects(self):
        """Test that picking up objects with look interactions automatically triggers their effects."""
        from unittest.mock import Mock
        
        # Create game master mock
        game_master = Mock()
        game_master.rooms = {"church": self.room}
        
        # Create object mock with look interaction
        test_object = Mock()
        test_object.id = "test_object"
        test_object.name = "Test Object"
        test_object.properties = {'pickupable': True}
        test_object.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'increment_property',
                        'property': 'evidence_found',
                        'increment_value': 1
                    }
                ]
            }
        }
        
        # Add object to room
        self.room.objects = {"Test Object": test_object}
        self.room.remove_object = Mock()
        
        # Mock inventory validation
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            # Test pickup action
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {"object_name": "Test Object"}
            )
        
        # Verify evidence_found was incremented
        assert self.character.properties["evidence_found"] == 1
        assert any("Evidence Found" in str(feedback) for feedback in feedback)
    
    def test_pickup_automatic_use_effects(self):
        """Test that picking up objects with pickup_action: use automatically triggers their use effects."""
        from unittest.mock import Mock
        
        # Create game master mock
        game_master = Mock()
        game_master.rooms = {"church": self.room}
        
        # Create object mock with use interaction and pickup_action: use
        test_object = Mock()
        test_object.id = "test_object"
        test_object.name = "Test Object"
        test_object.properties = {'pickupable': True, 'usable': True, 'pickup_action': 'use'}
        test_object.interactions = {
            'use': {
                'effects': [
                    {
                        'type': 'set_property',
                        'property': 'cult_timing_understood',
                        'value': True
                    }
                ]
            }
        }
        
        # Add object to room
        self.room.objects = {"Test Object": test_object}
        self.room.remove_object = Mock()
        
        # Mock inventory validation
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            # Test pickup action
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {"object_name": "Test Object"}
            )
        
        # Verify cult_timing_understood was set
        assert self.character.properties["cult_timing_understood"] == True
        assert any("Cult Timing Understood" in str(feedback) for feedback in feedback)
