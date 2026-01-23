"""Tests for market CLI and items_loader.

The "weapon_destroyer incident" (2026-01-23) taught us: always validate item data!
"""

import pytest


class TestItemsLoader:
    """Test the dynamic items loader."""

    def test_load_items_returns_dict(self):
        """Should return a dict of items."""
        from leekwars_agent.cli.items_loader import load_items
        items = load_items()
        assert isinstance(items, dict)
        assert len(items) > 0

    def test_items_have_required_fields(self):
        """Every item must have name, type, level, price."""
        from leekwars_agent.cli.items_loader import load_items
        items = load_items()
        required = {"name", "type", "level", "price"}

        for item_id, item in items.items():
            missing = required - set(item.keys())
            assert not missing, f"Item {item_id} missing: {missing}"

    def test_get_chips_filters_correctly(self):
        """get_chips should only return chips (type 2)."""
        from leekwars_agent.cli.items_loader import get_chips, ITEM_TYPE_CHIP
        chips = get_chips()
        for item_id, item in chips.items():
            assert item["type"] == ITEM_TYPE_CHIP, f"Item {item_id} is not a chip"

    def test_get_weapons_filters_correctly(self):
        """get_weapons should only return weapons (type 1)."""
        from leekwars_agent.cli.items_loader import get_weapons, ITEM_TYPE_WEAPON
        weapons = get_weapons()
        for item_id, item in weapons.items():
            assert item["type"] == ITEM_TYPE_WEAPON, f"Item {item_id} is not a weapon"

    def test_max_level_filter_works(self):
        """Should filter items by max level."""
        from leekwars_agent.cli.items_loader import get_market_items
        items = get_market_items(max_level=10)
        for item_id, item in items.items():
            assert item["level"] <= 10, f"Item {item_id} level {item['level']} > 10"

    def test_get_item_returns_correct_data(self):
        """get_item should return item data or None."""
        from leekwars_agent.cli.items_loader import get_item

        # Pistol should exist
        pistol = get_item(37)
        assert pistol is not None
        assert pistol["name"] == "weapon_pistol"

        # Nonexistent item
        fake = get_item(999999)
        assert fake is None


class TestWeaponDestroyerRegression:
    """Regression tests for the weapon_destroyer incident.

    On 2026-01-23, we had hardcoded ID 40 as "weapon_magnum" (L27)
    when it's actually "weapon_destroyer" (L85). This caused:
    - Failed equip with "too_high_level" error
    - Wasted 7,510 habs on wrong weapon

    These tests ensure we never confuse these weapons again.
    """

    def test_magnum_is_id_45(self):
        """weapon_magnum MUST be ID 45."""
        from leekwars_agent.cli.items_loader import get_item

        magnum = get_item(45)
        assert magnum is not None, "Magnum (ID 45) not found"
        assert magnum["name"] == "weapon_magnum"
        assert magnum["level"] == 27

    def test_destroyer_is_id_40(self):
        """weapon_destroyer is ID 40 - don't confuse with magnum!"""
        from leekwars_agent.cli.items_loader import get_item

        destroyer = get_item(40)
        if destroyer:  # May not be in filtered results
            assert destroyer["name"] == "weapon_destroyer"
            assert destroyer["level"] == 85

    def test_id_40_is_not_magnum(self):
        """ID 40 must NOT be named magnum."""
        from leekwars_agent.cli.items_loader import get_item

        item = get_item(40)
        if item:
            assert "magnum" not in item["name"].lower(), (
                "ID 40 is weapon_destroyer, NOT magnum!"
            )


class TestMarketItemsCompleteness:
    """Test we have essential items for gameplay."""

    def test_has_starter_weapon(self):
        """Should have pistol (ID 37) for new players."""
        from leekwars_agent.cli.items_loader import get_item
        pistol = get_item(37)
        assert pistol is not None
        assert pistol["level"] == 1

    def test_has_essential_chips(self):
        """Should have basic damage and healing chips."""
        from leekwars_agent.cli.items_loader import get_chips
        chips = get_chips(max_level=30)
        names = {c["name"] for c in chips.values()}

        # Essential chips
        assert "chip_flash" in names, "Missing chip_flash (AOE damage)"
        assert "chip_cure" in names or "chip_bandage" in names, "Missing healing chip"
