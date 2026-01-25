"""Alpha Strike metrics and constants.

Derived from Kaggle notebooks analyzing Top-10 LeekWars builds.
See docs/project_alpha_strike_integration.md for full research notes.
"""

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# CHIP TAXONOMIES (IDs from leek-wars-generator)
# =============================================================================

# Opening buff gatekeeper: 5/5 = elite opener
OPENING_BUFF_CHIPS = {
    # Chip name -> ID (from tools/leek-wars/src/model/chips.ts)
    "knowledge": 57,      # CHIP_KNOWLEDGE - TP buff
    "adrenaline": 55,     # CHIP_ADRENALINE - Extra TP on damage
    "elevation": 45,      # CHIP_ELEVATION - +MP
    "armoring": 48,       # CHIP_ARMORING - Armor buff
    "steroid": 53,        # CHIP_STEROID - STR buff
    # Also track our available buffs for comparison
    "protein": 8,         # CHIP_PROTEIN - STR buff (we have this)
    "motivation": 5,      # CHIP_MOTIVATION - MP buff (we have this)
}

# High-win chips (binary gatekeeper for elite play)
HIGH_WIN_CHIPS = {
    "brainwashing": 121,   # Control
    "punishment": 110,     # Damage return
    "ball_and_chain": 105, # Root/slow
    "soporific": 82,       # Sleep/disable
    "fracture": 107,       # Armor break
}

# Top 20 action quality chips/weapons (curated from elite play)
TOP_20_ACTIONS = {
    "adrenaline": 55,
    "knowledge": 57,
    "armoring": 48,
    "wall": 73,           # CHIP_WALL - summon
    "lightninger": 193,   # WEAPON_LIGHTNINGER
    "steroid": 53,
    "jump": 88,           # CHIP_JUMP - teleport
    "protein": 8,
    "serum": 79,          # Heal
    "armor": 21,          # Basic armor
    "vaccine": 66,        # Poison cure
    "remission": 71,      # Heal over time
    "mutation": 115,      # Transform
    "thorn": 109,         # Damage return
    "lightning": 32,      # Damage chip
    "neutrino": 182,      # WEAPON_NEUTRINO
    "shield": 47,         # Defense
}

# Elite weapons
ELITE_WEAPONS = {
    "gazor": 199,         # WEAPON_GAZOR
    "lightninger": 193,   # WEAPON_LIGHTNINGER
    "b_laser": 197,       # WEAPON_B_LASER
    "flame_thrower": 51,  # WEAPON_FLAME_THROWER
}

# Volatility suppression chips (control the RNG)
VOLATILITY_CHIPS = {
    "soporific": 82,
    "tranquilizer": 83,
}

# Poison chips for attrition
POISON_CHIPS = {
    "arsenic": 37,
    "plague": 94,
    "covid": 172,  # If exists
    "toxin": 36,
    "venom": 35,
}


# =============================================================================
# ALPHA STRIKE METRICS
# =============================================================================

@dataclass
class TPMetrics:
    """TP efficiency tracking per entity."""
    tp_available: int = 0
    tp_spent: int = 0
    tp_wasted: int = 0  # TP left at end of turn

    @property
    def efficiency(self) -> float:
        """TP efficiency ratio (target >= 0.9)."""
        if self.tp_available == 0:
            return 0.0
        return self.tp_spent / self.tp_available


@dataclass
class OpeningBuffs:
    """Opening buff completion tracking."""
    buffs_used: list[int] = field(default_factory=list)
    gatekeeper_count: int = 0  # Out of 5
    total_buffs: int = 0

    @property
    def gatekeeper_complete(self) -> bool:
        """True if 5/5 gatekeeper buffs used."""
        return self.gatekeeper_count >= 5


@dataclass
class AlphaStrikeMetrics:
    """Full Alpha Strike analysis for an entity."""
    entity_id: int

    # TP Efficiency
    tp_early: TPMetrics = field(default_factory=TPMetrics)   # Turns 0-2
    tp_mid: TPMetrics = field(default_factory=TPMetrics)     # Turns 3-10
    tp_late: TPMetrics = field(default_factory=TPMetrics)    # Turns 11+

    # Opening buffs
    opening_buffs: OpeningBuffs = field(default_factory=OpeningBuffs)

    # High-win chip usage
    high_win_chips_used: list[int] = field(default_factory=list)
    top_20_actions_count: int = 0

    # Build metrics (if stats available)
    stat_cv: float | None = None
    mobility_ratio: float | None = None

    # PONR estimation
    hp_advantage_turn_3: float = 0.0  # HP% difference at turn 3

    @property
    def overall_tp_efficiency(self) -> float:
        """Overall TP efficiency across all phases."""
        total_available = (
            self.tp_early.tp_available +
            self.tp_mid.tp_available +
            self.tp_late.tp_available
        )
        total_spent = (
            self.tp_early.tp_spent +
            self.tp_mid.tp_spent +
            self.tp_late.tp_spent
        )
        if total_available == 0:
            return 0.0
        return total_spent / total_available


