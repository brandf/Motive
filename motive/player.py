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
        # Try to remove by ID first
        if item_id in self.inventory:
            return self.inventory.pop(item_id)
        
        # If not found by ID, try to find by name (case-insensitive) and remove
        for game_obj_id, game_obj in list(self.inventory.items()): # Use list() to allow modification during iteration
            if game_obj.name.lower() == item_id.lower():
                return self.inventory.pop(game_obj_id)
        return None

    def has_item_in_inventory(self, item_name_or_id: str) -> bool:
        """Checks if an item is in the inventory by its ID or name (case-insensitive)."""
        return self.get_item_in_inventory(item_name_or_id) is not None

    def get_item_in_inventory(self, item_name_or_id: str) -> Optional[GameObject]:
        """Gets a GameObject from inventory by its ID or name (case-insensitive)."""
        # Try to find by ID first
        item = self.inventory.get(item_name_or_id)
        if item:
            return item
        
        # If not found by ID, try to find by name (case-insensitive)
        for game_obj in self.inventory.values():
            if game_obj.name.lower() == item_name_or_id.lower():
                return game_obj
        return None

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
        handler = logging.FileHandler(player_log_file, mode="w", encoding="utf-8")
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

