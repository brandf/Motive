import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import AIMessage

from motive.game_master import GameMaster
from motive.config import (
    GameConfig, PlayerConfig, ThemeConfig, EditionConfig, ObjectTypeConfig, 
    ActionConfig, CharacterConfig, RoomConfig, ExitConfig, ObjectInstanceConfig, 
    ActionRequirementConfig, ActionEffectConfig, ParameterConfig, GameSettings, CoreConfig
)
from motive.player import Player
from motive.character import Character
from motive.game_object import GameObject
from motive.room import Room


@pytest.fixture
def mock_game_master_validation():
    with (
            patch('os.makedirs'),
            patch('logging.FileHandler') as mock_file_handler_class, 
            patch('motive.player.create_llm_client', return_value=MagicMock()),                                                           
            patch('motive.player.Player') as mock_player_class,      
            patch('motive.game_initializer.GameInitializer._load_yaml_config') as mock_load_yaml_config,                                  
            patch('motive.game_master.GameMaster._load_manual_content') as mock_load_manual_content,                                      
            patch('sys.stdout') as mock_stdout,
            patch('motive.hooks.core_hooks.look_at_target', return_value=([MagicMock()], ["Mock look feedback"])),                        
            patch('motive.hooks.core_hooks.generate_help_message', return_value=([MagicMock()], ["Mock help feedback"])),                 
            patch('motive.hooks.core_hooks.handle_move_action', return_value=([MagicMock()], ["Mock move feedback"])),                    
            patch('motive.hooks.core_hooks.handle_say_action', return_value=([MagicMock()], ["Mock say feedback"])),                      
            patch('motive.hooks.core_hooks.handle_pickup_action', return_value=([MagicMock()], ["Mock pickup feedback"]))                 
        ):
        mock_file_handler_instance = MagicMock()
        mock_file_handler_instance.level = 20  # INFO level
        mock_file_handler_class.return_value = mock_file_handler_instance

        mock_stdout.write.return_value = None

        class MockPlayer:
            def __init__(self, name: str, provider: str, model: str, log_dir: str):
                self.name = name
                self.llm_client = MagicMock() 
                self.chat_history = []
                self.log_dir = log_dir
                self.logger = MagicMock()
                self.logger.info = MagicMock()
                self.logger.error = MagicMock()
                self.character = Character(
                    char_id=f"hero_instance_{name}",
                    name=name,
                    backstory="",
                    motive="Defeat evil.",
                    current_room_id="start_room",
                    action_points=20
                )

            def add_message(self, message):
                self.chat_history.append(message)

            async def get_response_and_update_history(self, messages_for_llm: list) -> AIMessage:
                # Return a response that will trigger the validation we want to test
                if "test_say_action" in str(messages_for_llm):
                    return AIMessage(content="> look\n> say \"Hello there!\"")
                elif "test_invalid_action" in str(messages_for_llm):
                    return AIMessage(content="> invalid_action")
                elif "test_continue" in str(messages_for_llm):
                    return AIMessage(content="> continue")
                else:
                    return AIMessage(content="> help")
        
        mock_player_class.side_effect = MockPlayer

        # Create a minimal game config for testing
        dummy_core_config = CoreConfig(
            actions={
                "look": ActionConfig(
                    id="look", 
                    name="look", 
                    cost=10, 
                    description="Look around.", 
                    parameters=[], 
                    requirements=[], 
                    effects=[ActionEffectConfig(type="code_binding", function_module="motive.hooks.core_hooks", function_name="look_at_target", observers=["player"])]
                ),
                "say": ActionConfig(
                    id="say", 
                    name="say", 
                    cost=10, 
                    description="Say something.", 
                    parameters=[ParameterConfig(name="phrase", type="string", description="What to say")], 
                    requirements=[], 
                    effects=[ActionEffectConfig(type="code_binding", function_module="motive.hooks.core_hooks", function_name="handle_say_action", observers=["player", "room_characters"])]
                ),
                "help": ActionConfig(
                    id="help", 
                    name="help", 
                    cost=10, 
                    description="Get help.", 
                    parameters=[], 
                    requirements=[], 
                    effects=[ActionEffectConfig(type="code_binding", function_module="motive.hooks.core_hooks", function_name="generate_help_message", observers=["player"])]
                )
            }
        )

        dummy_theme_config = ThemeConfig(
            id="test_theme",
            name="Test Theme",
            object_types={},
            actions={},
            character_types={
                "hero": CharacterConfig(id="hero", name="Hero", backstory="A brave adventurer.", motive="Defeat evil.")
            }
        )

        dummy_edition_config = EditionConfig(
            id="test_edition",
            name="Test Edition",
            theme_id="test_theme",
            rooms={
                "start_room": RoomConfig(
                    id="start_room",
                    name="Starting Room",
                    description="A simple starting room.",
                    exits={},
                    objects={}
                )
            },
            characters={
                "hero": CharacterConfig(id="hero", name="Hero", backstory="A brave adventurer.", motive="Defeat evil.")
            }
        )

        # Create a proper hierarchical config for testing
        from motive.cli import load_config
        game_config = load_config('configs/game.yaml')
        
        # Override with test-specific settings
        game_config.game_settings.num_rounds = 1
        game_config.game_settings.initial_ap_per_turn = 20
        game_config.players = [
            PlayerConfig(name="TestPlayer", provider="mock", model="mock-model")
        ]
        
        mock_game_config = game_config

        # No need for mock config loading with hierarchical configs
        mock_load_manual_content.return_value = "Mock manual content."

        # Create GameMaster with mocked LLM client
        with patch('motive.llm_factory.create_llm_client') as mock_create_llm:
            mock_llm = MagicMock()
            mock_create_llm.return_value = mock_llm
            
            gm = GameMaster(game_config=mock_game_config, game_id="test_game_id")
            
            # Patch the game_logger directly after GameMaster instantiation
            gm.game_logger = MagicMock()
            gm.game_logger.info = MagicMock()
            gm.game_logger.error = MagicMock()

        # Set up the player
        test_player = gm.players[0]
        test_player.logger = MagicMock()
        test_player.logger.info = MagicMock()
        test_player.logger.error = MagicMock()
        
        # Create a simple room for testing
        gm.rooms["start_room"] = Room(
            room_id="start_room",
            name="Starting Room", 
            description="A simple starting room.",
            exits={},
            objects={}
        )
        
        # Ensure player has a character assigned (simulate game initialization)
        if test_player.character is None:
            # Create a mock character for testing
            from motive.character import Character
            test_character = Character(
                char_id="test_char",
                name="Test Character",
                backstory="A test character for validation tests",
                current_room_id="start_room",
                action_points=30
            )
            test_player.character = test_character
        
        # Add player character to room
        gm.rooms["start_room"].add_player(test_player.character)

        yield gm


