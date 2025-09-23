"""Test to debug the object instantiation process."""

import pytest
from unittest.mock import Mock
from motive.hooks.core_hooks import handle_pickup_action
from motive.character import Character


class TestObjectInstantiationDebug:
    """Test to debug the object instantiation process."""
    
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
    
    def test_simulate_object_instantiation_process(self):
        """Test simulating the actual object instantiation process."""
        # Simulate the object type definition (from hearth_and_shadow_objects.yaml)
        obj_type_definition = {
            'interactions': {
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
                            'message': "{{player_name}} examines the partner's evidence and finds crucial clues!",
                            'observers': ['room_characters']
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
                        },
                        {
                            'type': 'generate_event',
                            'message': "{{player_name}} collects the partner's evidence!",
                            'observers': ['room_characters']
                        }
                    ]
                }
            }
        }
        
        # Simulate the room instance (from hearth_and_shadow_rooms.yaml)
        obj_instance_cfg = {
            'id': 'partner_evidence',
            'name': "Partner's Evidence",
            'object_type_id': 'partner_evidence',
            'current_room_id': 'town_square',
            'description': 'A bloodstained notebook and a broken badge - the remains of Detective Thorne\'s murdered partner.'
            # No interactions defined here - should inherit from object type
        }
        
        # Simulate the object instantiation process (from _instantiate_rooms_and_objects)
        obj_type_interactions = obj_type_definition['interactions']
        obj_instance_interactions = obj_instance_cfg.get('interactions', {})
        final_interactions = {**obj_type_interactions, **obj_instance_interactions}
        
        # Create the final object
        final_object = Mock()
        final_object.id = obj_instance_cfg['id']
        final_object.name = obj_instance_cfg['name']
        final_object.description = obj_instance_cfg['description']
        final_object.properties = {'pickupable': True, 'size': 'small', 'readable': True}
        final_object.interactions = final_interactions
        
        # Verify the final object has interactions
        assert 'interactions' in final_object.__dict__, "Final object should have interactions"
        assert 'look' in final_object.interactions, "Final object should have 'look' interaction"
        assert 'pickup' in final_object.interactions, "Final object should have 'pickup' interaction"
        
        # Verify the interactions have effects
        assert 'effects' in final_object.interactions['look'], "Look interaction should have effects"
        assert 'effects' in final_object.interactions['pickup'], "Pickup interaction should have effects"
        
        # Verify the effects are correct
        look_effects = final_object.interactions['look']['effects']
        pickup_effects = final_object.interactions['pickup']['effects']
        
        assert len(look_effects) > 0, "Look interaction should have effects"
        assert len(pickup_effects) > 0, "Pickup interaction should have effects"
        
        # Check that the effects set the right property
        look_set_property_effect = None
        pickup_set_property_effect = None
        
        for effect in look_effects:
            if effect.get('type') == 'set_property' and effect.get('property') == 'partner_evidence_found':
                look_set_property_effect = effect
                break
        
        for effect in pickup_effects:
            if effect.get('type') == 'set_property' and effect.get('property') == 'partner_evidence_found':
                pickup_set_property_effect = effect
                break
        
        assert look_set_property_effect is not None, "Look interaction should have set_property effect for partner_evidence_found"
        assert pickup_set_property_effect is not None, "Pickup interaction should have set_property effect for partner_evidence_found"
        
        assert look_set_property_effect['value'] == True, "Look effect should set partner_evidence_found to True"
        assert pickup_set_property_effect['value'] == True, "Pickup effect should set partner_evidence_found to True"
        
        print("Object instantiation simulation successful!")
        print(f"Final object interactions: {final_object.interactions}")
        
        # Now test the actual pickup action
        mock_room = Mock()
        mock_room.objects = {final_object.id: final_object}
        mock_room.get_object = Mock(return_value=final_object)
        self.game_master.rooms = {'town_square': mock_room}
        
        # Test pickup action
        events, feedback = handle_pickup_action(
            self.game_master,
            self.character,
            self.action_config,
            {'object_name': final_object.name}
        )
        
        # Check that the flag was set
        assert self.character.properties.get('partner_evidence_found', False) == True, f"partner_evidence_found should be True, got {self.character.properties.get('partner_evidence_found', False)}"
        assert self.character.evidence_found == 1, f"evidence_found should be 1, got {self.character.evidence_found}"
        
        print(f"Character properties after pickup: {self.character.properties}")
        print(f"Evidence found: {self.character.evidence_found}")
        print(f"Feedback: {feedback}")
    
    def test_debug_actual_game_object(self):
        """Test debugging the actual game object that Thorne picked up."""
        # Create a mock object that exactly matches what should be in the game
        partner_evidence = Mock()
        partner_evidence.id = "partner_evidence"
        partner_evidence.name = "Partner's Evidence"
        partner_evidence.description = "A bloodstained notebook and a broken badge - the remains of Detective Thorne's murdered partner."
        partner_evidence.properties = {
            'pickupable': True,
            'size': 'small',
            'readable': True
        }
        
        # This should be the interactions from the object type definition
        partner_evidence.interactions = {
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
                        'message': "{{player_name}} examines the partner's evidence and finds crucial clues!",
                        'observers': ['room_characters']
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
                    },
                    {
                        'type': 'generate_event',
                        'message': "{{player_name}} collects the partner's evidence!",
                        'observers': ['room_characters']
                    }
                ]
            }
        }
        
        # Debug: Check if the object has interactions
        print(f"Object has interactions: {hasattr(partner_evidence, 'interactions')}")
        print(f"Object interactions: {partner_evidence.interactions}")
        print(f"Object has 'look' interaction: {'look' in partner_evidence.interactions}")
        print(f"Object has 'pickup' interaction: {'pickup' in partner_evidence.interactions}")
        
        if 'look' in partner_evidence.interactions:
            print(f"Look interaction effects: {partner_evidence.interactions['look'].get('effects', [])}")
        
        if 'pickup' in partner_evidence.interactions:
            print(f"Pickup interaction effects: {partner_evidence.interactions['pickup'].get('effects', [])}")
        
        # Mock the room and objects
        mock_room = Mock()
        mock_room.objects = {'partner_evidence': partner_evidence}
        mock_room.get_object = Mock(return_value=partner_evidence)
        self.game_master.rooms = {'town_square': mock_room}
        
        # Test pickup action
        events, feedback = handle_pickup_action(
            self.game_master,
            self.character,
            self.action_config,
            {'object_name': "Partner's Evidence"}
        )
        
        # Check that the flag was set
        assert self.character.properties.get('partner_evidence_found', False) == True, f"partner_evidence_found should be True, got {self.character.properties.get('partner_evidence_found', False)}"
        assert self.character.evidence_found == 1, f"evidence_found should be 1, got {self.character.evidence_found}"
        
        print(f"Character properties after pickup: {self.character.properties}")
        print(f"Evidence found: {self.character.evidence_found}")
        print(f"Feedback: {feedback}")


