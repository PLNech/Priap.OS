"""PySim map library — real maps extracted from online fight replays.

Extracts obstacle layouts and spawn positions from fights stored in
fights_meta.db. Each 1v1 fight has a unique procedurally-generated map.

Usage:
    lib = RealMapLibrary()          # loads from DB on first access
    m = lib.random_map(rng)         # pick a random 1v1 map
    m = lib.get_map(index)          # deterministic by index
    grid = Grid(18, 18, obstacles=m.obstacles)
"""

from __future__ import annotations

import json
import pickle
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FightMap:
    """A map extracted from a real online fight."""
    obstacles: frozenset[int]  # cell IDs blocked by obstacles
    spawn1: int                # team 1 spawn cell
    spawn2: int                # team 2 spawn cell
    map_type: int              # game map type (0-7)
    fight_id: int              # source fight for provenance

    @property
    def obstacle_set(self) -> set[int]:
        return set(self.obstacles)


# Default DB path
_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "fights_meta.db"


class RealMapLibrary:
    """Library of real 1v1 maps from our fight database."""

    def __init__(self, db_path: Path | str | None = None):
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._maps: list[FightMap] | None = None

    def _load(self):
        if self._maps is not None:
            return

        # Try pickle cache first (>100x faster than JSON parsing)
        cache_path = self._db_path.with_suffix(".maps.pkl")
        if cache_path.exists() and self._db_path.exists():
            if cache_path.stat().st_mtime >= self._db_path.stat().st_mtime:
                try:
                    with open(cache_path, "rb") as f:
                        self._maps = pickle.load(f)
                    return
                except Exception:
                    pass  # stale/corrupt cache — rebuild

        self._maps = []

        if not self._db_path.exists():
            return

        conn = sqlite3.connect(str(self._db_path))
        cur = conn.cursor()
        cur.execute("SELECT fight_id, json_data FROM fights")

        for fight_id, json_str in cur.fetchall():
            try:
                fight = json.loads(json_str)
                d = fight.get("data", {})
                if isinstance(d, str):
                    d = json.loads(d)
                if not isinstance(d, dict):
                    continue

                m = d.get("map", {})
                if not isinstance(m, dict) or "obstacles" not in m:
                    continue

                leeks = d.get("leeks", [])
                teams: dict[int, list[int]] = {}
                for leek in leeks:
                    t = leek.get("team", 0)
                    teams.setdefault(t, []).append(leek.get("cellPos", -1))

                # Only 1v1: exactly 1 leek per team, 2 teams
                if len(teams) != 2 or any(len(v) != 1 for v in teams.values()):
                    continue

                sorted_teams = sorted(teams.keys())
                s1 = teams[sorted_teams[0]][0]
                s2 = teams[sorted_teams[1]][0]
                obs = frozenset(int(k) for k in m["obstacles"].keys())

                self._maps.append(FightMap(
                    obstacles=obs,
                    spawn1=s1,
                    spawn2=s2,
                    map_type=m.get("type", 0),
                    fight_id=fight_id,
                ))
            except Exception:
                continue

        conn.close()

        # Save cache for next load
        if self._maps:
            try:
                with open(cache_path, "wb") as f:
                    pickle.dump(self._maps, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception:
                pass

    @property
    def count(self) -> int:
        self._load()
        return len(self._maps)

    def get_map(self, index: int) -> FightMap:
        """Get map by index (wraps around). Deterministic."""
        self._load()
        if not self._maps:
            return FightMap(
                obstacles=frozenset(), spawn1=100, spawn2=450,
                map_type=0, fight_id=0,
            )
        return self._maps[index % len(self._maps)]

    def random_map(self, rng: random.Random | None = None) -> FightMap:
        """Pick a random map."""
        self._load()
        if not self._maps:
            return self.get_map(0)
        r = rng or random.Random()
        return r.choice(self._maps)

    def __repr__(self) -> str:
        self._load()
        return f"<RealMapLibrary: {len(self._maps)} 1v1 maps>"
