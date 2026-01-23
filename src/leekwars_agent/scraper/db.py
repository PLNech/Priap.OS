"""Fight database for scraper.

SQLite database for storing scraped fights and derived analytics.
Schema adapted from tagadai's comprehensive design.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Any


SCHEMA = """
-- Enable WAL mode for better concurrent access
PRAGMA journal_mode=WAL;

-- Main fights table
CREATE TABLE IF NOT EXISTS fights (
    fight_id INTEGER PRIMARY KEY,
    json_data TEXT NOT NULL,
    winner INTEGER,              -- 0=draw, 1=team1, 2=team2
    fight_type INTEGER,          -- 0=solo, 1=farmer, 2=team, 3=br
    context INTEGER,             -- 0=test, 1=challenge, 2=garden, 3=tournament
    duration INTEGER,            -- turns
    team1_levels INTEGER,        -- sum of team1 levels
    team2_levels INTEGER,        -- sum of team2 levels
    fight_date INTEGER,          -- unix timestamp
    downloaded_at TEXT NOT NULL
);

-- Scrape queue with priority
CREATE TABLE IF NOT EXISTS scrape_queue (
    fight_id INTEGER PRIMARY KEY,
    source TEXT,                 -- e.g., "leek:12345" or "tournament:108000"
    priority INTEGER DEFAULT 0,  -- higher = more important
    added_at TEXT NOT NULL
);

-- Leek observations from fights (authoritative stats at fight time)
CREATE TABLE IF NOT EXISTS leek_observations (
    fight_id INTEGER NOT NULL,
    leek_id INTEGER NOT NULL,
    farmer_id INTEGER,
    level INTEGER,
    talent INTEGER,
    team INTEGER,                -- 1 or 2
    won BOOLEAN,
    -- Stats at fight time
    life INTEGER,
    strength INTEGER,
    agility INTEGER,
    wisdom INTEGER,
    resistance INTEGER,
    magic INTEGER,
    science INTEGER,
    frequency INTEGER,
    tp INTEGER,
    mp INTEGER,
    -- Fight performance
    damage_dealt INTEGER DEFAULT 0,
    damage_received INTEGER DEFAULT 0,
    cells_moved INTEGER DEFAULT 0,
    weapons_used TEXT,           -- JSON array of weapon IDs
    chips_used TEXT,             -- JSON array of chip IDs
    turns_alive INTEGER DEFAULT 0,
    observed_at TEXT NOT NULL,
    PRIMARY KEY (fight_id, leek_id)
);

-- Level bracket statistics (aggregated)
CREATE TABLE IF NOT EXISTS level_stats (
    level_bucket TEXT PRIMARY KEY,  -- e.g., "25-30", "30-40"
    fight_count INTEGER DEFAULT 0,
    mean_talent REAL DEFAULT 0,
    mean_strength REAL DEFAULT 0,
    mean_agility REAL DEFAULT 0,
    win_rate_team1 REAL DEFAULT 0,  -- attacker advantage?
    avg_duration REAL DEFAULT 0,
    updated_at TEXT
);

-- Equipment usage statistics
CREATE TABLE IF NOT EXISTS equipment_stats (
    level_bucket TEXT NOT NULL,
    item_type TEXT NOT NULL,     -- "weapon" or "chip"
    item_id INTEGER NOT NULL,
    item_name TEXT,
    use_count INTEGER DEFAULT 0,
    leek_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    total_damage INTEGER DEFAULT 0,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (level_bucket, item_type, item_id)
);

-- Scraped players tracking (avoid re-scraping)
CREATE TABLE IF NOT EXISTS scraped_players (
    player_type TEXT,            -- "leek" or "farmer"
    player_id INTEGER,
    level INTEGER,
    talent INTEGER,
    last_scraped TEXT,
    PRIMARY KEY (player_type, player_id)
);

