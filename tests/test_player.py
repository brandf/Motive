import logging
import os # Import os for mocking os.makedirs
from unittest.mock import MagicMock, AsyncMock
from motive.player import Player
from langchain_core.messages import AIMessage, HumanMessage

# Helper function to mock the create_llm_client
def _mock_create_llm_client(monkeypatch, mock_llm_return_value):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_llm_return_value)
    mock_create_llm = MagicMock(return_value=mock_llm)
    monkeypatch.setattr("motive.player.create_llm_client", mock_create_llm)
    return mock_llm

def test_player_initialization(monkeypatch):
    """
    Tests that a Player instance is correctly initialized.
    """
    # Mock os.makedirs to prevent directory creation during tests
    monkeypatch.setattr(os, "makedirs", MagicMock())
    # Mock logging.FileHandler to prevent actual file writing
    monkeypatch.setattr(logging, "FileHandler", MagicMock())
    
    _mock_create_llm_client(monkeypatch, AIMessage(content="irrelevant"))

    test_player = Player(name="TestPlayer", provider="mock", model="mock-model", log_dir="mock_log_dir")

    assert test_player.name == "TestPlayer"
    assert test_player.chat_history == []
    assert isinstance(test_player.llm_client, MagicMock)
    assert isinstance(test_player.logger, logging.Logger)
    assert test_player.logger.name == "TestPlayer"


async def test_player_processes_message_and_updates_history(monkeypatch):
    """
    Tests that the player's LLM client is invoked with the correct chat history
    and that the chat history is updated with both the user message and the AI's response.
    """
    # Mock os.makedirs to prevent directory creation during tests
    monkeypatch.setattr(os, "makedirs", MagicMock())
    # Mock logging.FileHandler to prevent actual file writing
    monkeypatch.setattr(logging, "FileHandler", MagicMock())
    
    ai_response_content = "I check for traps."
    mock_llm = _mock_create_llm_client(monkeypatch, AIMessage(content=ai_response_content))

    test_player = Player(name="TestPlayer", provider="mock", model="mock-model", log_dir="mock_log_dir")
    user_message = "What do you do next?"
    test_player.add_message(HumanMessage(content=user_message))

    response = await test_player.get_response_and_update_history(test_player.chat_history)

    mock_llm.ainvoke.assert_called_once_with(
        [HumanMessage(content=user_message)]
    )
    assert response.content == ai_response_content
    assert len(test_player.chat_history) == 2
    assert test_player.chat_history[0].content == user_message
    assert test_player.chat_history[1].content == ai_response_content


def test_player_logs_messages(monkeypatch):
    """
    Tests that the player correctly logs messages to its dedicated log file.
    """
    # Mock os.makedirs to prevent directory creation during tests
    monkeypatch.setattr(os, "makedirs", MagicMock())

    # Mock the logger's handler to capture log records
    mock_file_handler = MagicMock()
    mock_logger = MagicMock(spec=logging.Logger)
    mock_logger.setLevel.return_value = None
    mock_logger.propagate = False
    mock_logger.handlers = [] # Simulate no handlers initially

    # Ensure addHandler is called
    mock_logger.addHandler.return_value = None

    # Save original getLogger to avoid recursion
    original_get_logger = logging.getLogger

    # Replace logging.getLogger for the player's logger setup
    def mock_get_logger(name=None):
        if name == "TestPlayer":
            return mock_logger
        # For other names or no name (root logger), return the actual logger
        return original_get_logger(name) if name else original_get_logger()

    monkeypatch.setattr(logging, "getLogger", mock_get_logger)

    # Mock the FileHandler to prevent actual file writing
    monkeypatch.setattr(logging, "FileHandler", MagicMock(return_value=mock_file_handler))
    monkeypatch.setattr(logging.FileHandler, "setFormatter", MagicMock())


    _mock_create_llm_client(monkeypatch, AIMessage(content="irrelevant"))
    test_player = Player(name="TestPlayer", provider="mock", model="mock-model", log_dir="mock_log_dir")

    test_player.logger.info("Test message 1")
    test_player.logger.info("Test message 2")

    mock_logger.info.assert_any_call("Test message 1")
    mock_logger.info.assert_any_call("Test message 2")
    assert mock_logger.info.call_count == 2
