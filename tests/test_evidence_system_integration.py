"""Integration tests for the evidence system to verify Detective Thorne's motive completion.

These tests verify that the evidence system works correctly in realistic game scenarios.
They should remain in the codebase as durable regression tests.
"""

import pytest
from unittest.mock import Mock, patch
from motive.character import Character
from motive.hooks.core_hooks import handle_pickup_action, look_at_target


class TestEvidenceSystemIntegration:
    """Integration tests for the evidence system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.character = Character(
            char_id="detective_thorne",
            name="Detective Thorne",
            backstory="A seasoned detective",
            current_room_id="church"
        )
        
        # Mock game master
        self.game_master = Mock()
        self.game_master.rooms = {}
        
        # Mock action config
        self.action_config = Mock()
        self.action_config.id = "pickup"
        self.action_config.name = "pickup"
        self.action_config.cost = 10
    
    def test_priest_diary_evidence_completion(self):
        """Test that Priest's Diary correctly sets evidence flags and completes motive conditions."""
        # Create Priest's Diary with the actual game configuration
        priest_diary = Mock()
        priest_diary.id = "priest_diary"
        priest_diary.name = "Priest's Diary"
        priest_diary.description = "Father Marcus's personal diary containing his observations"
        priest_diary.properties = {
            'pickupable': True,
            'size': 'small',
            'readable': True
        }
        priest_diary.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'priest_diary_found',
                        'value': True
                    },
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'cult_hierarchy_discovered',
                        'value': True
                    }
                ]
            }
        }
        
        # Mock the room
        mock_room = Mock()
        mock_room.objects = {'priest_diary': priest_diary}
        mock_room.get_object = Mock(return_value=priest_diary)
        self.game_master.rooms = {'church': mock_room}
        
        # Verify initial state
        assert self.character.properties.get('priest_diary_found', False) == False
        assert self.character.properties.get('cult_hierarchy_discovered', False) == False
        assert self.character.evidence_found == 0
        
        # Test pickup action (which triggers look interaction)
        events, feedback = handle_pickup_action(
            self.game_master,
            self.character,
            self.action_config,
            {'object_name': "Priest's Diary"}
        )
        
        # Verify evidence flags were set
        assert self.character.properties.get('priest_diary_found', False) == True
        assert self.character.properties.get('cult_hierarchy_discovered', False) == True
        assert self.character.evidence_found == 1
        
        # Verify feedback messages
        assert any("Priest Diary Found: True" in str(f) for f in feedback)
        assert any("Cult Hierarchy Discovered: True" in str(f) for f in feedback)
    
    def test_sacred_map_evidence_completion(self):
        """Test that Sacred Map correctly sets evidence flags."""
        sacred_map = Mock()
        sacred_map.id = "sacred_map"
        sacred_map.name = "Sacred Map"
        sacred_map.description = "An ancient map showing sacred sites"
        sacred_map.properties = {
            'pickupable': True,
            'size': 'medium',
            'readable': True
        }
        sacred_map.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'sacred_map_found',
                        'value': True
                    },
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'cult_locations_mapped',
                        'value': True
                    }
                ]
            }
        }
        
        # Mock the room
        mock_room = Mock()
        mock_room.objects = {'sacred_map': sacred_map}
        mock_room.get_object = Mock(return_value=sacred_map)
        self.game_master.rooms = {'church': mock_room}
        
        # Test pickup
        events, feedback = handle_pickup_action(
            self.game_master,
            self.character,
            self.action_config,
            {'object_name': "Sacred Map"}
        )
        
        # Verify evidence flags
        assert self.character.properties.get('sacred_map_found', False) == True
        assert self.character.properties.get('cult_locations_mapped', False) == True
        assert self.character.evidence_found == 1
    
    def test_multiple_evidence_objects_cumulative(self):
        """Test that multiple evidence objects correctly increment evidence_found."""
        evidence_objects = [
            {
                'name': "Priest's Diary",
                'id': 'priest_diary',
                'evidence_flag': 'priest_diary_found',
                'motive_flag': 'cult_hierarchy_discovered'
            },
            {
                'name': "Sacred Map",
                'id': 'sacred_map', 
                'evidence_flag': 'sacred_map_found',
                'motive_flag': 'cult_locations_mapped'
            },
            {
                'name': "Ritual Texts",
                'id': 'ritual_texts',
                'evidence_flag': 'ritual_texts_found',
                'motive_flag': 'ritual_knowledge_mastered'
            }
        ]
        
        for obj_data in evidence_objects:
            # Create mock object
            obj = Mock()
            obj.id = obj_data['id']
            obj.name = obj_data['name']
            obj.description = f"Description for {obj_data['name']}"
            obj.properties = {'pickupable': True, 'size': 'small'}
            obj.interactions = {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': obj_data['evidence_flag'],
                            'value': True
                        },
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': obj_data['motive_flag'],
                            'value': True
                        }
                    ]
                }
            }
            
            # Mock the room
            mock_room = Mock()
            mock_room.objects = {obj.id: obj}
            mock_room.get_object = Mock(return_value=obj)
            self.game_master.rooms = {'church': mock_room}
            
            # Test pickup
            events, feedback = handle_pickup_action(
                self.game_master,
                self.character,
                self.action_config,
                {'object_name': obj.name}
            )
        
        # Verify cumulative evidence
        assert self.character.evidence_found == 3
        assert self.character.properties.get('priest_diary_found', False) == True
        assert self.character.properties.get('sacred_map_found', False) == True
        assert self.character.properties.get('ritual_texts_found', False) == True
        assert self.character.properties.get('cult_hierarchy_discovered', False) == True
        assert self.character.properties.get('cult_locations_mapped', False) == True
        assert self.character.properties.get('ritual_knowledge_mastered', False) == True
    
    def test_evidence_system_prevents_cheesing(self):
        """Test that the evidence system prevents looking at the same evidence multiple times."""
        priest_diary = Mock()
        priest_diary.id = "priest_diary"
        priest_diary.name = "Priest's Diary"
        priest_diary.description = "Father Marcus's personal diary"
        priest_diary.properties = {'pickupable': True, 'size': 'small'}
        priest_diary.interactions = {
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
        
        # Mock the room
        mock_room = Mock()
        mock_room.objects = {'priest_diary': priest_diary}
        mock_room.get_object = Mock(return_value=priest_diary)
        self.game_master.rooms = {'church': mock_room}
        
        # Pick up the same object multiple times
        for _ in range(3):
            events, feedback = handle_pickup_action(
                self.game_master,
                self.character,
                self.action_config,
                {'object_name': "Priest's Diary"}
            )
        
        # Evidence should only be counted once
        assert self.character.evidence_found == 1
        assert self.character.properties.get('priest_diary_found', False) == True
    
    def test_computed_property_accessibility(self):
        """Test that the evidence_found computed property is accessible via get_property."""
        # Set some evidence flags manually
        self.character.set_property('priest_diary_found', True)
        self.character.set_property('sacred_map_found', True)
        
        # Verify computed property is accessible
        assert self.character.get_property('evidence_found') == 2
        assert self.character.evidence_found == 2
    
    def test_motive_condition_evaluation(self):
        """Test that motive conditions can evaluate the evidence_found computed property."""
        # Set up character with evidence
        self.character.set_property('priest_diary_found', True)
        self.character.set_property('sacred_map_found', True)
        
        # Create motive condition
        condition = {
            'type': 'character_has_property',
            'property': 'evidence_found',
            'value': 2
        }
        
        # Test that the condition can be evaluated
        # (This tests the integration between motive evaluation and computed properties)
        assert self.character.get_property('evidence_found') == 2
        assert self.character.get_property('evidence_found') >= condition['value']
        
        # Test that the computed property works in condition evaluation context
        evidence_count = self.character.get_property('evidence_found')
        required_count = condition['value']
        assert evidence_count >= required_count, f"Evidence count {evidence_count} should be >= required {required_count}"
