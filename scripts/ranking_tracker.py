#!/usr/bin/env python3
"""Ranking tracker — snapshot leaderboard to SQLite for historical tracking.

Usage:
    # Quick check: our rank only
    poetry run python scripts/ranking_tracker.py --quick

    # Full snapshot: top 2000 leeks (40 pages)
    poetry run python scripts/ranking_tracker.py

    # Custom depth
    poetry run python scripts/ranking_tracker.py --pages 200  # top 10K

    # Show history
    poetry run python scripts/ranking_tracker.py --history

    # Show movers (biggest rank changes since last snapshot)
    poetry run python scripts/ranking_tracker.py --movers

Designed for local cron (not CI — needs persistent SQLite DB).
Cron example:
    0 8 * * * cd /path/to/project && poetry run python scripts/ranking_tracker.py >> logs/ranking.log 2>&1
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from leekwars_agent.auth import login_api

OUR_LEEK_ID = 131321
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "rankings.db"
ENTRIES_PER_PAGE = 50


def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_entries INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rankings (
            snapshot_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            leek_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            talent INTEGER NOT NULL,
            level INTEGER NOT NULL,
            farmer TEXT,
            country TEXT,
            team TEXT,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rankings_leek ON rankings(leek_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rankings_snapshot ON rankings(snapshot_id)
    """)
    conn.commit()


def quick_rank(api) -> dict:
    """Get our leek's current rank (single API call)."""
    data = api._request(
        "get", f"/ranking/get-leek-rank-active/{OUR_LEEK_ID}/talent",
        headers=api._headers()
    ).json()
    return data


def fetch_ranking_page(api, page: int) -> list[dict]:
    """Fetch one page (50 entries) of leek talent ranking."""
    data = api._request(
        "get", f"/ranking/get-active/leek/talent/{page}/null",
        headers=api._headers()
    ).json()
    return data.get("ranking", [])