@pytest.mark.asyncio
async def test_valid_actions_work_correctly(mock_game_master_validation):
    """Test that valid actions are processed correctly without penalties."""
    gm = mock_game_master_validation
    player = gm.players[0]
    
    # Mock the player's response to include valid actions
    player.get_response_and_update_history = AsyncMock(return_value=AIMessage(content="> look\n> say \"Hello there!\""))
    
    # Execute the player's turn
    await gm._execute_player_turn(player, 1)
    
    # Verify that the player's logger was called with expected messages
    player.logger.info.assert_called()
    
    # Verify that no error logging occurred
    player.logger.error.assert_not_called()
    gm.game_logger.error.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_actions_trigger_penalty_and_logging(mock_game_master_validation):
    """Test that invalid actions trigger proper penalty and detailed logging."""
    gm = mock_game_master_validation
    player = gm.players[0]
    
    # Mock the player's response to include invalid actions
    player.get_response_and_update_history = AsyncMock(return_value=AIMessage(content="> invalid_action"))
    
    # Execute the player's turn
    await gm._execute_player_turn(player, 1)
    
    # Verify that error logging occurred with detailed information
    gm.game_logger.error.assert_called()
    
    # Check that the error logs contain the expected information
    error_calls = [call[0][0] for call in gm.game_logger.error.call_args_list]
    print(f"Error calls: {error_calls}")  # Debug output
    assert any("provided invalid actions" in call for call in error_calls)
    assert any("Invalid actions were:" in call for call in error_calls)


@pytest.mark.asyncio
async def test_no_actions_trigger_penalty(mock_game_master_validation):
    """Test that providing no valid actions triggers a penalty."""
    gm = mock_game_master_validation
    player = gm.players[0]
    
    # Mock the player's response with no actions
    player.get_response_and_update_history = AsyncMock(return_value=AIMessage(content="I don't know what to do."))
    
    # Execute the player's turn
    await gm._execute_player_turn(player, 1)
    
    # Verify that the player's action points were set to 0 (penalty)
    assert player.character.action_points == 0


