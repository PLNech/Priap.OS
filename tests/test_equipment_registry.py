"""Regression tests for equipment registry parsed from submodule source.

These tests ensure the registry correctly parses chips.ts and weapons.ts,
and that the chip_id ↔ template mappings we rely on everywhere are correct.
"""
import pytest

from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY


class TestChipRegistry:
    def test_loads_chips(self):
        assert len(CHIP_REGISTRY) > 50, "Should parse 50+ chips from chips.ts"

    def test_flame_by_name(self):
        flame = CHIP_REGISTRY.by_name("flame")
        assert flame is not None
        assert flame.id == 5
        assert flame.template == 10
        assert flame.cost == 4
        assert flame.leekscript_constant == "CHIP_FLAME"

    def test_tranquilizer_template_is_57_not_20(self):
        """S31 bug: we assumed Tranquilizer template=20, but it's 57.
        Template 20 is actually Armor. This caused fight log misreading."""
        tranq = CHIP_REGISTRY.by_name("tranquilizer")
        assert tranq is not None
        assert tranq.template == 57
        assert tranq.id == 94

    def test_armor_template_is_20_not_21(self):
        """S31 bug: we assumed Armor template=21, but it's 20."""
        armor = CHIP_REGISTRY.by_name("armor")
        assert armor is not None
        assert armor.template == 20
        assert armor.id == 22

    def test_shield_and_helmet_not_swapped(self):
        """S31 bug: Shield template=18, Helmet template=19 — we had them swapped."""
        shield = CHIP_REGISTRY.by_name("shield")
        helmet = CHIP_REGISTRY.by_name("helmet")
        assert shield.template == 18
        assert helmet.template == 19

    def test_motivation_template(self):
        mot = CHIP_REGISTRY.by_name("motivation")
        assert mot is not None
        assert mot.template == 33
        assert mot.id == 15

    def test_template_lookup_roundtrip(self):
        """by_id and by_template should return the same object."""
        for chip in CHIP_REGISTRY.all():
            assert CHIP_REGISTRY.by_id(chip.id) is chip
            assert CHIP_REGISTRY.by_template(chip.template) is chip
            assert CHIP_REGISTRY.by_name(chip.name) is chip

    def test_our_equipped_chips_all_exist(self):
        """All 6 equipped chips must be in the registry."""
        for name in ["flame", "tranquilizer", "motivation", "helmet", "shield", "armor"]:
            assert CHIP_REGISTRY.by_name(name) is not None, f"{name} not found"


class TestWeaponRegistry:
    def test_loads_weapons(self):
        assert len(WEAPON_REGISTRY) > 10, "Should parse 10+ weapons from weapons.ts"

    def test_b_laser(self):
        bl = WEAPON_REGISTRY.by_name("b_laser")
        assert bl is not None
        assert bl.id == 13
        assert bl.template == 13
        assert bl.item == 60
        assert bl.cost == 5
        assert len(bl.effects) == 2
        # First effect: damage 50±10
        assert bl.effects[0].type == 1
        assert bl.effects[0].value1 == 50
        # Second effect: heal 50±10
        assert bl.effects[1].type == 2
        assert bl.effects[1].value1 == 50

    def test_laser(self):
        laser = WEAPON_REGISTRY.by_name("laser")
        assert laser is not None
        assert laser.template == 6
        assert laser.cost == 6

    def test_magnum(self):
        magnum = WEAPON_REGISTRY.by_name("magnum")
        assert magnum is not None
        assert magnum.template == 5
        assert magnum.cost == 5

    def test_our_equipped_weapons_all_exist(self):
        for name in ["b_laser", "laser", "magnum"]:
            assert WEAPON_REGISTRY.by_name(name) is not None, f"{name} not found"

    def test_template_lookup_roundtrip(self):
        for weapon in WEAPON_REGISTRY.all():
            assert WEAPON_REGISTRY.by_id(weapon.id) is weapon
            assert WEAPON_REGISTRY.by_template(weapon.template) is weapon
