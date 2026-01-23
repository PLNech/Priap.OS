import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import random
from dataclasses import dataclass, asdict

from leekwars_agent.simulator import FightOutcome
from leekwars_agent.py4j_simulator import Py4JSimulator

@dataclass
class SimulationStats:
    total_fights: int
    ai1_wins: int
    ai2_wins: int
    draws: int
    total_duration_ms: float
    avg_ms_per_fight: float
    fights_per_second: float

    def __str__(self):
        return (f"Total Fights: {self.total_fights}\n"
                f"Wins: AI1: {self.ai1_wins} ({self.ai1_wins/self.total_fights*100:.1f}%), "
                f"AI2: {self.ai2_wins} ({self.ai2_wins/self.total_fights*100:.1f}%), "
                f"Draws: {self.draws} ({self.draws/self.total_fights*100:.1f}%)\n"
                f"Performance: {self.fights_per_second:.2f} fights/sec ({self.avg_ms_per_fight:.2f} ms/fight)")

class ParallelSimulator:
    def __init__(self, use_py4j: bool = True):
        self.use_py4j = use_py4j
        self.project_root = Path(__file__).parent.parent.parent
        self.gen_path = self.project_root / "tools" / "leek-wars-generator"

    def run_batch(self, fights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a batch of fights."""
        start_time = time.perf_counter()
        
        results = []
        if self.use_py4j:
            sim = Py4JSimulator()
            for f in fights:
                try:
                    outcome = sim.run_1v1(f["ai1"], f["ai2"], level=f.get("level", 100), seed=f.get("seed", 0))
                    results.append({
                        "ai1": f["ai1"],
                        "ai2": f["ai2"],
                        "winner": outcome.winner,
                        "turns": outcome.turns,
                        "duration_ms": outcome.duration_ms,
                        "success": True
                    })
                except Exception as e:
                    results.append({"ai1": f["ai1"], "ai2": f["ai2"], "error": str(e), "success": False})
        else:
            # Fallback to single-process subprocess if needed, but Py4J is preferred
            from leekwars_agent.simulator import Simulator
            sim = Simulator(generator_path=self.gen_path)
            for f in fights:
                try:
                    outcome = sim.run_1v1(f["ai1"], f["ai2"], level=f.get("level", 100), seed=f.get("seed", 0))
                    results.append({
                        "ai1": f["ai1"],
                        "ai2": f["ai2"],
                        "winner": outcome.winner,
                        "turns": outcome.turns,
                        "duration_ms": outcome.duration_ms,
                        "success": True
                    })
                except Exception as e:
                    results.append({"ai1": f["ai1"], "ai2": f["ai2"], "error": str(e), "success": False})
            
        total_duration = (time.perf_counter() - start_time) * 1000
        
        # Calculate stats
        ai1_wins = sum(1 for r in results if r.get("winner") == 1)
        ai2_wins = sum(1 for r in results if r.get("winner") == 2)
        draws = sum(1 for r in results if r.get("winner") == 0)
        
        stats = SimulationStats(
            total_fights=len(fights),
            ai1_wins=ai1_wins,
            ai2_wins=ai2_wins,
            draws=draws,
            total_duration_ms=total_duration,
            avg_ms_per_fight=total_duration / len(fights) if fights else 0,
            fights_per_second=len(fights) / (total_duration / 1000) if total_duration > 0 else 0
        )
        
        return {"results": results, "stats": stats}

    def save_results(self, batch_result: Dict[str, Any], output_path: str):
        """Save simulation results to a JSON file for observability."""
        data = {
            "timestamp": time.time(),
            "stats": asdict(batch_result["stats"]),
            "results": batch_result["results"]
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Results saved to {output_path}")

if __name__ == "__main__":
    # Quick test
    psim = ParallelSimulator(use_py4j=True)
    
    # Get available AIs
    ais_dir = Path(__file__).parent.parent.parent / "ais"
    leek_files = list(ais_dir.glob("*.leek"))
    gen_path = Path(__file__).parent.parent.parent / "tools" / "leek-wars-generator"
    
    # Ensure AIs are in generator dir
    for f in leek_files:
        target = gen_path / f.name
        if not target.exists():
            target.write_text(f.read_text())

    test_fights = []
    for _ in range(50):
        test_fights.append({
            "ai1": random.choice(leek_files).name,
            "ai2": random.choice(leek_files).name,
            "level": 100,
            "seed": random.randint(0, 10000)
        })

    print(f"Running {len(test_fights)} fights with Py4J...")
    batch_result = psim.run_batch(test_fights)
    
    print("\n" + str(batch_result["stats"]))
    
    # Save for observability
    output_dir = Path(__file__).parent.parent.parent / "data" / "sim_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    psim.save_results(batch_result, str(output_dir / f"sim_{int(time.time())}.json"))