@pytest.mark.asyncio
async def test_turn_end_confirmation_works(mock_game_master_validation):
    """Test that turn end confirmation process works correctly."""
    gm = mock_game_master_validation
    player = gm.players[0]
    
    # Mock the player to choose continue
    player.get_response_and_update_history = AsyncMock(return_value=AIMessage(content="> continue"))
    
    # Test the turn end confirmation
    result = await gm._handle_turn_end_confirmation(player, player.character)
    
    # Verify that the player chose to continue
    assert result == True
    assert player.character.action_points != -1  # Not marked as quit


@pytest.mark.asyncio
async def test_turn_end_confirmation_quit_works(mock_game_master_validation):
    """Test that turn end confirmation quit option works correctly."""
    gm = mock_game_master_validation
    player = gm.players[0]
    
    # Mock the player to choose quit
    player.get_response_and_update_history = AsyncMock(return_value=AIMessage(content="> quit"))
    
    # Test the turn end confirmation
    result = await gm._handle_turn_end_confirmation(player, player.character)
    
    # Verify that the player chose to quit
    assert result == False
    assert player.character.action_points == -1  # Marked as quit


def test_action_parsing_with_say_action():
    """Test that say action parsing works correctly with quoted parameters."""
    from motive.action_parser import parse_player_response
    
    # Create a minimal actions dict for testing
    actions = {
        "say": ActionConfig(
            id="say",
            name="say", 
            cost=10,
            description="Say something",
            parameters=[ParameterConfig(name="phrase", type="string", description="What to say")],
            requirements=[],
            effects=[]
        )
    }
    
    # Test parsing a say action with quoted parameter
    response = '> say "Hello there!"'
    parsed_actions, invalid_actions = parse_player_response(response, actions)
    
    # Verify the action was parsed correctly
    assert len(parsed_actions) == 1
    assert len(invalid_actions) == 0
    action_config, params = parsed_actions[0]
    assert action_config.name == "say"
    assert params["phrase"] == "Hello there!"


def test_action_parsing_with_multiple_actions():
    """Test that multiple actions in one response are parsed correctly."""
    from motive.action_parser import parse_player_response
    
    # Create a minimal actions dict for testing
    actions = {
        "look": ActionConfig(
            id="look",
            name="look",
            cost=10,
            description="Look around",
            parameters=[],
            requirements=[],
            effects=[]
        ),
        "say": ActionConfig(
            id="say",
            name="say",
            cost=10,
            description="Say something",
            parameters=[ParameterConfig(name="phrase", type="string", description="What to say")],
            requirements=[],
            effects=[]
        )
    }
    
    # Test parsing multiple actions
    response = '> look\n> say "Hello there!"'
    parsed_actions, invalid_actions = parse_player_response(response, actions)
    
    # Verify both actions were parsed correctly
    assert len(parsed_actions) == 2
    assert len(invalid_actions) == 0
    
    # Check first action (look)
    action_config1, params1 = parsed_actions[0]
    assert action_config1.name == "look"
    assert params1 == {}
    
    # Check second action (say)
    action_config2, params2 = parsed_actions[1]
    assert action_config2.name == "say"
    assert params2["phrase"] == "Hello there!"


def test_action_parsing_invalid_action():
    """Test that invalid actions are not parsed."""
    from motive.action_parser import parse_player_response
    
    # Create a minimal actions dict for testing
    actions = {
        "look": ActionConfig(
            id="look",
            name="look",
            cost=10,
            description="Look around",
            parameters=[],
            requirements=[],
            effects=[]
        )
    }
    
    # Test parsing an invalid action
    response = '> invalid_action'
    parsed_actions, invalid_actions = parse_player_response(response, actions)
    
    # Verify no valid actions were parsed but invalid action was captured
    assert len(parsed_actions) == 0
    assert len(invalid_actions) == 1
    assert invalid_actions[0] == "invalid_action"


def test_action_parsing_no_actions():
    """Test that responses with no actions return empty list."""
    from motive.action_parser import parse_player_response
    
    # Create a minimal actions dict for testing
    actions = {
        "look": ActionConfig(
            id="look",
            name="look",
            cost=10,
            description="Look around",
            parameters=[],
            requirements=[],
            effects=[]
        )
    }
    
    # Test parsing a response with no actions
    response = 'I don\'t know what to do.'
    parsed_actions, invalid_actions = parse_player_response(response, actions)
    
    # Verify no actions were parsed
    assert len(parsed_actions) == 0
    assert len(invalid_actions) == 0
