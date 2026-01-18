#!/usr/bin/env python3
"""Scrape fights from top LeekWars players.

Uses public APIs to collect fight data from top-ranked leeks.
Stores everything in SQLite for analysis.

Usage:
    poetry run python scripts/scrape_top_fights.py [--count N] [--headful]

API Discovery:
- /ranking/get/leek/talent/page/count - Geo-blocked (returns incorrect_country)
- /ranking/fun - Works! Returns top farmers by various metrics
- /farmer/get/<id> - Works! Returns farmer with all their leeks
- /leek/get/<id> - Works! Returns leek info + recent fights (6 fights)
- /fight/get/<id> - Works! Returns full fight data (public, no auth)

Strategy:
1. Get top farmers from /ranking/fun (trophies ranking = most active)
2. For each farmer, get their leeks from /farmer/get
3. For each leek, get recent fights from /leek/get
4. Fetch full fight data from /fight/get (cached)
5. Store in SQLite for analysis
"""

import argparse
import json
import sqlite3
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from leekwars_agent import cache

BASE_URL = "https://leekwars.com/api"
DB_PATH = Path(__file__).parent.parent / "data" / "fights.db"
RATE_LIMIT_DELAY = 0.5  # seconds between API calls


def init_db(conn: sqlite3.Connection, force_recreate: bool = False) -> None:
    """Initialize database schema.

    Args:
        force_recreate: If True, drop and recreate all tables
    """
    if force_recreate:
        conn.executescript("""
            DROP TABLE IF EXISTS fights;
            DROP TABLE IF EXISTS leeks;
            DROP TABLE IF EXISTS farmers;
            DROP TABLE IF EXISTS fight_participants;
        """)

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS fights (
            id INTEGER PRIMARY KEY,
            date INTEGER,
            winner INTEGER,
            type INTEGER,
            context INTEGER,
            data JSON,
            parsed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS leeks (
            id INTEGER PRIMARY KEY,
            name TEXT,
            level INTEGER,
            talent INTEGER,
            farmer_id INTEGER,
            last_scraped TEXT
        );

        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            talent INTEGER,
            last_scraped TEXT
        );

        CREATE TABLE IF NOT EXISTS fight_participants (
            fight_id INTEGER,
            leek_id INTEGER,
            team INTEGER,
            PRIMARY KEY (fight_id, leek_id)
        );

        CREATE INDEX IF NOT EXISTS idx_fights_date ON fights(date);
        CREATE INDEX IF NOT EXISTS idx_leeks_talent ON leeks(talent DESC);
        CREATE INDEX IF NOT EXISTS idx_leeks_farmer ON leeks(farmer_id);
        CREATE INDEX IF NOT EXISTS idx_participants_leek ON fight_participants(leek_id);
    """)
    conn.commit()


def get_top_farmers(count: int = 20) -> list[dict[str, Any]]:
    """Get top farmers from fun ranking (trophy count = most active)."""
    print(f"Fetching top {count} farmers from ranking/fun...")

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        resp = client.get("/ranking/fun")
        resp.raise_for_status()
        data = resp.json()

    # Get trophies ranking (most active players)
    for ranking in data.get("rankings", []):
        if ranking["title"] == "trophies":
            farmers = ranking["ranking"]["ranking"][:count]
            print(f"  Found {len(farmers)} farmers")
            return farmers

    return []


def get_farmer_leeks(farmer_id: int, client: httpx.Client) -> list[dict[str, Any]]:
    """Get all leeks for a farmer."""
    resp = client.get(f"/farmer/get/{farmer_id}")
    resp.raise_for_status()
    data = resp.json()

    farmer = data.get("farmer", {})
    leeks_dict = farmer.get("leeks", {})

    # Convert dict to list with farmer info
    leeks = []
    for leek_id, leek in leeks_dict.items():
        leek["farmer_id"] = farmer_id
        leek["farmer_name"] = farmer.get("name", "Unknown")
        leeks.append(leek)

    return leeks


def get_leek_fights(leek_id: int, client: httpx.Client) -> list[dict[str, Any]]:
    """Get recent fights for a leek."""
    resp = client.get(f"/leek/get/{leek_id}")
    resp.raise_for_status()
    data = resp.json()

    return data.get("fights", [])


def get_fight_data(fight_id: int, client: httpx.Client) -> dict[str, Any] | None:
    """Get full fight data (uses cache)."""
    # Check cache first
    cached = cache.get_fight(fight_id)
    if cached is not None:
        return cached

    # Fetch from API
    resp = client.get(f"/fight/get/{fight_id}")
    if resp.status_code == 429:  # Rate limited
        print(f"  Rate limited on fight {fight_id}, waiting...")
        time.sleep(5)
        return None

    resp.raise_for_status()
    data = resp.json()

    # Cache for future use
    cache.save_fight(fight_id, data)
    return data


def extract_participants(fight_data: dict[str, Any]) -> list[tuple[int, int, int]]:
    """Extract leek participants from fight data.

    Returns list of (fight_id, leek_id, team)
    """
    fight_id = fight_data.get("id")
    participants = []

    # From leeks1/leeks2 arrays (fight list format)
    for leek in fight_data.get("leeks1", []):
        leek_id = leek.get("id") if isinstance(leek, dict) else leek
        participants.append((fight_id, leek_id, 1))

    for leek in fight_data.get("leeks2", []):
        leek_id = leek.get("id") if isinstance(leek, dict) else leek
        participants.append((fight_id, leek_id, 2))

    return participants


def save_to_db(conn: sqlite3.Connection,
               farmers: list[dict],
               leeks: list[dict],
               fights: list[dict]) -> dict[str, int]:
    """Save scraped data to database."""
    now = datetime.now().isoformat()
    stats = {"farmers": 0, "leeks": 0, "fights": 0, "participants": 0}

    # Save farmers
    for farmer in farmers:
        conn.execute("""
            INSERT OR REPLACE INTO farmers (id, name, talent, last_scraped)
            VALUES (?, ?, ?, ?)
        """, (farmer["id"], farmer["name"], farmer.get("value", 0), now))
        stats["farmers"] += 1

    # Save leeks
    for leek in leeks:
        conn.execute("""
            INSERT OR REPLACE INTO leeks (id, name, level, talent, farmer_id, last_scraped)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (leek["id"], leek["name"], leek.get("level", 0),
              leek.get("talent", 0), leek.get("farmer_id"), now))
        stats["leeks"] += 1

    # Save fights
    for fight in fights:
        conn.execute("""
            INSERT OR REPLACE INTO fights (id, date, winner, type, context, data, parsed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fight["id"], fight.get("date"), fight.get("winner"),
              fight.get("type"), fight.get("context"),
              json.dumps(fight), now))
        stats["fights"] += 1

        # Save participants
        for fight_id, leek_id, team in extract_participants(fight):
            conn.execute("""
                INSERT OR IGNORE INTO fight_participants (fight_id, leek_id, team)
                VALUES (?, ?, ?)
            """, (fight_id, leek_id, team))
            stats["participants"] += 1

    conn.commit()
    return stats


def scrape_api(farmer_count: int = 10, verbose: bool = True, force_recreate: bool = False) -> dict[str, int]:
    """Scrape fights using public APIs."""
    # Initialize database
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn, force_recreate=force_recreate)

    all_farmers = []
    all_leeks = []
    all_fights = []
    seen_fights = set()

    # Step 1: Get top farmers
    top_farmers = get_top_farmers(farmer_count)
    all_farmers.extend(top_farmers)

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Step 2: Get leeks for each farmer
        for i, farmer in enumerate(top_farmers):
            farmer_id = farmer["id"]
            farmer_name = farmer["name"]

            if verbose:
                print(f"\n[{i+1}/{len(top_farmers)}] Scraping farmer: {farmer_name} (ID: {farmer_id})")

            time.sleep(RATE_LIMIT_DELAY)
            leeks = get_farmer_leeks(farmer_id, client)
            all_leeks.extend(leeks)

            if verbose:
                print(f"  Found {len(leeks)} leeks")

            # Step 3: Get fights for each leek
            for leek in leeks:
                leek_id = leek["id"]
                leek_name = leek["name"]

                time.sleep(RATE_LIMIT_DELAY)
                fights = get_leek_fights(leek_id, client)

                if verbose:
                    print(f"    Leek {leek_name}: {len(fights)} recent fights")

                # Step 4: Fetch full fight data
                for fight_meta in fights:
                    fight_id = fight_meta["id"]
                    if fight_id in seen_fights:
                        continue
                    seen_fights.add(fight_id)

                    time.sleep(RATE_LIMIT_DELAY)
                    fight_data = get_fight_data(fight_id, client)

                    if fight_data:
                        all_fights.append(fight_data)
                        if verbose:
                            print(f"      Fetched fight {fight_id}")

    # Save to database
    if verbose:
        print(f"\nSaving to database: {DB_PATH}")

    stats = save_to_db(conn, all_farmers, all_leeks, all_fights)
    conn.close()

    return stats


def scrape_browser_fallback(farmer_count: int = 10) -> dict[str, int]:
    """Fallback: Use Playwright for browser-based scraping.

    Only needed if API is blocked or rate limited.
    """
    print("Browser fallback not implemented yet")
    print("API scraping should work - try reducing farmer_count if rate limited")
    return {"farmers": 0, "leeks": 0, "fights": 0, "participants": 0}


def print_db_stats(conn: sqlite3.Connection) -> None:
    """Print database statistics."""
    print("\n=== Database Statistics ===")

    for table in ["farmers", "leeks", "fights", "fight_participants"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows")

    # Top leeks by talent
    print("\nTop 10 leeks by talent:")
    rows = conn.execute("""
        SELECT l.name, l.level, l.talent, f.name as farmer
        FROM leeks l
        LEFT JOIN farmers f ON l.farmer_id = f.id
        ORDER BY l.talent DESC
        LIMIT 10
    """).fetchall()
    for row in rows:
        print(f"  {row[0]} (L{row[1]}, T{row[2]}) - {row[3]}")

    # Recent fights
    print("\nRecent fights:")
    rows = conn.execute("""
        SELECT id, date, winner, type
        FROM fights
        ORDER BY date DESC
        LIMIT 5
    """).fetchall()
    for row in rows:
        dt = datetime.fromtimestamp(row[1]).strftime("%Y-%m-%d %H:%M")
        print(f"  Fight {row[0]}: {dt}, winner team {row[2]}")


def scrape_player(farmer_id: int, verbose: bool = True) -> dict[str, int]:
    """Scrape all fights from a specific farmer's leeks."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    all_leeks = []
    all_fights = []
    seen_fights = set()

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Get farmer info
        if verbose:
            print(f"Fetching farmer {farmer_id}...")
        resp = client.get(f"/farmer/get/{farmer_id}")
        resp.raise_for_status()
        data = resp.json()

        farmer = data.get("farmer", {})
        farmer_name = farmer.get("name", "Unknown")
        leeks_dict = farmer.get("leeks", {})

        if verbose:
            print(f"  Farmer: {farmer_name}")
            print(f"  Leeks: {len(leeks_dict)}")

        # Get leeks
        for leek_id, leek in leeks_dict.items():
            leek["farmer_id"] = farmer_id
            leek["farmer_name"] = farmer_name
            leek["id"] = int(leek_id)
            all_leeks.append(leek)

        # Get fights for each leek
        for leek in all_leeks:
            leek_id = leek["id"]
            leek_name = leek["name"]

            time.sleep(RATE_LIMIT_DELAY)
            fights = get_leek_fights(leek_id, client)

            if verbose:
                print(f"  Leek {leek_name}: {len(fights)} recent fights")

            for fight_meta in fights:
                fight_id = fight_meta["id"]
                if fight_id in seen_fights:
                    continue
                seen_fights.add(fight_id)

                time.sleep(RATE_LIMIT_DELAY)
                fight_data = get_fight_data(fight_id, client)

                if fight_data:
                    all_fights.append(fight_data)
                    if verbose:
                        print(f"    Fetched fight {fight_id}")

    # Save to database
    if verbose:
        print(f"\nSaving to database: {DB_PATH}")

    stats = save_to_db(conn, [{"id": farmer_id, "name": farmer_name, "value": 0}],
                       all_leeks, all_fights)
    conn.close()

    return stats


def main():
    parser = argparse.ArgumentParser(description="Scrape top LeekWars fights")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of top farmers to scrape (default: 10)")
    parser.add_argument("--player", type=int,
                        help="Scrape fights from a specific farmer ID")
    parser.add_argument("--headful", action="store_true",
                        help="Use browser-based scraping (fallback)")
    parser.add_argument("--stats", action="store_true",
                        help="Show database statistics and exit")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Reduce output verbosity")
    parser.add_argument("--reset", action="store_true",
                        help="Drop and recreate database tables (fixes schema issues)")
    args = parser.parse_args()

    # Stats only
    if args.stats:
        if not DB_PATH.exists():
            print(f"Database not found: {DB_PATH}")
            return
        conn = sqlite3.connect(DB_PATH)
        print_db_stats(conn)
        conn.close()
        return

    # Run scraper
    print(f"Starting LeekWars fight scraper...")
    print(f"  Database: {DB_PATH}")

    if args.player:
        print(f"  Target: Farmer ID {args.player}")
        stats = scrape_player(args.player, verbose=not args.quiet)
    elif args.headful:
        print(f"  Target: Top {args.count} farmers")
        print(f"  Mode: Browser")
        stats = scrape_browser_fallback(args.count)
    else:
        print(f"  Target: Top {args.count} farmers")
        print(f"  Mode: API")
        if args.reset:
            print(f"  Reset: Dropping and recreating tables")
        stats = scrape_api(args.count, verbose=not args.quiet, force_recreate=args.reset)

    print("\n=== Scraping Complete ===")
    print(f"  Farmers: {stats['farmers']}")
    print(f"  Leeks: {stats['leeks']}")
    print(f"  Fights: {stats['fights']}")
    print(f"  Participants: {stats['participants']}")

    # Show stats
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        print_db_stats(conn)
        conn.close()


if __name__ == "__main__":
    main()
