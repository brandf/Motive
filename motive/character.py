from typing import List, Dict, Any, Optional
from motive.game_object import GameObject


class Character:
    """Represents the in-game state of a character."""
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
        action_points: int = 3, # Default action points
        aliases: Optional[List[str]] = None
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
        self.aliases = aliases if aliases else []

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

    def get_introduction_message(self) -> str:
        """Generate a character introduction message for the player."""
        return f"**Character:**\nYou are {self.name}, {self.backstory}.\n\n**Motive:**\n{self.motive}"

    def __repr__(self):
        return f"Character(id='{self.id}', name='{self.name}', room='{self.current_room_id}', ap={self.action_points})"
