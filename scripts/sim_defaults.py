"""Shared defaults for simulation scripts.

Single source of truth for our leek's current build.
Update here when spending capital, changing equipment, or leveling up.
All simulation scripts (compare_ais, debug_fight, etc.) import from here.
"""

# === Our Leek: IAdonis (ID: 131321) ===

LEEK_LEVEL = 117
LEEK_LIFE = 792   # 692 base + 100 (Apple component)
LEEK_TP = 14      # S28: +4 TP from capital spend
LEEK_MP = 4       # S28: +1 MP from capital spend

# Stats (base + component bonuses)
LEEK_STR = 452
LEEK_AGI = 10     # 10 base
LEEK_FREQ = 140   # 100 base + 40 (Fan component)
LEEK_WIS = 40     # 0 base + 40 (CD component)
LEEK_RES = 0
LEEK_SCI = 0
LEEK_MAG = 0

# Equipment (item IDs from tools/leek-wars/src/model/)
# Weapons: Magnum(45, 4TP, range 3-6) + Laser(42, 5TP, range 2-7) + b_laser(60, 5TP, range 2-8, +heal)
# S30: Added b_laser (50±10 dmg + 50±10 self-heal, 3 uses/fight)
DEFAULT_WEAPONS = [45, 42, 60]

# Chips: TRANQUILIZER(94), FLAME(5), ARMOR(22), MOTIVATION(15), SHIELD(20), HELMET(21)
# S29: Cure(4) removed (0 heals/12 fights), Tranquilizer(94) added
DEFAULT_CHIPS = [94, 5, 22, 15, 20, 21]
