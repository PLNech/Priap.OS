"""Local fight simulator using Java generator subprocess.

This simulator uses real map layouts from the map library for accurate
simulation that matches online fight conditions.
"""

import json
import random
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
GENERATOR_PATH = PROJECT_ROOT / "tools" / "leek-wars-generator"
GENERATOR_JAR = GENERATOR_PATH / "generator.jar"
MAP_LIBRARY_FILE = PROJECT_ROOT / "data" / "map_library.json"


@dataclass
class MapConfig:
    """Map configuration for simulation."""
    id: int  # Non-zero to force spawn position usage
    width: int
    height: int
    type: int
    obstacles: dict[str, int]  # cell_id -> obstacle_type
    team1_spawns: list[int]  # Spawn cells for team 1
    team2_spawns: list[int]  # Spawn cells for team 2
    pattern: list[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "width": self.width,
            "height": self.height,
            "type": self.type,
            "obstacles": self.obstacles,
            "team1": self.team1_spawns,
            "team2": self.team2_spawns,
        }

    @classmethod
    def symmetric_empty(cls, width: int = 18, height: int = 18) -> "MapConfig":
        """Create an empty map with symmetric spawn positions."""
        stride = width * 2 - 1
        total_cells = stride * height - (width - 1)
        center = total_cells // 2

        return cls(
            id=1,
            width=width,
            height=height,
            type=0,
            obstacles={},
            team1_spawns=[center - 36],  # ~2 rows above center
            team2_spawns=[center + 36],  # ~2 rows below center
        )


class MapLibrary:
    """Library of real map layouts for simulation."""

    def __init__(self, library_path: Path = MAP_LIBRARY_FILE):
        self.library_path = library_path
        self._maps: list[dict] = []
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        if self.library_path.exists():
            data = json.loads(self.library_path.read_text())
            self._maps = data.get("maps", [])
        self._loaded = True

    def get_random_map(self) -> MapConfig:
        """Get a random map from the library with symmetric spawns."""
        self._load()
        if not self._maps:
            return MapConfig.symmetric_empty()

        m = random.choice(self._maps)
        return MapConfig(
            id=m.get("fight_id", 1),  # Use fight_id as map id
            width=m.get("width", 18),
            height=m.get("height", 18),
            type=m.get("type", 0),
            obstacles=m.get("obstacles", {}),
            team1_spawns=m.get("symmetric_spawns", {}).get("team1", [306]),
            team2_spawns=m.get("symmetric_spawns", {}).get("team2", [308]),
            pattern=m.get("pattern"),
        )

    def get_map_by_index(self, index: int) -> MapConfig:
        """Get a specific map by index."""
        self._load()
        if not self._maps:
            return MapConfig.symmetric_empty()

        m = self._maps[index % len(self._maps)]
        return MapConfig(
            id=m.get("fight_id", 1),
            width=m.get("width", 18),
            height=m.get("height", 18),
            type=m.get("type", 0),
            obstacles=m.get("obstacles", {}),
            team1_spawns=m.get("symmetric_spawns", {}).get("team1", [306]),
            team2_spawns=m.get("symmetric_spawns", {}).get("team2", [308]),
        )

    def get_map_with_real_spawns(self, index: int = 0) -> MapConfig:
        """Get map with original (non-symmetric) spawn positions."""
        self._load()
        if not self._maps:
            return MapConfig.symmetric_empty()

        m = self._maps[index % len(self._maps)]
        return MapConfig(
            id=m.get("fight_id", 1),
            width=m.get("width", 18),
            height=m.get("height", 18),
            type=m.get("type", 0),
            obstacles=m.get("obstacles", {}),
            team1_spawns=m.get("team1_spawns", [306]),
            team2_spawns=m.get("team2_spawns", [308]),
        )

    @property
    def count(self) -> int:
        self._load()
        return len(self._maps)


# Global map library instance
_map_library: MapLibrary | None = None


def get_map_library() -> MapLibrary:
    global _map_library
    if _map_library is None:
        _map_library = MapLibrary()
    return _map_library


