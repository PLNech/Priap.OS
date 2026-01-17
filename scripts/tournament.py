#!/usr/bin/env python3
"""AI Tournament with ELO Rating System."""

import itertools
import math
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.leekwars_agent.simulator import Simulator


@dataclass
class TournamentResult:
    name: str
    elo: float = 1000.0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    games: int = 0

    @property
    def win_rate(self) -> float:
        if self.games == 0:
            return 0.5
        return (self.wins + 0.5 * self.draws) / self.games


class ELOTournament:
    def __init__(self, ais: list[str], k_factor: float = 32.0):
        self.ais = ais
        self.k_factor = k_factor
        self.results = {ai: TournamentResult(name=ai) for ai in ais}
        self.matches = []
        self.simulator = Simulator()

    def expected_score(self, elo_a: float, elo_b: float) -> float:
        return 1.0 / (1.0 + math.pow(10, (elo_b - elo_a) / 400))

    def update_elo(self, ai1: str, ai2: str, ai1_score: float):
        r1, r2 = self.results[ai1], self.results[ai2]
        expected1 = self.expected_score(r1.elo, r2.elo)
        r1.elo += self.k_factor * (ai1_score - expected1)
        r2.elo += self.k_factor * ((1 - ai1_score) - (1 - expected1))

    def run_match(self, ai1: str, ai2: str, n_rounds: int = 10):
        result = self.simulator.run_1v1_fair(ai1, ai2, n_rounds=n_rounds)
        
        r1, r2 = self.results[ai1], self.results[ai2]
        r1.wins += result["ai1_wins"]
        r1.losses += result["ai2_wins"]
        r1.draws += result["draws"]
        r1.games += result["total_fights"]

        r2.wins += result["ai2_wins"]
        r2.losses += result["ai1_wins"]
        r2.draws += result["draws"]
        r2.games += result["total_fights"]

        self.update_elo(ai1, ai2, result["ai1_win_rate"])
        self.matches.append((ai1, ai2, result))
        return result

    def run_tournament(self, rounds_per_match: int = 10, verbose: bool = True):
        pairs = list(itertools.combinations(self.ais, 2))
        for i, (ai1, ai2) in enumerate(pairs):
            if verbose:
                print(f"[{i+1}/{len(pairs)}] {ai1} vs {ai2}...", end=" ", flush=True)
            result = self.run_match(ai1, ai2, n_rounds=rounds_per_match)
            if verbose:
                print(f"{result['ai1_wins']}-{result['ai2_wins']} (d:{result['draws']})")


if __name__ == "__main__":
    ais = [
        "fighter_v1.leek",
        "fighter_v2.leek", 
        "fighter_v3.leek",
        "alpha_strike.leek",
        "v1f_aggressive.leek",
    ]

    tournament = ELOTournament(ais, k_factor=32)
    tournament.run_tournament(rounds_per_match=20, verbose=True)

    print("\n" + "=" * 60)
    print("FINAL RANKINGS")
    print("=" * 60)
    sorted_results = sorted(tournament.results.values(), key=lambda r: r.elo, reverse=True)
    print(f"{'Rank':<5} {'AI':<25} {'ELO':<8} {'W-L-D':<12} {'Win%':<8}")
    print("-" * 60)
    for i, r in enumerate(sorted_results, 1):
        print(f"{i:<5} {r.name:<25} {r.elo:<8.1f} {r.wins}-{r.losses}-{r.draws:<6} {r.win_rate*100:.1f}%")
