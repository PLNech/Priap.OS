#!/usr/bin/env python3
"""
Backfill fights_meta.db from locally-cached fights.db.

Why this exists
---------------
`fights_meta.db` stopped capturing our fights after 2026-03-01 because the
scraper's default level filter (25-100) rejected every fight once IAdonis
crossed L150. The primary `fights.db` kept growing (auto_daily_fights.py
stores raw JSONs there directly), so we can replay those JSONs into the
meta DB without any API calls.

Usage:
    poetry run python scripts/backfill_fights_meta.py
    poetry run python scripts/backfill_fights_meta.py --since 2026-03-01
    poetry run python scripts/backfill_fights_meta.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leekwars_agent.scraper.scraper import FightScraper
from leekwars_agent.scraper.db import FightDB


def parse_since(since: str) -> int:
    return int(dt.datetime.fromisoformat(since).timestamp())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary", default="data/fights.db", help="Source DB (raw JSONs)")
    ap.add_argument("--meta", default="data/fights_meta.db", help="Target DB (analytics)")
    ap.add_argument("--since", default="2026-03-01", help="Only backfill fights after this date (ISO)")
    ap.add_argument("--limit", type=int, default=0, help="Max fights to process (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="Only report what would be done")
    args = ap.parse_args()

    primary_path = ROOT / args.primary
    meta_path = ROOT / args.meta
    if not primary_path.exists():
        print(f"ERROR: {primary_path} not found")
        return 1

    since_ts = parse_since(args.since)
    print(f"Scanning {primary_path} for fights after {args.since} ({since_ts})")

    # Candidate fight IDs from primary DB
    with sqlite3.connect(primary_path) as src:
        rows = src.execute(
            "SELECT id, data FROM fights WHERE date > ? ORDER BY date ASC",
            (since_ts,),
        ).fetchall()
    print(f"  {len(rows)} candidates in primary")

    # Filter to those missing from meta DB
    meta_conn = sqlite3.connect(meta_path)
    existing = {r[0] for r in meta_conn.execute("SELECT fight_id FROM fights").fetchall()}
    meta_conn.close()
    missing = [(fid, data) for fid, data in rows if fid not in existing]
    print(f"  {len(missing)} missing from meta DB")

    if args.limit:
        missing = missing[: args.limit]
        print(f"  limiting to {len(missing)}")

    if args.dry_run:
        print("DRY RUN — no writes")
        return 0

    if not missing:
        print("Nothing to backfill.")
        return 0

    # API client is required by FightScraper but we never call it (we use _store_fight_data)
    # Pass None — any code path that dereferences api would be a bug in our backfill path.
    fight_db = FightDB(str(meta_path))
    scraper = FightScraper(api=None, db=fight_db)  # type: ignore[arg-type]

    stored = 0
    errors = 0
    for i, (fid, data_json) in enumerate(missing, start=1):
        try:
            data = json.loads(data_json) if isinstance(data_json, str) else data_json
            if scraper._store_fight_data(fid, data, force=True):
                stored += 1
        except Exception as e:
            errors += 1
            print(f"  fight {fid}: {e}")
        if i % 25 == 0:
            print(f"  [{i}/{len(missing)}] stored={stored} errors={errors}")

    print(f"\nDone: stored={stored} / {len(missing)}, errors={errors}")
    fight_db.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
