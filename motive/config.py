from pydantic import BaseModel, Field
from typing import List

class PlayerConfig(BaseModel):
    """Configuration for a single AI player."""
    name: str
    provider: str
    model: str

class GameSettings(BaseModel):
    """General game settings."""
    num_rounds: int = Field(..., gt=0, description="Number of rounds the game will run.")

class GameConfig(BaseModel):
    """Overall game configuration."""
    game_settings: GameSettings
    players: List[PlayerConfig] = Field(..., min_length=1, description="List of AI players participating in the game.")

