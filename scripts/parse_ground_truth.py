#!/usr/bin/env python3
"""Parse ground truth from LeekWars submodules.

Extracts authoritative game data from:
- tools/leek-wars/src/model/weapons.ts
- tools/leek-wars/src/model/chips.ts
- tools/leek-wars-generator/.../FightConstants.java

Usage:
    python scripts/parse_ground_truth.py                    # Print summary
    python scripts/parse_ground_truth.py --output FILE      # Generate markdown
    python scripts/parse_ground_truth.py --verify           # Verify against docs
    python scripts/parse_ground_truth.py --json             # Output as JSON
"""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WeaponInfo:
    """Weapon data from weapons.ts."""
    id: int
    name: str
    level: int
    cost: int
    max_uses: int
    min_range: int
    max_range: int
    item_id: int
    damage_base: int = 0
    damage_variance: int = 0


@dataclass
class ChipInfo:
    """Chip data from chips.ts."""
    id: int
    name: str
    level: int
    cost: int
    cooldown: int
    max_uses: int
    min_range: int
    max_range: int
    effect_type: int
    effect_base: int = 0
    effect_variance: int = 0


def parse_weapons_ts(path: Path) -> dict[int, WeaponInfo]:
    """Parse weapons.ts TypeScript file."""
    content = path.read_text()
    weapons = {}

    # Match weapon objects: '1': { id: 1, name: 'pistol', ... }
    pattern = r"'(\d+)':\s*\{([^}]+)\}"
    for match in re.finditer(pattern, content):
        weapon_id = int(match.group(1))
        obj_str = match.group(2)

        # Extract fields
        def extract(field: str, default=0):
            m = re.search(rf"{field}:\s*([^,\s]+)", obj_str)
            if m:
                val = m.group(1).strip("'\"")
                try:
                    return int(val)
                except ValueError:
                    return val
            return default

        # Extract damage from effects (first effect with type 1)
        damage_base = 0
        damage_variance = 0
        effects_match = re.search(r"effects:\s*\[(.*?)\]", obj_str)
        if effects_match:
            effects_str = effects_match.group(1)
            effect_match = re.search(r"value1:\s*(\d+)[^}]*value2:\s*(\d+)", effects_str)
            if effect_match:
                damage_base = int(effect_match.group(1))
                damage_variance = int(effect_match.group(2))

        weapons[weapon_id] = WeaponInfo(
            id=weapon_id,
            name=extract("name", ""),
            level=extract("level"),
            cost=extract("cost"),
            max_uses=extract("max_uses"),
            min_range=extract("min_range"),
            max_range=extract("max_range"),
            item_id=extract("item"),
            damage_base=damage_base,
            damage_variance=damage_variance,
        )

    return weapons


def parse_chips_ts(path: Path) -> dict[int, ChipInfo]:
    """Parse chips.ts TypeScript file."""
    content = path.read_text()
    chips = {}

    # Match chip objects
    pattern = r"'(\d+)':\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}"
    for match in re.finditer(pattern, content):
        chip_id = int(match.group(1))
        obj_str = match.group(2)

        def extract(field: str, default=0):
            m = re.search(rf"{field}:\s*([^,\s\[]+)", obj_str)
            if m:
                val = m.group(1).strip("'\"")
                try:
                    return int(val)
                except ValueError:
                    try:
                        return float(val)
                    except ValueError:
                        return val
            return default

        # Extract effect info
        effect_base = 0
        effect_variance = 0
        effect_type = 0
        effects_match = re.search(r"effects:\s*\[(.*?)\]", obj_str, re.DOTALL)
        if effects_match:
            effects_str = effects_match.group(1)
            # Get first effect
            first_effect = re.search(r"\{([^}]+)\}", effects_str)
            if first_effect:
                eff_str = first_effect.group(1)
                v1_match = re.search(r"value1:\s*([\d.]+)", eff_str)
                v2_match = re.search(r"value2:\s*([\d.]+)", eff_str)
                type_match = re.search(r"type:\s*(\d+)", eff_str)
                if v1_match:
                    effect_base = int(float(v1_match.group(1)))
                if v2_match:
                    effect_variance = int(float(v2_match.group(1)))
                if type_match:
                    effect_type = int(type_match.group(1))

        chips[chip_id] = ChipInfo(
            id=chip_id,
            name=extract("name", ""),
            level=extract("level"),
            cost=extract("cost"),
            cooldown=extract("cooldown"),
            max_uses=extract("max_uses"),
            min_range=extract("min_range"),
            max_range=extract("max_range"),
            effect_type=effect_type,
            effect_base=effect_base,
            effect_variance=effect_variance,
        )

    return chips


