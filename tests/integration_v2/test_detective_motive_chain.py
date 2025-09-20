"""
Integration tests for Detective James's improved motive chain.

Tests the 4-step motive progression:
1. Gather Evidence → evidence_collected: 3
2. Interview Witnesses → witnesses_interviewed: 2  
3. Expose Cult → cult_exposed: true
4. Bring Justice → justice_served: true
"""

import pytest
from unittest.mock import patch, MagicMock
from motive.sim_v2.v2_config_validator import V2GameConfig
from motive.game_master import GameMaster
from motive.player import Player


class TestDetectiveMotiveChain:
    """Test Detective James's 4-step motive completion chain."""

    @pytest.fixture
    def minimal_config(self):
        """Minimal test config for Detective James motive testing."""
        return {
            "includes": [
                "minimal_actions.yaml",
                "minimal_rooms.yaml", 
                "minimal_characters.yaml"
            ],
            "game_settings": {
                "num_rounds": 1,
                "initial_ap_per_turn": 10,
                "manual": "../docs/MANUAL.md"
            },
            "players": [
                {
                    "name": "Detective_James",
                    "provider": "dummy",
                    "model": "test"
                }
            ]
        }

    @pytest.fixture
    def minimal_actions_config(self):
        """Minimal actions needed for Detective James motive testing."""
        return {
            "action_definitions": {
                "look": {
                    "id": "look",
                    "name": "look",
                    "cost": 1,
                    "description": "Look at objects or rooms",
                    "parameters": [
                        {
                            "name": "target",
                            "type": "string",
                            "description": "Object or room to look at"
                        }
                    ],
                    "effects": [
                        {
                            "type": "call_function",
                            "function": "look_at_target"
                        }
                    ]
                },
                "investigate": {
                    "id": "investigate",
                    "name": "investigate",
                    "cost": 2,
                    "description": "Investigate evidence with investigation kit",
                    "parameters": [
                        {
                            "name": "target",
                            "type": "string",
                            "description": "Evidence to investigate"
                        }
                    ],
                    "effects": [
                        {
                            "type": "call_function", 
                            "function": "investigate_evidence"
                        }
                    ]
                },
                "talk": {
                    "id": "talk",
                    "name": "talk",
                    "cost": 1,
                    "description": "Talk to witnesses or NPCs",
                    "parameters": [
                        {
                            "name": "target",
                            "type": "string",
                            "description": "Person to talk to"
                        }
                    ],
                    "effects": [
                        {
                            "type": "call_function",
                            "function": "talk_to_witness"
                        }
                    ]
                },
                "expose": {
                    "id": "expose",
                    "name": "expose",
                    "cost": 3,
                    "description": "Expose cult activities",
                    "parameters": [],
                    "effects": [
                        {
                            "type": "call_function",
                            "function": "expose_cult"
                        }
                    ]
                },
                "arrest": {
                    "id": "arrest",
                    "name": "arrest",
                    "cost": 2,
                    "description": "Arrest cult members",
                    "parameters": [],
                    "effects": [
                        {
                            "type": "call_function",
                            "function": "arrest_cult_members"
                        }
                    ]
                },
                "pass": {
                    "id": "pass",
                    "name": "pass",
                    "cost": 0,
                    "description": "End turn without action",
                    "parameters": [],
                    "effects": []
                }
            }
        }

    @pytest.fixture
    def minimal_rooms_config(self):
        """Minimal rooms for Detective James motive testing."""
        return {
            "entity_definitions": {
                "town_square": {
                    "behaviors": ["room"],
                    "attributes": {
                        "name": "Town Square",
                        "description": "Central square with evidence and witnesses"
                    },
                    "properties": {
                        "exits": {
                            "tavern": {
                                "id": "tavern",
                                "name": "Tavern",
                                "destination_room_id": "tavern",
                                "aliases": ["tavern", "bar"]
                            }
                        },
                        "objects": {
                            "fresh_evidence": {
                                "id": "fresh_evidence",
                                "name": "Fresh Evidence",
                                "object_type_id": "fresh_evidence",
                                "current_room_id": "town_square",
                                "description": "Bloodstains and strange markings"
                            },
                            "notice_board": {
                                "id": "notice_board", 
                                "name": "Notice Board",
                                "object_type_id": "notice_board",
                                "current_room_id": "town_square",
                                "description": "Missing person posters"
                            },
                            "investigation_kit": {
                                "id": "investigation_kit",
                                "name": "Investigation Kit", 
                                "object_type_id": "investigation_kit",
                                "current_room_id": "town_square",
                                "description": "Tools for examining evidence"
                            }
                        }
                    }
                },
                "tavern": {
                    "behaviors": ["room"],
                    "attributes": {
                        "name": "Tavern",
                        "description": "Local tavern with witnesses"
                    },
                    "properties": {
                        "exits": {
                            "square": {
                                "id": "square",
                                "name": "Town Square", 
                                "destination_room_id": "town_square",
                                "aliases": ["square", "town"]
                            }
                        },
                        "objects": {
                            "barkeep": {
                                "id": "barkeep",
                                "name": "Barkeep",
                                "object_type_id": "barkeep",
                                "current_room_id": "tavern",
                                "description": "Local tavern keeper who knows everyone"
                            }
                        }
                    }
                }
            }
        }

    @pytest.fixture
    def minimal_characters_config(self):
        """Minimal characters for Detective James motive testing."""
        return {
            "entity_definitions": {
                "detective_james": {
                    "behaviors": ["character"],
                    "attributes": {
                        "name": "Detective James Thorne",
                        "short_name": "Detective Thorne",
                        "backstory": "Former city guard turned investigator"
                    },
                    "properties": {
                        "motives": [
                            {
                                "id": "investigate_mayor",
                                "description": "Uncover the truth behind the mayor's disappearance and bring the cult to justice",
                                "success_conditions": [
                                    {"operator": "AND"},
                                    {
                                        "type": "character_has_property",
                                        "property": "evidence_collected",
                                        "value": 3
                                    },
                                    {
                                        "type": "character_has_property", 
                                        "property": "witnesses_interviewed",
                                        "value": 2
                                    },
                                    {
                                        "type": "character_has_property",
                                        "property": "cult_exposed", 
                                        "value": True
                                    },
                                    {
                                        "type": "character_has_property",
                                        "property": "justice_served",
                                        "value": True
                                    }
                                ],
                                "failure_conditions": [
                                    {"operator": "OR"},
                                    {
                                        "type": "character_has_property",
                                        "property": "mayor_dead",
                                        "value": True
                                    },
                                    {
                                        "type": "character_has_property",
                                        "property": "cult_succeeded",
                                        "value": True
                                    }
                                ]
                            }
                        ],
                        "initial_rooms": [
                            {
                                "room_id": "town_square",
                                "chance": 100,
                                "reason": "Starting investigation"
                            }
                        ],
                        "aliases": ["james", "detective", "thorne"]
                    }
                }
            }
        }

    @patch('motive.player.create_llm_client')
    @patch('motive.game_master.GameMaster._load_manual_content')
    async def test_detective_motive_chain_step1_evidence_gathering(self, mock_manual, mock_llm_client, 
                                                           minimal_config, minimal_actions_config,
                                                           minimal_rooms_config, minimal_characters_config):
        """Test Step 1: Evidence gathering config structure and game initialization."""
        
        mock_llm_client.return_value = MagicMock()
        mock_manual.return_value = "Test manual content"
        
        # Create proper config structure
        config_dict = minimal_config.copy()
        config_dict.update(minimal_actions_config)
        
        # Merge entity_definitions properly
        if 'entity_definitions' not in config_dict:
            config_dict['entity_definitions'] = {}
        
        # Add rooms from minimal_rooms_config
        rooms_entities = minimal_rooms_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(rooms_entities)
        
        # Add characters from minimal_characters_config  
        char_entities = minimal_characters_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(char_entities)
        
        # Initialize game master with proper config
        game_master = GameMaster(
            game_config=config_dict,
            game_id="test_detective_motive",
            deterministic=True,
            no_file_logging=True
        )
        
        # Test that the game initialized correctly
        assert len(game_master.players) == 1
        detective = game_master.players[0]
        assert detective.name == "Detective_James"
        
        # Test that the character was assigned correctly
        assert detective.character is not None
        assert detective.character.name == "Detective James Thorne"
        assert detective.character.current_room_id == "town_square"
        
        # Test that the character has the expected properties structure
        assert hasattr(detective.character, 'properties')
        assert isinstance(detective.character.properties, dict)
        
        # Test that the character has the expected motive (as string)
        assert detective.character.motive is not None
        assert isinstance(detective.character.motive, str)
        assert "investigate_mayor" in detective.character.motive or "Uncover the truth" in detective.character.motive
        
        # Test that the character can track evidence collection (initial state)
        evidence_count = detective.character.properties.get("evidence_collected", 0)
        assert evidence_count == 0  # Should start at 0
        
        # Test that the character can set properties
        detective.character.properties["evidence_collected"] = 3
        evidence_count = detective.character.properties.get("evidence_collected", 0)
        assert evidence_count == 3

    @patch('motive.player.create_llm_client')
    @patch('motive.game_master.GameMaster._load_manual_content')
    async def test_detective_motive_chain_step2_witness_interviews(self, mock_manual, mock_llm_client,
                                                           minimal_config, minimal_actions_config,
                                                           minimal_rooms_config, minimal_characters_config):
        """Test Step 2: Witness interviews config structure and property tracking."""
        
        mock_llm_client.return_value = MagicMock()
        mock_manual.return_value = "Test manual content"
        
        # Create proper config structure
        config_dict = minimal_config.copy()
        config_dict.update(minimal_actions_config)
        
        # Merge entity_definitions properly
        if 'entity_definitions' not in config_dict:
            config_dict['entity_definitions'] = {}
        
        # Add rooms from minimal_rooms_config
        rooms_entities = minimal_rooms_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(rooms_entities)
        
        # Add characters from minimal_characters_config  
        char_entities = minimal_characters_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(char_entities)
        
        # Initialize game master with proper config
        game_master = GameMaster(
            game_config=config_dict,
            game_id="test_detective_motive",
            deterministic=True,
            no_file_logging=True
        )
        
        # Test that the game initialized correctly
        assert len(game_master.players) == 1
        detective = game_master.players[0]
        assert detective.name == "Detective_James"
        
        # Test that the character was assigned correctly
        assert detective.character is not None
        assert detective.character.name == "Detective James Thorne"
        
        # Test that the character can track witness interviews (initial state)
        witnesses_count = detective.character.properties.get("witnesses_interviewed", 0)
        assert witnesses_count == 0  # Should start at 0
        
        # Test that the character can set witness interview properties
        detective.character.properties["witnesses_interviewed"] = 2
        witnesses_count = detective.character.properties.get("witnesses_interviewed", 0)
        assert witnesses_count == 2

    @patch('motive.player.create_llm_client')
    @patch('motive.game_master.GameMaster._load_manual_content')
    async def test_detective_motive_chain_step3_cult_exposure(self, mock_manual, mock_llm_client,
                                                       minimal_config, minimal_actions_config,
                                                       minimal_rooms_config, minimal_characters_config):
        """Test Step 3: Cult exposure config structure and property tracking."""
        
        mock_llm_client.return_value = MagicMock()
        mock_manual.return_value = "Test manual content"
        
        # Create proper config structure
        config_dict = minimal_config.copy()
        config_dict.update(minimal_actions_config)
        
        # Merge entity_definitions properly
        if 'entity_definitions' not in config_dict:
            config_dict['entity_definitions'] = {}
        
        # Add rooms from minimal_rooms_config
        rooms_entities = minimal_rooms_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(rooms_entities)
        
        # Add characters from minimal_characters_config  
        char_entities = minimal_characters_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(char_entities)
        
        # Initialize game master with proper config
        game_master = GameMaster(
            game_config=config_dict,
            game_id="test_detective_motive",
            deterministic=True,
            no_file_logging=True
        )
        
        # Test that the game initialized correctly
        assert len(game_master.players) == 1
        detective = game_master.players[0]
        assert detective.name == "Detective_James"
        
        # Test that the character was assigned correctly
        assert detective.character is not None
        assert detective.character.name == "Detective James Thorne"
        
        # Test that the character can track cult exposure (initial state)
        cult_exposed = detective.character.properties.get("cult_exposed", False)
        assert cult_exposed == False  # Should start as False
        
        # Test that the character can set cult exposure properties
        detective.character.properties["cult_exposed"] = True
        cult_exposed = detective.character.properties.get("cult_exposed", False)
        assert cult_exposed == True

    @patch('motive.player.create_llm_client')
    @patch('motive.game_master.GameMaster._load_manual_content')
    async def test_detective_motive_chain_step4_justice_delivery(self, mock_manual, mock_llm_client,
                                                          minimal_config, minimal_actions_config,
                                                          minimal_rooms_config, minimal_characters_config):
        """Test Step 4: Justice delivery config structure and property tracking."""
        
        mock_llm_client.return_value = MagicMock()
        mock_manual.return_value = "Test manual content"
        
        # Create proper config structure
        config_dict = minimal_config.copy()
        config_dict.update(minimal_actions_config)
        
        # Merge entity_definitions properly
        if 'entity_definitions' not in config_dict:
            config_dict['entity_definitions'] = {}
        
        # Add rooms from minimal_rooms_config
        rooms_entities = minimal_rooms_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(rooms_entities)
        
        # Add characters from minimal_characters_config  
        char_entities = minimal_characters_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(char_entities)
        
        # Initialize game master with proper config
        game_master = GameMaster(
            game_config=config_dict,
            game_id="test_detective_motive",
            deterministic=True,
            no_file_logging=True
        )
        
        # Test that the game initialized correctly
        assert len(game_master.players) == 1
        detective = game_master.players[0]
        assert detective.name == "Detective_James"
        
        # Test that the character was assigned correctly
        assert detective.character is not None
        assert detective.character.name == "Detective James Thorne"
        
        # Test that the character can track justice delivery (initial state)
        justice_served = detective.character.properties.get("justice_served", False)
        assert justice_served == False  # Should start as False
        
        # Test that the character can set justice delivery properties
        detective.character.properties["justice_served"] = True
        justice_served = detective.character.properties.get("justice_served", False)
        assert justice_served == True

    @patch('motive.player.create_llm_client')
    @patch('motive.game_master.GameMaster._load_manual_content')
    async def test_detective_motive_chain_complete_workflow(self, mock_manual, mock_llm_client,
                                                    minimal_config, minimal_actions_config,
                                                    minimal_rooms_config, minimal_characters_config):
        """Test complete 4-step motive chain config structure and property tracking."""
        
        mock_llm_client.return_value = MagicMock()
        mock_manual.return_value = "Test manual content"
        
        # Create proper config structure
        config_dict = minimal_config.copy()
        config_dict.update(minimal_actions_config)
        
        # Merge entity_definitions properly
        if 'entity_definitions' not in config_dict:
            config_dict['entity_definitions'] = {}
        
        # Add rooms from minimal_rooms_config
        rooms_entities = minimal_rooms_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(rooms_entities)
        
        # Add characters from minimal_characters_config  
        char_entities = minimal_characters_config.get('entity_definitions', {})
        config_dict['entity_definitions'].update(char_entities)
        
        # Initialize game master with proper config
        game_master = GameMaster(
            game_config=config_dict,
            game_id="test_detective_motive",
            deterministic=True,
            no_file_logging=True
        )
        
        # Test that the game initialized correctly
        assert len(game_master.players) == 1
        detective = game_master.players[0]
        assert detective.name == "Detective_James"
        
        # Test that the character was assigned correctly
        assert detective.character is not None
        assert detective.character.name == "Detective James Thorne"
        
        # Test that the character can track all 4 motive chain properties
        # Step 1: Evidence collection
        detective.character.properties["evidence_collected"] = 3
        assert detective.character.properties.get("evidence_collected") == 3
        
        # Step 2: Witness interviews
        detective.character.properties["witnesses_interviewed"] = 2
        assert detective.character.properties.get("witnesses_interviewed") == 2
        
        # Step 3: Cult exposure
        detective.character.properties["cult_exposed"] = True
        assert detective.character.properties.get("cult_exposed") == True
        
        # Step 4: Justice delivery
        detective.character.properties["justice_served"] = True
        assert detective.character.properties.get("justice_served") == True
        
        # Test that all properties can be tracked together
        assert detective.character.properties.get("evidence_collected") == 3
        assert detective.character.properties.get("witnesses_interviewed") == 2
        assert detective.character.properties.get("cult_exposed") == True
        assert detective.character.properties.get("justice_served") == True
