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
OUR_LEEKS = {131321: "IAdonis", 132531: "AnansAI"}
TRACKED_NAMES = ["Claudios"]  # partial match — tracks sensei + anyone with "Claud" prefix


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

    # Find our leeks — prefer leek_ranks table (persisted even outside top N snapshot)
    our_leeks = {}
    leek_rank_rows = conn.execute("""
        SELECT leek_id, name, rank, talent, level FROM leek_ranks
        WHERE snapshot_id = ?
    """, (snapshot_id,)).fetchall()
    for lid, name, rank, talent, level in leek_rank_rows:
        if lid in OUR_LEEKS:
            our_leeks[lid] = {"name": name, "rank": rank, "talent": talent, "level": level}

    # Fallback: check snapshot rows directly
    for lid, default_name in OUR_LEEKS.items():
        if lid not in our_leeks:
            entry = next((r for r in rows if r[4] == lid), None)
            if entry:
                our_leeks[lid] = {"name": default_name, "rank": entry[0], "talent": entry[2], "level": entry[3]}
            else:
                print(f"  Warning: {default_name} (#{lid}) not found in snapshot — rank unknown")
                our_leeks[lid] = {"name": default_name, "rank": None, "talent": None, "level": None}

    # Primary leek for neighborhood/contender calculations (IAdonis = 131321)
    primary = our_leeks.get(131321, list(our_leeks.values())[0] if our_leeks else {})
    our_rank = primary.get("rank") or 0
    our_talent = primary.get("talent") or 0
    our_level = primary.get("level") or 0

    # Talent histogram (bins of 50)
    talent_bins = {}
    for t in talents:
        b = (t // 50) * 50
        talent_bins[b] = talent_bins.get(b, 0) + 1

    # Level histogram (bins of 10)
    level_bins = {}
    for lv in levels:
        b = (lv // 10) * 10
        level_bins[b] = level_bins.get(b, 0) + 1

    # Neighborhood (rank ±50 around IAdonis if in snapshot)
    neighborhood = [[r[0], r[1], r[2], r[3]] for r in rows if our_rank and abs(r[0] - our_rank) <= 50]

    # Contenders: same talent band (±100) AND similar level (±50)
    our_ids = set(OUR_LEEKS.keys())
    contenders = [
        [r[0], r[1], r[2], r[3]]
        for r in rows
        if our_talent and abs(r[2] - our_talent) <= 100 and abs(r[3] - our_level) <= 50
        and r[4] not in our_ids
    ]

    # Tracked names (sensei + Claud* pattern)
    tracked = []
    for name_pattern in TRACKED_NAMES:
        for r in rows:
            if name_pattern.lower() in r[1].lower():
                tracked.append({"rank": r[0], "name": r[1], "talent": r[2], "level": r[3]})
    # Keep first match per pattern (highest rank)
    seen_patterns = set()
    sensei_list = []
    for t in tracked:
        key = next((p for p in TRACKED_NAMES if p.lower() in t["name"].lower()), None)
        if key and key not in seen_patterns:
            sensei_list.append(t)
            seen_patterns.add(key)
    sensei = sensei_list[0] if sensei_list else None

    # Scatter (sampled every 5th)
    scatter = [[r[2], r[3], r[0]] for r in rows[::5]]

    # Top 20
    top20 = [[r[0], r[1], r[2], r[3]] for r in rows[:20]]

    data = {
        "snapshot": timestamp,
        "snapshot_id": snapshot_id,
        "total": len(rows),
        "our": list(our_leeks.values()),       # all our leeks
        "our_primary": primary,                # IAdonis (for charts)
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
    for leek in our_leeks.values():
        print(f"  {leek['name']}: rank #{leek.get('rank', '?')}, T{leek.get('talent', '?')}, L{leek.get('level', '?')}")
    if sensei:
        print(f"  Sensei {sensei['name']}: rank #{sensei['rank']}, T{sensei['talent']}")
    print(f"  Output: {OUT_PATH}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=int, help="Snapshot ID (default: latest)")
    args = parser.parse_args()
    export(args.snapshot)