-- Scraper state (resumable)
CREATE TABLE IF NOT EXISTS scraper_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_fights_type ON fights(fight_type);
CREATE INDEX IF NOT EXISTS idx_fights_context ON fights(context);
CREATE INDEX IF NOT EXISTS idx_fights_date ON fights(fight_date DESC);
CREATE INDEX IF NOT EXISTS idx_queue_priority ON scrape_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_leek_obs_level ON leek_observations(level);
CREATE INDEX IF NOT EXISTS idx_leek_obs_leek ON leek_observations(leek_id);
CREATE INDEX IF NOT EXISTS idx_equipment_bucket ON equipment_stats(level_bucket);
"""


class FightDB:
    """SQLite database for fight scraping and analysis."""

    def __init__(self, db_path: str | Path = "data/fights_meta.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        conn = self._get_conn()
        conn.executescript(SCHEMA)
        conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # =========================================================================
    # Fight Storage
    # =========================================================================

    def has_fight(self, fight_id: int) -> bool:
        """Check if fight already exists in database."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT 1 FROM fights WHERE fight_id = ?", (fight_id,)
        )
        return cursor.fetchone() is not None

    def store_fight(self, fight_id: int, fight_data: dict) -> bool:
        """Store a fight in the database.

        Returns True if stored, False if already exists.
        """
        if self.has_fight(fight_id):
            return False

        fight = fight_data.get("fight", fight_data)

        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO fights (
                fight_id, json_data, winner, fight_type, context,
                duration, team1_levels, team2_levels, fight_date, downloaded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fight_id,
                json.dumps(fight_data),
                fight.get("winner"),
                fight.get("type"),
                fight.get("context"),
                len(fight.get("actions", [])),  # approximate duration
                sum(l.get("level", 0) for l in fight.get("leeks1", [])),
                sum(l.get("level", 0) for l in fight.get("leeks2", [])),
                fight.get("date"),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return True

    def get_fight(self, fight_id: int) -> dict | None:
        """Retrieve a fight from the database."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT json_data FROM fights WHERE fight_id = ?", (fight_id,)
        )
        row = cursor.fetchone()
        return json.loads(row["json_data"]) if row else None

    def fight_count(self) -> int:
        """Get total number of stored fights."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT COUNT(*) FROM fights")
        return cursor.fetchone()[0]

    # =========================================================================
    # Queue Management
    # =========================================================================

    def queue_fight(self, fight_id: int, source: str, priority: int = 0):
        """Add a fight ID to the scrape queue."""
        if self.has_fight(fight_id):
            return  # Already have it

        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR IGNORE INTO scrape_queue (fight_id, source, priority, added_at)
            VALUES (?, ?, ?, ?)
            """,
            (fight_id, source, priority, datetime.utcnow().isoformat()),
        )
        conn.commit()

    def pop_queue(self, limit: int = 1) -> list[int]:
        """Get and remove highest priority fight IDs from queue."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT fight_id FROM scrape_queue ORDER BY priority DESC LIMIT ?",
            (limit,),
        )
        fight_ids = [row["fight_id"] for row in cursor.fetchall()]

        if fight_ids:
            placeholders = ",".join("?" * len(fight_ids))
            conn.execute(
                f"DELETE FROM scrape_queue WHERE fight_id IN ({placeholders})",
                fight_ids,
            )
            conn.commit()

        return fight_ids

    def queue_size(self) -> int:
        """Get number of fights in queue."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT COUNT(*) FROM scrape_queue")
        return cursor.fetchone()[0]

    # =========================================================================
    # Leek Observations
    # =========================================================================

    def store_leek_observation(self, fight_id: int, leek_data: dict, team: int, won: bool):
        """Store a leek's stats from a fight."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO leek_observations (
                fight_id, leek_id, farmer_id, level, talent, team, won,
                life, strength, agility, wisdom, resistance, magic, science, frequency,
                tp, mp, observed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fight_id,
                leek_data.get("id"),
                leek_data.get("farmer"),
                leek_data.get("level"),
                leek_data.get("talent"),
                team,
                won,
                leek_data.get("life"),
                leek_data.get("strength"),
                leek_data.get("agility"),
                leek_data.get("wisdom"),
                leek_data.get("resistance"),
                leek_data.get("magic"),
                leek_data.get("science"),
                leek_data.get("frequency"),
                leek_data.get("tp"),
                leek_data.get("mp"),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

    # =========================================================================
    # Scraper State
    # =========================================================================

    def get_state(self, key: str, default: str = "") -> str:
        """Get scraper state value."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT value FROM scraper_state WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return row["value"] if row else default

    def set_state(self, key: str, value: str):
        """Set scraper state value."""
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO scraper_state (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()

    # =========================================================================
    # Analytics Queries
    # =========================================================================

    def get_level_distribution(self, min_level: int = 25, max_level: int = 100) -> dict:
        """Get fight count by level bracket."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT level, COUNT(*) as count
            FROM leek_observations
            WHERE level BETWEEN ? AND ?
            GROUP BY level
            ORDER BY level
            """,
            (min_level, max_level),
        )
        return {row["level"]: row["count"] for row in cursor.fetchall()}

    def get_stats_summary(self) -> dict:
        """Get summary statistics."""
        conn = self._get_conn()
        return {
            "fights": self.fight_count(),
            "queue": self.queue_size(),
            "observations": conn.execute(
                "SELECT COUNT(*) FROM leek_observations"
            ).fetchone()[0],
        }
