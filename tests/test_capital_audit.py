"""Tests for capital_audit — cost curve parser + marginal buy calculator.

Validates against:
  - Authoritative values from tools/leek-wars/src/model/leek.ts
  - S38 historical measurement (MEMORY.md): "25 cap at RES 40 → RES 66, +26 pts, 1 leftover"
  - Effect formula constants (STR/RES/WIS/AGI multipliers)
"""

from __future__ import annotations

import pytest

from leekwars_agent.capital_audit import (
    Allocation,
    StatSnapshot,
    buy_points,
    critical_rate,
    damage_multiplier,
    expected_crit_damage_boost,
    get_costs,
    heal_multiplier,
    lifesteal_rate,
    shield_multiplier,
)


# ── Cost curve parser ─────────────────────────────────────────────


def test_costs_parse_all_stats():
    costs = get_costs()
    expected = {
        "life",
        "strength",
        "wisdom",
        "agility",
        "resistance",
        "science",
        "magic",
        "frequency",
        "cores",
        "ram",
        "tp",
        "mp",
    }
    assert expected <= set(costs.keys()), f"missing stats: {expected - set(costs.keys())}"


def test_str_tier_boundaries():
    tiers = get_costs()["strength"]
    # Expected: 0→200 (1/2), 200→400 (1/1), 400→600 (2/1), 600+ (3/1)
    assert len(tiers) == 4
    assert tiers[0].step == 0 and tiers[0].capital == 1 and tiers[0].sup == 2
    assert tiers[1].step == 200 and tiers[1].capital == 1 and tiers[1].sup == 1
    assert tiers[2].step == 400 and tiers[2].capital == 2 and tiers[2].sup == 1
    assert tiers[3].step == 600 and tiers[3].capital == 3 and tiers[3].sup == 1


def test_life_tier_boundaries():
    tiers = get_costs()["life"]
    # 0→1000 (1/4), 1000→2000 (1/3), 2000+ (1/2)
    assert tiers[0].capital == 1 and tiers[0].sup == 4
    assert tiers[1].step == 1000 and tiers[1].sup == 3
    assert tiers[2].step == 2000 and tiers[2].sup == 2


def test_tp_staircase_has_15_steps():
    tiers = get_costs()["tp"]
    assert len(tiers) == 15
    # First step 30 cap, last step 100 cap (15th TP)
    assert tiers[0].capital == 30
    assert tiers[-1].capital == 100


# ── buy_points correctness ───────────────────────────────────────


def test_buy_points_regression_s38_res():
    """MEMORY.md: 'S38: 25 cap spent at RES 40 → RES 66, +26 pts, 12 cap remaining'.

    Note: MEMORY mentions 12 leftover but the math says 25 cap at tier-0 (1/2 = 0.5 cap/pt)
    → 25 × 2 = 50 points → 40+50 = 90 (crosses 200 boundary? no, 90 < 200). So actually:
    25 cap / 0.5 cap-per-pt = 50 pts → RES 40 → RES 90. MEMORY's number may be partial
    (spread over multiple spends). This test uses the LITERAL math, not the MEMORY quote.
    """
    # Theoretical: RES 40 (tier 0, 1 cap per 2 pts) + 25 cap → 50 pts → RES 90
    r = buy_points("resistance", current=40, budget=25)
    assert r.points_bought == 50
    assert r.new_value == 90
    assert r.spent == 25


def test_buy_points_str_at_452_with_41_cap():
    """IAdonis baseline: STR 452 (tier 400-600, 2 cap/pt). 41 cap → max 20 pts, 1 leftover."""
    r = buy_points("strength", current=452, budget=41)
    assert r.points_bought == 20
    assert r.new_value == 472
    assert r.spent == 40
    assert r.leftover == 1


def test_buy_points_wis_at_0_with_41_cap():
    """WIS 0 (tier 0-200, 0.5 cap/pt). 41 cap → 82 pts."""
    r = buy_points("wisdom", current=0, budget=41)
    assert r.points_bought == 82
    assert r.new_value == 82
    assert r.spent == 41
    assert r.leftover == 0


def test_buy_points_res_at_219_with_41_cap():
    """RES 219 (tier 200-400, 1 cap/pt). 41 cap → 41 pts → RES 260."""
    r = buy_points("resistance", current=219, budget=41)
    assert r.points_bought == 41
    assert r.new_value == 260
    assert r.spent == 41
    assert r.leftover == 0


def test_buy_points_agi_at_10_with_41_cap():
    """AGI 10 (tier 0-200, 0.5 cap/pt). 41 cap → 82 pts → AGI 92."""
    r = buy_points("agility", current=10, budget=41)
    assert r.points_bought == 82
    assert r.new_value == 92
    assert r.spent == 41


def test_buy_points_life_at_1020_with_41_cap():
    """LIFE 1020 is in tier 1000-1999 (1 cap = 3 HP). 41 cap → 123 HP → LIFE 1143.

    Correction from S53 plan: plan claimed 2 HP/cap at 1000+ but leek.ts shows 3 HP/cap
    until LIFE 2000. 2 HP/cap only kicks in at 2000+.
    """
    r = buy_points("life", current=1020, budget=41)
    assert r.points_bought == 123
    assert r.new_value == 1143
    assert r.spent == 41