@dataclass
class EntityConfig:
    """Configuration for a fight entity (leek/bulb)."""
    id: int
    name: str
    ai: str  # Path to AI file relative to generator dir
    level: int = 1
    life: int = 100
    tp: int = 10
    mp: int = 3
    strength: int = 0
    agility: int = 0
    wisdom: int = 0
    resistance: int = 0
    science: int = 0
    magic: int = 0
    frequency: int = 0
    cores: int = 1
    ram: int = 100
    farmer: int = 1
    team: int = 1
    weapons: list[int] = field(default_factory=list)
    chips: list[int] = field(default_factory=list)
    type: int = 0  # 0=Leek, 1=Bulb, 2=Turret

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "ai": self.ai,
            "type": self.type,
            "farmer": self.farmer,
            "team": self.team,
            "level": self.level,
            "life": self.life,
            "tp": self.tp,
            "mp": self.mp,
            "strength": self.strength,
            "agility": self.agility,
            "wisdom": self.wisdom,
            "resistance": self.resistance,
            "science": self.science,
            "magic": self.magic,
            "frequency": self.frequency,
            "cores": self.cores,
            "ram": self.ram,
            "weapons": self.weapons,
            "chips": self.chips,
            # cell omitted - uses map.team1/team2 spawn arrays
        }


@dataclass
class ScenarioConfig:
    """Full scenario configuration."""
    team1: list[EntityConfig]
    team2: list[EntityConfig]
    map_config: MapConfig | None = None  # Use real map if provided
    seed: int | None = None
    max_turns: int = 64
    starter_team: int = 0  # 0=frequency-based, 1=team1 first, 2=team2 first

    def to_dict(self) -> dict[str, Any]:
        # Collect unique farmers
        farmers = {}
        for e in self.team1 + self.team2:
            if e.farmer not in farmers:
                farmers[e.farmer] = {
                    "id": e.farmer,
                    "name": f"Farmer{e.farmer}",
                    "country": "fr"
                }

        # Collect unique teams
        teams = {}
        for e in self.team1:
            if e.team not in teams:
                teams[e.team] = {"id": e.team, "name": f"Team{e.team}"}
        for e in self.team2:
            if e.team not in teams:
                teams[e.team] = {"id": e.team, "name": f"Team{e.team}"}

        # Use provided map or default symmetric map
        if self.map_config:
            map_dict = self.map_config.to_dict()
        else:
            # Fallback to symmetric empty map (not recommended)
            map_dict = MapConfig.symmetric_empty().to_dict()

        scenario = {
            "farmers": list(farmers.values()),
            "teams": list(teams.values()),
            "entities": [
                [e.to_dict() for e in self.team1],
                [e.to_dict() for e in self.team2],
            ],
            "map": map_dict,
            "max_turns": self.max_turns,
        }
        if self.seed is not None:
            scenario["random_seed"] = self.seed
        if self.starter_team > 0:
            scenario["starter_team"] = self.starter_team
        return scenario


@dataclass
class FightOutcome:
    """Result of a simulated fight."""
    winner: int  # 0=draw/timeout, 1=team1, 2=team2
    turns: int
    actions: list[list[Any]]
    duration_ms: float
    raw_output: dict[str, Any]
    map_id: int = 0

    @property
    def team1_won(self) -> bool:
        return self.winner == 1

    @property
    def team2_won(self) -> bool:
        return self.winner == 2

    @property
    def is_draw(self) -> bool:
        return self.winner == 0


