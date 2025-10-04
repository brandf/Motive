from pydantic import BaseModel, Field, conint, field_validator
from typing import List, Dict, Any, Optional, Literal, Union

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
    observers: List[Literal[
        "player",
        "room_players",
        "adjacent_rooms",
        "all_players",
        "game_master",
        # New v2 names (backward compatible)
        "room_characters",
        "adjacent_rooms_characters",
    ]] = Field(..., description="Scopes of observers who should receive this event.")

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
    operator: Optional[str] = None # For numeric comparisons (==, >=, <=, >, <)
    progress_message: Optional[str] = Field(
        default=None,
        description="Optional narrative update delivered when this requirement is first satisfied as part of a motive."
    )

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
    increment_value: Optional[int] = None
    condition: Optional[str] = None # Condition parameter name for conditional effects

    # Fields for generate_event effect
    message: Optional[str] = None
    observers: Optional[List[Literal[
        "player",
        "room_players",
        "adjacent_rooms",
        "all_players",
        "game_master",
        # New v2 names (backward compatible)
        "room_characters",
        "adjacent_rooms_characters",
    ]]] = None

    # Fields for code_binding effect
    function_name: Optional[str] = None

class CostConfig(BaseModel):
    """Configuration for action cost - can be static or dynamic."""
    type: str = Field(..., description="Type of cost calculation ('static' or 'code_binding').")
    value: Optional[int] = Field(None, description="Static cost value (for type='static').")
    function_name: Optional[str] = Field(None, description="Function name for dynamic cost calculation (for type='code_binding').")

class ActionConfig(BaseModel):
    """Configuration for a single action."""
    id: str = Field(..., description="Unique identifier for the action.")
    name: str = Field(..., description="The command name for the action (e.g., 'look', 'pickup').")
    cost: Union[int, CostConfig] = Field(..., description="Action points consumed by this action (int for static, CostConfig for dynamic).")
    description: str
    category: Optional[str] = Field(None, description="Category for grouping actions (e.g., 'movement', 'communication', 'inventory').")
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
    action_aliases: Dict[str, str] = Field(default_factory=dict, description="Action aliases for this object type.")
    interactions: Dict[str, Any] = Field(default_factory=dict, description="Interactions for this object type.")

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
    aliases: List[str] = []  # Alternative names for this exit

class RoomConfig(BaseModel):
    """Configuration for a single room in the game world."""
    id: str = Field(..., description="Unique identifier for the room.")
    name: str
    description: str
    exits: Dict[str, ExitConfig] = {}
    objects: Dict[str, ObjectInstanceConfig] = {}
    tags: List[str] = []
    properties: Dict[str, Any] = {}

class MotiveConditionGroup(BaseModel):
    """A group of conditions with an explicit operator."""
    operator: Literal["AND", "OR"] = Field(..., description="How to combine conditions: AND (all must pass) or OR (any must pass).")
    conditions: List[ActionRequirementConfig] = Field(..., description="List of conditions to evaluate.")


class MotiveStatusPrompt(BaseModel):
    """Configurable narrative status prompt for a motive."""

    condition: Optional[Union[ActionRequirementConfig, MotiveConditionGroup]] = Field(
        default=None,
        description="Optional condition that must be satisfied for this prompt to appear. If omitted, the prompt always applies.",
    )
    message: str = Field(..., description="Narrative status message shown to the player when the condition matches.")

    @field_validator('condition', mode='before')
    @classmethod
    def convert_condition(cls, v):
        """Normalize YAML input into requirement or condition group objects."""
        if not v:
            return None
        if isinstance(v, (ActionRequirementConfig, MotiveConditionGroup)):
            return v
        if isinstance(v, dict):
            if 'type' in v:
                return ActionRequirementConfig(**v)
            if 'operator' in v:
                operator = v['operator']
                raw_conditions = v.get('conditions', [])
                conditions = [ActionRequirementConfig(**cond) for cond in raw_conditions]
                return MotiveConditionGroup(operator=operator, conditions=conditions)
        if isinstance(v, list):
            if len(v) == 1 and isinstance(v[0], dict) and 'type' in v[0]:
                return ActionRequirementConfig(**v[0])
            if len(v) > 1 and isinstance(v[0], dict) and 'operator' in v[0]:
                operator = v[0]['operator']
                conditions = [ActionRequirementConfig(**cond) for cond in v[1:]]
                return MotiveConditionGroup(operator=operator, conditions=conditions)
        raise ValueError("Invalid condition format for MotiveStatusPrompt")


