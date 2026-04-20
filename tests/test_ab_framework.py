"""Regression tests for the A/B framework (leek ab)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from leekwars_agent import ab_framework as ab


LEEK_ID = 131321  # IAdonis


# ----- Ledger round-trip ---------------------------------------------------

def test_ledger_round_trip(tmp_path):
    ledger = tmp_path / "ab_deploys.jsonl"
    ai = tmp_path / "fake_ai.leek"
    ai.write_text("// v14 fake")

    rec = ab.append_deploy("v14", ai, LEEK_ID, note="initial", ledger=ledger)
    assert rec.variant == "v14"
    assert rec.leek_id == LEEK_ID
    assert rec.sha1 == ab.sha1_file(ai)

    loaded = ab.load_deploys(ledger)
    assert len(loaded) == 1
    assert loaded[0] == rec


def test_ledger_multiple_appends_sorted(tmp_path):
    ledger = tmp_path / "ab_deploys.jsonl"
    ai = tmp_path / "x.leek"
    ai.write_text("x")
    t0 = datetime(2026, 4, 21, tzinfo=timezone.utc)
    ab.append_deploy("v14", ai, LEEK_ID, ledger=ledger, ts=t0 + timedelta(days=2))
    ab.append_deploy("v15", ai, LEEK_ID, ledger=ledger, ts=t0)
    ab.append_deploy("v14", ai, LEEK_ID, ledger=ledger, ts=t0 + timedelta(days=1))
    loaded = ab.load_deploys(ledger)
    assert [r.ts for r in loaded] == [t0, t0 + timedelta(days=1), t0 + timedelta(days=2)]


# ----- Scheduler -----------------------------------------------------------

def test_schedule_alternates_on_day_parity():
    start = datetime(2026, 4, 21, tzinfo=timezone.utc)
    v_day0 = ab.schedule_today(LEEK_ID, today=start, start_date=start)
    v_day1 = ab.schedule_today(LEEK_ID, today=start + timedelta(days=1), start_date=start)
    v_day2 = ab.schedule_today(LEEK_ID, today=start + timedelta(days=2), start_date=start)
    assert v_day0 == "v14"
    assert v_day1 == "v15"
    assert v_day2 == "v14"


# ----- Attribution ---------------------------------------------------------

def _build_fights_db(path: Path, fights: list[tuple[int, int, int]], leek_id: int):
    """Helper: create a minimal fights_meta.db shape.
    Each fight tuple: (fight_id, fight_date_ts, won_int).
    winner is derived: won=1 -> winner=1, won=0 -> winner=2 (no draws here).
    """
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE fights (
            fight_id INTEGER PRIMARY KEY, json_data TEXT, winner INTEGER,
            fight_type INTEGER, context INTEGER, duration INTEGER,
            team1_levels INTEGER, team2_levels INTEGER,
            fight_date INTEGER, downloaded_at TEXT
        );
        CREATE TABLE leek_observations (
            fight_id INTEGER, leek_id INTEGER, farmer_id INTEGER,
            level INTEGER, talent INTEGER, team INTEGER, won BOOLEAN,
            life INTEGER, strength INTEGER, agility INTEGER, wisdom INTEGER,
            resistance INTEGER, magic INTEGER, science INTEGER, frequency INTEGER,
            tp INTEGER, mp INTEGER, damage_dealt INTEGER, damage_received INTEGER,
            cells_moved INTEGER, weapons_used TEXT, chips_used TEXT,
            turns_alive INTEGER, observed_at TEXT,
            PRIMARY KEY (fight_id, leek_id)
        );
    """)
    for fid, ts, won in fights:
        winner = 1 if won == 1 else (2 if won == 0 else 0)
        conn.execute(
            "INSERT INTO fights (fight_id, json_data, winner, context, fight_date, downloaded_at) "
            "VALUES (?, '{}', ?, 2, ?, 'test')",
            (fid, winner, ts),
        )
        conn.execute(
            "INSERT INTO leek_observations (fight_id, leek_id, team, won, observed_at) "
            "VALUES (?, ?, 1, ?, 'test')",
            (fid, leek_id, won),
        )
    conn.commit()
    conn.close()


