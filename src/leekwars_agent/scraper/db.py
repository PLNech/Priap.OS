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
    ops_used INTEGER DEFAULT 0,  -- Operations consumed (from fight.data.ops)
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

-- Alpha Strike metrics per fight
CREATE TABLE IF NOT EXISTS alpha_strike_metrics (
    fight_id INTEGER PRIMARY KEY,
    team1_tp_efficiency REAL,
    team2_tp_efficiency REAL,
    team1_opening_buffs INTEGER,
    team2_opening_buffs INTEGER,
    opening_buff_delta INTEGER,
    ponr_turn INTEGER,
    high_win_chips_t1 INTEGER,
    high_win_chips_t2 INTEGER,
    computed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alpha_ponr ON alpha_strike_metrics(ponr_turn);

-- Opponent database: track rematches, identify easy/hard opponents
CREATE TABLE IF NOT EXISTS opponents (
    leek_id INTEGER PRIMARY KEY,
    leek_name TEXT,
    farmer_id INTEGER,
    farmer_name TEXT,
    total_fights INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0,
    avg_duration REAL DEFAULT 0,
    last_seen INTEGER,           -- fight_date of most recent fight
    last_fought_with INTEGER,    -- our leek_id at last encounter
    archetype TEXT,              -- inferred playstyle: rusher, kiter, tank, balanced
    common_chips TEXT,          -- JSON array of frequently used chips
    common_weapons TEXT,        -- JSON array of frequently used weapons
    level_first_seen INTEGER,
    level_last_seen INTEGER,
    talent_last_seen INTEGER,
    notes TEXT,                  -- manual notes
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_opponents_name ON opponents(leek_name);
CREATE INDEX IF NOT EXISTS idx_opponents_last_seen ON opponents(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_opponents_archetype ON opponents(archetype);
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

        fight_payload = fight_data.get("fight", fight_data)
        report = fight_payload.get("report", {}) or {}
        duration = report.get("duration")
        if duration is None:
            actions = fight_payload.get("data", {}).get("actions", [])
            duration = sum(1 for action in actions if action and action[0] == 6)

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
                fight_payload.get("winner"),
                fight_payload.get("type"),
                fight_payload.get("context"),
                duration or 0,
                sum(l.get("level", 0) for l in fight_payload.get("leeks1", [])),
                sum(l.get("level", 0) for l in fight_payload.get("leeks2", [])),
                fight_payload.get("date"),
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

    def store_leek_observation(self, fight_id: int, leek_data: dict, team: int, won: bool, ops_used: int = 0):
        """Store a leek's stats from a fight."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO leek_observations (
                fight_id, leek_id, farmer_id, level, talent, team, won,
                life, strength, agility, wisdom, resistance, magic, science, frequency,
                tp, mp, ops_used, observed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ops_used,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

    # =========================================================================
    # Alpha Strike Metrics
    # =========================================================================

    def store_alpha_strike(self, fight_id: int, metrics: dict):
        """Store Alpha Strike metrics for a fight."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO alpha_strike_metrics (
                fight_id,
                team1_tp_efficiency,
                team2_tp_efficiency,
                team1_opening_buffs,
                team2_opening_buffs,
                opening_buff_delta,
                ponr_turn,
                high_win_chips_t1,
                high_win_chips_t2,
                computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fight_id,
                metrics.get("team1_tp_efficiency"),
                metrics.get("team2_tp_efficiency"),
                metrics.get("team1_opening_buffs"),
                metrics.get("team2_opening_buffs"),
                metrics.get("opening_buff_delta"),
                metrics.get("ponr_turn"),
                metrics.get("high_win_chips_t1"),
                metrics.get("high_win_chips_t2"),
                metrics.get("computed_at", datetime.utcnow().isoformat()),
            ),
        )
        conn.commit()

    def get_alpha_strike(self, fight_id: int) -> dict | None:
        """Retrieve Alpha Strike metrics for a fight."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT
                team1_tp_efficiency,
                team2_tp_efficiency,
                team1_opening_buffs,
                team2_opening_buffs,
                opening_buff_delta,
                ponr_turn,
                high_win_chips_t1,
                high_win_chips_t2,
                computed_at
            FROM alpha_strike_metrics
            WHERE fight_id = ?
            """,
            (fight_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

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

    # =========================================================================
    # Opponent Tracking
    # =========================================================================

    def get_opponent(self, leek_id: int) -> dict | None:
        """Retrieve opponent record by leek_id."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM opponents WHERE leek_id = ?", (leek_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        # Parse JSON arrays
        if result.get("common_chips"):
            result["common_chips"] = json.loads(result["common_chips"])
        if result.get("common_weapons"):
            result["common_weapons"] = json.loads(result["common_weapons"])
        return result

    def get_opponent_by_name(self, name: str) -> dict | None:
        """Retrieve opponent record by leek name (partial match)."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM opponents WHERE leek_name LIKE ? LIMIT 1",
            (f"%{name}%",)
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        if result.get("common_chips"):
            result["common_chips"] = json.loads(result["common_chips"])
        if result.get("common_weapons"):
            result["common_weapons"] = json.loads(result["common_weapons"])
        return result

    def update_opponent_from_fight(
        self,
        opponent_leek_id: int,
        opponent_name: str,
        opponent_farmer_id: int,
        opponent_farmer_name: str,
        opponent_level: int,
        opponent_talent: int,
        opponent_team: int,
        opponent_won: bool,
        fight_id: int,
        fight_date: int,
        fight_duration: int,
        opponent_chips: list[int],
        opponent_weapons: list[int],
        our_leek_id: int,
    ):
        """Update opponent record after a fight."""
        conn = self._get_conn()
        now = datetime.utcnow().isoformat()

        # Check if opponent exists
        existing = self.get_opponent(opponent_leek_id)

        if existing:
            # Update existing record
            new_fights = existing["total_fights"] + 1
            new_wins = existing["wins"] + (1 if opponent_won else 0)
            new_losses = existing["losses"] + (0 if opponent_won else 1)
            new_draws = existing["draws"] + (1 if opponent_won is None else 0)

            # Update common chips/weapons
            existing_chips = set(json.loads(existing["common_chips"] or "[]"))
            existing_weapons = set(json.loads(existing["common_weapons"] or "[]"))
            updated_chips = list(existing_chips.union(opponent_chips))
            updated_weapons = list(existing_weapons.union(opponent_weapons))

            # Calculate new avg duration (weighted)
            new_avg_duration = (
                (existing["avg_duration"] * existing["total_fights"] + fight_duration)
                / new_fights
            )

            conn.execute(
                """
                UPDATE opponents SET
                    total_fights = ?,
                    wins = ?,
                    losses = ?,
                    draws = ?,
                    win_rate = ?,
                    avg_duration = ?,
                    last_seen = ?,
                    last_fought_with = ?,
                    common_chips = ?,
                    common_weapons = ?,
                    level_last_seen = ?,
                    talent_last_seen = ?,
                    updated_at = ?
                WHERE leek_id = ?
                """,
                (
                    new_fights, new_wins, new_losses, new_draws,
                    new_wins / new_fights if new_fights > 0 else 0,
                    new_avg_duration,
                    fight_date,
                    our_leek_id,
                    json.dumps(updated_chips[:10]),  # Keep top 10
                    json.dumps(updated_weapons[:5]),  # Keep top 5
                    opponent_level,
                    opponent_talent,
                    now,
                    opponent_leek_id,
                ),
            )
        else:
            # Create new record
            conn.execute(
                """
                INSERT INTO opponents (
                    leek_id, leek_name, farmer_id, farmer_name,
                    total_fights, wins, losses, draws, win_rate,
                    avg_duration, last_seen, last_fought_with,
                    archetype, common_chips, common_weapons,
                    level_first_seen, level_last_seen, talent_last_seen,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    opponent_leek_id, opponent_name, opponent_farmer_id, opponent_farmer_name,
                    1, 1 if opponent_won else 0, 0 if opponent_won else 1, 1 if opponent_won is None else 0,
                    1.0 if opponent_won else 0.0,
                    fight_duration,
                    fight_date,
                    our_leek_id,
                    None,  # archetype to be inferred
                    json.dumps(opponent_chips[:10]),
                    json.dumps(opponent_weapons[:5]),
                    opponent_level,
                    opponent_level,
                    opponent_talent,
                    now,
                    now,
                ),
            )
        conn.commit()

    def infer_opponent_archetype(self, leek_id: int) -> str | None:
        """Infer opponent archetype based on fight history patterns.

        Returns: 'rusher', 'kiter', 'tank', 'balanced', or None
        """
        conn = self._get_conn()

        # Get opponent's fight history from observations
        fights = conn.execute(
            """
            SELECT lo.*, f.duration
            FROM leek_observations lo
            JOIN fights f ON lo.fight_id = f.fight_id
            WHERE lo.leek_id = ?
            ORDER BY f.fight_date DESC
            LIMIT 50
            """,
            (leek_id,)
        ).fetchall()

        if not fights:
            return None

        # Analyze patterns
        total_fights = len(fights)
        avg_duration = sum(f["duration"] or 0 for f in fights) / total_fights if total_fights > 0 else 0

        # Calculate avg stats
        avg_tp = sum(f["tp"] or 0 for f in fights) / total_fights
        avg_mp = sum(f["mp"] or 0 for f in fights) / total_fights
        avg_strength = sum(f["strength"] or 0 for f in fights) / total_fights
        avg_agility = sum(f["agility"] or 0 for f in fights) / total_fights
        avg_frequency = sum(f["frequency"] or 0 for f in fights) / total_fights

        # Archetype inference based on behavioral patterns
        #
        # Rusher: STR-focused build, wins fast. High STR/AGI ratio, short fights.
        # Kiter: AGI-focused build, runs away. High AGI/STR ratio, moderate duration.
        # Tank: Frequency-focused build, outlasts. High frequency, long fights.
        # Balanced: No strong pattern.

        # Ratios (higher = more skewed toward that stat)
        str_agi_ratio = avg_strength / (avg_agility + 1)  # >1 = STR-focused, <1 = AGI-focused
        freq_norm = avg_frequency / 145  # 145 is approximate median
        dur_norm = avg_duration / 8  # 8 turns is typical

        # Primary classification: STR vs AGI focus
        is_str_build = str_agi_ratio > 1.5
        is_agi_build = str_agi_ratio < 0.8

        # Secondary: fight duration
        is_fast = avg_duration <= 5
        is_slow = avg_duration >= 12

        # Frequency indicates tank-like behavior
        is_high_freq = freq_norm > 1.2

        # Scoring-based classification
        rusher_score = 0
        kiter_score = 0
        tank_score = 0

        # Rusher: STR-focused + fast fights
        if is_str_build:
            rusher_score += 2
        if is_fast:
            rusher_score += 2
        if avg_duration < 4:
            rusher_score += 1

        # Kiter: AGI-focused
        if is_agi_build:
            kiter_score += 3
        if avg_mp > 8:
            kiter_score += 1
        if not is_fast and not is_slow:
            kiter_score += 1  # Kiters prolong fights but don't drag on

        # Tank: High frequency + slow fights
        if is_high_freq:
            tank_score += 2
        if is_slow:
            tank_score += 2
        if avg_tp > 25:
            tank_score += 1

        # Pick highest score, default to balanced
        scores = {"rusher": rusher_score, "kiter": kiter_score, "tank": tank_score, "balanced": 0}
        max_score = max(scores.values())

        if max_score >= 4:
            for arch, score in scores.items():
                if score == max_score and arch != "balanced":
                    return arch
            return "balanced"
        else:
            return "balanced"

    def update_archetype_for_opponent(self, leek_id: int):
        """Update archetype for an opponent based on their fight history."""
        archetype = self.infer_opponent_archetype(leek_id)
        if archetype:
            conn = self._get_conn()
            conn.execute(
                "UPDATE opponents SET archetype = ?, updated_at = ? WHERE leek_id = ?",
                (archetype, datetime.utcnow().isoformat(), leek_id)
            )
            conn.commit()

    def update_archetypes_batch(self, limit: int = 100):
        """Update archetypes for opponents that don't have one."""
        conn = self._get_conn()
        opponents = conn.execute(
            "SELECT leek_id FROM opponents WHERE archetype IS NULL LIMIT ?",
            (limit,)
        ).fetchall()

        updated = 0
        for row in opponents:
            self.update_archetype_for_opponent(row["leek_id"])
            updated += 1

        return updated

    def get_opponents_by_win_rate(self, min_fights: int = 3, ascending: bool = True) -> list[dict]:
        """Get opponents sorted by win rate (hardest first if ascending=False)."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT * FROM opponents
            WHERE total_fights >= ?
            ORDER BY win_rate """ + ("ASC" if ascending else "DESC") + """
            LIMIT 50
            """,
            (min_fights,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_recurring_opponents(self, min_encounters: int = 3) -> list[dict]:
        """Get opponents we've faced multiple times."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT * FROM opponents
            WHERE total_fights >= ?
            ORDER BY total_fights DESC, last_seen DESC
            """,
            (min_encounters,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_opponent_count(self) -> int:
        """Get total number of tracked opponents."""
        conn = self._get_conn()
        return conn.execute("SELECT COUNT(*) FROM opponents").fetchone()[0]

    def populate_opponents_from_history(self, our_leek_id: int):
        """Populate opponent database from existing fight history."""
        conn = self._get_conn()

        # Get all fights involving our leek
        fights = conn.execute(
            """
            SELECT
                f.fight_id, f.fight_date, f.duration, f.winner,
                lo1.leek_id as opp_id, lo1.level as opp_level, lo1.talent as opp_talent,
                lo1.team as opp_team, lo1.won as opp_won,
                lo1.weapons_used as opp_weapons, lo1.chips_used as opp_chips,
                lo2.farmer_id as opp_farmer_id
            FROM fights f
            JOIN leek_observations lo1 ON f.fight_id = lo1.fight_id
            JOIN leek_observations lo2 ON f.fight_id = lo2.fight_id
            WHERE lo1.leek_id != ? AND lo2.leek_id = ?
            ORDER BY f.fight_date DESC
            """,
            (our_leek_id, our_leek_id)
        ).fetchall()

        # We need leek names - for now, just use IDs
        # In a full implementation, we'd join with farmer/leek API data
        updated = 0
        for fight in fights:
            # Extract chip/weapon IDs from JSON
            try:
                chips = json.loads(fight["opp_chips"] or "[]")
                weapons = json.loads(fight["opp_weapons"] or "[]")
            except (json.JSONDecodeError, TypeError):
                chips = []
                weapons = []

            self.update_opponent_from_fight(
                opponent_leek_id=fight["opp_id"],
                opponent_name=f"LeeK #{fight['opp_id']}",  # Placeholder
                opponent_farmer_id=fight["opp_farmer_id"] or 0,
                opponent_farmer_name=None,  # Would need API lookup
                opponent_level=fight["opp_level"],
                opponent_talent=fight["opp_talent"],
                opponent_team=fight["opp_team"],
                opponent_won=fight["opp_won"],
                fight_id=fight["fight_id"],
                fight_date=fight["fight_date"],
                fight_duration=fight["duration"] or 0,
                opponent_chips=chips,
                opponent_weapons=weapons,
                our_leek_id=our_leek_id,
            )
            updated += 1

        return updated