class MotiveConfig(BaseModel):
    """Configuration for a character motive with success/failure conditions."""
    id: str = Field(..., description="Unique identifier for the motive.")
    description: str = Field(..., description="Description shown to the player.")
    success_conditions: Union[ActionRequirementConfig, MotiveConditionGroup] = Field(default=[], description="Single condition or group with explicit operator.")
    failure_conditions: Union[ActionRequirementConfig, MotiveConditionGroup] = Field(default=[], description="Single condition or group with explicit operator.")
    status_prompts: List[MotiveStatusPrompt] = Field(
        default_factory=list,
        description="Ordered list of narrative status prompts evaluated each turn. The first matching condition provides the player's status summary.",
    )
    
    @field_validator('success_conditions', 'failure_conditions', mode='before')
    @classmethod
    def convert_conditions(cls, v):
        """Convert raw YAML data to proper condition objects."""
        if not v:
            return ActionRequirementConfig(type="player_has_tag", tag="dummy")
        
        # If it's already a proper object, return it
        if isinstance(v, (ActionRequirementConfig, MotiveConditionGroup)):
            return v
        
        # If it's a single condition (dict with 'type')
        if isinstance(v, dict) and 'type' in v:
            return ActionRequirementConfig(**v)
        
        # If it's a list of conditions
        if isinstance(v, list):
            if len(v) == 1:
                # Single condition in a list
                return ActionRequirementConfig(**v[0])
            else:
                # Multiple conditions - require explicit operator
                if not isinstance(v[0], dict) or 'operator' not in v[0]:
                    raise ValueError("Multiple conditions require explicit 'operator' field (AND or OR)")
                
                operator = v[0]['operator']
                conditions = []
                for condition_dict in v[1:]:
                    conditions.append(ActionRequirementConfig(**condition_dict))
                
                return MotiveConditionGroup(operator=operator, conditions=conditions)
        
        return ActionRequirementConfig(type="player_has_tag", tag="dummy")

class InitialRoomConfig(BaseModel):
    """Configuration for a character's initial room with reason."""
    room_id: str = Field(..., description="ID of the room where this character can start.")
    chance: int = Field(..., ge=0, le=100, description="Percentage chance (0-100) of starting in this room.")
    reason: str = Field(..., description="Story reason for why the character is in this location.")

class CharacterConfig(BaseModel):
    """Configuration for a character type or specific character."""
    id: str = Field(..., description="Unique identifier for the character.")
    name: str
    backstory: str
    motive: Optional[str] = None  # Legacy single motive field for backward compatibility
    motives: Optional[List[MotiveConfig]] = None  # New multiple motives field
    aliases: List[str] = []  # Alternative names for this character
    initial_rooms: Optional[List[InitialRoomConfig]] = None  # Character-specific starting locations
    short_name: Optional[str] = None  # Short display name for observations

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
    manual: str = Field("MANUAL.md", description="Path to the game manual markdown file.")
    initial_ap_per_turn: int = Field(20, description="Initial action points per player per turn. Defaults to 20 for testing.")
    hints: Optional[List[Dict[str, Any]]] = Field(None, description="Optional hints to guide LLM players toward specific actions for validation.")
    
    # Legacy fields for backward compatibility (deprecated)
    core_config_path: Optional[str] = Field(None, description="DEPRECATED: Use includes instead.")
    theme_config_path: Optional[str] = Field(None, description="DEPRECATED: Use includes instead.")
    edition_config_path: Optional[str] = Field(None, description="DEPRECATED: Use includes instead.")

class GameConfig(BaseModel):
    """Overall game configuration."""
    game_settings: GameSettings
    players: List[PlayerConfig] = Field(..., min_length=1, description="List of AI players participating in the game.")
    core_config: Optional[CoreConfig] = None # New: CoreConfig
    theme_config: Optional[ThemeConfig] = None
    edition_config: Optional[EditionConfig] = None
    # Support for standalone configs that define theme/edition directly
    theme_id: Optional[str] = None
    theme_name: Optional[str] = None
    edition_id: Optional[str] = None
    edition_name: Optional[str] = None
    
    # Support for hierarchical configs that merge everything into one structure
    actions: Optional[Dict[str, Any]] = None
    object_types: Optional[Dict[str, Any]] = None
    character_types: Optional[Dict[str, Any]] = None
    rooms: Optional[Dict[str, Any]] = None
    characters: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    name: Optional[str] = None
