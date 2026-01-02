"""LeekWars game data models and constants.

Extracted from leek-wars-generator Java source for use in Python AI/RL systems.
"""

from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Any


# === Effect Types (from Effect.java) ===
class EffectType(IntEnum):
    DAMAGE = 1
    HEAL = 2
    BUFF_STRENGTH = 3
    BUFF_AGILITY = 4
    RELATIVE_SHIELD = 5
    ABSOLUTE_SHIELD = 6
    BUFF_MP = 7
    BUFF_TP = 8
    DEBUFF = 9
    TELEPORT = 10
    PERMUTATION = 11
    VITALITY = 12
    POISON = 13
    SUMMON = 14
    RESURRECT = 15
    KILL = 16
    SHACKLE_MP = 17
    SHACKLE_TP = 18
    SHACKLE_STRENGTH = 19
    DAMAGE_RETURN = 20
    BUFF_RESISTANCE = 21
    BUFF_WISDOM = 22
    ANTIDOTE = 23
    SHACKLE_MAGIC = 24
    AFTEREFFECT = 25
    VULNERABILITY = 26
    ABSOLUTE_VULNERABILITY = 27
    LIFE_DAMAGE = 28
    STEAL_ABSOLUTE_SHIELD = 29
    NOVA_DAMAGE = 30
    RAW_BUFF_MP = 31
    RAW_BUFF_TP = 32
    POISON_TO_SCIENCE = 33
    DAMAGE_TO_ABSOLUTE_SHIELD = 34
    DAMAGE_TO_STRENGTH = 35
    NOVA_DAMAGE_TO_MAGIC = 36
    RAW_ABSOLUTE_SHIELD = 37
    RAW_BUFF_STRENGTH = 38
    RAW_BUFF_MAGIC = 39
    RAW_BUFF_SCIENCE = 40
    RAW_BUFF_AGILITY = 41
    RAW_BUFF_RESISTANCE = 42
    PROPAGATION = 43
    RAW_BUFF_WISDOM = 44
    NOVA_VITALITY = 45
    ATTRACT = 46
    SHACKLE_AGILITY = 47
    SHACKLE_WISDOM = 48
    REMOVE_SHACKLES = 49
    MOVED_TO_MP = 50
    PUSH = 51
    RAW_BUFF_POWER = 52
    REPEL = 53
    RAW_RELATIVE_SHIELD = 54
    ALLY_KILLED_TO_AGILITY = 55
    KILL_TO_TP = 56
    RAW_HEAL = 57
    CRITICAL_TO_HEAL = 58
    ADD_STATE = 59
    TOTAL_DEBUFF = 60
    STEAL_LIFE = 61


# === Target Flags (from Effect.java) ===
class TargetFlag(IntFlag):
    ENEMIES = 1
    ALLIES = 2
    CASTER = 4
    NON_SUMMONS = 8
    SUMMONS = 16


# === Effect Modifiers (from Effect.java) ===
class EffectModifier(IntFlag):
    STACKABLE = 1
    MULTIPLIED_BY_TARGETS = 2
    ON_CASTER = 4
    NOT_REPLACEABLE = 8
    IRREDUCTIBLE = 16


# === Action Types (from Action.java) ===
class ActionType(IntEnum):
    START_FIGHT = 0
    USE_WEAPON = 1
    USE_CHIP = 2
    SET_WEAPON = 3
    END_FIGHT = 4
    PLAYER_DEAD = 5
    NEW_TURN = 6
    LEEK_TURN = 7
    END_TURN = 8
    SUMMON = 9
    MOVE_TO = 10
    KILL = 11
    USE_CHIP_ON_CELL = 12
    ADD_EFFECT = 15
    USE_WEAPON_ON_CELL = 16
    REMOVE_EFFECT = 17
    UPDATE_EFFECT = 18
    ADD_STACKABLE_EFFECT = 19
    LOST_PT = 100
    LOST_LIFE = 101
    LOST_PM = 102
    HEAL = 103
    VITALITY = 104
    RESURRECT = 105
    LOSE_STRENGTH = 106
    NOVA_DAMAGE = 107
    DAMAGE_RETURN = 108
    LIFE_DAMAGE = 109
    POISON_DAMAGE = 110
    AFTEREFFECT = 111
    NOVA_VITALITY = 112
    MP_LOST_AS_DAMAGE = 113
    TP_LOST_AS_DAMAGE = 114
    REDUCE_EFFECTS = 306
    REMOVE_POISONS = 307
    REMOVE_SHACKLES = 308
    BUG = 1001
    ERROR = 1002


