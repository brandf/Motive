from pydantic import BaseModel, Field, conint
from typing import List, Dict, Any, Optional, Literal

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

class Event(BaseModel):
    """Represents a discrete event occurring in the game world."""
    message: str = Field(..., description="Human-readable description of the event.")
    event_type: str = Field(..., description="Categorization of the event (e.g., 'movement', 'interaction', 'status_change').")
    source_room_id: str = Field(..., description="The ID of the room where the event occurred.")
    timestamp: str = Field(..., description="ISO formatted timestamp when the event occurred.")
    related_object_id: Optional[str] = None
    related_player_id: Optional[str] = None
    observers: List[Literal["player", "room_players", "adjacent_rooms", "all_players", "game_master"]] = Field(..., description="Scopes of observers who should receive this event.")

class ActionRequirementConfig(BaseModel):
    """Base model for action requirements."""
    type: str = Field(..., description="Type of requirement (e.g., 'player_has_tag', 'object_in_room').")
    # Generic fields that can be used by various requirement types
    tag: Optional[str] = None
    object_name_param: Optional[str] = None # Refers to a parameter of the action
    property: Optional[str] = None # For object_property_equals
    value: Optional[Any] = None # For object_property_equals
    target_player_param: Optional[str] = None # For player_in_room, player_has_tag
    direction_param: Optional[str] = None # For exit_exists

class ActionEffectConfig(BaseModel):
    """Base model for action effects."""
    type: str = Field(..., description="Type of effect (e.g., 'add_tag', 'remove_tag', 'set_property', 'generate_event', 'code_binding').")
    
    # Fields for declarative effects (add_tag, remove_tag, set_property)
    target_type: Optional[Literal["player", "room", "object"]] = None
    target_id_param: Optional[str] = None # Name of the action parameter that holds the target ID
    target_id: Optional[str] = None # Direct ID of the target (if not from a parameter)
    tag: Optional[str] = None
    property: Optional[str] = None
    value: Any = None

    # Fields for generate_event effect
    message: Optional[str] = None
    observers: Optional[List[Literal["player", "room_players", "adjacent_rooms", "all_players", "game_master"]]] = None

    # Fields for code_binding effect
    function_module: Optional[str] = None
    function_name: Optional[str] = None

class ActionConfig(BaseModel):
    """Configuration for a single action."""
    id: str = Field(..., description="Unique identifier for the action.")
    name: str = Field(..., description="The command name for the action (e.g., 'look', 'pickup').")
    cost: int = Field(..., description="Action points consumed by this action.")
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

class CoreConfig(BaseModel):
    """Configuration for core game elements (e.g., universal actions)."""
    actions: Dict[str, ActionConfig] = {}

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
    core_config_path: str = Field(..., description="Path to the core YAML configuration file.")
    theme_config_path: str = Field(..., description="Path to the theme YAML configuration file.")
    edition_config_path: str = Field(..., description="Path to the edition YAML configuration file.")
    manual: str = Field("MOTIVE_MANUAL.md", description="Path to the game manual markdown file.")
    initial_ap_per_turn: int = Field(20, description="Initial action points per player per turn. Defaults to 20 for testing.")

class GameConfig(BaseModel):
    """Overall game configuration."""
    game_settings: GameSettings
    players: List[PlayerConfig] = Field(..., min_length=1, description="List of AI players participating in the game.")
    core_config: Optional[CoreConfig] = None # New: CoreConfig
    theme_config: Optional[ThemeConfig] = None
    edition_config: Optional[EditionConfig] = None