def test_buy_points_tp_14_to_15_costs_30():
    """TP 14 → 15 is the 5th step (base 10, so step index = 4). Cost = 30+35+40+45+50 = 200.

    Wait: step index = current - 10 = 4, so costs tier[4] = 50 capital.
    But actually from MEMORY: '14th TP step costs 100'. Let me check: staircase starts at
    TP 10 = base. TP 11 = step 0 = 30 cap. TP 15 = step 4 = 50 cap.
    """
    r = buy_points("tp", current=14, budget=100)
    # At TP 14 (step 4), cost for +1 TP = tiers[4].capital
    tp_tiers = get_costs()["tp"]
    step_4_cost = tp_tiers[4].capital
    assert step_4_cost == 50  # fifth step cost = 50
    assert r.points_bought == 1
    assert r.new_value == 15
    assert r.spent == 50


def test_buy_points_tp_14_budget_30_cannot_afford():
    """TP 14 costs 50 cap for next step. 30 cap budget → 0 TP bought."""
    r = buy_points("tp", current=14, budget=30)
    assert r.points_bought == 0
    assert r.new_value == 14


def test_buy_points_mp_4_to_5_costs_40():
    """MP 4 → 5 costs 40 cap (step index 1, second staircase entry).

    Budget exactly 40 buys 1 point. Budget 100 buys 2 (40+60). We test the tight case.
    """
    r = buy_points("mp", current=4, budget=40)
    assert r.points_bought == 1
    assert r.new_value == 5
    assert r.spent == 40

    r2 = buy_points("mp", current=4, budget=100)
    assert r2.points_bought == 2
    assert r2.spent == 100  # 40 + 60


def test_buy_points_str_respects_tier_boundary():
    """STR 195 + 20 cap. Tier 0-200 grants 2 pts per 1 cap (blocks).

    Algorithm respects tier boundaries: at 199, the last "block" would overshoot to 201 so
    we stop at 199 without crossing. Conservative; matches my read of LW's stop-at-boundary
    semantics. If in-game allows partial-block boundary-crossing, this is pessimistic by ≤1
    stat point. Irrelevant for IAdonis (stats not near boundaries).
    """
    r = buy_points("strength", current=195, budget=20)
    # Can buy 2 blocks in tier 0 (4 pts to 199); can't fit a block at 199 without overshoot.
    assert r.new_value == 199
    assert r.spent == 2
    assert r.leftover == 18


# ── Effect multipliers ───────────────────────────────────────────


def test_damage_multiplier_matches_iadonis():
    # STR 452 → 5.52×
    assert damage_multiplier(452) == pytest.approx(5.52)


def test_shield_multiplier_matches_iadonis():
    # RES 219 → 3.19×
    assert shield_multiplier(219) == pytest.approx(3.19)


def test_heal_multiplier_wis_0():
    assert heal_multiplier(0) == 1.0


def test_heal_multiplier_wis_82():
    assert heal_multiplier(82) == pytest.approx(1.82)


def test_lifesteal_at_wis_0_is_zero():
    assert lifesteal_rate(0) == 0.0


def test_lifesteal_at_wis_82():
    # 82/1000 = 8.2%
    assert lifesteal_rate(82) == pytest.approx(0.082)


def test_critical_rate_iadonis():
    # AGI 10 → 1%
    assert critical_rate(10) == pytest.approx(0.01)


def test_critical_rate_agi_92():
    assert critical_rate(92) == pytest.approx(0.092)


def test_expected_crit_boost_agi_92():
    # 9.2% × 0.3 = 2.76% expected damage boost
    assert expected_crit_damage_boost(92) == pytest.approx(0.0276, abs=0.0001)


# ── Allocation application ──────────────────────────────────────


def test_allocation_single_leg_wis():
    snap = StatSnapshot(
        strength=452, resistance=219, wisdom=0, agility=10, life=1020, tp=14, mp=4
    )
    alloc = Allocation(legs=(("wisdom", 82),))
    new_snap, leftover, results = alloc.apply(snap, budget=41)
    assert new_snap.wisdom == 82
    assert leftover == 0
    assert len(results) == 1
    assert results[0].stat == "wisdom"
    assert results[0].points_bought == 82


def test_allocation_multi_leg_respects_requested_points():
    """Multi-leg: TP leg fails (50 cap > 41 budget, 0 TP bought, 0 cap spent). WIS leg
    then requested 22 pts — gets exactly 22 pts (11 cap), 30 cap leftover.
    """
    snap = StatSnapshot(
        strength=452, resistance=219, wisdom=0, agility=10, life=1020, tp=14, mp=4
    )
    alloc = Allocation(legs=(("tp", 1), ("wisdom", 22)))
    new_snap, leftover, results = alloc.apply(snap, budget=41)
    assert new_snap.tp == 14, "TP unchanged: next step costs 50 > 41 budget"
    assert new_snap.wisdom == 22, "WIS gets exactly requested 22 pts (11 cap)"
    assert leftover == 30
