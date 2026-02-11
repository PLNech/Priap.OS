"""Tests for fight_parser.py — action log extraction and combat stats.

Validates:
- extract_combat_stats() correctly parses fight JSON action logs
- Entity ID → Leek ID mapping via (team, farmer) matching
- Damage dealt/received attribution during active turns
- Chip/weapon tracking per entity
- Edge cases: empty fights, summons, multi-leek teams
- Chip ID triple-mapping (API template ≠ chips.json key ≠ action log ID)
"""

import json
import pytest
from pathlib import Path

from leekwars_agent.fight_parser import (
    ActionType,
    extract_combat_stats,
    parse_action,
    parse_fight,
)


# =============================================================================
# Fixtures: synthetic fight data
# =============================================================================

def _make_fight(
    leeks1: list[dict],
    leeks2: list[dict],
    data_leeks: list[dict],
    actions: list[list],
    winner: int = 1,
) -> dict:
    """Build a minimal fight JSON for testing."""
    return {
        "id": 99999,
        "winner": winner,
        "leeks1": leeks1,
        "leeks2": leeks2,
        "data": {
            "leeks": data_leeks,
            "actions": actions,
        },
    }


LEEK_A = {"id": 131321, "name": "IAdonis", "farmer": 124831}
LEEK_B = {"id": 99999, "name": "Enemy", "farmer": 55555}

ENTITY_A = {
    "id": 0, "name": "IAdonis", "team": 1, "farmer": 124831,
    "life": 319, "strength": 452, "agility": 10, "summon": False,
}
ENTITY_B = {
    "id": 1, "name": "Enemy", "team": 2, "farmer": 55555,
    "life": 400, "strength": 200, "agility": 30, "summon": False,
}


@pytest.fixture
def simple_fight():
    """A 2-turn fight: A attacks B, B heals, A kills B."""
    actions = [
        [0],                          # START_FIGHT
        [6, 1],                       # NEW_TURN 1
        [7, 0],                       # LEEK_TURN entity 0 (IAdonis)
        [10, 0, 200, [150, 200]],     # MOVE_TO: A moves 2 cells
        [12, 10, 43, 1],              # USE_CHIP 10 (Flame template) at cell 43
        [101, 1, 80, 3],              # LOST_LIFE: entity 1 lost 80 HP
        [16, 5, 43],                  # USE_WEAPON 5 at cell 43
        [101, 1, 120, 4],             # LOST_LIFE: entity 1 lost 120 HP
        [8, 0, 3, 1],                 # END_TURN
        [7, 1],                       # LEEK_TURN entity 1 (Enemy)
        [12, 2, 50, 1],              # USE_CHIP 2 (Cure template)
        [103, 1, 50],                 # HEAL: entity 1 healed 50
        [10, 1, 180, [190, 180]],     # MOVE_TO: B moves 2 cells
        [8, 1, 4, 2],                 # END_TURN
        [6, 2],                       # NEW_TURN 2
        [7, 0],                       # LEEK_TURN entity 0
        [16, 5, 43],                  # USE_WEAPON 5
        [101, 1, 150, 4],             # LOST_LIFE: entity 1 lost 150 HP
        [5, 1],                       # PLAYER_DEAD: entity 1
        [4],                          # END_FIGHT
    ]

    return _make_fight(
        leeks1=[LEEK_A], leeks2=[LEEK_B],
        data_leeks=[ENTITY_A, ENTITY_B],
        actions=actions, winner=1,
    )


# =============================================================================
# Core extraction tests
# =============================================================================