# === Chip Types (from ChipType.java) ===
class ChipType(IntEnum):
    NONE = 0
    DAMAGE = 1
    HEAL = 2
    RETURN = 3
    PROTECTION = 4
    BOOST = 5
    POISON = 6
    SHACKLE = 7
    BULB = 8
    TELEPORTATION = 9
    DEBUFF = 10


# === Entity States (from EntityState.java) ===
class EntityState(IntEnum):
    NONE = 0
    RESURRECTED = 1
    UNHEALABLE = 2
    INVINCIBLE = 3
    PACIFIST = 4


# === Character Stats (from Entity.java) ===
class CharacterStat(IntEnum):
    TP = 0
    MP = 1
    STRENGTH = 2
    AGILITY = 3
    FREQUENCY = 4
    WISDOM = 5
    RESISTANCE = 6
    LIFE = 7
    ABSOLUTE_SHIELD = 8
    RELATIVE_SHIELD = 9
    TOTAL_TP = 10
    TOTAL_MP = 11
    SCIENCE = 12
    MAGIC = 13
    DAMAGE_RETURN = 14
    POWER = 15
    CORES = 16


# === Data Classes ===
@dataclass
class Effect:
    """An effect from a weapon or chip."""
    id: int
    type: EffectType
    value1: float
    value2: float
    turns: int
    targets: int  # TargetFlag bitmask
    modifiers: int  # EffectModifier bitmask

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Effect":
        # Effect ID is the effect type (1=damage, 2=heal, etc)
        effect_id = data.get("id", 1)
        try:
            effect_type = EffectType(effect_id)
        except ValueError:
            effect_type = EffectType.DAMAGE  # fallback
        return cls(
            id=effect_id,
            type=effect_type,
            value1=data.get("value1", 0),
            value2=data.get("value2", 0),
            turns=data.get("turns", 0),
            targets=data.get("targets", 31),
            modifiers=data.get("modifiers", 0),
        )