class Simulator:
    """Local fight simulator using Java generator with real maps."""

    def __init__(self, generator_path: Path = GENERATOR_PATH):
        self.generator_path = generator_path
        self.jar_path = generator_path / "generator.jar"
        self.map_library = get_map_library()

        if not self.jar_path.exists():
            raise FileNotFoundError(
                f"generator.jar not found at {self.jar_path}. "
                "Build with: cd tools/leek-wars-generator && ./gradlew jar"
            )

    def run_scenario(self, scenario: ScenarioConfig) -> FightOutcome:
        """Run a fight scenario and return the outcome."""
        scenario_dict = scenario.to_dict()
        map_id = scenario_dict.get("map", {}).get("id", 0)

        # Write scenario to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", dir=self.generator_path, delete=False
        ) as f:
            json.dump(scenario_dict, f)
            scenario_file = Path(f.name)

        try:
            start = time.perf_counter()
            result = subprocess.run(
                ["java", "-jar", "generator.jar", scenario_file.name],
                cwd=self.generator_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            duration_ms = (time.perf_counter() - start) * 1000

            if result.returncode != 0:
                raise RuntimeError(f"Generator failed: {result.stderr}")

            # Parse JSON output
            output = json.loads(result.stdout)

            # ALWAYS compute winner from dead status - generator's winner field
            # uses team INDEX (0-based) not team ID (1-based), so it's unreliable
            dead = output.get("fight", {}).get("dead", {})
            leeks = output.get("fight", {}).get("leeks", [])

            # Calculate who's alive by Team ID (1 or 2)
            team1_alive = any(not dead.get(str(l["id"]), False) for l in leeks if l["team"] == 1)
            team2_alive = any(not dead.get(str(l["id"]), False) for l in leeks if l["team"] == 2)

            if team1_alive and not team2_alive:
                winner = 1
            elif team2_alive and not team1_alive:
                winner = 2
            else:
                winner = 0  # Draw or both alive/dead

            fight = output.get("fight", {})

            return FightOutcome(
                winner=winner,
                turns=output.get("duration", 0),
                actions=fight.get("actions", []),
                duration_ms=duration_ms,
                raw_output=output,
                map_id=map_id,
            )

        finally:
            scenario_file.unlink()

    def run_1v1(
        self,
        ai1: str,
        ai2: str,
        level: int = 1,
        seed: int | None = None,
        map_config: MapConfig | None = None,
        use_random_map: bool = True,
    ) -> FightOutcome:
        """Run a 1v1 fight with real map and symmetric spawns.

        Args:
            ai1: AI file for team 1
            ai2: AI file for team 2
            level: Leek level (affects HP)
            seed: RNG seed for reproducibility
            map_config: Specific map to use (overrides random)
            use_random_map: Use random map from library (default True)
        """
        # Get map
        if map_config:
            game_map = map_config
        elif use_random_map and self.map_library.count > 0:
            game_map = self.map_library.get_random_map()
        else:
            game_map = MapConfig.symmetric_empty()

        # Create leeks
        leek1 = EntityConfig(
            id=0,
            name="Leek1",
            ai=ai1,
            level=level,
            life=100 + level * 3,
            tp=10,
            mp=3,
            farmer=1,
            team=1,
            weapons=[37],  # WEAPON_PISTOL
        )
        leek2 = EntityConfig(
            id=1,
            name="Leek2",
            ai=ai2,
            level=level,
            life=100 + level * 3,
            tp=10,
            mp=3,
            farmer=2,
            team=2,
            weapons=[37],
        )

        scenario = ScenarioConfig(
            team1=[leek1],
            team2=[leek2],
            map_config=game_map,
            seed=seed,
        )
        return self.run_scenario(scenario)

    def run_1v1_fair(
        self,
        ai1: str,
        ai2: str,
        level: int = 1,
        seed: int | None = None,
        n_rounds: int = 25,
    ) -> dict[str, Any]:
        """Run fair 1v1 comparison with position/turn-order swap.

        Each round runs the fight twice:
        - Round A: ai1=Team0, ai2=Team1
        - Round B: ai1=Team1, ai2=Team0

        This eliminates first-mover and positional bias.
        Returns aggregate statistics.
        """
        results = {
            "ai1_wins": 0,
            "ai2_wins": 0,
            "draws": 0,
            "total_fights": 0,
            "fights": [],
        }

        for i in range(n_rounds):
            map_config = self.map_library.get_map_by_index(i % self.map_library.count)
            fight_seed = (seed + i * 1000) if seed is not None else None

            # Round A: ai1 as Team0 (first position)
            result_a = self.run_1v1(ai1, ai2, level, fight_seed, map_config)
            results["total_fights"] += 1

            if result_a.team1_won:
                results["ai1_wins"] += 1
                winner_a = "ai1"
            elif result_a.team2_won:
                results["ai2_wins"] += 1
                winner_a = "ai2"
            else:
                results["draws"] += 1
                winner_a = "draw"

            # Round B: ai2 as Team0 (swap positions)
            result_b = self.run_1v1(ai2, ai1, level, fight_seed, map_config)
            results["total_fights"] += 1

            if result_b.team1_won:
                results["ai2_wins"] += 1  # ai2 was Team0
                winner_b = "ai2"
            elif result_b.team2_won:
                results["ai1_wins"] += 1  # ai1 was Team1
                winner_b = "ai1"
            else:
                results["draws"] += 1
                winner_b = "draw"

            results["fights"].append({
                "round": i,
                "map_id": result_a.map_id,
                "seed": fight_seed,
                "a_winner": winner_a,
                "b_winner": winner_b,
            })

        total_decided = results["ai1_wins"] + results["ai2_wins"]
        results["ai1_win_rate"] = results["ai1_wins"] / total_decided if total_decided > 0 else 0.5
        results["ai2_win_rate"] = results["ai2_wins"] / total_decided if total_decided > 0 else 0.5

        return results

    def run_mirror_fair(
        self,
        ai: str,
        level: int = 1,
        seed: int | None = None,
        n_rounds: int = 50,
    ) -> dict[str, Any]:
        """Run mirror match fairness test.

        For identical AIs, we expect ~50% win rate for each position.
        This validates the simulator has no inherent bias.
        """
        results = {
            "team0_wins": 0,
            "team1_wins": 0,
            "draws": 0,
            "total_fights": 0,
        }

        for i in range(n_rounds):
            map_config = self.map_library.get_map_by_index(i % self.map_library.count)
            fight_seed = (seed + i) if seed is not None else None

            result = self.run_1v1(ai, ai, level, fight_seed, map_config)
            results["total_fights"] += 1

            if result.team1_won:
                results["team0_wins"] += 1  # team1 in output = Team0 internally
            elif result.team2_won:
                results["team1_wins"] += 1
            else:
                results["draws"] += 1

        total_decided = results["team0_wins"] + results["team1_wins"]
        if total_decided > 0:
            results["team0_rate"] = results["team0_wins"] / total_decided
            results["team1_rate"] = results["team1_wins"] / total_decided
            results["bias"] = abs(results["team0_wins"] - results["team1_wins"]) / total_decided
        else:
            results["team0_rate"] = 0.5
            results["team1_rate"] = 0.5
            results["bias"] = 0.0

        return results


def benchmark(n_fights: int = 100, **kwargs) -> dict[str, float]:
    """Benchmark simulator throughput with real maps."""
    sim = Simulator()

    # Create a simple test AI
    test_ai = GENERATOR_PATH / "test_bench.leek"
    test_ai.write_text("""
var enemy = getNearestEnemy()
if (!enemy) return
moveToward(enemy)
if (getWeapon() != WEAPON_PISTOL) setWeapon(WEAPON_PISTOL)
useWeapon(enemy)
""")

    try:
        start = time.perf_counter()
        for i in range(n_fights):
            sim.run_1v1("test_bench.leek", "test_bench.leek", seed=i)
        total_time = time.perf_counter() - start

        return {
            "fights": n_fights,
            "total_seconds": total_time,
            "fights_per_second": n_fights / total_time,
            "ms_per_fight": (total_time / n_fights) * 1000,
            "maps_available": sim.map_library.count,
        }
    finally:
        test_ai.unlink()


if __name__ == "__main__":
    print("Testing simulator with real maps...")

    sim = Simulator()
    print(f"Maps available: {sim.map_library.count}")

    # Test mirror match fairness
    print("\nRunning 50 mirror matches with symmetric spawns...")
    wins = {0: 0, 1: 0, 2: 0}

    for i in range(50):
        result = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=i)
        wins[result.winner] = wins.get(result.winner, 0) + 1

    print(f"Results:")
    print(f"  Team 1 wins: {wins.get(1, 0)}/50 ({wins.get(1, 0) * 2}%)")
    print(f"  Team 2 wins: {wins.get(2, 0)}/50 ({wins.get(2, 0) * 2}%)")
    print(f"  Draws:       {wins.get(0, 0)}/50 ({wins.get(0, 0) * 2}%)")

    non_draws = wins.get(1, 0) + wins.get(2, 0)
    if non_draws > 0:
        bias = abs(wins.get(1, 0) - wins.get(2, 0)) / non_draws * 100
        print(f"  Bias: {bias:.1f}% (should be <10% for fair simulation)")
