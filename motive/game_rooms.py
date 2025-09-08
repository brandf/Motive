from typing import List, Dict, Any, Optional
from motive.game_objects import GameObject

class Room:
    """Represents a live instance of a room in the game environment."""
    def __init__(
        self,
        room_id: str,
        name: str,
        description: str,
        exits: Optional[Dict[str, Dict[str, Any]]] = None, # Simplified for now, will use ExitConfig later
        objects: Optional[Dict[str, GameObject]] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None
    ):
        self.id = room_id
        self.name = name
        self.description = description
        self.exits = exits if exits else {}
        self.objects = objects if objects else {}
        self.tags = set(tags) if tags else set()
        self.properties = properties if properties else {}

    def add_object(self, obj: GameObject):
        self.objects[obj.id] = obj
        obj.current_location_id = self.id

    def remove_object(self, obj_id: str) -> Optional[GameObject]:
        return self.objects.pop(obj_id, None)

    def get_object(self, obj_id: str) -> Optional[GameObject]:
        return self.objects.get(obj_id)

    def add_tag(self, tag: str):
        self.tags.add(tag)

    def remove_tag(self, tag: str):
        self.tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def __repr__(self):
        return f"Room(id='{self.id}', name='{self.name}', objects={list(self.objects.keys())})"
