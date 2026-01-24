"""Fight scraper for meta analysis.

Politely downloads fights from LeekWars API with rate limiting.
Adapted from tagadai's architecture.
"""

import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable

from ..api import LeekWarsAPI
from .db import FightDB

logger = logging.getLogger(__name__)


@dataclass
class ScraperStats:
    """Real-time scraper statistics."""
    fights_downloaded: int = 0
    fights_skipped: int = 0
    fights_queued: int = 0
    errors: int = 0
    rate_limits: int = 0
    start_time: datetime = field(default_factory=datetime.utcnow)
    current_action: str = ""

    @property
    def runtime_seconds(self) -> float:
        return (datetime.utcnow() - self.start_time).total_seconds()

    @property
    def fights_per_minute(self) -> float:
        if self.runtime_seconds < 1:
            return 0
        return (self.fights_downloaded / self.runtime_seconds) * 60


class FightScraper:
    """
    LeekWars fight scraper with rate limiting.

    Features:
    - Polite rate limiting (respects API)
    - Level filtering (focus on L25-100)
    - Tournament-based discovery
    - Leek history following
    - Resumable queue
    """

    # Fight types
    TYPE_SOLO = 0
    TYPE_FARMER = 1
    TYPE_TEAM = 2
    TYPE_BR = 3

    # Context types
    CONTEXT_TEST = 0
    CONTEXT_CHALLENGE = 1
    CONTEXT_GARDEN = 2
    CONTEXT_TOURNAMENT = 3

    def __init__(
        self,
        api: LeekWarsAPI,
        db: FightDB | None = None,
        delay: float = 0.15,  # ~6-7 req/sec (safe margin under 10)
        min_level: int = 25,
        max_level: int = 100,
        skip_test_fights: bool = True,
    ):
        """
        Initialize scraper.

        Args:
            api: Authenticated LeekWarsAPI client
            db: FightDB instance (creates default if None)
            delay: Seconds between API requests
            min_level: Minimum leek level to include
            max_level: Maximum leek level to include
            skip_test_fights: Skip test/challenge fights
        """
        self.api = api
        self.db = db or FightDB()
        self.delay = delay
        self.min_level = min_level
        self.max_level = max_level
        self.skip_test_fights = skip_test_fights

        self.stats = ScraperStats()
        self._stop_requested = False

    def _wait(self):
        """Wait between requests (rate limiting)."""
        time.sleep(self.delay)

    def _request(self, endpoint: str, require_auth: bool = True) -> dict | None:
        """Make an API request with rate limiting and error handling."""
        try:
            self._wait()

            url = f"{self.api.BASE_URL}/{endpoint}"
            headers = self.api._headers() if require_auth else {}

            response = self.api._client.get(url, headers=headers)

            if response.status_code == 429:
                self.stats.rate_limits += 1
                logger.warning("Rate limited, waiting 10s...")
                time.sleep(10)
                return self._request(endpoint, require_auth)  # Retry

            if response.status_code == 401:
                # Try without auth for public endpoints
                if require_auth:
                    return self._request(endpoint, require_auth=False)
                self.stats.errors += 1
                logger.debug(f"Auth required for: {endpoint}")
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Request failed: {endpoint} - {e}")
            return None

    # =========================================================================
    # Discovery Methods
    # =========================================================================

    def bootstrap_from_own_leek(self, leek_id: int, history_count: int = 100) -> int:
        """
        Bootstrap discovery from our own leek's history.

        This is the most reliable method - our own history is always accessible.
        """
        self.stats.current_action = f"Bootstrapping from leek {leek_id}"

        # Get our history
        queued = self.discover_from_leek_history(leek_id, count=history_count)

        # Also get our opponents to find more leeks
        data = self._request(f"garden/get-leek-opponents/{leek_id}")
        if data:
            for opponent in data.get("opponents", []):
                opp_id = opponent.get("id")
                level = opponent.get("level", 0)
                if opp_id and self.min_level <= level <= self.max_level:
                    # Queue their history
                    self.discover_from_leek_history(opp_id, count=20)

        return queued

    def discover_from_tournament(self, tournament_id: int) -> int:
        """
        Discover fights and players from a tournament.

        Returns number of fights queued.
        """
        self.stats.current_action = f"Exploring tournament {tournament_id}"
        data = self._request(f"tournament/get/{tournament_id}")

        if not data or "error" in data:
            return 0

        queued = 0
        tournament = data.get("tournament", data)

        # Queue all fights from the tournament
        for fight in tournament.get("fights", []):
            fight_id = fight.get("id")
            if fight_id:
                self.db.queue_fight(
                    fight_id,
                    source=f"tournament:{tournament_id}",
                    priority=50,  # Tournament fights are valuable
                )
                queued += 1

        self.stats.fights_queued += queued
        return queued

    def discover_from_leek_history(self, leek_id: int, count: int = 50) -> int:
        """
        Discover fights from a leek's history.

        Returns number of fights queued.
        Note: API returns ALL fights (no pagination), count limits how many we queue.
        """
        self.stats.current_action = f"Fetching history for leek {leek_id}"
        # Correct endpoint from: tools/leek-wars/src/component/history/history.vue:163
        data = self._request(f"history/get-leek-history/{leek_id}")

        if not data:
            return 0

        queued = 0
        fights = data.get("fights", [])[:count]  # API returns ALL, we limit
        for fight in fights:
            fight_id = fight.get("id")
            if fight_id:
                self.db.queue_fight(
                    fight_id,
                    source=f"leek:{leek_id}",
                    priority=30,
                )
                queued += 1

        self.stats.fights_queued += queued
        return queued

    def discover_from_ranking(self, page: int = 0, count: int = 50) -> list[int]:
        """
        Discover leeks from the ranking.

        Returns list of leek IDs found.
        """
        self.stats.current_action = f"Fetching ranking page {page}"
        data = self._request(f"ranking/get-leek-ranking/{page}/{count}/talent")

        if not data:
            return []

        leek_ids = []
        for leek in data.get("ranking", []):
            leek_id = leek.get("id")
            level = leek.get("level", 0)

            # Filter by level
            if self.min_level <= level <= self.max_level:
                leek_ids.append(leek_id)

        return leek_ids

    def find_latest_tournament(self, start_id: int = 108000) -> int:
        """
        Find the latest valid tournament ID using binary search.

        Args:
            start_id: Known valid tournament ID to start from
        """
        self.stats.current_action = "Finding latest tournament..."

        low = start_id
        high = low + 5000

        def is_valid(data):
            return data and "error" not in data

        # Find upper bound
        while True:
            data = self._request(f"tournament/get/{high}")
            if not is_valid(data):
                break
            high += 500
            if high > 150000:
                break

        # Binary search
        latest = low
        while low <= high:
            mid = (low + high) // 2
            data = self._request(f"tournament/get/{mid}")
            if is_valid(data):
                latest = mid
                low = mid + 1
            else:
                high = mid - 1

        return latest

    def discover_graph_bfs(self, max_leeks: int = 50, fights_per_leek: int = 20) -> int:
        """
        BFS graph traversal: discover new fights from leeks we've observed.

        Uses leek_observations as edges in bipartite graph:
        Fight → Leeks → Their histories → New Fights → ...

        Args:
            max_leeks: Max leeks to explore per call
            fights_per_leek: Fights to queue per leek history

        Returns number of fights queued.
        """
        self.stats.current_action = "Graph BFS discovery"
        conn = self.db._get_conn()

        # Find leeks we've observed but haven't scraped yet
        # Using scraped_players table to track
        unscraped = conn.execute(
            """
            SELECT DISTINCT lo.leek_id, lo.level
            FROM leek_observations lo
            LEFT JOIN scraped_players sp
                ON sp.player_type = 'leek' AND sp.player_id = lo.leek_id
            WHERE sp.player_id IS NULL
                AND lo.level BETWEEN ? AND ?
            ORDER BY lo.level DESC
            LIMIT ?
            """,
            (self.min_level, self.max_level, max_leeks)
        ).fetchall()

        logger.info(f"BFS: {len(unscraped)} unscraped leeks to explore")
        total_queued = 0

        for row in unscraped:
            leek_id, level = row[0], row[1]

            # Mark as scraped
            conn.execute(
                """
                INSERT OR REPLACE INTO scraped_players
                (player_type, player_id, level, last_scraped)
                VALUES ('leek', ?, ?, datetime('now'))
                """,
                (leek_id, level)
            )
            conn.commit()

            # Get their history
            queued = self.discover_from_leek_history(leek_id, count=fights_per_leek)
            total_queued += queued

            if queued > 0:
                logger.debug(f"  L{level} #{leek_id}: +{queued} fights")

        self.stats.fights_queued += total_queued
        return total_queued

    # =========================================================================
    # Fight Processing
    # =========================================================================

    def _should_include_fight(self, fight_data: dict) -> bool:
        """Check if a fight meets our criteria."""
        fight = fight_data.get("fight", fight_data)

        # Skip test/challenge fights if configured
        if self.skip_test_fights:
            context = fight.get("context", 0)
            if context in (self.CONTEXT_TEST, self.CONTEXT_CHALLENGE):
                return False

        # Check level range
        leeks1 = fight.get("leeks1", [])
        leeks2 = fight.get("leeks2", [])
        all_leeks = leeks1 + leeks2

        if not all_leeks:
            return False

        # At least one leek should be in our level range
        levels = [l.get("level", 0) for l in all_leeks]
        if not any(self.min_level <= lvl <= self.max_level for lvl in levels):
            return False

        return True

    def process_fight(self, fight_id: int) -> bool:
        """
        Download and process a single fight.

        Returns True if fight was stored, False otherwise.
        """
        self.stats.current_action = f"Downloading fight {fight_id}"

        # Skip if already have it
        if self.db.has_fight(fight_id):
            self.stats.fights_skipped += 1
            return False

        # Fetch fight data
        data = self._request(f"fight/get/{fight_id}")
        if not data:
            return False

        # Check criteria
        if not self._should_include_fight(data):
            self.stats.fights_skipped += 1
            return False

        # Store fight
        self.db.store_fight(fight_id, data)
        self.stats.fights_downloaded += 1

        # Extract leek observations
        fight = data.get("fight", data)
        winner = fight.get("winner", 0)

        for leek in fight.get("leeks1", []):
            self.db.store_leek_observation(fight_id, leek, team=1, won=(winner == 1))

        for leek in fight.get("leeks2", []):
            self.db.store_leek_observation(fight_id, leek, team=2, won=(winner == 2))

        # Note: We could discover more fights from participants' histories,
        # but that's expensive (1 API call per leek). Bootstrap provides enough.

        return True

    # =========================================================================
    # Main Scrape Loop
    # =========================================================================

    def scrape(
        self,
        target_count: int = 1000,
        bootstrap_leek_id: int | None = None,
        discover_tournaments: int = 5,
        progress_callback: Callable[[ScraperStats], None] | None = None,
    ):
        """
        Run the scraper.

        Args:
            target_count: Target number of fights to download
            bootstrap_leek_id: Our leek ID to bootstrap from (most reliable)
            discover_tournaments: Number of recent tournaments to explore
            progress_callback: Called periodically with stats
        """
        self.stats = ScraperStats()
        self._stop_requested = False

        logger.info(f"Starting scrape: target={target_count}, levels={self.min_level}-{self.max_level}")

        # Phase 1: Bootstrap from our own leek (most reliable)
        if bootstrap_leek_id:
            logger.info(f"Bootstrapping from leek {bootstrap_leek_id}")
            self.bootstrap_from_own_leek(bootstrap_leek_id, history_count=100)

            if progress_callback:
                progress_callback(self.stats)

        # Phase 2: Try tournaments (may fail if auth issues)
        if discover_tournaments > 0 and not self._stop_requested:
            try:
                latest = self.find_latest_tournament()
                if latest > 0:
                    logger.info(f"Latest tournament: {latest}")

                    for i in range(discover_tournaments):
                        if self._stop_requested:
                            break
                        tournament_id = latest - i * 10
                        queued = self.discover_from_tournament(tournament_id)
                        if queued > 0:
                            logger.info(f"Tournament {tournament_id}: queued {queued} fights")

                        if progress_callback:
                            progress_callback(self.stats)
            except Exception as e:
                logger.warning(f"Tournament discovery failed: {e}")

        # Phase 3: Process queue
        empty_retries = 0
        while self.stats.fights_downloaded < target_count and not self._stop_requested:
            fight_ids = self.db.pop_queue(limit=10)

            if not fight_ids:
                empty_retries += 1
                if empty_retries > 3:
                    logger.info("Queue exhausted after retries")
                    break

                logger.info("Queue empty, trying to discover more...")
                # Try ranking (may fail with auth)
                leek_ids = self.discover_from_ranking(page=empty_retries - 1)
                if leek_ids:
                    self.discover_from_leek_history(leek_ids[0], count=50)
                continue

            empty_retries = 0  # Reset on success

            for fight_id in fight_ids:
                if self._stop_requested:
                    break
                self.process_fight(fight_id)

                if progress_callback and self.stats.fights_downloaded % 10 == 0:
                    progress_callback(self.stats)

        logger.info(f"Scrape complete: {self.stats.fights_downloaded} fights downloaded")
        return self.stats

    def stop(self):
        """Request graceful stop."""
        self._stop_requested = True
