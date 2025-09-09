import pytest
from unittest.mock import MagicMock
from motive.action_parser import parse_player_response, _parse_single_action_line
from motive.config import ActionConfig, ParameterConfig

@pytest.fixture
def sample_actions():
    """Provides a dictionary of sample ActionConfig objects for testing."""
    return {
        "look": ActionConfig(
            id="look", name="look", cost=1, description="Look around.", 
            parameters=[], requirements=[], effects=[]
        ),
        "say": ActionConfig(
            id="say", name="say", cost=1, description="Say something.", 
            parameters=[ParameterConfig(name="phrase", type="string", description="The phrase to say.")], 
            requirements=[], effects=[]
        ),
        "pickup": ActionConfig(
            id="pickup", name="pickup", cost=1, description="Pick up an object.", 
            parameters=[ParameterConfig(name="object_name", type="string", description="The object to pick up.")], 
            requirements=[], effects=[]
        ),
        "use": ActionConfig(
            id="use", name="use", cost=1, description="Use an item.", 
            parameters=[ParameterConfig(name="item_name", type="string", description="The item to use."), 
                        ParameterConfig(name="target", type="string", description="The target of the item.")], 
            requirements=[], effects=[]
        ),
        "light torch": ActionConfig(
            id="light torch", name="light torch", cost=1, description="Light a torch.",
            parameters=[ParameterConfig(name="object_name", type="string", description="The torch to light.")],
            requirements=[], effects=[]
        )
    }

# --- Test _parse_single_action_line ---

def test_parse_single_action_line_valid_no_params(sample_actions):
    action_config, params = _parse_single_action_line("look", sample_actions)
    assert action_config.id == "look"
    assert params == {}

def test_parse_single_action_line_valid_single_param(sample_actions):
    action_config, params = _parse_single_action_line("pickup sword", sample_actions)
    assert action_config.id == "pickup"
    assert params == {"object_name": "sword"}

def test_parse_single_action_line_valid_quoted_param_single_quotes(sample_actions):
    action_config, params = _parse_single_action_line("say 'Hello there GM!'", sample_actions)
    assert action_config.id == "say"
    assert params == {"phrase": "Hello there GM!"}

def test_parse_single_action_line_valid_quoted_param_double_quotes(sample_actions):
    action_config, params = _parse_single_action_line('say "What a lovely day"' , sample_actions)
    assert action_config.id == "say"
    assert params == {"phrase": "What a lovely day"}

def test_parse_single_action_line_invalid_action_name(sample_actions):
    result = _parse_single_action_line("unknown_action", sample_actions)
    assert result is None

def test_parse_single_action_line_multiple_params_unsupported_for_now(sample_actions):
    action_config, params = _parse_single_action_line("use potion on goblin", sample_actions)
    assert action_config.id == "use"
    # With the improved parser, this should now correctly parse both parameters
    assert params == {"item_name": "potion", "target": "on goblin"}

def test_parse_single_action_line_empty_string(sample_actions):
    result = _parse_single_action_line("", sample_actions)
    assert result is None

# --- Test parse_player_response ---

def test_parse_player_response_no_actions():
    response = "Hello GM, I have no actions."
    parsed_actions, invalid_actions = parse_player_response(response, {})
    assert parsed_actions == []
    assert invalid_actions == []

def test_parse_player_response_single_action(sample_actions):
    response = "I will look around.\n> look\nThen I'll wait."
    parsed_actions, invalid_actions = parse_player_response(response, sample_actions)
    assert len(parsed_actions) == 1
    assert parsed_actions[0][0].id == "look"
    assert parsed_actions[0][1] == {}

def test_parse_player_response_multiple_actions(sample_actions):
    response = "First, I'll pick up the sword.\n> pickup sword\nThen I'll say something.\n> say 'Greetings!'\nFinally, I will wait."
    parsed_actions, invalid_actions = parse_player_response(response, sample_actions)
    assert len(parsed_actions) == 2
    assert parsed_actions[0][0].id == "pickup"
    assert parsed_actions[0][1] == {"object_name": "sword"}
    assert parsed_actions[1][0].id == "say"
    assert parsed_actions[1][1] == {"phrase": "Greetings!"}

def test_parse_player_response_action_with_leading_whitespace(sample_actions):
    response = "  > look"
    parsed_actions, invalid_actions = parse_player_response(response, sample_actions)
    assert len(parsed_actions) == 1
    assert parsed_actions[0][0].id == "look"

def test_parse_player_response_mixed_content_and_actions(sample_actions):
    response = (
        "GM, I need to do a few things.\n"
        "This is important context.\n"
        "> pickup torch\n"
        "And then I'll light it.\n"
        "> light torch 'my torch'\n"
        "What do you think?"
    )

    # The 'light torch' action is already part of sample_actions fixture
    parsed_actions, invalid_actions = parse_player_response(response, sample_actions)
    assert len(parsed_actions) == 2
    assert parsed_actions[0][0].id == "pickup"
    assert parsed_actions[0][1] == {"object_name": "torch"}
    assert parsed_actions[1][0].id == "light torch"
    assert parsed_actions[1][1] == {"object_name": "my torch"}

def test_parse_player_response_invalid_action_included(sample_actions):
    response = (
        "I will try something."
        "> walk north\n" # This action is not in sample_actions
        "> look"
    )
    parsed_actions, invalid_actions = parse_player_response(response, sample_actions)
    assert len(parsed_actions) == 1 # Only 'look' should be parsed successfully
    assert parsed_actions[0][0].id == "look"
