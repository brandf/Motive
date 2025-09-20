from typing import List, Dict, Any, Optional

class GameObject:
    """Represents a live instance of an object in the game world."""
    def __init__(
        self,
        obj_id: str,
        name: str,
        description: str,
        current_location_id: str, # Can be a room_id or player_character_id
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        action_aliases: Optional[Dict[str, str]] = None,
        interactions: Optional[Dict[str, Any]] = None
    ):
        self.id = obj_id
        self.name = name
        self.description = description
        self.current_location_id = current_location_id
        self.tags = set(tags) if tags else set()
        self.properties = properties if properties else {}
        self.action_aliases = action_aliases if action_aliases else {}
        self.interactions = interactions if interactions else {}

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
        return f"GameObject(id='{self.id}', name='{self.name}', location='{self.current_location_id}')"
