#!/usr/bin/env python3
"""Export rankings DB to JSON for the leaderboard dashboard.

Usage:
    poetry run python scripts/export_rankings.py
    poetry run python scripts/export_rankings.py --snapshot 2  # specific snapshot
"""
import argparse
import json
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "rankings.db"
OUT_PATH = Path(__file__).resolve().parent.parent / "site" / "data" / "rankings.json"
OUR_LEEK_ID = 131321
SENSEI_NAME = "Claudios"


def export(snapshot_id: int | None = None):
    conn = sqlite3.connect(DB_PATH)

    # Get latest snapshot if not specified
    if snapshot_id is None:
        row = conn.execute(
            "SELECT id, timestamp FROM snapshots ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if not row:
            print("No snapshots. Run ranking_tracker.py first.")
            return
        snapshot_id, timestamp = row
    else:
        row = conn.execute(
            "SELECT timestamp FROM snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
        timestamp = row[0] if row else "unknown"

    rows = conn.execute("""
        SELECT r.rank, r.name, r.talent, r.level, r.leek_id
        FROM rankings r WHERE r.snapshot_id = ?
        ORDER BY r.rank
    """, (snapshot_id,)).fetchall()

    if not rows:
        print(f"Snapshot {snapshot_id} has no data.")
        return

    talents = [r[2] for r in rows]
    levels = [r[3] for r in rows]

    # Find us
    our_entry = next((r for r in rows if r[4] == OUR_LEEK_ID), None)
    if not our_entry:
        print(f"IAdonis not found in snapshot {snapshot_id}!")
        our_rank, our_talent, our_level = 9999, 300, 117
    else:
        our_rank, _, our_talent, our_level, _ = our_entry

    # Talent histogram (bins of 50)
    talent_bins = {}
    for t in talents:
        b = (t // 50) * 50
        talent_bins[b] = talent_bins.get(b, 0) + 1

    # Level histogram (bins of 10)
    level_bins = {}
    for l in levels:
        b = (l // 10) * 10
        level_bins[b] = level_bins.get(b, 0) + 1

    # Neighborhood (rank ±50)
    neighborhood = [[r[0], r[1], r[2], r[3]] for r in rows if abs(r[0] - our_rank) <= 50]

    # Contenders: same talent band (±100) AND similar level (±50)
    contenders = [
        [r[0], r[1], r[2], r[3]]
        for r in rows
        if abs(r[2] - our_talent) <= 100 and abs(r[3] - our_level) <= 50
        and r[4] != OUR_LEEK_ID
    ]

    # Sensei
    sensei_entry = next((r for r in rows if r[1] == SENSEI_NAME), None)
    sensei = None
    if sensei_entry:
        sensei = {
            "rank": sensei_entry[0], "name": sensei_entry[1],
            "talent": sensei_entry[2], "level": sensei_entry[3]
        }

    # Scatter (sampled every 5th)
    scatter = [[r[2], r[3], r[0]] for r in rows[::5]]

    # Top 20
    top20 = [[r[0], r[1], r[2], r[3]] for r in rows[:20]]

    data = {
        "snapshot": timestamp,
        "snapshot_id": snapshot_id,
        "total": len(rows),
        "our": {"rank": our_rank, "talent": our_talent, "level": our_level, "name": "IAdonis"},
        "sensei": sensei,
        "talent_hist": sorted(talent_bins.items()),
        "level_hist": sorted(level_bins.items()),
        "neighborhood": neighborhood,
        "contenders": contenders[:100],
        "scatter": scatter,
        "top20": top20,
        "stats": {
            "min_talent": min(talents), "max_talent": max(talents),
            "avg_talent": round(sum(talents) / len(talents)),
            "min_level": min(levels), "max_level": max(levels),
            "avg_level": round(sum(levels) / len(levels)),
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, separators=(",", ":"))

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"Exported snapshot #{snapshot_id} ({timestamp})")
    print(f"  {len(rows)} leeks, {len(contenders)} contenders, {size_kb:.1f} KB")
    print(f"  IAdonis: rank #{our_rank}, T{our_talent}, L{our_level}")
    if sensei:
        print(f"  Sensei {sensei['name']}: rank #{sensei['rank']}, T{sensei['talent']}")
    print(f"  Output: {OUT_PATH}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=int, help="Snapshot ID (default: latest)")
    args = parser.parse_args()
    export(args.snapshot)
