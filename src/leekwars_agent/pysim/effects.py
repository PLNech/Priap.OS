"""PySim effects — pure combat formula functions from the Java generator."""
from __future__ import annotations

import random

# Critical hits multiply the base value by this factor.
CRITICAL_FACTOR = 1.3


def roll_critical(agility: int, rng: random.Random) -> bool:
    """Critical hit chance = agility / 1000."""
    return rng.random() < (agility / 1000)


def calc_damage(
    v1: float,
    v2: float,
    caster_str: int,
    caster_agi: int,
    rng: random.Random,
) -> tuple[int, bool]:
    """Calculate raw damage before shields.

    Returns (raw_damage, is_critical).
    Formula: raw = (v1 + jet * v2) * (1 + max(0, STR) / 100) * crit_factor
    where jet = uniform(0, 1).
    """
    jet = rng.random()
    crit = roll_critical(caster_agi, rng)
    factor = CRITICAL_FACTOR if crit else 1.0
    raw = (v1 + jet * v2) * (1 + max(0, caster_str) / 100) * factor
    return int(raw), crit


def calc_heal(
    v1: float,
    v2: float,
    caster_wis: int,
    caster_agi: int,
    rng: random.Random,
) -> tuple[int, bool]:
    """Calculate healing amount.

    Returns (heal_amount, is_critical).
    Formula: heal = (v1 + jet * v2) * (1 + WIS / 100) * crit_factor
    """
    jet = rng.random()
    crit = roll_critical(caster_agi, rng)
    factor = CRITICAL_FACTOR if crit else 1.0
    heal = (v1 + jet * v2) * (1 + max(0, caster_wis) / 100) * factor
    return int(heal), crit


def calc_abs_shield(
    v1: float,
    v2: float,
    caster_res: int,
    caster_agi: int,
    rng: random.Random,
) -> tuple[float, bool]:
    """Calculate absolute shield value.

    Returns (shield_value, is_critical).
    Formula: shield = (v1 + jet * v2) * (1 + RES / 100) * crit_factor
    """
    jet = rng.random()
    crit = roll_critical(caster_agi, rng)
    factor = CRITICAL_FACTOR if crit else 1.0
    shield = (v1 + jet * v2) * (1 + max(0, caster_res) / 100) * factor
    return shield, crit


def calc_rel_shield(
    v1: float,
    v2: float,
    caster_res: int,
    caster_agi: int,
    rng: random.Random,
) -> tuple[float, bool]:
    """Calculate relative shield percentage.

    Returns (shield_pct, is_critical). Same formula as abs_shield.
    """
    jet = rng.random()
    crit = roll_critical(caster_agi, rng)
    factor = CRITICAL_FACTOR if crit else 1.0
    shield = (v1 + jet * v2) * (1 + max(0, caster_res) / 100) * factor
    return shield, crit


def calc_tp_shackle(
    v1: float,
    v2: float,
    caster_mag: int,
    target_base_tp: int,
    caster_agi: int,
    rng: random.Random,
) -> tuple[int, bool]:
    """Calculate TP shackle (e.g. Tranquilizer).

    Returns (tp_lost, is_critical).
    Formula: shackle_pct = (v1 + jet * v2) * (1 + max(0, MAG) / 100) * crit
             shackle_tp  = round(target_base_tp * shackle_pct)

    Tranquilizer has v1=0.5, v2=0.1 → 50-60% TP shackle before magic scaling.
    """
    jet = rng.random()
    crit = roll_critical(caster_agi, rng)
    factor = CRITICAL_FACTOR if crit else 1.0
    shackle_pct = (v1 + jet * v2) * (1 + max(0, caster_mag) / 100) * factor
    shackle_tp = round(target_base_tp * shackle_pct)
    return shackle_tp, crit


def calc_raw_tp_buff(
    v1: float,
    v2: float,
    base_tp: int,
    caster_agi: int,
    rng: random.Random,
) -> tuple[int, bool]:
    """Calculate raw TP buff (e.g. Whip).

    Returns (tp_gained, is_critical).
    Formula: buff_pct = (v1 + jet * v2) * crit_factor
             buff_tp  = round(base_tp * buff_pct)

    Whip: v1=0.6, v2=0.1 → 60-70% TP buff. At base TP 14 → +8 to +10 TP.
    """
    jet = rng.random()
    crit = roll_critical(caster_agi, rng)
    factor = CRITICAL_FACTOR if crit else 1.0
    buff_pct = (v1 + jet * v2) * factor
    buff_tp = round(base_tp * buff_pct)
    return buff_tp, crit