def parse_fight_constants(path: Path) -> dict[str, int]:
    """Parse FightConstants.java for weapon/chip IDs."""
    content = path.read_text()
    constants = {}

    # Match: WEAPON_PISTOL(37, Type.INT),
    pattern = r"(\w+)\((\d+),\s*Type\.\w+\)"
    for match in re.finditer(pattern, content):
        name = match.group(1)
        value = int(match.group(2))
        constants[name] = value

    return constants


def print_summary(weapons: dict, chips: dict, constants: dict):
    """Print human-readable summary."""
    print("=" * 60)
    print("GROUND TRUTH SUMMARY")
    print("=" * 60)

    print(f"\nWeapons: {len(weapons)}")
    # Our weapons (by item ID)
    our_weapons = [37, 45, 40]  # Pistol, Magnum, Destroyer
    print("\nOur Weapons:")
    print(f"{'Weapon':15} {'TP':>3} {'Uses':>5} {'Range':>7} {'Item':>5} {'Level':>5}")
    for w in weapons.values():
        if w.item_id in our_weapons:
            print(f"{w.name:15} {w.cost:3} {w.max_uses:5} {w.min_range}-{w.max_range:3} {w.item_id:5} {w.level:5}")

    print(f"\nChips: {len(chips)}")
    # Our chips
    our_chips = [4, 5, 6, 8, 14, 15]  # Cure, Flame, Flash, Protein, Boots, Motivation
    print("\nOur Chips:")
    print(f"{'Chip':15} {'TP':>3} {'Uses':>5} {'CD':>3} {'Range':>7} {'Effect':>10}")
    for c in chips.values():
        if c.id in our_chips:
            uses = str(c.max_uses) if c.max_uses > 0 else "∞"
            effect = f"{c.effect_base}±{c.effect_variance}"
            print(f"{c.name:15} {c.cost:3} {uses:>5} {c.cooldown:3} {c.min_range}-{c.max_range:3} {effect:>10}")

    print(f"\nConstants: {len(constants)}")
    print("\nWeapon IDs (item IDs for setWeapon):")
    for name, value in sorted(constants.items()):
        if name.startswith("WEAPON_") and not name.startswith("WEAPON_TEMPLATE"):
            print(f"  {name} = {value}")


def generate_markdown(weapons: dict, chips: dict, constants: dict) -> str:
    """Generate GROUND_TRUTH.md content."""
    # This would regenerate the full markdown file
    # For now, just return a stub
    return f"""# Ground Truth Reference (Auto-Generated)

Generated from submodules. See scripts/parse_ground_truth.py.

## Summary
- Weapons: {len(weapons)}
- Chips: {len(chips)}
- Constants: {len(constants)}

See docs/GROUND_TRUTH.md for full reference.
"""


def main():
    parser = argparse.ArgumentParser(description="Parse LeekWars ground truth")
    parser.add_argument("--output", "-o", help="Output markdown file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verify", action="store_true", help="Verify against docs")
    args = parser.parse_args()

    # Paths
    base = Path(__file__).parent.parent
    weapons_path = base / "tools/leek-wars/src/model/weapons.ts"
    chips_path = base / "tools/leek-wars/src/model/chips.ts"
    constants_path = base / "tools/leek-wars-generator/src/main/java/com/leekwars/generator/FightConstants.java"

    # Parse
    weapons = parse_weapons_ts(weapons_path)
    chips = parse_chips_ts(chips_path)
    constants = parse_fight_constants(constants_path)

    if args.json:
        data = {
            "weapons": {k: vars(v) for k, v in weapons.items()},
            "chips": {k: vars(v) for k, v in chips.items()},
            "constants": constants,
        }
        print(json.dumps(data, indent=2))
    elif args.output:
        content = generate_markdown(weapons, chips, constants)
        Path(args.output).write_text(content)
        print(f"Wrote {args.output}")
    elif args.verify:
        # TODO: Compare against docs/GROUND_TRUTH.md
        print("Verification not implemented yet")
    else:
        print_summary(weapons, chips, constants)


if __name__ == "__main__":
    main()
