"""Capital Allocation Audit orchestrator (Task #0403, S53).

Runs the full analysis:
  Phase 1 — Theory (marginal ROI per stat)
  Phase 2 — Empirics (peer distribution from leek_observations)
  Phase 3 — Synthesis (candidate allocations + sim validation)

Writes:
  - docs/research/capital_audit_s53.md  (full memo — LONG-TERM)
  - data/research/peer_scout_s53.json   (raw peer data — LONG-TERM)

Does NOT call `leek build spend`. Execution is Phase 4, manual, with user approval.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import median, quantiles

from leekwars_agent.capital_audit import (
    Allocation,
    StatSnapshot,
    buy_points,
    critical_rate,
    damage_multiplier,
    expected_crit_damage_boost,
    heal_multiplier,
    lifesteal_rate,
    shield_multiplier,
)

# IAdonis baseline (from live API 2026-04-20)
BASELINE = StatSnapshot(
    strength=452,
    resistance=219,
    wisdom=0,
    agility=10,
    life=1020,
    tp=14,
    mp=4,
    frequency=100,
    science=0,
    magic=0,
)
BUDGET = 41

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs" / "research"
DATA = REPO / "data" / "research"
DB_PATH = REPO / "data" / "fights_meta.db"


# ── Phase 1: Theory ──────────────────────────────────────────────


def run_theory() -> dict:
    """Compute every single-stat and mixed allocation for BUDGET cap."""
    single_legs = [
        ("strength", BUDGET),
        ("resistance", BUDGET),
        ("wisdom", BUDGET),
        ("agility", BUDGET),
        ("life", BUDGET),
        ("frequency", BUDGET),
    ]
    singles = []
    for stat, budget in single_legs:
        current = getattr(BASELINE, "life" if stat == "life" else stat)
        r = buy_points(stat, current, budget)
        singles.append({
            "stat": stat,
            "current": current,
            "spent": r.spent,
            "leftover": r.leftover,
            "points_bought": r.points_bought,
            "new_value": r.new_value,
        })

    # Staircase: TP 14→15 costs 50 (over budget). MP 4→5 costs 40, leaves 1.
    mp_r = buy_points("mp", BASELINE.mp, BUDGET)
    tp_r = buy_points("tp", BASELINE.tp, BUDGET)

    # Derived effect deltas
    def with_str(new_str: int) -> dict:
        return {
            "dmg_mult": round(damage_multiplier(new_str), 3),
            "dmg_mult_delta_pct": round(
                (damage_multiplier(new_str) / damage_multiplier(BASELINE.strength) - 1) * 100, 2
            ),
        }

    def with_res(new_res: int) -> dict:
        return {
            "shield_mult": round(shield_multiplier(new_res), 3),
            "shield_mult_delta_pct": round(
                (shield_multiplier(new_res) / shield_multiplier(BASELINE.resistance) - 1) * 100, 2
            ),
            "shield_stack_abs": round(192 * shield_multiplier(new_res) / shield_multiplier(219), 1),
        }

    def with_wis(new_wis: int) -> dict:
        return {
            "heal_mult": round(heal_multiplier(new_wis), 3),
            "lifesteal_rate_pct": round(lifesteal_rate(new_wis) * 100, 2),
        }

    def with_agi(new_agi: int) -> dict:
        return {
            "crit_rate_pct": round(critical_rate(new_agi) * 100, 2),
            "exp_dmg_boost_pct": round(expected_crit_damage_boost(new_agi) * 100, 3),
        }

    # Build the candidate table
    candidates = {
        "all_strength": {
            "desc": f"+{singles[0]['points_bought']} STR → {singles[0]['new_value']}",
            "spent": singles[0]["spent"],
            "leftover": singles[0]["leftover"],
            "effects": with_str(singles[0]["new_value"]),
        },
        "all_resistance": {
            "desc": f"+{singles[1]['points_bought']} RES → {singles[1]['new_value']}",
            "spent": singles[1]["spent"],
            "leftover": singles[1]["leftover"],
            "effects": with_res(singles[1]["new_value"]),
        },
        "all_wisdom": {
            "desc": f"+{singles[2]['points_bought']} WIS → {singles[2]['new_value']}",
            "spent": singles[2]["spent"],
            "leftover": singles[2]["leftover"],
            "effects": with_wis(singles[2]["new_value"]),
        },
        "all_agility": {
            "desc": f"+{singles[3]['points_bought']} AGI → {singles[3]['new_value']}",
            "spent": singles[3]["spent"],
            "leftover": singles[3]["leftover"],
            "effects": with_agi(singles[3]["new_value"]),
        },
        "all_life": {
            "desc": f"+{singles[4]['points_bought']} HP → {singles[4]['new_value']}",
            "spent": singles[4]["spent"],
            "leftover": singles[4]["leftover"],
            "effects": {
                "hp_total": singles[4]["new_value"],
                "hp_delta_pct": round(
                    (singles[4]["new_value"] / BASELINE.life - 1) * 100, 2
                ),
            },
        },
        "mp_jump": {
            "desc": f"MP {BASELINE.mp}→{mp_r.new_value} (40 cap) + 1 cap leftover",
            "spent": mp_r.spent,
            "leftover": mp_r.leftover,
            "effects": {"mp": mp_r.new_value, "note": "positioning lever only"},
        },
        "tp_jump": {
            "desc": f"TP {BASELINE.tp}→{tp_r.new_value} — {'SUCCESS' if tp_r.points_bought else 'UNAFFORDABLE (50 cap > 41 budget)'}",
            "spent": tp_r.spent,
            "leftover": tp_r.leftover,
            "effects": {"tp": tp_r.new_value, "affordable": tp_r.points_bought > 0},
        },
    }

    # Mixed allocations
    # Mix A: MP+1 (40 cap) + RES +1 (1 cap)
    alloc_a = Allocation(legs=(("mp", 1), ("resistance", 1)))
    snap_a, left_a, _ = alloc_a.apply(BASELINE, BUDGET)
    candidates["mix_mp_and_res"] = {
        "desc": "MP 4→5 + RES 219→220 (1 residual)",
        "spent": BUDGET - left_a,
        "leftover": left_a,
        "effects": {"mp": snap_a.mp, "res": snap_a.resistance},
    }

    # Mix B: RES half + WIS half — 20 cap RES (+20) + 21 cap WIS (+42)
    alloc_b = Allocation(legs=(("resistance", 20), ("wisdom", 42)))
    snap_b, left_b, _ = alloc_b.apply(BASELINE, BUDGET)
    candidates["mix_res_and_wis"] = {
        "desc": f"+20 RES (20 cap) + +{snap_b.wisdom} WIS (21 cap)",
        "spent": BUDGET - left_b,
        "leftover": left_b,
        "effects": {
            "res": snap_b.resistance,
            "wis": snap_b.wisdom,
            "shield_stack_abs": round(192 * shield_multiplier(snap_b.resistance) / shield_multiplier(219), 1),
            "lifesteal_rate_pct": round(lifesteal_rate(snap_b.wisdom) * 100, 2),
        },
    }

    # Mix C: RES half + AGI half — 20 cap RES + 21 cap AGI
    alloc_c = Allocation(legs=(("resistance", 20), ("agility", 42)))
    snap_c, left_c, _ = alloc_c.apply(BASELINE, BUDGET)
    candidates["mix_res_and_agi"] = {
        "desc": f"+20 RES (20 cap) + +{snap_c.agility - BASELINE.agility} AGI (21 cap)",
        "spent": BUDGET - left_c,
        "leftover": left_c,
        "effects": {
            "res": snap_c.resistance,
            "agi": snap_c.agility,
            "crit_rate_pct": round(critical_rate(snap_c.agility) * 100, 2),
            "exp_dmg_boost_pct": round(expected_crit_damage_boost(snap_c.agility) * 100, 3),
        },
    }

    # Mix D: WIS half + AGI half — 20 cap WIS + 21 cap AGI (both tier 0, 0.5 cap/pt)
    alloc_d = Allocation(legs=(("wisdom", 40), ("agility", 42)))
    snap_d, left_d, _ = alloc_d.apply(BASELINE, BUDGET)
    candidates["mix_wis_and_agi"] = {
        "desc": f"+{snap_d.wisdom} WIS (20 cap) + +{snap_d.agility - BASELINE.agility} AGI (21 cap)",
        "spent": BUDGET - left_d,
        "leftover": left_d,
        "effects": {
            "wis": snap_d.wisdom,
            "agi": snap_d.agility,
            "lifesteal_rate_pct": round(lifesteal_rate(snap_d.wisdom) * 100, 2),
            "crit_rate_pct": round(critical_rate(snap_d.agility) * 100, 2),
        },
    }

    # Stalemate-breaker check: at what STR does Flame raw > 192 (peer shield stack)?
    # Flame raw = 30 × (1 + STR/100). 30 * multiplier > 192 → multiplier > 6.4 → STR > 540
    # Currently STR 452 → Flame 166. To break 192 shields need STR 541. We can't get there with +20 STR.
    flame_break_str = 540
    str_needed = flame_break_str - BASELINE.strength  # 88 points
    cap_needed_for_str = 88 * 2  # tier 400-600, 2 cap/pt (until 600)
    stalemate_check = {
        "question": "At what STR does Flame raw exceed 192 (typical peer shield stack)?",
        "current_flame_raw": round(30 * damage_multiplier(BASELINE.strength), 1),
        "required_str": flame_break_str,
        "str_delta_needed": str_needed,
        "capital_needed": cap_needed_for_str,
        "achievable_with_41_cap": False,
        "verdict": f"NO — need {cap_needed_for_str} cap (have {BUDGET}). Pure STR cannot break stalemates at our budget.",
    }

    # RES defensive curve: how much more shield do we gain per point at 219?
    # Shield multiplier is linear in RES. Each +1 RES = +1% of base shield.
    # At base stack 60 (sum of v1's = 15+20+25), +1 RES = 0.6 abs.
    # So +41 RES = +24 abs shield. Relative gain: 24/192 = 12.5%.
    res_check = {
        "question": "Does marginal RES keep paying at 219?",
        "current_shield_stack": 192,
        "after_41_res": round(192 * shield_multiplier(260) / shield_multiplier(219), 1),
        "abs_gain": round(192 * shield_multiplier(260) / shield_multiplier(219) - 192, 1),
        "pct_gain": round((shield_multiplier(260) / shield_multiplier(219) - 1) * 100, 2),
        "verdict": "Linear returns; 12.9% stack increase. Each cap buys 1 RES at tier 200-400.",
    }

    return {
        "candidates": candidates,
        "stalemate_check": stalemate_check,
        "res_check": res_check,
    }


# ── Phase 2: Empirics ───────────────────────────────────────────


def run_empirics() -> dict:
    """Query leek_observations for peer distribution at L150-170, T350-500."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get all distinct leeks in band
    cur.execute("""
        SELECT leek_id, MAX(observed_at) as latest,
               level, talent, life, strength, resistance, wisdom, agility,
               magic, science, tp, mp
        FROM leek_observations
        WHERE level BETWEEN 150 AND 170
          AND talent BETWEEN 350 AND 500
          AND strength IS NOT NULL
          AND observed_at > datetime('now', '-60 days')
        GROUP BY leek_id
        ORDER BY talent DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]

    # Exclude IAdonis/AnansAI (own leeks)
    rows = [r for r in rows if r["leek_id"] not in (131321, 132531)]

    if not rows:
        return {"n": 0, "note": "No peers in band with fresh stats"}

    def pct(values: list[float], p: float) -> float:
        values = sorted(values)
        if not values:
            return 0.0
        k = int(p * len(values))
        return values[min(k, len(values) - 1)]

    def stat_summary(key: str) -> dict:
        vals = [r[key] for r in rows if r[key] is not None]
        if not vals:
            return {"n": 0}
        return {
            "n": len(vals),
            "min": min(vals),
            "p25": pct(vals, 0.25),
            "median": median(vals),
            "p75": pct(vals, 0.75),
            "max": max(vals),
            "mean": round(sum(vals) / len(vals), 1),
        }

    summary = {stat: stat_summary(stat) for stat in
               ("life", "strength", "resistance", "wisdom", "agility", "magic", "science", "tp", "mp", "talent", "level")}

    # Top-10 talent in band
    top10 = rows[:10]
    # Also save all rows (reproducibility)
    DATA.mkdir(parents=True, exist_ok=True)
    out = {
        "snapshot_date": "2026-04-20",
        "band": {"level": [150, 170], "talent": [350, 500]},
        "n_peers": len(rows),
        "summary": summary,
        "top10_by_talent": [
            {k: r[k] for k in ("leek_id", "level", "talent", "life", "strength",
                               "resistance", "wisdom", "agility", "magic", "science", "tp", "mp")}
            for r in top10
        ],
        "iadonis_position": {
            "life": {"value": BASELINE.life, "vs_median": BASELINE.life - (summary["life"].get("median", 0) or 0)},
            "strength": {"value": BASELINE.strength, "vs_median": BASELINE.strength - (summary["strength"].get("median", 0) or 0)},
            "resistance": {"value": BASELINE.resistance, "vs_median": BASELINE.resistance - (summary["resistance"].get("median", 0) or 0)},
            "wisdom": {"value": BASELINE.wisdom, "vs_median": BASELINE.wisdom - (summary["wisdom"].get("median", 0) or 0)},
            "agility": {"value": BASELINE.agility, "vs_median": BASELINE.agility - (summary["agility"].get("median", 0) or 0)},
        },
    }
    with open(DATA / "peer_scout_s53.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    return out


# ── Report rendering ────────────────────────────────────────────


def render_memo(theory: dict, empirics: dict) -> str:
    """Render the full markdown memo."""
    baseline = BASELINE

    lines = [
        "# Capital Allocation Audit — IAdonis L153, 41 unspent capital (S53)",
        "",
        f"**Date**: 2026-04-20 · **Budget**: {BUDGET} capital · **Baseline**: STR {baseline.strength}, RES {baseline.resistance}, WIS {baseline.wisdom}, AGI {baseline.agility}, HP {baseline.life}, TP {baseline.tp}, MP {baseline.mp}",
        "",
        "## Executive summary (TL;DR)",
        "",
        "Compare the candidate 41-cap allocations against theory (formula-grounded marginal ROI) and peer empirics (leek_observations). Synthesis recommends a specific allocation after the sim-validation phase.",
        "",
        "---",
        "",
        "## Phase 1 — Theory (top-down)",
        "",
        "### Formulas (parsed from Effect*.java)",
        "",
        "- Damage: `(v1 + jet×v2) × (1 + max(0,STR)/100) × aoe × crit × targets × (1 + Power/100)`",
        "- Abs Shield: `(v1 + jet×v2) × (1 + RES/100) × aoe × crit`",
        "- Heal: `(v1 + jet×v2) × (1 + WIS/100) × aoe × crit × targets`",
        "- Lifesteal: `damage_dealt × WIS/1000` — **ZERO at WIS=0**",
        "- Crit rate: `AGI/1000` — AGI 10 → 1.0%, AGI 92 → 9.2%",
        "- ShackleTP scales with CASTER's MAGIC — **WIS does NOT grant debuff resistance** (folklore busted; confirmed absent from Java source)",
        "",
        "### Candidate allocations (41 cap)",
        "",
        "| Candidate | Spend | Leftover | Stat delta | Effect delta |",
        "|-----------|-------|----------|------------|--------------|",
    ]
    for key, c in theory["candidates"].items():
        effects_str = ", ".join(f"{k}={v}" for k, v in c["effects"].items() if k != "note")
        lines.append(f"| **{key}** | {c['spent']} | {c['leftover']} | {c['desc']} | {effects_str} |")

    lines += [
        "",
        "### Critical checks",
        "",
        f"**Stalemate-breaker**: {theory['stalemate_check']['verdict']}",
        f"- Current Flame raw: {theory['stalemate_check']['current_flame_raw']}",
        f"- To exceed 192 peer shield stack, need STR {theory['stalemate_check']['required_str']} (+{theory['stalemate_check']['str_delta_needed']} pts = {theory['stalemate_check']['capital_needed']} cap).",
        f"- **Implication**: Pure-STR allocation does NOT fix the stalemate problem. The gap is 2.1× our budget.",
        "",
        f"**RES marginal return**: {theory['res_check']['verdict']}",
        f"- Current shield stack: {theory['res_check']['current_shield_stack']}",
        f"- After +41 RES: {theory['res_check']['after_41_res']} (+{theory['res_check']['abs_gain']} abs, +{theory['res_check']['pct_gain']}%)",
        "",
        "### Theory interpretation per stat",
        "",
        f"- **STR** (+20 → 472): damage mult 5.52→5.72 = **+3.6% damage/hit**. Flame goes 166→172. Tiny. Cost-per-point tier (2 cap/pt) makes STR the worst per-capital damage lever at our tier.",
        f"- **RES** (+41 → 260): shield stack 192→216 = **+12.9%**. Linear, predictable. Each +1 RES adds ~0.6 abs shield.",
        f"- **WIS** (0→82): heal amp +82%, **lifesteal 0%→8.2%**. Unlocks a mechanic that currently doesn't exist for us. Over a fight dealing 720 damage, +59 HP via lifesteal.",
        f"- **AGI** (10→92): crit rate 1%→9.2%. Expected damage boost **+2.76%** (crit × (1.3-1)). Also scales damage-return chips if we ever use them.",
        f"- **LIFE** (+123 HP → 1143): +12% raw HP. Corrects earlier plan error (3 HP/cap in 1000-1999 tier, not 2).",
        f"- **FREQ** (+41 → 141): longer chip buff durations. Small incremental value; low priority.",
        f"- **TP** (14→15 costs **50 cap** > 41 budget): UNAFFORDABLE.",
        f"- **MP** (4→5 costs 40 cap → 1 leftover): positional lever; question is whether v15 AI uses extra MP.",
        "",
        "---",
        "",
        "## Phase 2 — Empirics (bottom-up)",
        "",
        f"**Sample**: `leek_observations` filtered to L150-170, T350-500, observed within 60 days.",
        f"**N peers (distinct leeks)**: {empirics.get('n_peers', 0)}",
        "",
    ]
    if empirics.get("n_peers", 0) > 0:
        s = empirics["summary"]
        lines += [
            "### Peer stat distribution (L150-170, T350-500)",
            "",
            "| Stat | n | min | p25 | median | p75 | max | mean | **IAdonis** | vs median |",
            "|------|---|-----|-----|--------|-----|-----|------|-------------|-----------|",
        ]
        for stat in ("life", "strength", "resistance", "wisdom", "agility", "magic", "science", "tp", "mp", "talent", "level"):
            ss = s.get(stat, {})
            if ss.get("n", 0) == 0:
                continue
            ours = getattr(baseline, "life" if stat == "life" else stat, None)
            if ours is None and stat == "talent":
                ours = 314
            if ours is None and stat == "level":
                ours = 153
            vs_med = (ours - ss["median"]) if ours is not None else ""
            lines.append(
                f"| {stat} | {ss['n']} | {ss.get('min','')} | {ss.get('p25','')} | {ss.get('median','')} | {ss.get('p75','')} | {ss.get('max','')} | {ss.get('mean','')} | **{ours}** | {vs_med:+} |" if vs_med != "" else f"| {stat} | {ss['n']} | {ss.get('min','')} | {ss.get('p25','')} | {ss.get('median','')} | {ss.get('p75','')} | {ss.get('max','')} | {ss.get('mean','')} | — | — |"
            )

        lines += [
            "",
            "### Top-10 by talent in band",
            "",
            "| leek_id | level | talent | LIFE | STR | RES | WIS | AGI | MAG | SCI | TP | MP |",
            "|---------|-------|--------|------|-----|-----|-----|-----|-----|-----|-----|-----|",
        ]
        for r in empirics.get("top10_by_talent", []):
            lines.append(
                f"| {r.get('leek_id','')} | {r.get('level','')} | {r.get('talent','')} | "
                f"{r.get('life','')} | {r.get('strength','')} | {r.get('resistance','')} | "
                f"{r.get('wisdom','')} | {r.get('agility','')} | {r.get('magic','')} | "
                f"{r.get('science','')} | {r.get('tp','')} | {r.get('mp','')} |"
            )
        lines += [
            "",
            "### Peer signal interpretation",
            "",
            "- **STR median**: see table. If IAdonis is near or above, marginal STR is low-ROI per peer signal.",
            "- **WIS median**: zero-centric or positive? Gates whether the WIS lever is validated by peers.",
            "- **AGI median**: climbers tend to invest in AGI if crit is valuable at this level; see S52 climber_study.",
            "- **RES**: IAdonis's RES 219 is historically ahead of climber-cohort peers (S52 NEW-B median ~42). More RES may have diminishing peer-validated value.",
            "",
            "---",
            "",
            "## Phase 3 — Synthesis",
            "",
            "### Theory × Peer 2×2 grid",
            "",
            "| Stat | Theory signal | Peer signal | Verdict |",
            "|------|---------------|-------------|---------|",
            "| STR | Weak (+3.6% dmg at 2 cap/pt) | Varies — check median above | Deprioritize |",
            "| RES | Moderate (+12.9% shield stack) | Already ahead of peers | Diminishing returns; keep some |",
            "| WIS | Strong (0→lifesteal 8.2% + heal amp 82%) | Most peers low or zero at L150-170 | Theory-first play: we'd be ahead of meta |",
            "| AGI | Weak (+2.76% dmg via crit) | Peers generally low at our level | Weak on both axes |",
            "| LIFE | Moderate (+12% HP) | Baseline, uncontroversial | Safe default |",
            "| MP | Conditional on AI use | N/A | Only if v15 AI would use it |",
            "",
            "### Candidate ranking (preliminary, pre-sim)",
            "",
            "1. **Pure WIS (+82)** — Strong theory (unlocks lifesteal mechanic from zero), peer-independent play. Biggest qualitative change.",
            "2. **RES+WIS mix (+20 RES, +42 WIS)** — Balanced: shield +6% + lifesteal +4.2%. Hedges the uncertainty in WIS peer validation.",
            "3. **MP jump + residual** — Only if AI exploits MP 5 materially.",
            "4. **Pure RES (+41)** — Lowest-risk, lowest-upside. Linear known returns.",
            "",
            "### Sim validation (pending)",
            "",
            "Run `compare_ais.py` with `--wis2 82` vs baseline. Multiple variants. 200 fights each vs fixed opponent pool. Results go here after execution.",
            "",
            "### Decision (pending sim)",
            "",
            "TBD after sim validation. Current leaning: **Pure WIS +82** unless sim reveals a regression.",
            "",
            "---",
            "",
            "## Phase 4 — Execute",
            "",
            "Dry-run + user approval required. Commands will go here once decided.",
            "",
        ]

    return "\n".join(lines)


# ── Entry point ─────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Compute + write memo, no API calls")
    ap.add_argument("--phase1-only", action="store_true", help="Skip empirics (DB query)")
    args = ap.parse_args()

    print("Running Phase 1: Theory …")
    theory = run_theory()

    if args.phase1_only:
        empirics = {"n_peers": 0, "note": "phase1-only"}
    else:
        print("Running Phase 2: Empirics …")
        empirics = run_empirics()

    memo = render_memo(theory, empirics)
    DOCS.mkdir(parents=True, exist_ok=True)
    memo_path = DOCS / "capital_audit_s53.md"
    memo_path.write_text(memo)
    print(f"✓ Wrote {memo_path}")
    print(f"✓ Wrote {DATA / 'peer_scout_s53.json'}" if not args.phase1_only else "")

    # Also print the theory candidates table to stdout for quick visual
    print("\n--- Phase 1 candidates ---")
    for k, c in theory["candidates"].items():
        print(f"  {k:24s} spent={c['spent']:3d} leftover={c['leftover']:2d}  {c['desc']}")
    print(f"\nStalemate check: {theory['stalemate_check']['verdict']}")
    print(f"RES check: {theory['res_check']['verdict']}")


if __name__ == "__main__":
    main()
