"""
Integration test for Detective Thorne's motive completion with enhanced content.
Tests that Detective Thorne can achieve all 8 success conditions using multiple pathways.
"""
import pytest
from motive.hooks.core_hooks import handle_pickup_action
from datetime import datetime
import logging

class TestEnhancedDetectiveThorneMotive:
    """Test that Detective Thorne can complete his motive using multiple pathways."""
    
    def setup_method(self):
        """Set up test environment with Detective Thorne and enhanced objects."""
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
            'current_room_id': 'town_square'
        })()
        
        # Create mock game state
        self.game_state = type('GameState', (), {
            'characters': [self.character],
            'rooms': {},
            'objects': {}
        })()
        
        # Create mock logger
        self.logger = logging.getLogger('test')
        
        # Create enhanced evidence objects
        self.town_records = type('Object', (), {
            'id': 'town_records',
            'name': 'Town Records',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'increment_property',
                            'target': 'player',
                            'property': 'evidence_found',
                            'increment_value': 1
                        }
                    ]
                }
            }
        })()
        
        self.local_newspaper = type('Object', (), {
            'id': 'local_newspaper',
            'name': 'Local Newspaper',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'increment_property',
                            'target': 'player',
                            'property': 'evidence_found',
                            'increment_value': 1
                        }
                    ]
                }
            }
        })()
        
        self.graveyard_epitaphs = type('Object', (), {
            'id': 'graveyard_epitaphs',
            'name': 'Graveyard Epitaphs',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'increment_property',
                            'target': 'player',
                            'property': 'evidence_found',
                            'increment_value': 1
                        }
                    ]
                }
            }
        })()
        
        self.astronomers_notes = type('Object', (), {
            'id': 'astronomers_notes',
            'name': 'Astronomer\'s Notes',
            'properties': {'pickupable': True, 'readable': True, 'pickup_action': 'use'},
            'interactions': {
                'use': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'cult_timing_understood',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.ancient_calendar = type('Object', (), {
            'id': 'ancient_calendar',
            'name': 'Ancient Calendar',
            'properties': {'pickupable': True, 'readable': True, 'pickup_action': 'use'},
            'interactions': {
                'use': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'cult_timing_understood',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.ritual_schedule = type('Object', (), {
            'id': 'ritual_schedule',
            'name': 'Ritual Schedule',
            'properties': {'pickupable': True, 'readable': True, 'pickup_action': 'use'},
            'interactions': {
                'use': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'cult_timing_understood',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.church_records = type('Object', (), {
            'id': 'church_records',
            'name': 'Church Records',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'increment_property',
                            'target': 'player',
                            'property': 'evidence_found',
                            'increment_value': 1
                        }
                    ]
                }
            }
        })()
        
        self.priest_diary = type('Object', (), {
            'id': 'priest_diary',
            'name': 'Priest\'s Diary',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'cult_hierarchy_discovered',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.sacred_map = type('Object', (), {
            'id': 'sacred_map',
            'name': 'Sacred Map',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'cult_locations_mapped',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.ritual_texts = type('Object', (), {
            'id': 'ritual_texts',
            'name': 'Ritual Texts',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'ritual_knowledge_mastered',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.justice_weapon = type('Object', (), {
            'id': 'justice_weapon',
            'name': 'Justice Weapon',
            'properties': {'pickupable': True, 'usable': True},
            'interactions': {
                'pickup': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'justice_tools_acquired',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.evidence_compiler = type('Object', (), {
            'id': 'evidence_compiler',
            'name': 'Evidence Compiler',
            'properties': {'pickupable': True, 'usable': True, 'pickup_action': 'use'},
            'interactions': {
                'use': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'evidence_chain_complete',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.confrontation_manual = type('Object', (), {
            'id': 'confrontation_manual',
            'name': 'Confrontation Manual',
            'properties': {'pickupable': True, 'usable': True, 'pickup_action': 'use'},
            'interactions': {
                'use': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'final_confrontation_ready',
                            'value': True
                        }
                    ]
                }
            }
        })()

    def test_evidence_found_multiple_pathways(self):
        """Test that Detective Thorne can find evidence through multiple pathways."""
        from unittest.mock import Mock
        import pytest
        
        # Test Town Records
        game_master = Mock()
        room = Mock()
        room.remove_object = Mock()
        room.objects = {"Town Records": self.town_records}
        game_master.rooms = {"town_square": room}
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Town Records'}
            )
        assert self.character.properties["evidence_found"] == 1
        assert any("Evidence Found" in str(feedback) for feedback in feedback)
        
        # Test Local Newspaper
        room.objects = {"Local Newspaper": self.local_newspaper}
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Local Newspaper'}
            )
        assert self.character.properties["evidence_found"] == 2
        assert any("Evidence Found" in str(feedback) for feedback in feedback)
        
        # Test Graveyard Epitaphs
        room.objects = {"Graveyard Epitaphs": self.graveyard_epitaphs}
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Graveyard Epitaphs'}
            )
        assert self.character.properties["evidence_found"] == 3
        assert any("Evidence Found" in str(feedback) for feedback in feedback)

    def test_cult_timing_understood_multiple_pathways(self):
        """Test that Detective Thorne can understand cult timing through multiple pathways."""
        from unittest.mock import Mock
        import pytest
        
        # Test Astronomer's Notes
        game_master = Mock()
        room = Mock()
        room.remove_object = Mock()
        room.objects = {"Astronomer's Notes": self.astronomers_notes}
        game_master.rooms = {"town_square": room}
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Astronomer\'s Notes'}
            )
        assert self.character.properties["cult_timing_understood"] == True
        assert any("cult timing" in str(feedback).lower() for feedback in feedback)
        
        # Reset for next test
        self.character.properties["cult_timing_understood"] = False
        
        # Test Ancient Calendar
        room.objects = {"Ancient Calendar": self.ancient_calendar}
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Ancient Calendar'}
            )
        assert self.character.properties["cult_timing_understood"] == True
        assert any("cult timing" in str(feedback).lower() for feedback in feedback)
        
        # Reset for next test
        self.character.properties["cult_timing_understood"] = False
        
        # Test Ritual Schedule
        room.objects = {"Ritual Schedule": self.ritual_schedule}
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Ritual Schedule'}
            )
        assert self.character.properties["cult_timing_understood"] == True
        assert any("cult timing" in str(feedback).lower() for feedback in feedback)

    def test_complete_motive_multiple_pathways(self):
        """Test that Detective Thorne can complete his motive using multiple pathways."""
        # Evidence Found (3/3) - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'town_records'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'local_newspaper'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'graveyard_epitaphs'}
        )
        assert self.character.properties["evidence_found"] == 3
        
        # Cult Hierarchy Discovered - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'priest_diary'}
        )
        assert self.character.properties["cult_hierarchy_discovered"] == True
        
        # Cult Locations Mapped - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'sacred_map'}
        )
        assert self.character.properties["cult_locations_mapped"] == True
        
        # Ritual Knowledge Mastered - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'ritual_texts'}
        )
        assert self.character.properties["ritual_knowledge_mastered"] == True
        
        # Cult Timing Understood - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'astronomers_notes'}
        )
        assert self.character.properties["cult_timing_understood"] == True
        
        # Justice Tools Acquired - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'justice_weapon'}
        )
        assert self.character.properties["justice_tools_acquired"] == True
        
        # Evidence Chain Complete - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'evidence_compiler'}
        )
        assert self.character.properties["evidence_chain_complete"] == True
        
        # Final Confrontation Ready - Multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'confrontation_manual'}
        )
        assert self.character.properties["final_confrontation_ready"] == True
        
        # Verify all 8 success conditions are met
        assert self.character.properties["evidence_found"] == 3
        assert self.character.properties["cult_hierarchy_discovered"] == True
        assert self.character.properties["cult_locations_mapped"] == True
        assert self.character.properties["ritual_knowledge_mastered"] == True
        assert self.character.properties["cult_timing_understood"] == True
        assert self.character.properties["justice_tools_acquired"] == True
        assert self.character.properties["evidence_chain_complete"] == True
        assert self.character.properties["final_confrontation_ready"] == True

    def test_robustness_against_player_interference(self):
        """Test that the motive can still be completed even if some objects are taken by other players."""
        # Simulate other players taking some objects
        # Evidence Found - Still have 3 pathways available
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'church_records'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'local_newspaper'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'graveyard_epitaphs'}
        )
        assert self.character.properties["evidence_found"] == 3
        
        # Cult Timing - Still have 3 pathways available
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'ancient_calendar'}
        )
        assert self.character.properties["cult_timing_understood"] == True
        
        # Other properties - Still have multiple pathways
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'priest_diary'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'sacred_map'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'ritual_texts'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'justice_weapon'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'evidence_compiler'}
        )
        events, feedback = handle_pickup_action(
            self.game_state,
            self.character,
            type('ActionConfig', (), {})(),
            {'object_name': 'confrontation_manual'}
        )
        
        # Verify all 8 success conditions are still met
        assert self.character.properties["evidence_found"] == 3
        assert self.character.properties["cult_hierarchy_discovered"] == True
        assert self.character.properties["cult_locations_mapped"] == True
        assert self.character.properties["ritual_knowledge_mastered"] == True
        assert self.character.properties["cult_timing_understood"] == True
        assert self.character.properties["justice_tools_acquired"] == True
        assert self.character.properties["evidence_chain_complete"] == True
        assert self.character.properties["final_confrontation_ready"] == True