@dataclass
class Weapon:
    """A weapon definition."""
    id: int
    name: str
    level: int
    min_range: int
    max_range: int
    cost: int
    effects: list[Effect]
    area: int
    los: bool
    max_uses: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Weapon":
        effects = [Effect.from_dict(e) for e in data.get("effects", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            level=data.get("level", 1),
            min_range=data.get("min_range", 1),
            max_range=data.get("max_range", 1),
            cost=data.get("cost", 1),
            effects=effects,
            area=data.get("area", 1),
            los=data.get("los", True),
            max_uses=data.get("max_uses", -1),
        )


@dataclass
class Chip:
    """A chip definition."""
    id: int
    name: str
    level: int
    min_range: int
    max_range: int
    cost: int
    cooldown: int
    effects: list[Effect]
    area: int
    chip_type: ChipType
    los: bool
    max_uses: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chip":
        effects = [Effect.from_dict(e) for e in data.get("effects", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            level=data.get("level", 1),
            min_range=data.get("min_range", 0),
            max_range=data.get("max_range", 0),
            cost=data.get("cost", 1),
            cooldown=data.get("cooldown", 0),
            effects=effects,
            area=data.get("area", 1),
            chip_type=ChipType(data.get("type", 0)),
            los=data.get("los", True),
            max_uses=data.get("max_uses", -1),
        )


# === Weapon Constants (for LeekScript) ===
WEAPON_PISTOL = 1
WEAPON_MACHINE_GUN = 2
WEAPON_DOUBLE_GUN = 3
WEAPON_SHOTGUN = 4
WEAPON_MAGNUM = 5
WEAPON_LASER = 6
WEAPON_GRENADE_LAUNCHER = 7
WEAPON_FLAME_THROWER = 8
WEAPON_DESTROYER = 9
WEAPON_GAZOR = 10
WEAPON_ELECTRISOR = 11
WEAPON_MLX2 = 12
WEAPON_BLX9 = 13
WEAPON_KATANA = 14
WEAPON_BROADSWORD = 15
WEAPON_AXE = 16
WEAPON_JLX9 = 17
WEAPON_RHINO = 18
WEAPON_ILOT = 19
WEAPON_SLX = 20
WEAPON_RIFLE = 21
WEAPON_GRAVITON = 22
WEAPON_NEUTRINO = 23


# === Use Result Constants ===
USE_SUCCESS = 1
USE_FAILED = 0
USE_INVALID_TARGET = -1
USE_NOT_ENOUGH_TP = -2
USE_INVALID_COOLDOWN = -3
USE_INVALID_POSITION = -4
USE_TOO_MANY_SUMMONS = -5
USE_RESURRECT_INVALID = -6
USE_MAX_USES = -7


# === Item IDs (used in fights, from constants.json) ===
WEAPON_PISTOL_ITEM = 37
WEAPON_MACHINE_GUN_ITEM = 38
WEAPON_DOUBLE_GUN_ITEM = 39
WEAPON_DESTROYER_ITEM = 40
WEAPON_SHOTGUN_ITEM = 41
WEAPON_LASER_ITEM = 42
WEAPON_GRENADE_LAUNCHER_ITEM = 43
WEAPON_ELECTRISOR_ITEM = 44
WEAPON_MAGNUM_ITEM = 45
WEAPON_FLAME_THROWER_ITEM = 46
WEAPON_M_LASER_ITEM = 47
WEAPON_GAZOR_ITEM = 48


# =============================================================================
# Build System
# =============================================================================

from dataclasses import field
from pathlib import Path
import json

DATA_DIR = Path(__file__).parent.parent.parent / "data"


# Capital cost per characteristic point (increases with investment)
def capital_for_characteristic(points: int) -> int:
    """Calculate total capital needed for N points in a characteristic.

    Cost increases: 1 cap/pt for 0-49, 2 cap/pt for 50-99, etc.
    """
    if points <= 0:
        return 0
    total = 0
    remaining = points
    cost = 1
    while remaining > 0:
        bracket = min(remaining, 50)
        total += bracket * cost
        remaining -= bracket
        cost += 1
    return total


def capital_available(level: int) -> int:
    """Total capital available at a given level (~10 per level)."""
    return level * 10


@dataclass
class LeekBuild:
    """Complete leek build configuration.

    Represents a character's stat allocation and equipment loadout.
    """
    level: int = 1

    # Characteristics (points allocated, not capital)
    strength: int = 0
    agility: int = 0
    wisdom: int = 0
    resistance: int = 0
    science: int = 0
    magic: int = 0
    frequency: int = 0

    # Equipment (item IDs used in fights)
    weapons: list[int] = field(default_factory=list)
    chips: list[int] = field(default_factory=list)

    @property
    def total_capital_spent(self) -> int:
        """Total capital spent on all characteristics."""
        return sum([
            capital_for_characteristic(self.strength),
            capital_for_characteristic(self.agility),
            capital_for_characteristic(self.wisdom),
            capital_for_characteristic(self.resistance),
            capital_for_characteristic(self.science),
            capital_for_characteristic(self.magic),
            capital_for_characteristic(self.frequency),
        ])

    @property
    def capital_remaining(self) -> int:
        """Capital left to spend."""
        return capital_available(self.level) - self.total_capital_spent

    def validate(self) -> tuple[bool, str]:
        """Check if build is valid for level."""
        if self.total_capital_spent > capital_available(self.level):
            return False, f"Over budget by {-self.capital_remaining} capital"
        return True, "Valid"

    # Derived stats
    @property
    def base_life(self) -> int:
        """Base HP = 100 + 3*level."""
        return 100 + self.level * 3

    @property
    def base_tp(self) -> int:
        """Base TP = 10 + wisdom bonus (1 per 200 wisdom)."""
        return 10 + self.wisdom // 200

    @property
    def base_mp(self) -> int:
        """Base MP = 3 + agility bonus (1 per 100 agility)."""
        return 3 + self.agility // 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for simulator EntityConfig."""
        return {
            "level": self.level,
            "life": self.base_life,
            "tp": self.base_tp,
            "mp": self.base_mp,
            "strength": self.strength,
            "agility": self.agility,
            "wisdom": self.wisdom,
            "resistance": self.resistance,
            "science": self.science,
            "magic": self.magic,
            "frequency": self.frequency,
            "weapons": self.weapons,
            "chips": self.chips,
        }


# =============================================================================
# Build Archetypes
# =============================================================================

def _points_for_capital(capital: int) -> int:
    """How many characteristic points can we buy with given capital?

    Inverse of capital_for_characteristic.
    """
    if capital <= 0:
        return 0
    points = 0
    remaining = capital
    cost = 1
    while remaining > 0:
        affordable = remaining // cost
        bracket = min(affordable, 50)
        if bracket <= 0:
            break
        points += bracket
        remaining -= bracket * cost
        cost += 1
    return points


def glass_cannon_build(level: int) -> LeekBuild:
    """High damage, low survivability."""
    cap = capital_available(level)
    # 70% strength, 30% agility
    str_pts = _points_for_capital(int(cap * 0.7))
    agi_pts = _points_for_capital(int(cap * 0.3))
    return LeekBuild(
        level=level,
        strength=str_pts,
        agility=agi_pts,
        weapons=[WEAPON_PISTOL_ITEM],
    )


def tank_build(level: int) -> LeekBuild:
    """High survivability, moderate damage."""
    cap = capital_available(level)
    # 50% resistance, 30% strength, 20% wisdom
    res_pts = _points_for_capital(int(cap * 0.5))
    str_pts = _points_for_capital(int(cap * 0.3))
    wis_pts = _points_for_capital(int(cap * 0.2))
    return LeekBuild(
        level=level,
        strength=str_pts,
        resistance=res_pts,
        wisdom=wis_pts,
        weapons=[WEAPON_PISTOL_ITEM],
    )


def balanced_build(level: int) -> LeekBuild:
    """Balanced stats across the board."""
    cap = capital_available(level)
    # 25% each to 4 stats
    pts = _points_for_capital(cap // 4)
    return LeekBuild(
        level=level,
        strength=pts,
        agility=pts,
        resistance=pts,
        wisdom=pts,
        weapons=[WEAPON_PISTOL_ITEM],
    )


def kiter_build(level: int) -> LeekBuild:
    """High mobility, chip-focused."""
    cap = capital_available(level)
    # 40% agility, 40% science, 20% frequency
    agi_pts = _points_for_capital(int(cap * 0.4))
    sci_pts = _points_for_capital(int(cap * 0.4))
    frq_pts = _points_for_capital(int(cap * 0.2))
    return LeekBuild(
        level=level,
        agility=agi_pts,
        science=sci_pts,
        frequency=frq_pts,
        weapons=[WEAPON_PISTOL_ITEM],
    )


BUILD_ARCHETYPES = {
    "glass_cannon": glass_cannon_build,
    "tank": tank_build,
    "balanced": balanced_build,
    "kiter": kiter_build,
}


# =============================================================================
# Equipment Catalog
# =============================================================================

class EquipmentCatalog:
    """Catalog of all weapons and chips from API data."""

    def __init__(self):
        self.weapons: dict[int, Weapon] = {}
        self.chips: dict[int, Chip] = {}
        self._item_to_weapon: dict[int, int] = {}  # item_id -> weapon_id
        self._load()

    def _load(self):
        """Load from data/*.json files."""
        # Weapons
        weapons_file = DATA_DIR / "weapons.json"
        if weapons_file.exists():
            data = json.loads(weapons_file.read_text())
            for wid, w in data.get("weapons", data).items():
                self.weapons[int(wid)] = Weapon.from_dict(w)
                self._item_to_weapon[w["item"]] = int(wid)

        # Chips
        chips_file = DATA_DIR / "chips.json"
        if chips_file.exists():
            data = json.loads(chips_file.read_text())
            for cid, c in data.get("chips", data).items():
                self.chips[int(cid)] = Chip.from_dict(c)

    def weapon_by_item_id(self, item_id: int) -> Weapon | None:
        """Get weapon by item ID (used in fights)."""
        wid = self._item_to_weapon.get(item_id)
        return self.weapons.get(wid) if wid else None

    def weapons_at_level(self, level: int) -> list[Weapon]:
        """Get weapons unlocked at or before level."""
        return sorted(
            [w for w in self.weapons.values() if w.level <= level],
            key=lambda w: w.level
        )

    def chips_at_level(self, level: int) -> list[Chip]:
        """Get chips unlocked at or before level."""
        return sorted(
            [c for c in self.chips.values() if c.level <= level],
            key=lambda c: c.level
        )


_catalog: EquipmentCatalog | None = None

def get_catalog() -> EquipmentCatalog:
    """Get singleton equipment catalog."""
    global _catalog
    if _catalog is None:
        _catalog = EquipmentCatalog()
    return _catalog


# =============================================================================
# Summary Helpers
# =============================================================================

def summarize_build(build: LeekBuild) -> str:
    """Return build summary string."""
    valid, msg = build.validate()
    return (
        f"Level {build.level} | "
        f"Capital: {build.total_capital_spent}/{capital_available(build.level)} | "
        f"STR:{build.strength} AGI:{build.agility} WIS:{build.wisdom} "
        f"RES:{build.resistance} SCI:{build.science} MAG:{build.magic} FRQ:{build.frequency} | "
        f"HP:{build.base_life} TP:{build.base_tp} MP:{build.base_mp} | "
        f"{msg}"
    )
