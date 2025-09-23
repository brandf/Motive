"""Test to simulate the actual game objects and see what's happening."""

import pytest
from unittest.mock import Mock
from motive.hooks.core_hooks import handle_pickup_action
from motive.character import Character


class TestActualGameObjects:
    """Test to simulate the actual game objects and debug the issue."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.character = Character(
            char_id="detective_thorne",
            name="Detective Thorne",
            backstory="A seasoned detective",
            current_room_id="town_square"
        )
        
        # Mock game master
        self.game_master = Mock()
        self.game_master.rooms = {}
        
        # Mock action config
        self.action_config = Mock()
        self.action_config.id = "pickup"
        self.action_config.name = "pickup"
        self.action_config.cost = 10
        
        # Mock logger
        self.logger = Mock()
    
    def test_simulate_actual_game_objects(self):
        """Test simulating the actual objects Thorne picked up in the game."""
        # Create mock objects that match what Thorne actually picked up
        objects_thorne_picked_up = [
            {
                'name': "Partner's Evidence",
                'id': 'partner_evidence',
                'interactions': {
                    'look': {
                        'effects': [
                            {
                                'type': 'set_property',
                                'target': 'player',
                                'property': 'partner_evidence_found',
                                'value': True
                            }
                        ]
                    },
                    'pickup': {
                        'effects': [
                            {
                                'type': 'set_property',
                                'target': 'player',
                                'property': 'partner_evidence_found',
                                'value': True
                            }
                        ]
                    }
                }
            },
            {
                'name': "Priest's Diary",
                'id': 'priest_diary',
                'interactions': {
                    'look': {
                        'effects': [
                            {
                                'type': 'set_property',
                                'target': 'player',
                                'property': 'priest_diary_found',
                                'value': True
                            }
                        ]
                    }
                }
            },
            {
                'name': "Sacred Map",
                'id': 'sacred_map',
                'interactions': {
                    'look': {
                        'effects': [
                            {
                                'type': 'set_property',
                                'target': 'player',
                                'property': 'sacred_map_found',
                                'value': True
                            }
                        ]
                    }
                }
            }
        ]
        
        # Test picking up each object
        for obj_data in objects_thorne_picked_up:
            # Create mock object
            obj = Mock()
            obj.id = obj_data['id']
            obj.name = obj_data['name']
            obj.description = f"Description for {obj_data['name']}"
            obj.properties = {'pickupable': True, 'size': 'small'}
            obj.interactions = obj_data['interactions']
            
            # Mock the room
            mock_room = Mock()
            mock_room.objects = {obj.id: obj}
            mock_room.get_object = Mock(return_value=obj)
            self.game_master.rooms = {'town_square': mock_room}
            
            # Test pickup
            events, feedback = handle_pickup_action(
                self.game_master,
                self.character,
                self.action_config,
                {'object_name': obj.name}
            )
            
            print(f"Picked up {obj.name}")
            print(f"Character properties: {self.character.properties}")
            print(f"Evidence found: {self.character.evidence_found}")
            print(f"Feedback: {feedback}")
            print("---")
        
        # Check final state
        expected_evidence_found = len(objects_thorne_picked_up)
        actual_evidence_found = self.character.evidence_found
        
        assert actual_evidence_found == expected_evidence_found, f"Expected evidence_found to be {expected_evidence_found}, got {actual_evidence_found}"
        
        # Check individual flags
        assert self.character.properties.get('partner_evidence_found', False) == True
        assert self.character.properties.get('priest_diary_found', False) == True
        assert self.character.properties.get('sacred_map_found', False) == True
    
    def test_debug_evidence_computed_property(self):
        """Test the evidence computed property directly."""
        # Set some evidence flags manually
        self.character.properties['partner_evidence_found'] = True
        self.character.properties['priest_diary_found'] = True
        self.character.properties['sacred_map_found'] = True
        
        # Check the computed property
        evidence_found = self.character.evidence_found
        assert evidence_found == 3, f"Expected evidence_found to be 3, got {evidence_found}"
        
        print(f"Manual flags set:")
        print(f"partner_evidence_found: {self.character.properties.get('partner_evidence_found', False)}")
        print(f"priest_diary_found: {self.character.properties.get('priest_diary_found', False)}")
        print(f"sacred_map_found: {self.character.properties.get('sacred_map_found', False)}")
        print(f"evidence_found computed property: {self.character.evidence_found}")
        
        # Test the get_property method
        evidence_found_via_get_property = self.character.get_property('evidence_found', 0)
        assert evidence_found_via_get_property == 3, f"Expected get_property('evidence_found') to be 3, got {evidence_found_via_get_property}"
        
        print(f"evidence_found via get_property: {evidence_found_via_get_property}")