class TestExtractCombatStats:
    """Test extract_combat_stats() on synthetic fight data."""

    def test_damage_dealt_and_received(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # IAdonis dealt 80 + 120 + 150 = 350 damage to Enemy
        assert stats[131321]["damage_dealt"] == 350
        assert stats[131321]["damage_received"] == 0
        # Enemy received 350, dealt 0
        assert stats[99999]["damage_received"] == 350
        assert stats[99999]["damage_dealt"] == 0

    def test_healing_done(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # IAdonis didn't heal
        assert stats[131321]["healing_done"] == 0
        # Enemy healed 50
        assert stats[99999]["healing_done"] == 50

    def test_chips_used(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # IAdonis used chip template 10 (Flame)
        assert 10 in stats[131321]["chips_used"]
        # Enemy used chip template 2 (Cure)
        assert 2 in stats[99999]["chips_used"]

    def test_weapons_used(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # IAdonis used weapon 5
        assert 5 in stats[131321]["weapons_used"]
        # Enemy didn't use weapons
        assert stats[99999]["weapons_used"] == []

    def test_turns_alive(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # IAdonis had 2 LEEK_TURN events
        assert stats[131321]["turns_alive"] == 2
        # Enemy had 1 LEEK_TURN event
        assert stats[99999]["turns_alive"] == 1

    def test_cells_moved(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # IAdonis moved: path [150, 200] = 2 cells
        assert stats[131321]["cells_moved"] == 2
        # Enemy moved: path [190, 180] = 2 cells
        assert stats[99999]["cells_moved"] == 2

    def test_death_turn(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # IAdonis survived
        assert stats[131321]["death_turn"] == 0
        # Enemy died on turn 2
        assert stats[99999]["death_turn"] == 2

    def test_ai_errors(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        assert stats[131321]["ai_errors"] == 0
        assert stats[99999]["ai_errors"] == 0

    def test_ai_error_tracking(self):
        """AI errors during a leek's turn are attributed to that leek."""
        actions = [
            [6, 1], [7, 0],
            [1000, 0, 113],        # ERROR during entity 0's turn
            [1002, 0, "too_much_ops"],  # AI_ERROR
            [8, 0, 10, 3],
        ]
        fight = _make_fight(
            leeks1=[LEEK_A], leeks2=[LEEK_B],
            data_leeks=[ENTITY_A, ENTITY_B],
            actions=actions,
        )
        stats = extract_combat_stats(fight)
        assert stats[131321]["ai_errors"] == 2
        assert stats[99999]["ai_errors"] == 0


class TestEntityMapping:
    """Test the entity_id → leek_id mapping logic."""

    def test_basic_mapping(self, simple_fight):
        stats = extract_combat_stats(simple_fight)
        # Should have exactly 2 leek entries
        assert set(stats.keys()) == {131321, 99999}

    def test_summons_excluded(self):
        """Summon entities should not appear in results."""
        data_leeks = [
            ENTITY_A,
            ENTITY_B,
            {"id": 2, "name": "Summon", "team": 1, "farmer": 124831, "summon": True},
        ]
        fight = _make_fight(
            leeks1=[LEEK_A], leeks2=[LEEK_B],
            data_leeks=data_leeks, actions=[[6, 1]],
        )
        stats = extract_combat_stats(fight)
        assert set(stats.keys()) == {131321, 99999}

    def test_empty_fight(self):
        """Fight with no actions returns empty stats."""
        fight = _make_fight(
            leeks1=[LEEK_A], leeks2=[LEEK_B],
            data_leeks=[ENTITY_A, ENTITY_B],
            actions=[],
        )
        stats = extract_combat_stats(fight)
        for leek_id, s in stats.items():
            assert s["damage_dealt"] == 0
            assert s["turns_alive"] == 0

    def test_no_leeks_data(self):
        """Fight with no data.leeks returns empty dict."""
        fight = {"id": 1, "data": {"actions": [[6, 1]]}}
        stats = extract_combat_stats(fight)
        assert stats == {}

    def test_fight_wrapper(self):
        """Handle both {fight: {...}} and direct dict formats."""
        inner = _make_fight(
            leeks1=[LEEK_A], leeks2=[LEEK_B],
            data_leeks=[ENTITY_A, ENTITY_B],
            actions=[[6, 1], [7, 0], [8, 0, 10, 3]],
        )
        wrapped = {"fight": inner}
        stats = extract_combat_stats(wrapped)
        assert 131321 in stats


class TestPoisonDamage:
    """Test poison damage is included in damage_received."""

    def test_poison_adds_to_received(self):
        actions = [
            [6, 1], [7, 0],
            [110, 1, 25, 3],   # POISON_DAMAGE: entity 1 takes 25
            [8, 0, 10, 3],
        ]
        fight = _make_fight(
            leeks1=[LEEK_A], leeks2=[LEEK_B],
            data_leeks=[ENTITY_A, ENTITY_B],
            actions=actions,
        )
        stats = extract_combat_stats(fight)
        assert stats[99999]["damage_received"] == 25


# =============================================================================
# Real fight validation (uses stored DB data)
# =============================================================================

class TestRealFightValidation:
    """Validate extraction against actual stored fights.

    These tests use the real fights_meta.db. They serve as integration tests
    and regression guards for the extraction logic.
    """

    DB_PATH = Path("data/fights_meta.db")

    @pytest.fixture
    def db_fight(self):
        """Load a real fight from the DB."""
        if not self.DB_PATH.exists():
            pytest.skip("fights_meta.db not available")

        import sqlite3
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT f.fight_id, f.json_data, f.winner
            FROM fights f
            JOIN leek_observations lo ON f.fight_id = lo.fight_id
            WHERE lo.leek_id = 131321 AND lo.level >= 60
            ORDER BY f.fight_id DESC LIMIT 1
            """
        ).fetchone()
        conn.close()

        if not row:
            pytest.skip("No IAdonis fights found at L60+")

        return json.loads(row["json_data"]), row["fight_id"], row["winner"]

    def test_real_fight_has_stats(self, db_fight):
        """A real fight should produce non-trivial stats."""
        fight_json, fight_id, winner = db_fight
        stats = extract_combat_stats(fight_json)

        assert len(stats) >= 2, "Should have at least 2 leeks"
        assert 131321 in stats, "IAdonis should be in stats"

        # At least one side should have dealt damage
        total_dmg = sum(s["damage_dealt"] for s in stats.values())
        assert total_dmg > 0, f"Fight {fight_id} should have damage"

    def test_real_fight_damage_balance(self, db_fight):
        """Damage dealt by one side ≈ damage received by the other."""
        fight_json, fight_id, _ = db_fight
        stats = extract_combat_stats(fight_json)

        leek_ids = list(stats.keys())
        if len(leek_ids) == 2:
            a, b = leek_ids
            # A's damage dealt should equal B's damage received (approx,
            # some damage sources like poison may cause slight mismatches)
            assert abs(stats[a]["damage_dealt"] - stats[b]["damage_received"]) < 50
            assert abs(stats[b]["damage_dealt"] - stats[a]["damage_received"]) < 50

    def test_winner_usually_dealt_more(self, db_fight):
        """The winner typically dealt more damage than they received."""
        fight_json, fight_id, winner = db_fight
        stats = extract_combat_stats(fight_json)

        # Find winner's leek_id
        fight = fight_json.get("fight", fight_json)
        winner_leeks = fight.get(f"leeks{winner}", [])
        if winner_leeks:
            winner_id = winner_leeks[0]["id"]
            if winner_id in stats:
                s = stats[winner_id]
                # Not guaranteed but expected in most fights
                assert s["damage_dealt"] >= s["damage_received"] * 0.5, (
                    f"Winner {winner_id} dealt {s['damage_dealt']} but took {s['damage_received']}"
                )


# =============================================================================
# Chip ID mapping regression tests
# =============================================================================

class TestChipIdMapping:
    """Verify the triple-ID system for chips.

    Three different ID systems exist:
    1. chips.json KEY (e.g., 5) — used in API leek equipment as "template"
    2. chips.json TEMPLATE field (e.g., 10) — used in fight action log
    3. Instance ID (e.g., 2435820) — used in API leek equipment as "id"

    The action log (USE_CHIP) uses system #2 (chips.json template field).
    The API leek equipment uses system #1 (chips.json key).
    """

    CHIPS_PATH = Path("data/chips.json")

    @pytest.fixture
    def chips_data(self):
        if not self.CHIPS_PATH.exists():
            pytest.skip("chips.json not available")
        with open(self.CHIPS_PATH) as f:
            data = json.load(f)
        return data.get("chips", data)

    # Our equipped chips: API template → expected name
    EQUIPPED_API_TEMPLATES = {
        8: "protein",
        15: "motivation",
        4: "cure",
        14: "leather_boots",
        6: "flash",
        5: "flame",
    }

    def test_api_template_to_name(self, chips_data):
        """API template IDs should map to correct chip names."""
        for api_template, expected_name in self.EQUIPPED_API_TEMPLATES.items():
            chip = chips_data.get(str(api_template))
            assert chip is not None, f"chips.json should have key {api_template}"
            assert chip["name"] == expected_name, (
                f"chips.json[{api_template}] should be {expected_name}, got {chip['name']}"
            )

    # Action log template → expected chip name
    ACTION_LOG_TEMPLATES = {
        10: "flame",      # Flame in action log = template 10
        7: "flash",       # Flash in action log = template 7
        24: "protein",    # Protein in action log = template 24
        33: "motivation", # Motivation in action log = template 33
        2: "cure",        # Cure in action log = template 2
        30: "leather_boots",  # Boots in action log = template 30
    }

    def test_action_log_template_to_name(self, chips_data):
        """Action log chip IDs should decode to correct names via template field."""
        # Build reverse lookup: template → name
        template_to_name = {}
        for key, chip in chips_data.items():
            template_to_name[chip.get("template")] = chip.get("name")

        for action_id, expected_name in self.ACTION_LOG_TEMPLATES.items():
            assert action_id in template_to_name, (
                f"Action log chip {action_id} should exist as a template value"
            )
            assert template_to_name[action_id] == expected_name, (
                f"Action log chip {action_id} should be {expected_name}, "
                f"got {template_to_name[action_id]}"
            )

    def test_api_to_action_roundtrip(self, chips_data):
        """API template → action log template should be consistent."""
        for api_template, expected_name in self.EQUIPPED_API_TEMPLATES.items():
            chip = chips_data[str(api_template)]
            action_template = chip["template"]
            # The action log template should map back to the same name
            assert self.ACTION_LOG_TEMPLATES.get(action_template) == expected_name, (
                f"API template {api_template} ({expected_name}) → "
                f"action template {action_template} should roundtrip"
            )


# =============================================================================
# Weapon ID mapping regression tests
# =============================================================================

class TestWeaponIdMapping:
    """Verify weapon ID mapping between API and data files.

    Weapons use a DIFFERENT mapping than chips:
    - API leek equipment "template" → weapons.json "item" field (NOT the key)
    - Fight action log → weapons.json "template" field

    Example: Magnum → API template 45, weapons.json key 5 (item=45), action template 5
    """

    WEAPONS_PATH = Path("data/weapons.json")

    @pytest.fixture
    def weapons_data(self):
        if not self.WEAPONS_PATH.exists():
            pytest.skip("weapons.json not available")
        with open(self.WEAPONS_PATH) as f:
            data = json.load(f)
        return data.get("weapons", data)

    # API template (item field) → expected weapon name
    EQUIPPED_API_TEMPLATES = {
        45: "magnum",
        42: "laser",
    }

    # Peer weapons for validation
    PEER_API_TEMPLATES = {
        37: "pistol",
        39: "double_gun",
        40: "destroyer",
        41: "shotgun",
        108: "broadsword",
    }

    def test_our_weapons_by_item(self, weapons_data):
        """Our weapon API templates should decode via item field."""
        item_to_name = {
            w["item"]: w["name"]
            for w in weapons_data.values()
            if w.get("item")
        }
        for api_template, expected_name in self.EQUIPPED_API_TEMPLATES.items():
            assert api_template in item_to_name, (
                f"No weapon with item={api_template}"
            )
            assert item_to_name[api_template] == expected_name, (
                f"Weapon item {api_template} should be {expected_name}, "
                f"got {item_to_name[api_template]}"
            )

    def test_peer_weapons_by_item(self, weapons_data):
        """Peer weapon API templates should also decode via item field."""
        item_to_name = {
            w["item"]: w["name"]
            for w in weapons_data.values()
            if w.get("item")
        }
        for api_template, expected_name in self.PEER_API_TEMPLATES.items():
            assert api_template in item_to_name, (
                f"No weapon with item={api_template}"
            )
            assert item_to_name[api_template] == expected_name, (
                f"Weapon item {api_template} should be {expected_name}, "
                f"got {item_to_name[api_template]}"
            )

    def test_weapon_action_log_format(self, weapons_data):
        """Weapon IDs in fight action log should use weapons.json template field."""
        # Magnum: key=5, template=5, item=45
        magnum = weapons_data.get("5")
        assert magnum is not None, "Magnum should be at key 5"
        assert magnum["name"] == "magnum"
        assert magnum["template"] == 5, "Magnum action log template should be 5"
        assert magnum["item"] == 45, "Magnum API item should be 45"

        # Laser: key=6, template=6, item=42
        laser = weapons_data.get("6")
        assert laser is not None, "Laser should be at key 6"
        assert laser["name"] == "laser"
        assert laser["template"] == 6, "Laser action log template should be 6"
        assert laser["item"] == 42, "Laser API item should be 42"


# =============================================================================
# Backfill integrity tests
# =============================================================================

class TestBackfillIntegrity:
    """Verify that backfilled data is consistent and complete."""

    DB_PATH = Path("data/fights_meta.db")

    @pytest.fixture
    def db(self):
        if not self.DB_PATH.exists():
            pytest.skip("fights_meta.db not available")
        import sqlite3
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()

    def test_backfill_coverage(self, db):
        """At least 50% of observations should have damage data."""
        total = db.execute("SELECT COUNT(*) FROM leek_observations").fetchone()[0]
        with_damage = db.execute(
            "SELECT COUNT(*) FROM leek_observations WHERE damage_dealt > 0 OR damage_received > 0"
        ).fetchone()[0]
        ratio = with_damage / total if total > 0 else 0
        assert ratio > 0.5, f"Only {ratio:.1%} of observations have damage data"

    def test_iadonis_has_fights(self, db):
        """IAdonis should have both wins and losses with damage data."""
        wins = db.execute(
            "SELECT COUNT(*) FROM leek_observations WHERE leek_id=131321 AND won=1 AND damage_dealt > 0"
        ).fetchone()[0]
        losses = db.execute(
            "SELECT COUNT(*) FROM leek_observations WHERE leek_id=131321 AND won=0 AND damage_received > 0"
        ).fetchone()[0]
        assert wins > 100, f"Expected 100+ wins with damage data, got {wins}"
        assert losses > 100, f"Expected 100+ losses with damage data, got {losses}"

    def test_winners_deal_more_damage_on_average(self, db):
        """Statistical sanity: winners should deal more damage on average."""
        row = db.execute("""
            SELECT
                AVG(CASE WHEN won=1 THEN damage_dealt END) as win_dmg,
                AVG(CASE WHEN won=0 THEN damage_dealt END) as loss_dmg
            FROM leek_observations
            WHERE leek_id=131321 AND damage_dealt > 0
        """).fetchone()
        assert row["win_dmg"] > row["loss_dmg"], (
            f"Winners should deal more: win={row['win_dmg']:.0f} vs loss={row['loss_dmg']:.0f}"
        )
