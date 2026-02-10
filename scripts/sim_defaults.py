"""Shared defaults for simulation scripts.

Single source of truth for our leek's current build.
Update here when spending capital, changing equipment, or leveling up.
All simulation scripts (compare_ais, debug_fight, etc.) import from here.
"""

# === Our Leek: IAdonis (ID: 131321) ===

LEEK_LEVEL = 73
LEEK_LIFE = 316
LEEK_TP = 10
LEEK_MP = 3

# Stats
LEEK_STR = 452
LEEK_AGI = 10
LEEK_FREQ = 0
LEEK_WIS = 0
LEEK_RES = 0
LEEK_SCI = 0
LEEK_MAG = 0

# Equipment (item IDs from tools/leek-wars/src/model/)
# Weapons: Magnum(45, 5TP, range 1-8) + Laser(42, 6TP, range 2-9)
DEFAULT_WEAPONS = [45, 42]

# Chips: CURE(4), FLAME(5), FLASH(6), PROTEIN(8), BOOTS(14), MOTIVATION(15)
DEFAULT_CHIPS = [4, 5, 6, 8, 14, 15]
