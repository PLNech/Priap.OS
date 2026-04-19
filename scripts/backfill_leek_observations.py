#!/usr/bin/env python3
"""
Backfill NULL stat columns in leek_observations from stored fight JSONs.

Why this exists
---------------
Around 2026-01-23→25 (early bulk scrape), a bug in the scraper skipped the
stats-merge step, inserting leek_observations rows with level/talent but
NULL on strength/agility/wisdom/resistance/magic/science/life/tp/mp/frequency.
The bug was fixed Jan 25 but the broken rows remained — 12,968 of 29,089
(44.6%) observations carry NULL stats. See task #127.

The fight JSONs are intact (fights.json_data) so we can replay them through
the current _enhance_leek logic to recover the stats. Zero API calls.

Usage:
    poetry run python scripts/backfill_leek_observations.py --dry-run
    poetry run python scripts/backfill_leek_observations.py
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leekwars_agent.scraper.scraper import FightScraper


STAT_COLS = (
    "life", "strength", "agility", "wisdom", "resistance",
    "magic", "science", "frequency", "tp", "mp",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/fights_meta.db")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Max rows to repair (0 = all)")
    args = ap.parse_args()

    db_path = ROOT / args.db
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Find NULL-stat rows joined with their fight JSONs
    rows = conn.execute("""
        SELECT lo.fight_id, lo.leek_id, lo.team, f.json_data
        FROM leek_observations lo
        JOIN fights f ON f.fight_id = lo.fight_id
        WHERE lo.strength IS NULL
        ORDER BY lo.fight_id
    """).fetchall()

    if args.limit:
        rows = rows[: args.limit]

    print(f"Found {len(rows)} NULL-stat rows with stored JSON")
    if not rows:
        return 0

    # Group by fight_id so we parse each JSON only once
    fights: dict[int, tuple[str, list[tuple[int, int]]]] = {}
    for r in rows:
        fid = r["fight_id"]
        if fid not in fights:
            fights[fid] = (r["json_data"], [])
        fights[fid][1].append((r["leek_id"], r["team"]))

    print(f"Across {len(fights)} unique fights")

    repaired = 0
    missing = 0
    errors = 0

    for i, (fight_id, (json_str, targets)) in enumerate(fights.items(), start=1):
        try:
            data = json.loads(json_str)
            fight = data.get("fight", data)
            entity_lookup = FightScraper._build_entity_lookup(
                fight.get("data", {}).get("leeks", [])
            )

            # Build leek_id -> team from leeks1/leeks2
            leek_index: dict[int, tuple[int, dict]] = {}
            for leek in fight.get("leeks1", []):
                leek_index[leek.get("id")] = (1, leek)
            for leek in fight.get("leeks2", []):
                leek_index[leek.get("id")] = (2, leek)

            for leek_id, team in targets:
                pair = leek_index.get(leek_id)
                if not pair:
                    missing += 1
                    continue
                stored_team, leek = pair
                merged, _ = FightScraper._enhance_leek(
                    leek, team=stored_team, entity_lookup=entity_lookup
                )
                stat_vals = tuple(merged.get(c) for c in STAT_COLS)
                if all(v is None for v in stat_vals):
                    missing += 1
                    continue

                if not args.dry_run:
                    set_clause = ", ".join(f"{c} = ?" for c in STAT_COLS)
                    conn.execute(
                        f"UPDATE leek_observations SET {set_clause} "
                        f"WHERE fight_id = ? AND leek_id = ?",
                        stat_vals + (fight_id, leek_id),
                    )
                repaired += 1

            if i % 200 == 0:
                print(f"  [{i}/{len(fights)}] repaired={repaired} missing={missing} errors={errors}")
                if not args.dry_run:
                    conn.commit()
        except Exception as e:
            errors += 1
            print(f"  fight {fight_id}: {e}")

    if not args.dry_run:
        conn.commit()

    print(f"\nDone: repaired={repaired} missing={missing} errors={errors}")
    print(f"{'(dry run — no writes)' if args.dry_run else 'Committed.'}")
    conn.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
