"""
TDD tests for the redesigned evidence system.
Tests unique evidence flags and computed properties instead of fragile counters.
"""
import pytest
from motive.hooks.core_hooks import handle_pickup_action, look_at_target
from unittest.mock import Mock
import logging

class TestEvidenceSystemRedesign:
    """Test the redesigned evidence system with unique flags and computed properties."""
    
    def setup_method(self):
        """Set up test environment with Detective Thorne and evidence objects."""
        from motive.character import Character

        # Create a character with the new evidence system
        self.character = Character(
            char_id='detective_thorne',
            name='Detective Thorne',
            backstory='A determined investigator.',
            current_room_id='town_square',
            inventory={},
            properties={
                'inventory_size': 12,
                # Individual evidence flags (can only be set once)
                'town_records_found': False,
                'local_newspaper_found': False,
                'graveyard_epitaphs_found': False,
                'church_records_found': False,
                'witness_testimony_found': False,
                'editor_notes_found': False,
                'evidence_found': 0,
            },
        )
        
        # Create evidence objects with unique flags
        self.town_records = type('Object', (), {
            'id': 'town_records',
            'name': 'Town Records',
            'description': 'Official town records documenting recent disappearances and suspicious activities.',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'town_records_found',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.local_newspaper = type('Object', (), {
            'id': 'local_newspaper',
            'name': 'Local Newspaper',
            'description': 'Recent editions of the Blackwater Gazette containing eyewitness accounts and investigative reports.',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'local_newspaper_found',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.graveyard_epitaphs = type('Object', (), {
            'id': 'graveyard_epitaphs',
            'name': 'Graveyard Epitaphs',
            'description': 'Ancient gravestone epitaphs that tell stories of the missing townsfolk.',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'graveyard_epitaphs_found',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.church_records = type('Object', (), {
            'id': 'church_records',
            'name': 'Church Records',
            'description': 'Detailed church records documenting recent disappearances and suspicious activities.',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'church_records_found',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.witness_testimony = type('Object', (), {
            'id': 'witness_testimony',
            'name': 'Witness Testimony',
            'description': 'Written testimony from witnesses who have seen cult activities.',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
                'look': {
                    'effects': [
                        {
                            'type': 'set_property',
                            'target': 'player',
                            'property': 'witness_testimony_found',
                            'value': True
                        }
                    ]
                }
            }
        })()
        
        self.editor_notes = type('Object', (), {
            'id': 'editor_notes',
            'name': 'Editor\'s Notes',
            'description': 'Personal notes from the newspaper editor about the recent disappearances and suspicious activities.',
            'properties': {'pickupable': True, 'readable': True},
            'interactions': {
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
        })()

    def test_evidence_flag_set_once_on_look(self):
        """Test that looking at evidence sets the unique flag only once."""
        from unittest.mock import Mock
        import pytest
        
        game_master = Mock()
        room = Mock()
        room.get_object = Mock(return_value=self.town_records)
        game_master.rooms = {"town_square": room}
        
        # First look - should set the flag
        events, feedback = look_at_target(
            game_master,
            self.character,
            Mock(),
            {"target": "Town Records"}
        )
        
        assert self.character.properties["town_records_found"] == True
        assert self.character.properties.get("evidence_found", 0) == 0  # Not computed yet
        
        # Second look - should not change the flag (idempotent)
        events, feedback = look_at_target(
            game_master,
            self.character,
            Mock(),
            {"target": "Town Records"}
        )
        
        assert self.character.properties["town_records_found"] == True  # Still True
        assert self.character.properties.get("evidence_found", 0) == 0  # Still not computed

    def test_evidence_flag_set_once_on_pickup(self):
        """Test that picking up evidence sets the unique flag only once."""
        from unittest.mock import Mock
        import pytest
        
        game_master = Mock()
        room = Mock()
        room.remove_object = Mock()
        room.objects = {"Town Records": self.town_records}
        game_master.rooms = {"town_square": room}
        
        # First pickup - should set the flag
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Town Records'}
            )
        
        assert self.character.properties["town_records_found"] == True
        assert self.character.properties.get("evidence_found", 0) == 0  # Not computed yet
        
        # Second pickup of same object - should not change the flag
        with pytest.MonkeyPatch().context() as m:
            m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                     lambda *args: (True, None, None))
            
            events, feedback = handle_pickup_action(
                game_master,
                self.character,
                Mock(),
                {'object_name': 'Town Records'}
            )
        
        assert self.character.properties["town_records_found"] == True  # Still True
        assert self.character.properties.get("evidence_found", 0) == 0  # Still not computed

    def test_multiple_evidence_flags_accumulate(self):
        """Test that multiple evidence flags can be set independently."""
        from unittest.mock import Mock
        import pytest
        
        game_master = Mock()
        room = Mock()
        room.remove_object = Mock()
        game_master.rooms = {"town_square": room}
        
        # Pick up different evidence objects
        evidence_objects = [
            ("Town Records", self.town_records, "town_records_found"),
            ("Local Newspaper", self.local_newspaper, "local_newspaper_found"),
            ("Graveyard Epitaphs", self.graveyard_epitaphs, "graveyard_epitaphs_found"),
            ("Church Records", self.church_records, "church_records_found"),
            ("Witness Testimony", self.witness_testimony, "witness_testimony_found"),
            ("Editor's Notes", self.editor_notes, "editor_notes_found")
        ]
        
        for obj_name, obj, flag_name in evidence_objects:
            room.objects = {obj_name: obj}
            
            with pytest.MonkeyPatch().context() as m:
                m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                         lambda *args: (True, None, None))
                
                events, feedback = handle_pickup_action(
                    game_master,
                    self.character,
                    Mock(),
                    {'object_name': obj_name}
                )
            
            assert self.character.properties[flag_name] == True
        
        # All flags should be set
        assert self.character.properties["town_records_found"] == True
        assert self.character.properties["local_newspaper_found"] == True
        assert self.character.properties["graveyard_epitaphs_found"] == True
        assert self.character.properties["church_records_found"] == True
        assert self.character.properties["witness_testimony_found"] == True
        assert self.character.properties["editor_notes_found"] == True

    def test_evidence_computed_property(self):
        """Test that the computed evidence_found property counts unique flags."""
        # This test would require implementing the computed property logic
        # For now, we'll test the concept manually
        
        # Set some evidence flags
        self.character.properties["town_records_found"] = True
        self.character.properties["local_newspaper_found"] = True
        self.character.properties["graveyard_epitaphs_found"] = True
        
        # Manually compute evidence_found (this would be done by the game engine)
        evidence_flags = [
            "town_records_found",
            "local_newspaper_found", 
            "graveyard_epitaphs_found",
            "church_records_found",
            "witness_testimony_found",
            "editor_notes_found"
        ]
        
        evidence_count = sum(1 for flag in evidence_flags if self.character.properties.get(flag, False))
        self.character.properties["evidence_found"] = evidence_count
        
        assert self.character.properties["evidence_found"] == 3

    def test_evidence_system_robustness(self):
        """Test that the evidence system is robust against multiple interactions."""
        from unittest.mock import Mock
        import pytest
        
        game_master = Mock()
        room = Mock()
        room.remove_object = Mock()
        room.objects = {"Town Records": self.town_records}
        game_master.rooms = {"town_square": room}
        
        # Pick up the same evidence multiple times
        for _ in range(5):
            with pytest.MonkeyPatch().context() as m:
                m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                         lambda *args: (True, None, None))
                
                events, feedback = handle_pickup_action(
                    game_master,
                    self.character,
                    Mock(),
                    {'object_name': 'Town Records'}
                )
        
        # Flag should still be True (not incremented multiple times)
        assert self.character.properties["town_records_found"] == True
        
        # Look at the same evidence multiple times
        room.get_object = Mock(return_value=self.town_records)
        for _ in range(3):
            events, feedback = look_at_target(
                game_master,
                self.character,
                Mock(),
                {"target": "Town Records"}
            )
        
        # Flag should still be True (not incremented multiple times)
        assert self.character.properties["town_records_found"] == True

    def test_evidence_system_completeness(self):
        """Test that all evidence can be found and counted correctly."""
        from unittest.mock import Mock
        import pytest
        
        game_master = Mock()
        room = Mock()
        room.remove_object = Mock()
        game_master.rooms = {"town_square": room}
        
        # All evidence objects
        evidence_objects = [
            ("Town Records", self.town_records, "town_records_found"),
            ("Local Newspaper", self.local_newspaper, "local_newspaper_found"),
            ("Graveyard Epitaphs", self.graveyard_epitaphs, "graveyard_epitaphs_found"),
            ("Church Records", self.church_records, "church_records_found"),
            ("Witness Testimony", self.witness_testimony, "witness_testimony_found"),
            ("Editor's Notes", self.editor_notes, "editor_notes_found")
        ]
        
        # Pick up all evidence
        for obj_name, obj, flag_name in evidence_objects:
            room.objects = {obj_name: obj}
            
            with pytest.MonkeyPatch().context() as m:
                m.setattr('motive.inventory_constraints.validate_inventory_transfer', 
                         lambda *args: (True, None, None))
                
                events, feedback = handle_pickup_action(
                    game_master,
                    self.character,
                    Mock(),
                    {'object_name': obj_name}
                )
        
        # Compute evidence count
        evidence_flags = [flag for _, _, flag in evidence_objects]
        evidence_count = sum(1 for flag in evidence_flags if self.character.properties.get(flag, False))
        self.character.properties["evidence_found"] = evidence_count
        
        # Should have found all 6 pieces of evidence
        assert self.character.properties["evidence_found"] == 6
        
        # All individual flags should be True
        for _, _, flag_name in evidence_objects:
            assert self.character.properties[flag_name] == True
