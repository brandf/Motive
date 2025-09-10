from typing import List, Dict, Any, Optional
from motive.game_objects import GameObject
from motive.character import Character

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
        self.players: Dict[str, Character] = {} # New: Stores Character instances in the room

    def add_object(self, obj: GameObject):
        self.objects[obj.id] = obj
        obj.current_location_id = self.id

    def remove_object(self, obj_id: str) -> Optional[GameObject]:
        return self.objects.pop(obj_id, None)

    def get_object(self, obj_id: str) -> Optional[GameObject]:
        """Gets a GameObject in this room by its ID or name (case-insensitive)."""
        # Try to find by ID first
        obj = self.objects.get(obj_id)
        if obj:
            return obj

        # If not found by ID, try to find by name (case-insensitive)
        for game_obj in self.objects.values():
            if game_obj.name.lower() == obj_id.lower(): # obj_id is now used for name as well
                return game_obj
        return None

    def add_player(self, player_char: Character):
        """Adds a Character to this room."""
        self.players[player_char.id] = player_char
        player_char.current_room_id = self.id

    def remove_player(self, player_char_id: str) -> Optional[Character]:
        """Removes a Character from this room."""
        return self.players.pop(player_char_id, None)

    def get_player(self, player_char_id: str) -> Optional[Character]:
        """Gets a Character in this room by ID."""
        return self.players.get(player_char_id)

    def get_all_characters_in_room(self) -> List[Character]:
        """Returns a list of all Character instances currently in this room."""
        return list(self.players.values())

    def add_tag(self, tag: str):
        self.tags.add(tag)

    def remove_tag(self, tag: str):
        self.tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def get_formatted_description(self) -> str:
        """Returns a formatted description of the room with objects and exits in outline format."""
        room_description_parts = [self.description]
        
        if self.objects:
            object_names = [obj.name for obj in self.objects.values()]
            room_description_parts.append(f"\n\n**Objects in the room:**")
            for obj_name in object_names:
                room_description_parts.append(f"\n  • {obj_name}")
        
        if self.exits:
            exit_names = [exit_data['name'] for exit_data in self.exits.values() if not exit_data.get('is_hidden', False)]
            if exit_names:
                room_description_parts.append(f"\n\n**Exits:**")
                for exit_name in exit_names:
                    room_description_parts.append(f"\n  • {exit_name}")
        
        return "".join(room_description_parts)

    def __repr__(self):
        return f"Room(id='{self.id}', name='{self.name}', objects={list(self.objects.keys())})"
