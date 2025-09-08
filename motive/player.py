from typing import List, Dict, Any, Optional
import logging
import os
from motive.llm_factory import create_llm_client
from langchain_core.messages import AIMessage, HumanMessage
from motive.game_objects import GameObject # Import GameObject


class PlayerCharacter:
    """Represents the in-game state of a player's character."""
    def __init__(
        self,
        char_id: str,
        name: str,
        backstory: str,
        motive: str,
        current_room_id: str,
        inventory: Optional[Dict[str, GameObject]] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        action_points: int = 3 # Default action points
    ):
        self.id = char_id
        self.name = name
        self.backstory = backstory
        self.motive = motive
        self.current_room_id = current_room_id
        self.inventory = inventory if inventory else {}
        self.tags = set(tags) if tags else set()
        self.properties = properties if properties else {}
        self.action_points = action_points

    def add_item_to_inventory(self, item: GameObject):
        self.inventory[item.id] = item
        item.current_location_id = self.id

    def remove_item_from_inventory(self, item_id: str) -> Optional[GameObject]:
        return self.inventory.pop(item_id, None)

    def has_item_in_inventory(self, item_id: str) -> bool:
        return item_id in self.inventory

    def get_item_in_inventory(self, item_id: str) -> Optional[GameObject]:
        return self.inventory.get(item_id)

    def add_tag(self, tag: str):
        self.tags.add(tag)

    def remove_tag(self, tag: str):
        self.tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def set_property(self, key: str, value: Any):
        self.properties[key] = value

    def get_property(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)

    def __repr__(self):
        return f"PlayerCharacter(id='{self.id}', name='{self.name}', room='{self.current_room_id}', ap={self.action_points})"


class Player:
    """
    Represents a single AI player, managing their LLM client,
    chat history, and logging.
    """

    def __init__(self, name: str, provider: str, model: str, log_dir: str):
        self.name = name
        self.llm_client = create_llm_client(provider, model)
        self.chat_history = []
        self.log_dir = log_dir
        self.logger = self._setup_logger()
        self.character: Optional[PlayerCharacter] = None # Link to PlayerCharacter instance

    def _setup_logger(self):
        """Sets up a dedicated logger for this player's chat history."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        # Prevent logs from propagating to the root logger
        logger.propagate = False

        # Create a file handler
        player_log_file = os.path.join(self.log_dir, f"{self.name}_chat.log")
        handler = logging.FileHandler(player_log_file, mode="w")
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

