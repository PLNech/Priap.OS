"""Unified fight database with SQLite backend.

Provides cache-first access pattern:
1. Check local DB
2. Fetch from API if missing
3. Store in DB for future access

This replaces scattered JSON files with a single source of truth.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any
from contextlib import contextmanager


DB_PATH = Path(__file__).parent.parent.parent / "data" / "fights.db"


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize database schema with migration support."""
    with db_connection() as conn:
        # Create table if not exists
        conn.executescript("""
            -- Core fight data
            CREATE TABLE IF NOT EXISTS fights (
                id INTEGER PRIMARY KEY,
                date INTEGER,
                winner INTEGER,
                status INTEGER,
                context INTEGER,
                seed INTEGER,
                duration INTEGER,
                data JSON,
                fetched_at TEXT,
                parsed_at TEXT
            );

            -- Leek metadata
            CREATE TABLE IF NOT EXISTS leeks (
                id INTEGER PRIMARY KEY,
                name TEXT,
                level INTEGER,
                talent INTEGER,
                farmer_id INTEGER,
                farmer_name TEXT,
                last_seen TEXT
            );

            -- Fight participants (many-to-many)
            CREATE TABLE IF NOT EXISTS fight_participants (
                fight_id INTEGER,
                leek_id INTEGER,
                team INTEGER,
                strength INTEGER,
                agility INTEGER,
                wisdom INTEGER,
                resistance INTEGER,
                science INTEGER,
                magic INTEGER,
                frequency INTEGER,
                ops_used INTEGER,
                damage_dealt INTEGER,
                damage_taken INTEGER,
                PRIMARY KEY (fight_id, leek_id),
                FOREIGN KEY (fight_id) REFERENCES fights(id),
                FOREIGN KEY (leek_id) REFERENCES leeks(id)
            );

            -- Fight index for quick lookups
            CREATE INDEX IF NOT EXISTS idx_fights_date ON fights(date DESC);
            CREATE INDEX IF NOT EXISTS idx_fights_winner ON fights(winner);
            CREATE INDEX IF NOT EXISTS idx_participants_leek ON fight_participants(leek_id);
            CREATE INDEX IF NOT EXISTS idx_leeks_talent ON leeks(talent DESC);
        """)
        
        # Migration: Add missing columns if they don't exist
        try:
            conn.execute("ALTER TABLE fights ADD COLUMN status INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            conn.execute("ALTER TABLE fights ADD COLUMN seed INTEGER")
        except sqlite3.OperationalError:
            pass
        
        try:
            conn.execute("ALTER TABLE fights ADD COLUMN duration INTEGER")
        except sqlite3.OperationalError:
            pass
        
        try:
            conn.execute("ALTER TABLE fights ADD COLUMN fetched_at TEXT")
        except sqlite3.OperationalError:
            pass

        # Migration for leeks table
        try:
            conn.execute("ALTER TABLE leeks ADD COLUMN farmer_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE leeks ADD COLUMN farmer_name TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE leeks ADD COLUMN last_seen TEXT")
        except sqlite3.OperationalError:
            pass

        # Migration for fight_participants table (create if not exists)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS fight_participants (
                fight_id INTEGER,
                leek_id INTEGER,
                team INTEGER,
                strength INTEGER,
                agility INTEGER,
                wisdom INTEGER,
                resistance INTEGER,
                science INTEGER,
                magic INTEGER,
                frequency INTEGER,
                ops_used INTEGER,
                damage_dealt INTEGER,
                damage_taken INTEGER,
                PRIMARY KEY (fight_id, leek_id),
                FOREIGN KEY (fight_id) REFERENCES fights(id),
                FOREIGN KEY (leek_id) REFERENCES leeks(id)
            );
        """)

        # Add missing columns to fight_participants
        for col, type_ in [
            ("strength", "INTEGER"),
            ("agility", "INTEGER"),
            ("wisdom", "INTEGER"),
            ("resistance", "INTEGER"),
            ("science", "INTEGER"),
            ("magic", "INTEGER"),
            ("frequency", "INTEGER"),
            ("ops_used", "INTEGER"),
            ("damage_dealt", "INTEGER"),
            ("damage_taken", "INTEGER"),
        ]:
            try:
                conn.execute(f"ALTER TABLE fight_participants ADD COLUMN {col} {type_}")
            except sqlite3.OperationalError:
                pass


def store_fight(fight_data: dict) -> int:
    """Store a fight in the database. Returns fight ID."""
    fight_id = fight_data.get("id")
    if not fight_id:
        raise ValueError("Fight data missing ID")

    # Skip incomplete fights (status=0 means still processing)
    if fight_data.get("status") == 0:
        return fight_id  # Return but don't store incomplete fight

    data = fight_data.get("data") or {}
    actions = data.get("actions", [])
    turns = sum(1 for a in actions if a[0] == 6)  # NEW_TURN = 6

    with db_connection() as conn:
        # Insert or update fight
        conn.execute("""
            INSERT OR REPLACE INTO fights
            (id, date, winner, status, context, seed, duration, data, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fight_id,
            fight_data.get("date"),
            fight_data.get("winner"),
            fight_data.get("status"),
            fight_data.get("context"),
            fight_data.get("seed"),
            turns,
            json.dumps(fight_data),
            datetime.now().isoformat(),
        ))

        # Store leeks from both teams
        for team_num, team_key in [(1, "leeks1"), (2, "leeks2")]:
            for leek in fight_data.get(team_key, []):
                leek_id = leek.get("id")
                farmer_id = leek.get("farmer")
                farmer_name = None

                # Get farmer name if available
                farmers_key = f"farmers{team_num}"
                if farmers_key in fight_data and farmer_id:
                    farmer_info = fight_data[farmers_key].get(str(farmer_id), {})
                    farmer_name = farmer_info.get("name")

                conn.execute("""
                    INSERT OR REPLACE INTO leeks
                    (id, name, level, talent, farmer_id, farmer_name, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    leek_id,
                    leek.get("name"),
                    leek.get("level"),
                    leek.get("talent"),
                    farmer_id,
                    farmer_name,
                    datetime.now().isoformat(),
                ))

        # Store participant stats from fight data
        leeks_data = data.get("leeks", [])
        ops_data = data.get("ops", {})

        for leek_data in leeks_data:
            entity_id = leek_data.get("id")  # 0 or 1
            leek_id = None
            team = leek_data.get("team")

            # Map entity_id to actual leek_id
            if team == 1 and fight_data.get("leeks1"):
                leek_id = fight_data["leeks1"][0].get("id") if entity_id == 0 else None
            elif team == 2 and fight_data.get("leeks2"):
                leek_id = fight_data["leeks2"][0].get("id") if entity_id == 1 else None

            # Better mapping: use farmer_id from leek_data
            farmer_id = leek_data.get("farmer")
            for team_key in ["leeks1", "leeks2"]:
                for l in fight_data.get(team_key, []):
                    if l.get("farmer") == farmer_id:
                        leek_id = l.get("id")
                        break

            if not leek_id:
                continue

            # Calculate damage dealt/taken from actions
            damage_dealt = 0
            damage_taken = 0
            for action in actions:
                if action[0] == 101:  # LOST_LIFE
                    damaged_entity = action[1]
                    dmg = action[2]
                    if damaged_entity == entity_id:
                        damage_taken += dmg
                    else:
                        damage_dealt += dmg

            conn.execute("""
                INSERT OR REPLACE INTO fight_participants
                (fight_id, leek_id, team, strength, agility, wisdom, resistance,
                 science, magic, frequency, ops_used, damage_dealt, damage_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fight_id,
                leek_id,
                team,
                leek_data.get("strength"),
                leek_data.get("agility"),
                leek_data.get("wisdom"),
                leek_data.get("resistance"),
                leek_data.get("science"),
                leek_data.get("magic"),
                leek_data.get("frequency"),
                ops_data.get(str(entity_id), 0),
                damage_dealt,
                damage_taken,
            ))

    return fight_id


