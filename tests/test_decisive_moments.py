"""Regression tests for the decisive-moment detector."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from leekwars_agent import decisive_moments as dm


def _synthetic_fight(
    fight_id: int,
    winner_team: int,
    hp_a: int,
    hp_b: int,
    actions: list[list],
) -> dict:
    """Minimal fight JSON for tests. A=team1 eid=0, B=team2 eid=1."""
    return {
        "id": fight_id,
        "winner": winner_team,
        "status": "finished",
        "data": {
            "leeks": [
                {"id": 0, "team": 1, "farmer": 1, "name": "A", "life": hp_a},
                {"id": 1, "team": 2, "farmer": 2, "name": "B", "life": hp_b},
            ],
            "map": {},
            "actions": actions,
        },
    }


def test_hp_crossover_in_comeback():
    # B leads early, then loses HP fast in turn 3 and A wins by turn 5
    actions = [
        [6, 0],                       # NEW_TURN 0
        [7, 0], [101, 0, 100], [8, 0, 0, 0],   # A loses 100 HP
        [7, 1], [8, 1, 0, 0],
        [6, 1],                       # NEW_TURN 1 -- after snapshot: A=900 B=1000
        [7, 0], [101, 0, 50], [8, 0, 0, 0],    # A loses more: A=850 B=1000
        [7, 1], [8, 1, 0, 0],
        [6, 2],
        [7, 0], [101, 1, 400], [8, 0, 0, 0],   # A hits B hard: B=600, A=850
        [7, 1], [8, 1, 0, 0],
        [6, 3],
        [7, 0], [101, 1, 600], [8, 0, 0, 0],   # B down to 0
        [5, 1],                                # PLAYER_DEAD B
    ]
    fight = _synthetic_fight(42, winner_team=1, hp_a=1000, hp_b=1000, actions=actions)
    trace = dm.build_hp_trace(fight)
    assert trace is not None
    moment = dm.detect_hp_crossover(42, trace)
    assert moment is not None
    assert moment.moment_type == "hp_crossover"
    # At turn 2, B just dropped below A (A=850%, B=600). Before that A was lower.
    assert moment.turn == 2
    assert moment.actor == 0  # winner A
    assert moment.victim == 1


def test_hp_crossover_none_on_wire_to_wire_win():
    # A wins and never loses the HP lead
    actions = [
        [6, 0],
        [7, 0], [101, 1, 300], [8, 0, 0, 0],   # A damages B: A=1000, B=700
        [7, 1], [8, 1, 0, 0],
        [6, 1],
        [7, 0], [101, 1, 700], [8, 0, 0, 0],
        [5, 1],
    ]
    fight = _synthetic_fight(43, winner_team=1, hp_a=1000, hp_b=1000, actions=actions)
    trace = dm.build_hp_trace(fight)
    moment = dm.detect_hp_crossover(43, trace)
    assert moment is None  # wire-to-wire, no momentum flip


def test_hp_crossover_none_when_loser_never_led():
    # Both at 1000/1000 at turn 0 (tie), then winner deals damage.
    # Loser was never *strictly* ahead -> no momentum flip -> no crossover.
    actions = [
        [6, 0],
        [7, 0], [8, 0, 0, 0],                 # turn 0: tie (both 1000)
        [7, 1], [8, 1, 0, 0],
        [6, 1],
        [7, 0], [101, 1, 500], [8, 0, 0, 0],  # turn 1: winner ahead (B=500)
        [7, 1], [8, 1, 0, 0],
        [6, 2],
        [7, 0], [101, 1, 500], [8, 0, 0, 0],
        [5, 1],
    ]
    fight = _synthetic_fight(46, winner_team=1, hp_a=1000, hp_b=1000, actions=actions)
    trace = dm.build_hp_trace(fight)
    moment = dm.detect_hp_crossover(46, trace)
    assert moment is None


def test_hp_crossover_none_on_draw():
    actions = [[6, 0], [7, 0], [8, 0, 0, 0]]
    fight = _synthetic_fight(44, winner_team=0, hp_a=1000, hp_b=1000, actions=actions)
    trace = dm.build_hp_trace(fight)
    assert trace is not None
    assert trace.winner_entity is None
    moment = dm.detect_hp_crossover(44, trace)
    assert moment is None


def test_hp_trace_skips_non_1v1():
    # 3 entities -> out of scope
    data = {
        "leeks": [
            {"id": 0, "team": 1, "farmer": 1, "name": "A", "life": 1000},
            {"id": 1, "team": 2, "farmer": 2, "name": "B", "life": 1000},
            {"id": 2, "team": 2, "farmer": 3, "name": "C", "life": 1000},
        ],
        "map": {}, "actions": [],
    }
    trace = dm.build_hp_trace({"winner": 1, "data": data})
    assert trace is None


def test_detect_moments_filters_empty_cases():
    actions = [[6, 0], [7, 0], [8, 0, 0, 0]]
    fight = _synthetic_fight(45, winner_team=1, hp_a=1000, hp_b=1000, actions=actions)
    moments = dm.detect_moments(45, fight)
    # A never damaged B, so this is a draw-like trace with winner=team1 declared
    # but no crossover (both at 1000 the whole fight). Expect empty.
    assert moments == []


# ----- Storage ------------------------------------------------------------

def test_save_and_query_moments(tmp_path):
    db = tmp_path / "meta.db"
    # bootstrap the fights table since ensure_schema only creates moments
    conn = sqlite3.connect(db); conn.executescript("""
        CREATE TABLE fights (fight_id INTEGER PRIMARY KEY, json_data TEXT);
    """); conn.commit(); conn.close()

    m = dm.DecisiveMoment(
        fight_id=1, turn=3, moment_type="hp_crossover",
        actor=0, victim=1, details={"x": 1},
    )
    n = dm.save_moments([m], db=db)
    assert n == 1

    # Idempotent: saving the same (fight_id, turn, moment_type) overwrites
    m2 = dm.DecisiveMoment(
        fight_id=1, turn=3, moment_type="hp_crossover",
        actor=0, victim=1, details={"x": 2},
    )
    n2 = dm.save_moments([m2], db=db)
    assert n2 == 1

    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT details FROM decisive_moments WHERE fight_id=1"
    ).fetchall()
    conn.close()
    assert len(rows) == 1
    assert json.loads(rows[0][0])["x"] == 2


def test_iter_candidate_fights(tmp_path):
    db = tmp_path / "meta.db"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE fights (
            fight_id INTEGER PRIMARY KEY, json_data TEXT NOT NULL,
            winner INTEGER, fight_type INTEGER, context INTEGER,
            duration INTEGER, team1_levels INTEGER, team2_levels INTEGER,
            fight_date INTEGER, downloaded_at TEXT
        );
    """)
    sample = json.dumps({"id": 1, "winner": 1, "data": {"leeks": [], "actions": []}})
    conn.execute(
        "INSERT INTO fights VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (100, sample, 1, 0, 2, 5, 100, 100, 1775764852, "now"),
    )
    conn.execute(
        "INSERT INTO fights VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (101, sample, 1, 0, 3, 5, 100, 100, 1775764853, "now"),  # tournament
    )
    conn.commit(); conn.close()

    got = list(dm.iter_candidate_fights(db=db, context=2))
    assert [fid for fid, _ in got] == [100]
