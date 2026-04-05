"""Shared defaults for simulation scripts.

Single source of truth for our leek's current build.
Update here when spending capital, changing equipment, or leveling up.
All simulation scripts (compare_ais, debug_fight, etc.) import from here.
"""

# === Our Leek: IAdonis (ID: 131321) ===

LEEK_LEVEL = 146
LEEK_LIFE = 1099  # 999 base (level 146) + 100 (Apple component)
LEEK_TP = 14      # S28: +4 TP from capital spend
LEEK_MP = 4       # S28: +1 MP from capital spend

# Stats (base + component bonuses)
LEEK_STR = 452
LEEK_AGI = 10     # 10 base
LEEK_FREQ = 140   # 100 base + 40 (Fan component)
LEEK_WIS = 40     # 0 base + 40 (CD component)
LEEK_RES = 219    # S39: 86 capital → RES 66→219 (bracket meta: 50-200, now above avg)
LEEK_SCI = 0
LEEK_MAG = 0

# Equipment (item IDs from tools/leek-wars/src/model/)
# Weapons: Magnum(45, 4TP, range 3-6) + Laser(42, 5TP, range 2-7) + b_laser(60, 5TP, range 2-8, +heal)
# S30: Added b_laser (50±10 dmg + 50±10 self-heal, 3 uses/fight)
DEFAULT_WEAPONS = [45, 42, 60]

# Chips: TRANQUILIZER(94), FLAME(5), ARMOR(22), WHIP(88), SHIELD(20), HELMET(21)
# S39: Ferocity(102) removed (can't self-cast!), Whip(88) added (+60% TP, 2t, CD 1)
DEFAULT_CHIPS = [94, 5, 22, 88, 20, 21]
