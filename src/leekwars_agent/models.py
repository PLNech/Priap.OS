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
        return cls(
            id=data.get("id", 0),
            type=EffectType(data.get("type", data.get("id", 1))),
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
USE_SUCCESS = 0
USE_FAILED = 1
USE_INVALID = 2
USE_NOT_ENOUGH_TP = 3
USE_INVALID_POSITION = 4
USE_INVALID_COOLDOWN = 5
USE_TOO_MANY_SUMMONS = 6
USE_LEEK_DEAD = 7
USE_INVALID_TARGET = 8
USE_NOT_EQUIPPED = 9