def get_fight(fight_id: int) -> dict | None:
    """Get fight from database."""
    with db_connection() as conn:
        row = conn.execute(
            "SELECT data FROM fights WHERE id = ?", (fight_id,)
        ).fetchone()
        if row:
            return json.loads(row["data"])
    return None


def get_fight_ids() -> list[int]:
    """Get all stored fight IDs."""
    with db_connection() as conn:
        rows = conn.execute("SELECT id FROM fights ORDER BY date DESC").fetchall()
        return [row["id"] for row in rows]


def get_leek_fights(leek_id: int, limit: int = 100) -> list[dict]:
    """Get fights for a specific leek."""
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT f.data FROM fights f
            JOIN fight_participants fp ON f.id = fp.fight_id
            WHERE fp.leek_id = ?
            ORDER BY f.date DESC
            LIMIT ?
        """, (leek_id, limit)).fetchall()
        return [json.loads(row["data"]) for row in rows]


def get_stats() -> dict:
    """Get database statistics."""
    with db_connection() as conn:
        fights = conn.execute("SELECT COUNT(*) as c FROM fights").fetchone()["c"]
        leeks = conn.execute("SELECT COUNT(*) as c FROM leeks").fetchone()["c"]
        participants = conn.execute("SELECT COUNT(*) as c FROM fight_participants").fetchone()["c"]

        return {
            "fights": fights,
            "leeks": leeks,
            "participants": participants,
            "db_path": str(DB_PATH),
        }


def migrate_from_cache():
    """Migrate existing cached JSON files to SQLite."""
    from leekwars_agent import cache

    init_db()
    migrated = 0

    cache_dir = Path(__file__).parent.parent.parent / "data" / "cache" / "fights"
    for fight_file in cache_dir.glob("*.json"):
        try:
            fight_data = json.loads(fight_file.read_text())
            store_fight(fight_data)
            migrated += 1
        except Exception as e:
            print(f"Failed to migrate {fight_file}: {e}")

    return migrated


class FightDB:
    """High-level interface combining DB and API access."""

    def __init__(self, api=None):
        self.api = api
        init_db()

    def get_fight(self, fight_id: int, fetch: bool = True) -> dict | None:
        """Get fight, fetching from API if needed."""
        # Check DB first
        fight = get_fight(fight_id)
        if fight:
            return fight

        # Fetch from API if enabled
        if fetch and self.api:
            try:
                fight = self.api.get_fight(fight_id, use_cache=False)
                if fight:
                    store_fight(fight)
                    return fight
            except Exception as e:
                print(f"API fetch failed for {fight_id}: {e}")

        return None

    def batch_fetch(self, fight_ids: list[int], delay: float = 0.5) -> int:
        """Batch fetch multiple fights from API."""
        import time

        fetched = 0
        existing = set(get_fight_ids())

        for fight_id in fight_ids:
            if fight_id in existing:
                continue

            fight = self.get_fight(fight_id, fetch=True)
            if fight:
                fetched += 1

            if delay > 0:
                time.sleep(delay)

        return fetched

    def analyze_leek(self, leek_id: int) -> dict:
        """Analyze a leek's fight history."""
        fights = get_leek_fights(leek_id)

        if not fights:
            return {"error": "No fights found", "leek_id": leek_id}

        wins = 0
        losses = 0
        draws = 0
        total_damage = 0
        total_ops = 0

        for fight in fights:
            # Determine which team this leek was on
            leeks1 = fight.get("leeks1", [])
            leeks2 = fight.get("leeks2", [])

            if any(l.get("id") == leek_id for l in leeks1):
                our_team = 1
            else:
                our_team = 2

            winner = fight.get("winner")
            if winner == our_team:
                wins += 1
            elif winner == 0:
                draws += 1
            else:
                losses += 1

        return {
            "leek_id": leek_id,
            "total_fights": len(fights),
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": wins / len(fights) if fights else 0,
        }
