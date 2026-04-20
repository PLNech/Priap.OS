#!/usr/bin/env python3
"""PySim ↔ Online correlation study (task #120, P0 #1).

Does PySim agree with the real game on fight outcomes?

Methodology
-----------
1. Sample N recent duels where IAdonis fought a single opponent with
   fully-captured stats.
2. For each fight, classify the opponent's archetype from its dominant
   stat (STR / MAG / AGI / balanced) and pick a matching sparring AI
   from `ais/opponents/`.
3. Replay the fight K times in PySim (varied seeds) using our v14 on our
   side and the archetype proxy on the opponent side. Equipment, spawns,
   and obstacles come from the real fight JSON via setup_from_fight.
4. Take majority winner across K sim runs. Compare to real winner.
5. Report accuracy, confusion matrix, turn-count correlation, and
   per-archetype breakdown.

What this measures
------------------
End-to-end predictive fidelity of PySim, bounded by archetype-proxy
error. If accuracy ≥ 70%, PySim tournament ELO is trustworthy as a
v15-deploy gate. If accuracy < 70%, fix fidelity before betting.

Usage:
    poetry run python scripts/pysim_online_correlation.py --n 50 --k 5
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import sqlite3
import statistics
import sys
import traceback
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leekwars_agent.pysim.runner import PySimRunner  # noqa: E402


OUR_LEEK = 131321
OUR_AI = ROOT / "ais" / "fighter_v14_flat.leek"

ARCHETYPE_AI = {
    # NOTE (2026-04-20): v2 run (correlation_study_v2.md) swapped
    # str_heavy/balanced to proxy_defensive_striker.leek. Result was 46.0%
    # — WORSE than 54.0% with cktang88_magnum1. The proxy swap fixed the
    # "shield timing" surface problem but revealed the real gap is
    # deeper: v14 executes too fast in PySim regardless of defense. FP
    # ratio barely moved (0.48 → 0.53). Reverted here; the proxy file
    # stays as an artifact.
    "str_heavy":  ROOT / "ais" / "opponents" / "cktang88_magnum1.leek",
    "mag_heavy":  ROOT / "ais" / "opponents" / "cktang88_flamethrower-destroyer.leek",
    "agi_heavy":  ROOT / "ais" / "opponents" / "cktang88_magnum-12.leek",
    "balanced":   ROOT / "ais" / "opponents" / "pbondoer_silly_lemon.leek",
}


def classify_archetype(strength, agility, magic, wisdom, resistance=0) -> str:
    """Assign an opponent to one of four sparring archetypes.

    Tank classification comes first: high WIS+RES with low offense was
    previously misfiring to str_heavy, e.g. (STR 70, WIS 380, RES 380)
    which is a healer/tank, not a striker. For now we fold tanks into
    `balanced` because we lack a dedicated tank proxy AI.
    """
    s = strength or 0
    a = agility or 0
    m = magic or 0
    w = wisdom or 0
    r = resistance or 0

    if max(s, a, m) == 0:
        return "balanced"
    if (w + r) >= 2 * max(s, a, m):
        return "balanced"  # tank/healer — no dedicated proxy yet
    if s >= 1.5 * (a + m):
        return "str_heavy"
    if m > s and m >= a:
        return "mag_heavy"
    if a > s and a >= m:
        return "agi_heavy"
    return "balanced"


def sample_fights(conn: sqlite3.Connection, n: int) -> list[dict]:
    """Return recent 1v1 fights where both leeks have complete stats."""
    rows = conn.execute("""
        SELECT lo.fight_id, lo.won AS won,
               opp.leek_id AS opp_id, opp.strength, opp.agility,
               opp.magic, opp.wisdom, opp.resistance
        FROM leek_observations lo
        JOIN leek_observations opp
          ON opp.fight_id = lo.fight_id AND opp.leek_id != lo.leek_id
        WHERE lo.leek_id = ?
          AND opp.strength IS NOT NULL
          AND (SELECT COUNT(*) FROM leek_observations x
               WHERE x.fight_id = lo.fight_id) = 2
        ORDER BY lo.fight_id DESC
        LIMIT ?
    """, (OUR_LEEK, n)).fetchall()
    return [
        {
            "fight_id": r[0],
            "real_won": bool(r[1]),
            "opp_id": r[2],
            "strength": r[3], "agility": r[4],
            "magic": r[5], "wisdom": r[6], "resistance": r[7],
        }
        for r in rows
    ]


def load_fight_json(conn: sqlite3.Connection, fight_id: int) -> dict | None:
    row = conn.execute(
        "SELECT json_data FROM fights WHERE fight_id = ?", (fight_id,)
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def run_one(runner: PySimRunner, fight_json: dict, opp_ai: Path,
            seed: int) -> dict | None:
    """Run a single PySim replay. Returns dict with pysim_winner + turns."""
    fight = fight_json.get("fight", fight_json)
    try:
        engine = runner.setup_from_fight(
            fight, ai_path=OUR_AI, ai_path_2=opp_ai,
            seed=seed, restrict_equipment=True,
        )
        result = engine.run()
        return {
            "winner": result.get("winner", 0),
            "turns": result.get("turns", 0),
        }
    except Exception:
        return None


def pysim_real_team(fight_json: dict) -> int:
    """Which PySim team corresponds to our leek? (1 or 2)."""
    fight = fight_json.get("fight", fight_json)
    for l in fight.get("leeks1", []):
        if l.get("id") == OUR_LEEK:
            return 1
    for l in fight.get("leeks2", []):
        if l.get("id") == OUR_LEEK:
            return 2
    return 1


def run_study(n: int, k: int) -> dict:
    db_path = ROOT / "data" / "fights_meta.db"
    conn = sqlite3.connect(db_path)

    fights = sample_fights(conn, n)
    print(f"Sampled {len(fights)} fights")
    runner = PySimRunner()

    records: list[dict] = []
    archetype_counts: Counter[str] = Counter()
    skipped = 0
    errors = 0

    for i, f in enumerate(fights, start=1):
        archetype = classify_archetype(
            f["strength"], f["agility"], f["magic"], f["wisdom"],
            f["resistance"],
        )
        archetype_counts[archetype] += 1
        opp_ai = ARCHETYPE_AI[archetype]
        if not opp_ai.exists():
            skipped += 1
            continue

        fight_json = load_fight_json(conn, f["fight_id"])
        if not fight_json:
            skipped += 1
            continue

        our_team = pysim_real_team(fight_json)
        outcomes: list[int] = []
        turn_counts: list[int] = []
        for rep in range(k):
            result = run_one(runner, fight_json, opp_ai, seed=1000 + rep)
            if result is None:
                errors += 1
                continue
            outcomes.append(result["winner"])
            turn_counts.append(result["turns"])

        if not outcomes:
            skipped += 1
            continue

        majority = Counter(outcomes).most_common(1)[0][0]
        pysim_won = (majority == our_team)

        records.append({
            "fight_id": f["fight_id"],
            "archetype": archetype,
            "real_won": f["real_won"],
            "pysim_won": pysim_won,
            "real_turns": None,
            "pysim_turns_mean": statistics.mean(turn_counts) if turn_counts else 0,
            "outcomes_raw": outcomes,
            "opp_stats": {
                "str": f["strength"], "agi": f["agility"],
                "mag": f["magic"], "wis": f["wisdom"], "res": f["resistance"],
            },
        })

        if i % 5 == 0:
            agreed = sum(1 for r in records if r["real_won"] == r["pysim_won"])
            print(f"  [{i}/{len(fights)}] agreement so far: "
                  f"{agreed}/{len(records)} "
                  f"= {agreed/len(records)*100:.1f}%")

    # Aggregate
    agree = sum(1 for r in records if r["real_won"] == r["pysim_won"])
    total = len(records)
    accuracy = agree / total if total else 0.0

    # Confusion matrix
    tp = sum(1 for r in records if r["real_won"] and r["pysim_won"])
    tn = sum(1 for r in records if not r["real_won"] and not r["pysim_won"])
    fp = sum(1 for r in records if not r["real_won"] and r["pysim_won"])
    fn = sum(1 for r in records if r["real_won"] and not r["pysim_won"])

    # Per archetype
    per_arch = {}
    for arch in ARCHETYPE_AI.keys():
        arch_records = [r for r in records if r["archetype"] == arch]
        arch_agree = sum(1 for r in arch_records if r["real_won"] == r["pysim_won"])
        per_arch[arch] = {
            "n": len(arch_records),
            "agree": arch_agree,
            "accuracy": arch_agree / len(arch_records) if arch_records else 0.0,
        }

    conn.close()
    return {
        "total": total,
        "agree": agree,
        "accuracy": accuracy,
        "confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "per_archetype": per_arch,
        "archetype_distribution": dict(archetype_counts),
        "skipped": skipped,
        "errors": errors,
        "records": records,
    }


def render_markdown(result: dict, k: int) -> str:
    acc = result["accuracy"] * 100
    c = result["confusion"]
    lines = []
    lines.append("# PySim ↔ Online Correlation Study\n")
    lines.append(f"> Generated {dt.datetime.now().isoformat(timespec='seconds')}  ")
    lines.append(f"> Sample: {result['total']} fights × {k} sim reps = "
                 f"{result['total']*k} PySim runs\n")

    lines.append("## Headline\n")
    lines.append(f"**Agreement**: {result['agree']}/{result['total']} "
                 f"= **{acc:.1f}%**\n")

    if acc >= 70:
        lines.append("✅ **Gate passed**: PySim tournament ELO is trustworthy "
                     "as a v15-deploy gate.\n")
    elif acc >= 55:
        lines.append("⚠️ **Marginal**: PySim directionally agrees but has "
                     "sizable miss rate. Use tournament ELO with a confidence "
                     "band, not as a sole gate.\n")
    else:
        lines.append("❌ **Gate failed**: PySim disagrees with reality too "
                     "often. Fix fidelity before trusting tournament outcomes.\n")

    lines.append("## Confusion matrix\n")
    lines.append("| | PySim says WIN | PySim says LOSS |")
    lines.append("|---|---:|---:|")
    lines.append(f"| **Real WIN** | {c['tp']} (TP) | {c['fn']} (FN) |")
    lines.append(f"| **Real LOSS** | {c['fp']} (FP) | {c['tn']} (TN) |")
    lines.append("")

    lines.append("## Per-archetype breakdown\n")
    lines.append("| Archetype | N | Agree | Accuracy |")
    lines.append("|:--|-:|-:|-:|")
    for arch, stats in result["per_archetype"].items():
        if stats["n"] == 0:
            continue
        lines.append(f"| {arch} | {stats['n']} | {stats['agree']} | "
                     f"{stats['accuracy']*100:.1f}% |")
    lines.append("")

    lines.append("## Archetype distribution in sample\n")
    for arch, n in result["archetype_distribution"].items():
        lines.append(f"- {arch}: {n}")
    lines.append("")

    lines.append("## Methodology notes\n")
    lines.append("- Our AI: `fighter_v14_flat.leek` (deployed version).")
    lines.append("- Opponent AI: archetype proxy from `ais/opponents/` selected by dominant opponent stat.")
    lines.append("- Equipment / stats / spawn / obstacles: faithfully lifted from real fight JSON via `setup_from_fight(restrict_equipment=True)`.")
    lines.append("- Seed varied per replay; majority winner taken across K reps.")
    lines.append("- **Noise floor** of archetype proxy: expect ≤5pp loss vs. true opponent AI source.")
    lines.append(f"- Skipped: {result['skipped']}; Per-rep errors: {result['errors']}.")
    lines.append("")

    lines.append("## Next steps\n")
    if acc >= 70:
        lines.append("- Run 24-AI tournament with v14 + v15 → trust the ELO delta as ship/no-ship signal.")
    else:
        lines.append("- Diagnose top FN/FP fights — read action logs, look for systemic fidelity gaps.")
        lines.append("- Expand archetype proxy set or tighten selection rule.")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50, help="Number of fights to sample")
    ap.add_argument("--k", type=int, default=5, help="Replays per fight (majority vote)")
    ap.add_argument("--out", default="docs/research/correlation_study.md")
    ap.add_argument("--json-out", default="docs/research/correlation_study.json")
    args = ap.parse_args()

    random.seed(1337)
    try:
        result = run_study(args.n, args.k)
    except Exception:
        traceback.print_exc()
        return 1

    md = render_markdown(result, args.k)
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md)
    print(f"\nWrote {out_path}")

    json_path = ROOT / args.json_out
    json_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"Wrote {json_path}")

    print(f"\nFinal accuracy: {result['accuracy']*100:.1f}% "
          f"({result['agree']}/{result['total']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
