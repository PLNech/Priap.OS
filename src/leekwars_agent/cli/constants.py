"""Shared constants for LeekWars CLI."""

# Our account
FARMER_ID = 124831
LEEK_ID = 131321
LEEK_NAME = "IAdonis"

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