@dataclass
class AlphaStrikeFightSummary:
    """Alpha Strike comparison between two fighters."""
    fight_id: int
    winner: int
    duration: int

    team1_metrics: AlphaStrikeMetrics | None = None
    team2_metrics: AlphaStrikeMetrics | None = None

    # Deltas (team1 - team2)
    opening_buff_delta: int = 0
    tp_efficiency_delta: float = 0.0
    high_win_chip_delta: int = 0

    # PONR
    ponr_turn: int | None = None  # Turn when fight was 80% decided

    def summary_dict(self) -> dict[str, Any]:
        """Return dict for DB storage or JSON serialization."""
        return {
            "fight_id": self.fight_id,
            "winner": self.winner,
            "duration": self.duration,
            "opening_buff_delta": self.opening_buff_delta,
            "tp_efficiency_t1": self.team1_metrics.overall_tp_efficiency if self.team1_metrics else 0,
            "tp_efficiency_t2": self.team2_metrics.overall_tp_efficiency if self.team2_metrics else 0,
            "high_win_chips_t1": len(self.team1_metrics.high_win_chips_used) if self.team1_metrics else 0,
            "high_win_chips_t2": len(self.team2_metrics.high_win_chips_used) if self.team2_metrics else 0,
            "ponr_turn": self.ponr_turn,
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_stat_cv(stats: dict) -> float:
    """Calculate stat coefficient of variation.

    Lower CV = more hybrid/balanced build = better for elite play.

    Args:
        stats: Dict with strength, agility, wisdom, resistance, magic, science

    Returns:
        CV = std / mean of primary stats
    """
    primary_stats = [
        stats.get("strength", 0),
        stats.get("agility", 0),
        stats.get("wisdom", 0),
        stats.get("resistance", 0),
        stats.get("magic", 0),
        stats.get("science", 0),
    ]

    # Filter out zeros (unallocated stats)
    active_stats = [s for s in primary_stats if s > 0]

    if len(active_stats) < 2:
        return 1.0  # Single-stat = max CV

    mean = sum(active_stats) / len(active_stats)
    if mean == 0:
        return 1.0

    variance = sum((s - mean) ** 2 for s in active_stats) / len(active_stats)
    std = variance ** 0.5

    return std / mean


def calculate_mobility_ratio(mp: int, total_life: int) -> float:
    """Calculate mobility ratio.

    Elite threshold TBD from data analysis.

    Args:
        mp: Movement points
        total_life: Total HP

    Returns:
        mobility_ratio = MP / (total_life / 1000)
    """
    if total_life == 0:
        return 0.0
    return mp / (total_life / 1000)


def is_opening_buff(chip_id: int) -> bool:
    """Check if chip is in the opening buff gatekeeper set."""
    gatekeeper_ids = {
        OPENING_BUFF_CHIPS["knowledge"],
        OPENING_BUFF_CHIPS["adrenaline"],
        OPENING_BUFF_CHIPS["elevation"],
        OPENING_BUFF_CHIPS["armoring"],
        OPENING_BUFF_CHIPS["steroid"],
    }
    return chip_id in gatekeeper_ids


def is_high_win_chip(chip_id: int) -> bool:
    """Check if chip is in the high-win set."""
    return chip_id in HIGH_WIN_CHIPS.values()


def is_top_20_action(action_id: int) -> bool:
    """Check if action (chip or weapon) is in top-20 quality set."""
    return action_id in TOP_20_ACTIONS.values() or action_id in ELITE_WEAPONS.values()


# =============================================================================
# TP COST REFERENCE (from GROUND_TRUTH.md)
# =============================================================================

# Common action TP costs for efficiency calculation
TP_COSTS = {
    "set_weapon": 1,
    "say": 1,
    # Weapon costs vary - need to look up per weapon
    # Chip costs vary - need to look up per chip
}


def get_action_tp_cost(action_type: str, action_id: int | None = None) -> int:
    """Get TP cost for an action.

    TODO: Load from GROUND_TRUTH.md or API for accurate costs.
    For now, use rough estimates.
    """
    if action_type == "set_weapon":
        return 1
    elif action_type == "weapon":
        # Most weapons 3-5 TP, use 4 as average
        return 4
    elif action_type == "chip":
        # Chips vary widely, use 3 as average
        return 3
    return 0
