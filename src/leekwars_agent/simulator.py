"""Local fight simulator using Java generator subprocess."""

import json
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Path to generator
GENERATOR_PATH = Path(__file__).parent.parent.parent / "tools" / "leek-wars-generator"
GENERATOR_JAR = GENERATOR_PATH / "generator.jar"


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
    cell: int | None = None
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
            "cell": self.cell if self.cell is not None else 100,  # Default cell
        }


@dataclass
class ScenarioConfig:
    """Full scenario configuration."""
    team1: list[EntityConfig]
    team2: list[EntityConfig]
    seed: int | None = None
    max_turns: int = 64
    map_width: int = 17
    map_height: int = 17
    obstacles: list[int] = field(default_factory=list)
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

        scenario = {
            "farmers": list(farmers.values()),
            "teams": list(teams.values()),
            "entities": [
                [e.to_dict() for e in self.team1],
                [e.to_dict() for e in self.team2],
            ],
            "map": {
                "width": self.map_width,
                "height": self.map_height,
                "type": 0,
                "obstacles": {str(o): True for o in self.obstacles},
            },
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
    winner: int  # -1=draw/timeout, 1=team1, 2=team2
    turns: int
    actions: list[list[Any]]
    duration_ms: float
    raw_output: dict[str, Any]

    @property
    def team1_won(self) -> bool:
        return self.winner == 1

    @property
    def team2_won(self) -> bool:
        return self.winner == 2

    @property
    def is_draw(self) -> bool:
        return self.winner in (0, -1)  # -1 = timeout draw


class Simulator:
    """Local fight simulator using Java generator."""

    def __init__(self, generator_path: Path = GENERATOR_PATH):
        self.generator_path = generator_path
        self.jar_path = generator_path / "generator.jar"

        if not self.jar_path.exists():
            raise FileNotFoundError(
                f"generator.jar not found at {self.jar_path}. "
                "Build with: cd tools/leek-wars-generator && ./gradlew jar"
            )

    def run_scenario(self, scenario: ScenarioConfig) -> FightOutcome:
        """Run a fight scenario and return the outcome."""
        scenario_dict = scenario.to_dict()

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

            # Compute winner from dead status (Java generator might return wrong winner)
            winner = output.get("winner", 0)
            dead = output.get("fight", {}).get("dead", {})
            leeks = output.get("fight", {}).get("leeks", [])

            # If winner is 0 (draw) but someone is dead, compute correct winner
            if winner == 0 and leeks and dead:
                team1_alive = any(not dead.get(str(l["id"]), False) for l in leeks if l["team"] == 1)
                team2_alive = any(not dead.get(str(l["id"]), False) for l in leeks if l["team"] == 2)

                if team1_alive and not team2_alive:
                    winner = 1
                elif team2_alive and not team1_alive:
                    winner = 2

            # Actions and turns are inside the "fight" object
            fight = output.get("fight", {})

            return FightOutcome(
                winner=winner,
                turns=output.get("duration", 0),  # "duration" is turn count
                actions=fight.get("actions", []),
                duration_ms=duration_ms,
                raw_output=output,
            )

        finally:
            scenario_file.unlink()

    def run_1v1(
        self,
        ai1: str,
        ai2: str,
        level: int = 1,
        seed: int | None = None,
    ) -> FightOutcome:
        """Convenience method for 1v1 fights with default stats."""
        # Level 1 stats: 100 HP, 10 TP, 3 MP, pistol
        # Map is 17x17 diamond, cells ~0-600
        # WEAPON_PISTOL = 37 (from FightConstants.java)
        leek1 = EntityConfig(
            id=1,
            name="Leek1",
            ai=ai1,
            level=level,
            life=100 + level * 3,
            tp=10,
            mp=3,
            farmer=1,
            team=1,
            cell=100,  # Near top
            weapons=[37],  # WEAPON_PISTOL = 37
        )
        leek2 = EntityConfig(
            id=2,
            name="Leek2",
            ai=ai2,
            level=level,
            life=100 + level * 3,
            tp=10,
            mp=3,
            farmer=2,
            team=2,
            cell=450,  # Near bottom
            weapons=[37],  # WEAPON_PISTOL = 37
        )

        scenario = ScenarioConfig(
            team1=[leek1],
            team2=[leek2],
            seed=seed,
        )
        return self.run_scenario(scenario)


def benchmark(n_fights: int = 100, **kwargs) -> dict[str, float]:
    """Benchmark simulator throughput."""
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
        }
    finally:
        test_ai.unlink()


if __name__ == "__main__":
    print("Benchmarking simulator...")
    results = benchmark(n_fights=50)
    print(f"Results: {results['fights_per_second']:.1f} fights/sec")
    print(f"         {results['ms_per_fight']:.1f} ms/fight")
