"""PySim effects — generic combat formula driven by parsed Java metadata.

All constants parsed from Effect.java. Per-effect formula metadata parsed from Effect*.java.
One function computes all effect values: calc_effect_value().
"""
from __future__ import annotations

import random

from .java_formulas import get_constants, get_formula

# Parsed from Effect.java
_consts = get_constants()
CRITICAL_FACTOR = _consts.critical_factor
EROSION_BASE = _consts.erosion_base
EROSION_POISON = _consts.erosion_poison
EROSION_CRIT_BONUS = _consts.erosion_crit_bonus


def roll_critical(agility: int, rng: random.Random) -> bool:
    """Critical hit chance = agility / 1000."""
    return rng.random() < (agility / 1000)


def erosion_rate(is_poison: bool, is_critical: bool) -> float:
    """Erosion rate from Effect.java:206-207."""
    base = EROSION_POISON if is_poison else EROSION_BASE
    return base + (EROSION_CRIT_BONUS if is_critical else 0.0)


def calc_effect_value(
    v1: float,
    v2: float,
    effect_id: int,
    caster_stats: dict[str, int],
    rng: random.Random,
) -> tuple[int, bool]:
    """Calculate any effect's value using parsed Java formula metadata.

    Every Effect*.java formula follows the same template:
        value = round((v1 + jet*v2) * (1 + stat/100) * critPower * (1 + power/100))

    The parser tells us which stat and which flags to plug in.

    Args:
        caster_stats: {strength, agility, resistance, wisdom, magic, science, power}

    Returns:
        (value, is_critical)
    """
    formula = get_formula(effect_id)
    jet = rng.random()
    crit = roll_critical(caster_stats.get("agility", 0), rng)
    crit_factor = CRITICAL_FACTOR if crit else 1.0

    base = v1 + jet * v2

    if formula and formula.primary_stat:
        stat_val = caster_stats.get(formula.primary_stat, 0)
        if formula.max_zero_stat:
            stat_val = max(0, stat_val)
        base *= (1 + stat_val / 100)

    if formula and formula.has_power:
        base *= (1 + caster_stats.get("power", 0) / 100)

    return int(round(base * crit_factor)), crit
