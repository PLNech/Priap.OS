"""Ground-truth chip data from leek-wars frontend source.

Source: tools/leek-wars/src/model/chips.ts
Last updated: 2026-01-23

This is the authoritative chip reference for simulation and AI development.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ChipInfo:
    """Chip stats from ground truth."""
    id: int
    name: str
    level: int
    cost: int  # TP cost
    cooldown: int  # turns between uses (-1 = once per fight)
    min_range: int
    max_range: int
    max_uses: int  # per turn, -1 = unlimited
    area: int  # 1 = single, 3 = small AOE, etc.
    los: bool  # requires line of sight

    # Primary effect (simplified)
    effect_type: str  # "damage", "heal", "buff_str", "buff_mp", "buff_tp", etc.
    effect_value: int  # base value
    effect_variance: int  # +/- range
    effect_turns: int  # duration for buffs


# Our equipped chips (verified from source)
OUR_CHIPS = {
    4: ChipInfo(
        id=4, name="cure", level=20, cost=4, cooldown=2,
        min_range=0, max_range=5, max_uses=-1, area=1, los=True,
        effect_type="heal", effect_value=38, effect_variance=8, effect_turns=0
    ),
    5: ChipInfo(
        id=5, name="flame", level=29, cost=4, cooldown=0,
        min_range=2, max_range=7, max_uses=3,  # IMPORTANT: only 3 uses/turn!
        area=1, los=True,
        effect_type="damage", effect_value=29, effect_variance=2, effect_turns=0
    ),
    6: ChipInfo(
        id=6, name="flash", level=24, cost=3, cooldown=1,
        min_range=1, max_range=10, max_uses=-1, area=3, los=True,
        effect_type="damage", effect_value=32, effect_variance=3, effect_turns=0
    ),
    8: ChipInfo(
        id=8, name="protein", level=6, cost=3, cooldown=3,
        min_range=0, max_range=4, max_uses=-1, area=1, los=True,
        effect_type="buff_str", effect_value=80, effect_variance=20, effect_turns=2
    ),
    14: ChipInfo(
        id=14, name="leather_boots", level=22, cost=3, cooldown=5,
        min_range=0, max_range=5, max_uses=-1, area=1, los=True,
        effect_type="buff_mp", effect_value=2, effect_variance=0, effect_turns=2
    ),
    15: ChipInfo(
        id=15, name="motivation", level=14, cost=4, cooldown=6,
        min_range=0, max_range=5, max_uses=-1, area=1, los=True,
        effect_type="buff_tp", effect_value=2, effect_variance=0, effect_turns=3
    ),
}


def print_chip_summary():
    """Print formatted chip summary."""
    print("=" * 70)
    print("OUR EQUIPPED CHIPS (Ground Truth)")
    print("=" * 70)

    for chip_id, chip in sorted(OUR_CHIPS.items()):
        uses = f"x{chip.max_uses}/turn" if chip.max_uses > 0 else "unlimited"
        cd = f"CD{chip.cooldown}" if chip.cooldown >= 0 else "1/fight"

        print(f"\nCHIP_{chip.name.upper()} (ID {chip_id})")
        print(f"  Level: {chip.level} | TP: {chip.cost} | {cd} | {uses}")
        print(f"  Range: {chip.min_range}-{chip.max_range} | LOS: {chip.los} | Area: {chip.area}")
        print(f"  Effect: {chip.effect_type} {chip.effect_value}±{chip.effect_variance}", end="")
        if chip.effect_turns > 0:
            print(f" for {chip.effect_turns} turns")
        else:
            print()


if __name__ == "__main__":
    print_chip_summary()
