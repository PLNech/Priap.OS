"""Shared constants for LeekWars CLI."""

# Our account
FARMER_ID = 124831
LEEK_ID = 131321  # Default (IAdonis) — prefer ctx.obj["leek_id"] in commands
LEEK_NAME = "IAdonis"

# Multi-leek registry
LEEKS = {
    "iadonis": 131321,
    "anansai": 132531,
}
DEFAULT_LEEK = "iadonis"


def resolve_leek(name_or_id: str) -> int:
    """Resolve leek name or ID to numeric ID.

    Supports: exact name, partial prefix, or numeric ID.
    Raises ValueError if unresolvable.
    """
    # Try as int first
    try:
        return int(name_or_id)
    except ValueError:
        pass
    # Try as name (case-insensitive)
    key = name_or_id.lower()
    if key in LEEKS:
        return LEEKS[key]
    # Partial match
    matches = [v for k, v in LEEKS.items() if k.startswith(key)]
    if len(matches) == 1:
        return matches[0]
    known = ", ".join(LEEKS.keys())
    raise ValueError(f"Unknown leek: {name_or_id}. Known: {known}")

# Item type IDs (from leek-wars/src/model/item.ts)
class ItemType:
    ALL = 0
    WEAPON = 1
    CHIP = 2
    POTION = 3
    HAT = 4
    POMP = 5
    FIGHT_PACK = 6
    RESOURCE = 7
    COMPONENT = 8
    SCHEME = 9

ITEM_TYPE_NAMES = {
    ItemType.WEAPON: "weapons",
    ItemType.CHIP: "chips",
    ItemType.POTION: "potions",
    ItemType.HAT: "hats",
    ItemType.RESOURCE: "resources",
    ItemType.COMPONENT: "components",
    ItemType.SCHEME: "schemes",
}

# Special item IDs
HABS_ITEM_ID = 148  # Currency used in recipes

# Weapon IDs
WEAPON_PISTOL = 37