def snapshot(api, max_pages: int = 40) -> int:
    """Take a full ranking snapshot. Returns snapshot ID."""
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    ts = datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO snapshots (timestamp, total_entries) VALUES (?, 0)", (ts,)
    )
    snap_id = cur.lastrowid

    total = 0
    for page in range(1, max_pages + 1):
        entries = fetch_ranking_page(api, page)
        if not entries:
            break

        for e in entries:
            conn.execute(
                """INSERT INTO rankings
                   (snapshot_id, rank, leek_id, name, talent, level, farmer, country, team)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (snap_id, e["rank"], e["id"], e["name"], e["talent"],
                 e["level"], e.get("farmer"), e.get("country"), e.get("team"))
            )
        total += len(entries)

        if page % 10 == 0:
            print(f"  Page {page}/{max_pages}: {total} entries...")
            conn.commit()

        # Rate limit: ~100ms between pages
        time.sleep(0.1)

    conn.execute("UPDATE snapshots SET total_entries = ? WHERE id = ?", (total, snap_id))
    conn.commit()
    conn.close()
    return snap_id


def show_history():
    """Show our rank across all snapshots."""
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    rows = conn.execute("""
        SELECT s.timestamp, r.rank, r.talent, r.level
        FROM rankings r
        JOIN snapshots s ON r.snapshot_id = s.id
        WHERE r.leek_id = ?
        ORDER BY s.timestamp
    """, (OUR_LEEK_ID,)).fetchall()

    if not rows:
        print("No ranking history yet. Run a snapshot first.")
        conn.close()
        return

    print(f"{'Date':<20} {'Rank':>6} {'Talent':>7} {'Level':>5}  Delta")
    print("-" * 55)
    prev_rank = None
    for ts, rank, talent, level in rows:
        date = ts[:16]
        delta = ""
        if prev_rank is not None:
            d = prev_rank - rank  # positive = climbed
            if d > 0:
                delta = f"+{d} ↑"
            elif d < 0:
                delta = f"{d} ↓"
            else:
                delta = "  ="
        print(f"{date:<20} {rank:>6} {talent:>7} {level:>5}  {delta}")
        prev_rank = rank

    conn.close()


def show_movers():
    """Show biggest movers between last 2 snapshots."""
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    snaps = conn.execute(
        "SELECT id FROM snapshots ORDER BY timestamp DESC LIMIT 2"
    ).fetchall()

    if len(snaps) < 2:
        print("Need at least 2 snapshots to show movers.")
        conn.close()
        return

    new_id, old_id = snaps[0][0], snaps[1][0]

    # Join old and new rankings by leek_id
    movers = conn.execute("""
        SELECT n.name, n.rank, o.rank, n.talent, n.level,
               (o.rank - n.rank) as climb
        FROM rankings n
        JOIN rankings o ON n.leek_id = o.leek_id AND o.snapshot_id = ?
        WHERE n.snapshot_id = ?
        ORDER BY climb DESC
        LIMIT 20
    """, (old_id, new_id)).fetchall()

    print("Top 20 Climbers (since last snapshot):")
    print(f"{'Name':<20} {'Old':>6} {'New':>6} {'Delta':>7} {'Talent':>7} {'Level':>5}")
    print("-" * 60)
    for name, new_rank, old_rank, talent, level, climb in movers:
        print(f"{name:<20} {old_rank:>6} {new_rank:>6} {'+' + str(climb) if climb > 0 else climb:>7} {talent:>7} {level:>5}")

    # Also show biggest fallers
    fallers = conn.execute("""
        SELECT n.name, n.rank, o.rank, n.talent, n.level,
               (o.rank - n.rank) as climb
        FROM rankings n
        JOIN rankings o ON n.leek_id = o.leek_id AND o.snapshot_id = ?
        WHERE n.snapshot_id = ?
        ORDER BY climb ASC
        LIMIT 10
    """, (old_id, new_id)).fetchall()

    print("\nTop 10 Fallers:")
    for name, new_rank, old_rank, talent, level, climb in fallers:
        print(f"{name:<20} {old_rank:>6} {new_rank:>6} {climb:>7} {talent:>7} {level:>5}")

    conn.close()


def show_neighborhood(snap_id: int = None):
    """Show leeks around our rank in the latest snapshot."""
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    if snap_id is None:
        row = conn.execute(
            "SELECT id FROM snapshots ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if not row:
            print("No snapshots yet.")
            conn.close()
            return
        snap_id = row[0]

    our = conn.execute(
        "SELECT rank FROM rankings WHERE snapshot_id = ? AND leek_id = ?",
        (snap_id, OUR_LEEK_ID)
    ).fetchone()

    if not our:
        print("We're not in this snapshot (rank too low?).")
        conn.close()
        return

    our_rank = our[0]
    neighbors = conn.execute("""
        SELECT rank, name, talent, level, farmer
        FROM rankings
        WHERE snapshot_id = ? AND rank BETWEEN ? AND ?
        ORDER BY rank
    """, (snap_id, max(1, our_rank - 10), our_rank + 10)).fetchall()

    print(f"Neighborhood (our rank: #{our_rank}):")
    print(f"{'Rank':>6} {'Name':<20} {'Talent':>7} {'Level':>5} {'Farmer':<15}")
    print("-" * 60)
    for rank, name, talent, level, farmer in neighbors:
        marker = " ◄" if name == "IAdonis" else ""
        print(f"{rank:>6} {name:<20} {talent:>7} {level:>5} {farmer or '':>15}{marker}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ranking tracker for LeekWars")
    parser.add_argument("--quick", action="store_true", help="Just check our rank (no snapshot)")
    parser.add_argument("--pages", type=int, default=40, help="Pages to fetch (50 entries/page, default 40=top 2000)")
    parser.add_argument("--history", action="store_true", help="Show our rank history")
    parser.add_argument("--movers", action="store_true", help="Show biggest movers since last snapshot")
    parser.add_argument("--neighborhood", action="store_true", help="Show leeks around our rank")
    args = parser.parse_args()

    if args.history:
        show_history()
        return

    if args.movers:
        show_movers()
        return

    api = login_api()
    try:
        # Always show our current rank
        rank_data = quick_rank(api)
        rank = rank_data.get("rank", "?")
        print(f"IAdonis rank: #{rank} (active: {rank_data.get('active', '?')})")

        if args.quick:
            return

        if args.neighborhood and not args.quick:
            # Take snapshot if needed, then show neighborhood
            pass

        # Take snapshot
        print(f"\nSnapshotting top {args.pages * ENTRIES_PER_PAGE} leeks...")
        snap_id = snapshot(api, max_pages=args.pages)
        print(f"Snapshot #{snap_id} complete.")

        # Show neighborhood
        show_neighborhood(snap_id)

    finally:
        api.close()


if __name__ == "__main__":
    main()