def test_attribute_fights_splits_by_deploy_boundary(tmp_path):
    db = tmp_path / "fights.db"
    t0 = datetime(2026, 4, 21, 8, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=1)  # second deploy (v15) next day
    # 2 fights on day 0 under v14, 3 fights on day 1 under v15
    _build_fights_db(db, [
        (1, int((t0 + timedelta(hours=2)).timestamp()), 1),
        (2, int((t0 + timedelta(hours=4)).timestamp()), 0),
        (3, int((t1 + timedelta(hours=1)).timestamp()), 1),
        (4, int((t1 + timedelta(hours=2)).timestamp()), 1),
        (5, int((t1 + timedelta(hours=3)).timestamp()), 0),
    ], LEEK_ID)

    ai = tmp_path / "ai.leek"
    ai.write_text("x")
    deploys = [
        ab.DeployRecord(ts=t0, leek_id=LEEK_ID, variant="v14",
                         ai_file=str(ai), sha1="a"),
        ab.DeployRecord(ts=t1, leek_id=LEEK_ID, variant="v15",
                         ai_file=str(ai), sha1="b"),
    ]
    atts = ab.attribute_fights(LEEK_ID, deploys, fights_db=db)
    assert len(atts) == 5
    assert [a.variant for a in atts] == ["v14", "v14", "v15", "v15", "v15"]


def test_attribute_fights_ignores_pre_start_fights(tmp_path):
    db = tmp_path / "fights.db"
    t0 = datetime(2026, 4, 21, 8, tzinfo=timezone.utc)
    pre = int((t0 - timedelta(days=7)).timestamp())
    post = int((t0 + timedelta(hours=1)).timestamp())
    _build_fights_db(db, [(1, pre, 1), (2, post, 1)], LEEK_ID)
    ai = tmp_path / "ai.leek"; ai.write_text("x")
    deploys = [ab.DeployRecord(ts=t0, leek_id=LEEK_ID, variant="v14",
                                ai_file=str(ai), sha1="a")]
    atts = ab.attribute_fights(LEEK_ID, deploys, fights_db=db)
    assert len(atts) == 1
    assert atts[0].fight_id == 2


# ----- Evaluator -----------------------------------------------------------

def _fake_atts(variant: ab.Variant, wins: int, losses: int, draws: int = 0) -> list[ab.FightAttribution]:
    out = []
    fid = 0
    for _ in range(wins):
        fid += 1
        out.append(ab.FightAttribution(fid, 0, LEEK_ID, variant, True, False))
    for _ in range(losses):
        fid += 1
        out.append(ab.FightAttribution(fid, 0, LEEK_ID, variant, False, False))
    for _ in range(draws):
        fid += 1
        out.append(ab.FightAttribution(fid, 0, LEEK_ID, variant, False, True))
    return out


def test_evaluate_continues_under_min_arm():
    atts = _fake_atts("v14", 30, 20) + _fake_atts("v15", 35, 15)
    r = ab.evaluate(atts)
    assert r.decision == "continue"
    assert r.v14.wr == pytest.approx(0.60)
    assert r.v15.wr == pytest.approx(0.70)


def test_evaluate_stops_significant_when_ci_excludes_zero():
    # Large delta, enough samples: v15 60% vs v14 40% over 150 per arm
    atts = _fake_atts("v14", 60, 90) + _fake_atts("v15", 90, 60)
    r = ab.evaluate(atts)
    assert r.decision == "stop-significant"
    assert r.ci_low > 0 or r.ci_high < 0


def test_evaluate_stops_futile_at_max_arm_no_signal():
    # No real delta: both 50%, 500 per arm -> CI straddles zero
    atts = _fake_atts("v14", 250, 250) + _fake_atts("v15", 250, 250)
    r = ab.evaluate(atts)
    assert r.decision == "stop-futile"
    assert r.ci_low < 0 < r.ci_high


def test_evaluate_ci_shrinks_with_more_samples():
    small = ab.evaluate(_fake_atts("v14", 10, 10) + _fake_atts("v15", 12, 8))
    big = ab.evaluate(_fake_atts("v14", 100, 100) + _fake_atts("v15", 120, 80))
    small_width = small.ci_high - small.ci_low
    big_width = big.ci_high - big.ci_low
    assert big_width < small_width


# ----- Utility -------------------------------------------------------------

def test_current_variant_returns_latest():
    t0 = datetime(2026, 4, 21, tzinfo=timezone.utc)
    deploys = [
        ab.DeployRecord(ts=t0, leek_id=LEEK_ID, variant="v14", ai_file="a", sha1="x"),
        ab.DeployRecord(ts=t0 + timedelta(days=1), leek_id=LEEK_ID,
                         variant="v15", ai_file="a", sha1="y"),
        ab.DeployRecord(ts=t0 + timedelta(days=2), leek_id=99999,
                         variant="v14", ai_file="a", sha1="z"),
    ]
    assert ab.current_variant(LEEK_ID, deploys) == "v15"
    assert ab.current_variant(99999, deploys) == "v14"
    assert ab.current_variant(42, deploys) is None
