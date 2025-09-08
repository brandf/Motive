from pydantic import BaseModel, Field, conint
from typing import List, Dict, Any, Optional

class PlayerConfig(BaseModel):
    """Configuration for a single AI player."""
    name: str
    provider: str
    model: str

class ParameterConfig(BaseModel):
    """Configuration for an action parameter."""
    name: str
    type: str = Field(..., description="Data type of the parameter (e.g., 'string', 'integer').")
    description: str

class ActionRequirementConfig(BaseModel):
    """Base model for action requirements."""
    type: str = Field(..., description="Type of requirement (e.g., 'player_has_tag', 'object_in_room').")
    # Generic fields that can be used by various requirement types
    tag: Optional[str] = None
    object_name_param: Optional[str] = None # Refers to a parameter of the action
    property: Optional[str] = None # For object_property_equals
    value: Optional[Any] = None # For object_property_equals
    target_player_param: Optional[str] = None # For player_in_room, player_has_tag

class ActionEffectConfig(BaseModel):
    """Base model for action effects."""
    type: str = Field(..., description="Type of effect (e.g., 'add_tag', 'move_object', 'generate_event').")
    # Generic fields that can be used by various effect types
    target: Optional[str] = None # e.g., 'player', 'room', 'object'
    tag: Optional[str] = None # For add_tag, remove_tag
    object_name_param: Optional[str] = None # For move_object, set_object_property
    destination_type: Optional[str] = None # For move_object (e.g., 'player_inventory', 'room')
    destination_id: Optional[str] = None # For move_object (e.g., a specific room ID)
    property: Optional[str] = None # For set_object_property
    value: Optional[Any] = None # For set_object_property
    message: Optional[str] = None # For generate_event
    observers: Optional[List[str]] = None # For generate_event (e.g., ['room_players', 'adjacent_rooms'])
    function_module: Optional[str] = None # For call_custom_logic
    function_name: Optional[str] = None # For call_custom_logic
    args: Optional[Dict[str, Any]] = None # For call_custom_logic

class ActionConfig(BaseModel):
    """Configuration for a single action."""
    id: str = Field(..., description="Unique identifier for the action.")
    name: str = Field(..., description="The command name for the action (e.g., 'look', 'pickup').")
    cost: conint(gt=0) = Field(..., description="Action points consumed by this action.")
    description: str
    parameters: List[ParameterConfig] = []
    requirements: List[ActionRequirementConfig] = []
    effects: List[ActionEffectConfig] = []

class ObjectTypeConfig(BaseModel):
    """Configuration for a type of game object (e.g., 'torch', 'key')."""
    id: str = Field(..., description="Unique identifier for the object type.")
    name: str
    description: str
    tags: List[str] = []
    properties: Dict[str, Any] = {}

class ObjectInstanceConfig(BaseModel):
    """Configuration for a specific instance of a game object."""
    id: str = Field(..., description="Unique identifier for this specific object instance.")
    name: str # Overrides object_type's name if present
    object_type_id: str = Field(..., description="The ID of the object type this instance is based on.")
    description: Optional[str] = None # Overrides object_type's description
    current_room_id: Optional[str] = None # Initial location of the object
    tags: List[str] = [] # Additional tags for this instance
    properties: Dict[str, Any] = {} # Overrides/adds properties for this instance

class ExitConfig(BaseModel):
    """Configuration for an exit from a room."""
    id: str = Field(..., description="Unique identifier for the exit.")
    name: str
    destination_room_id: str
    is_hidden: bool = False
    is_locked: bool = False

class RoomConfig(BaseModel):
    """Configuration for a single room in the game world."""
    id: str = Field(..., description="Unique identifier for the room.")
    name: str
    description: str
    exits: Dict[str, ExitConfig] = {}
    objects: Dict[str, ObjectInstanceConfig] = {}
    tags: List[str] = []
    properties: Dict[str, Any] = {}

class CharacterConfig(BaseModel):
    """Configuration for a character type or specific character."""
    id: str = Field(..., description="Unique identifier for the character.")
    name: str
    backstory: str
    motive: str # Could be a list of motives later

class ThemeConfig(BaseModel):
    """Configuration for a game theme (e.g., 'Fantasy')."""
    id: str = Field(..., description="Unique identifier for the theme.")
    name: str
    object_types: Dict[str, ObjectTypeConfig] = {}
    actions: Dict[str, ActionConfig] = {}
    character_types: Dict[str, CharacterConfig] = {}

class EditionConfig(BaseModel):
    """Configuration for a specific game edition (e.g., 'HearthAndShadow')."""
    id: str = Field(..., description="Unique identifier for the edition.")
    name: str
    theme_id: str = Field(..., description="The ID of the theme this edition is based on.")
    rooms: Dict[str, RoomConfig] = {}
    objects: Dict[str, ObjectInstanceConfig] = {} # Additional objects or overrides
    characters: Dict[str, CharacterConfig] = {} # Specific characters or overrides

class GameSettings(BaseModel):
    """General game settings."""
    num_rounds: int = Field(..., gt=0, description="Number of rounds the game will run.")
    theme_config_path: str = Field(..., description="Path to the theme YAML configuration file.")
    edition_config_path: str = Field(..., description="Path to the edition YAML configuration file.")
    manual: str = Field("MOTIVE_MANUAL.md", description="Path to the game manual markdown file.")

class GameConfig(BaseModel):
    """Overall game configuration."""
    game_settings: GameSettings
    players: List[PlayerConfig] = Field(..., min_length=1, description="List of AI players participating in the game.")
    theme_config: Optional[ThemeConfig] = None
    edition_config: Optional[EditionConfig] = None

