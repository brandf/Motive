"""
Test to debug why the evidence system isn't working in the actual game.
"""

import pytest
from unittest.mock import Mock, MagicMock
from motive.character import Character
from motive.hooks.core_hooks import handle_pickup_action, look_at_target


class TestEvidenceSystemDebug:
    """Test class to debug evidence system issues."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock character
        self.character = Character(
            char_id="detective_thorne",
            name="Detective James Thorne",
            backstory="A seasoned detective",
            current_room_id="church",
            action_points=30
        )
        
        # Create mock game master
        self.game_master = Mock()
        self.game_master.rooms = {}
        
        # Create mock logger
        self.logger = Mock()
        
        # Create mock action config
        self.action_config = Mock()
        self.action_config.id = "pickup"
        self.action_config.name = "pickup"
        self.action_config.cost = 10
        
    def test_evidence_system_basic_functionality(self):
        """Test that the evidence system works in isolation."""
        # Test initial state
        assert self.character.evidence_found == 0
        
        # Set evidence flags manually
        self.character.properties['partner_evidence_found'] = True
        self.character.properties['notice_board_found'] = True
        
        # Test computed property
        assert self.character.evidence_found == 2
        
    def test_evidence_object_pickup_effect(self):
        """Test that picking up evidence objects sets the correct flags."""
        # Create a mock evidence object
        evidence_object = Mock()
        evidence_object.id = "partner_evidence"
        evidence_object.name = "Partner's Evidence"
        evidence_object.description = "A bloodstained notebook"
        evidence_object.properties = {
            'pickupable': True,
            'size': 'small',
            'pickup_action': 'look'
        }
        evidence_object.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'partner_evidence_found',
                        'value': True
                    },
                    {
                        'type': 'generate_event',
                        'message': '{{player_name}} examines the partner\'s evidence and finds crucial clues!',
                        'observers': ['room_characters']
                    }
                ]
            }
        }
        
        # Mock the room and objects
        mock_room = Mock()
        mock_room.objects = {'partner_evidence': evidence_object}
        mock_room.get_object = Mock(return_value=evidence_object)
        self.game_master.rooms = {'church': mock_room}
        
        # Test pickup action
        events, feedback = handle_pickup_action(
            self.game_master,
            self.character,
            self.action_config,
            {'object_name': "Partner's Evidence"}
        )
        
        
        # Check that the property was set
        assert self.character.properties.get('partner_evidence_found', False) == True
        assert self.character.evidence_found == 1
        
        # Check that feedback was generated
        assert any('Partner Evidence Found: True' in str(f) for f in feedback)
        
    def test_evidence_object_look_effect(self):
        """Test that looking at evidence objects sets the correct flags."""
        # Create a mock evidence object
        evidence_object = Mock()
        evidence_object.id = "notice_board"
        evidence_object.name = "Notice Board"
        evidence_object.description = "A weathered wooden board"
        evidence_object.interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'notice_board_found',
                        'value': True
                    },
                    {
                        'type': 'generate_event',
                        'message': '{{player_name}} examines the notice board and finds important information!',
                        'observers': ['room_characters']
                    }
                ]
            }
        }
        
        # Mock the room and objects
        mock_room = Mock()
        mock_room.objects = {'notice_board': evidence_object}
        mock_room.get_object = Mock(return_value=evidence_object)
        self.game_master.rooms = {'church': mock_room}
        
        # Mock character methods
        self.character.get_item_in_inventory = Mock(return_value=None)
        self.character.get_display_name = Mock(return_value="Detective James Thorne")
        
        # Test look action
        events, feedback = look_at_target(
            self.game_master,
            self.character,
            self.action_config,
            {'target': 'notice_board'}
        )
        
        # Check that the property was set
        assert self.character.properties.get('notice_board_found', False) == True
        assert self.character.evidence_found == 1
        
        # Check that feedback was generated
        assert any('Notice Board Found: True' in str(f) for f in feedback)
        
    def test_multiple_evidence_objects(self):
        """Test that multiple evidence objects increment the counter correctly."""
        # Set up multiple evidence objects
        evidence_objects = {
            'partner_evidence': Mock(),
            'notice_board': Mock(),
            'editor_notes': Mock()
        }
        
        # Configure each evidence object
        evidence_objects['partner_evidence'].id = "partner_evidence"
        evidence_objects['partner_evidence'].name = "Partner's Evidence"
        evidence_objects['partner_evidence'].properties = {'pickupable': True}
        evidence_objects['partner_evidence'].interactions = {
            'look': {
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
        
        evidence_objects['notice_board'].id = "notice_board"
        evidence_objects['notice_board'].name = "Notice Board"
        evidence_objects['notice_board'].description = "A weathered board"
        evidence_objects['notice_board'].interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'notice_board_found',
                        'value': True
                    }
                ]
            }
        }
        
        evidence_objects['editor_notes'].id = "editor_notes"
        evidence_objects['editor_notes'].name = "Editor's Notes"
        evidence_objects['editor_notes'].description = "Editor's notes"
        evidence_objects['editor_notes'].interactions = {
            'look': {
                'effects': [
                    {
                        'type': 'set_property',
                        'target': 'player',
                        'property': 'editor_notes_found',
                        'value': True
                    }
                ]
            }
        }
        
        # Mock the room
        mock_room = Mock()
        mock_room.objects = evidence_objects
        mock_room.get_object = Mock(side_effect=lambda name: evidence_objects.get(name))
        self.game_master.rooms = {'church': mock_room}
        
        # Mock character methods
        self.character.get_item_in_inventory = Mock(return_value=None)
        self.character.get_display_name = Mock(return_value="Detective James Thorne")
        
        # Test looking at each evidence object
        look_at_target(self.game_master, self.character, self.action_config, {'target': 'partner_evidence'})
        assert self.character.evidence_found == 1
        
        look_at_target(self.game_master, self.character, self.action_config, {'target': 'notice_board'})
        assert self.character.evidence_found == 2
        
        look_at_target(self.game_master, self.character, self.action_config, {'target': 'editor_notes'})
        assert self.character.evidence_found == 3
        
        # Verify all flags are set
        assert self.character.properties.get('partner_evidence_found', False) == True
        assert self.character.properties.get('notice_board_found', False) == True
        assert self.character.properties.get('editor_notes_found', False) == True
