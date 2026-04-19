"""Regression tests for FightScraper._enhance_leek / _build_entity_lookup.

Bug #127: the old lookup key `(team, farmer)` gated on `team in (1, 2)`,
which silently dropped every tournament entity (teams 4-9) and left
~44% of leek_observations rows with NULL stats.

The current matcher keys on `(farmer, name)` — unique within any fight
and stable across duel/team/tournament/BR formats.
"""
from __future__ import annotations

from leekwars_agent.scraper.scraper import FightScraper


def _mk_entity(entity_id, team, farmer, name, strength=100, life=500):
    return {
        "id": entity_id,
        "team": team,
        "farmer": farmer,
        "name": name,
        "summon": False,
        "strength": strength,
        "life": life,
        "agility": 10,
        "wisdom": 20,
        "resistance": 30,
        "magic": 0,
        "science": 0,
        "frequency": 100,
        "tp": 14,
        "mp": 4,
    }


def test_duel_stats_merge():
    leeks_data = [
        _mk_entity(0, 1, 111, "Alice", strength=200),
        _mk_entity(1, 2, 222, "Bob", strength=300),
    ]
    lookup = FightScraper._build_entity_lookup(leeks_data)
    assert len(lookup) == 2

    alice_pub = {"id": 1001, "farmer": 111, "name": "Alice", "level": 50}
    merged, eid = FightScraper._enhance_leek(alice_pub, team=1, entity_lookup=lookup)
    assert merged["strength"] == 200
    assert merged["life"] == 500
    assert eid == 0


def test_tournament_stats_merge_regression():
    """Tournament entities carry team 4-9; the old lookup rejected them."""
    leeks_data = [
        _mk_entity(0, 5, 111, "Alice", strength=200),
        _mk_entity(1, 7, 222, "Bob", strength=300),
        _mk_entity(2, 9, 333, "Carol", strength=400),
    ]
    lookup = FightScraper._build_entity_lookup(leeks_data)
    assert len(lookup) == 3, "tournament entities must survive the lookup build"

    alice_pub = {"id": 1001, "farmer": 111, "name": "Alice", "level": 50}
    merged, _ = FightScraper._enhance_leek(alice_pub, team=1, entity_lookup=lookup)
    assert merged["strength"] == 200, "tournament stats must merge (regression #127)"


def test_summons_excluded():
    leeks_data = [
        _mk_entity(0, 1, 111, "Alice"),
        {"id": 5, "team": 1, "farmer": 111, "name": "Bulb", "summon": True, "strength": 0},
    ]
    lookup = FightScraper._build_entity_lookup(leeks_data)
    assert len(lookup) == 1


def test_unknown_leek_falls_through_without_merge():
    leeks_data = [_mk_entity(0, 1, 111, "Alice", strength=200)]
    lookup = FightScraper._build_entity_lookup(leeks_data)

    stranger = {"id": 9999, "farmer": 777, "name": "Nobody", "level": 10}
    merged, eid = FightScraper._enhance_leek(stranger, team=1, entity_lookup=lookup)
    assert "strength" not in merged
    assert eid is None
