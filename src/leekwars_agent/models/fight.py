"""Pydantic models for LeekWars fight data.

These models document the structure of fight replays from the API.
Used for type-safe extraction and analysis.

Data sources:
- GET /fight/get/{fight_id} → FightResponse
- fight.data contains replay details (leeks, actions, ops)
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# =============================================================================
# Fight Replay Data (fight.data)
# =============================================================================

class ReplayEntity(BaseModel):
    """Entity in fight replay (from fight.data.leeks).

    Note: 'id' here is entity position (0-13), NOT the leek's actual ID.
    Match to actual leek by 'name' field.
    """
    id: int = Field(description="Entity position in fight (0-based index)")
    name: str
    team: int = Field(description="Team number (1 or 2)")
    level: int | None = None
    life: int | None = None
    strength: int | None = None
    agility: int | None = None
    wisdom: int | None = None
    resistance: int | None = None
    magic: int | None = None
    science: int | None = None
    frequency: int | None = None
    tp: int | None = None
    mp: int | None = None

    # Equipment at fight time
    weapons: list[int] | None = Field(default=None, description="Weapon IDs equipped")
    chips: list[int] | None = Field(default=None, description="Chip IDs equipped")


class ReplayMap(BaseModel):
    """Map layout for fight replay."""
    width: int
    height: int
    obstacles: dict[str, int] = Field(default_factory=dict, description="cell_id -> obstacle_type")


class FightReplayData(BaseModel):
    """Inner replay data (fight.data).

    Contains the actual fight simulation results.
    """
    leeks: list[ReplayEntity] = Field(description="All entities in fight, indexed by position")
    map: ReplayMap | dict | None = None
    actions: list[list[Any]] = Field(default_factory=list, description="Action log (encoded)")
    dead: dict[str, bool] = Field(default_factory=dict, description="entity_id -> is_dead")
    ops: dict[str, int] = Field(default_factory=dict, description="entity_id -> total_operations_used")


# =============================================================================
# Leek Summary (fight.leeks1, fight.leeks2)
# =============================================================================

class LeekSummary(BaseModel):
    """Leek info from fight summary (fight.leeks1/leeks2).

    Note: 'id' here is the actual leek ID (e.g., 131321).
    """
    id: int = Field(description="Actual leek ID (persistent)")
    name: str
    level: int
    talent: int | None = None
    farmer: int | None = Field(default=None, description="Farmer ID who owns this leek")

    # Stats at fight time
    life: int | None = None
    strength: int | None = None
    agility: int | None = None
    wisdom: int | None = None
    resistance: int | None = None
    magic: int | None = None
    science: int | None = None
    frequency: int | None = None
    tp: int | None = None
    mp: int | None = None


# =============================================================================
# Full Fight Response
# =============================================================================

class Fight(BaseModel):
    """Fight record from API.

    Combines summary info (leeks1/leeks2) with replay data (data).
    """
    id: int
    date: int | None = Field(default=None, description="Unix timestamp")
    winner: int = Field(description="Winning team (1 or 2), 0 for draw")
    starter: int | None = Field(default=None, description="Team that moved first")

    # Team summaries
    leeks1: list[LeekSummary] = Field(default_factory=list, description="Team 1 leeks")
    leeks2: list[LeekSummary] = Field(default_factory=list, description="Team 2 leeks")

    # Farmer info
    farmer1: int | None = None
    farmer2: int | None = None

    # Replay data
    data: FightReplayData | None = Field(default=None, description="Full replay if fetched")

    # Metadata
    type: int | None = Field(default=None, description="Fight type (solo, team, etc)")
    context: str | None = None
    tournament: int | None = None

    def get_ops_by_leek_name(self) -> dict[str, int]:
        """Map leek name -> total ops used in fight."""
        if not self.data or not self.data.ops:
            return {}

        result = {}
        for i, entity in enumerate(self.data.leeks):
            ops = self.data.ops.get(str(i), 0)
            if ops > 0:
                result[entity.name] = ops
        return result

    def get_leek_ops(self, leek_id: int) -> int:
        """Get ops used by a specific leek (by ID)."""
        # Find leek name from summary
        name = None
        for leek in self.leeks1 + self.leeks2:
            if leek.id == leek_id:
                name = leek.name
                break

        if not name:
            return 0

        return self.get_ops_by_leek_name().get(name, 0)


class FightResponse(BaseModel):
    """Full API response from GET /fight/get/{id}."""
    fight: Fight

    # Additional fields sometimes present
    logs: dict[str, Any] | None = Field(default=None, description="Debug logs if available")


# =============================================================================
# Observation (extracted for analysis)
# =============================================================================

class LeekObservation(BaseModel):
    """Extracted observation of a leek's performance in one fight.

    Denormalized for easy analysis.
    """
    fight_id: int
    leek_id: int
    leek_name: str
    farmer_id: int | None

    # Context
    level: int
    talent: int | None
    team: int
    won: bool

    # Stats at fight time
    life: int
    strength: int
    agility: int
    wisdom: int = 0
    resistance: int = 0
    magic: int = 0
    science: int = 0
    frequency: int = 0
    tp: int = 10
    mp: int = 3

    # Performance
    ops_used: int = Field(default=0, description="Total operations consumed")
    damage_dealt: int = 0
    damage_received: int = 0
    turns_alive: int = 0

    # Equipment used
    weapons_used: list[int] = Field(default_factory=list)
    chips_used: list[int] = Field(default_factory=list)

    observed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def ops_per_turn(self) -> float:
        """Average operations per turn survived."""
        if self.turns_alive <= 0:
            return 0
        return self.ops_used / self.turns_alive

    @property
    def ops_efficiency(self) -> float:
        """Operations per damage dealt (lower = more efficient)."""
        if self.damage_dealt <= 0:
            return float('inf')
        return self.ops_used / self.damage_dealt
