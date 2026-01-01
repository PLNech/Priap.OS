#!/usr/bin/env python3
"""Evaluate baseline agents against each other.

Measures win rates to establish performance baselines.
"""

import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.simulator import Simulator, GENERATOR_PATH


@dataclass
class EvalResult:
    """Evaluation results."""
    ai1: str
    ai2: str
    wins_ai1: int
    wins_ai2: int
    draws: int
    total: int

    @property
    def win_rate_ai1(self) -> float:
        return self.wins_ai1 / self.total if self.total > 0 else 0

    @property
    def win_rate_ai2(self) -> float:
        return self.wins_ai2 / self.total if self.total > 0 else 0


def copy_ai_to_generator(source: Path, name: str) -> str:
    """Copy AI file to generator directory."""
    dest = GENERATOR_PATH / name
    dest.write_text(source.read_text())
    return name


def evaluate(ai1: str, ai2: str, n_games: int = 50, seed_base: int = 0) -> EvalResult:
    """Evaluate two AIs against each other."""
    sim = Simulator()
    wins_ai1 = 0
    wins_ai2 = 0
    draws = 0

    for i in range(n_games):
        outcome = sim.run_1v1(ai1, ai2, seed=seed_base + i)
        if outcome.team1_won:
            wins_ai1 += 1
        elif outcome.team2_won:
            wins_ai2 += 1
        else:
            draws += 1

    return EvalResult(
        ai1=ai1, ai2=ai2,
        wins_ai1=wins_ai1, wins_ai2=wins_ai2, draws=draws,
        total=n_games
    )


def main():
    """Run baseline evaluations."""
    agents_dir = Path(__file__).parent.parent / "src" / "leekwars_agent" / "agents" / "ai"

    # Copy baseline AIs to generator directory
    print("Setting up AIs...")
    random_ai = copy_ai_to_generator(agents_dir / "random.leek", "baseline_random.leek")
    heuristic_ai = copy_ai_to_generator(agents_dir / "heuristic.leek", "baseline_heuristic.leek")

    # Fighter v1 should already exist
    fighter_ai = "fighter_v1.leek"

    n_games = 50

    print(f"\n=== Baseline Evaluation ({n_games} games each) ===\n")

    # Random vs Random (sanity check - should be ~50%)
    print("Random vs Random...")
    result = evaluate(random_ai, random_ai, n_games)
    print(f"  AI1 wins: {result.wins_ai1} ({result.win_rate_ai1:.1%})")
    print(f"  AI2 wins: {result.wins_ai2} ({result.win_rate_ai2:.1%})")
    print(f"  Draws: {result.draws}")

    # Heuristic vs Random
    print("\nHeuristic vs Random...")
    result = evaluate(heuristic_ai, random_ai, n_games)
    print(f"  Heuristic wins: {result.wins_ai1} ({result.win_rate_ai1:.1%})")
    print(f"  Random wins: {result.wins_ai2} ({result.win_rate_ai2:.1%})")
    print(f"  Draws: {result.draws}")

    # Heuristic vs Fighter v1
    print("\nHeuristic vs Fighter_v1...")
    result = evaluate(heuristic_ai, fighter_ai, n_games)
    print(f"  Heuristic wins: {result.wins_ai1} ({result.win_rate_ai1:.1%})")
    print(f"  Fighter_v1 wins: {result.wins_ai2} ({result.win_rate_ai2:.1%})")
    print(f"  Draws: {result.draws}")

    # Heuristic vs Heuristic (should be ~50% with seed variation)
    print("\nHeuristic vs Heuristic...")
    result = evaluate(heuristic_ai, heuristic_ai, n_games)
    print(f"  AI1 wins: {result.wins_ai1} ({result.win_rate_ai1:.1%})")
    print(f"  AI2 wins: {result.wins_ai2} ({result.win_rate_ai2:.1%})")
    print(f"  Draws: {result.draws}")

    # Cleanup
    print("\nCleaning up...")
    (GENERATOR_PATH / random_ai).unlink(missing_ok=True)
    (GENERATOR_PATH / heuristic_ai).unlink(missing_ok=True)

    print("\nDone!")


if __name__ == "__main__":
    main()
