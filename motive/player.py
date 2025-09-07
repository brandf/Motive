import logging
from motive.llm_factory import create_llm_client
from langchain_core.messages import AIMessage, HumanMessage


class Player:
    """
    Represents a single AI player, managing their LLM client,
    chat history, and logging.
    """

    def __init__(self, name: str, provider: str, model: str):
        self.name = name
        self.llm_client = create_llm_client(provider, model)
        self.chat_history = []
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Sets up a dedicated logger for this player's chat history."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        # Prevent logs from propagating to the root logger
        logger.propagate = False

        # Create a file handler
        handler = logging.FileHandler(f"logs/{self.name}_chat.log", mode="w")
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)

        # Add the handler to the logger if it doesn't have one already
        if not logger.handlers:
            logger.addHandler(handler)

        return logger

    def add_message(self, message):
        """Adds a message to the player's chat history."""
        self.chat_history.append(message)

    async def get_response_and_update_history(self, messages_for_llm: list) -> AIMessage:
        """
        Invokes the LLM client with the given messages, appends the AI's response
        to the player's chat history, and returns the response.
        """
        response = await self.llm_client.ainvoke(messages_for_llm.copy())
        ai_response = AIMessage(content=response.content)
        self.add_message(ai_response)
        return ai_response

