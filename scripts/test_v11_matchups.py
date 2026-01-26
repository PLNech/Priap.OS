#!/usr/bin/env python3
"""Test v11 against all archetypes - comprehensive matchup analysis.

Usage:
    poetry run python scripts/test_v11_matchups.py -n 200 --level 36
"""

import sys
import os
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator


# Archetype definitions - map names to AI files
ARCHETYPES = {
    "rusher": "ais/archetype_rusher.leek",
    "kiter": "ais/archetype_kiter.leek",
    "balanced": "ais/archetype_balanced.leek",
    "tank": "ais/archetype_tank.leek",
    "burst": "ais/archetype_burst.leek",
}

# Our AI to test
OUR_AI = "ais/fighter_v11.leek"


def run_matchup(sim: Simulator, ai1: str, ai2: str, n_fights: int, level: int) -> dict:
    """Run fair matchup between two AIs."""
    results = {"W": 0, "L": 0, "D": 0, "turns": []}

    for seed in range(n_fights):
        outcome = sim.run_1v1_fair(ai1, ai2, level=level, seed=seed, n_rounds=1)
        # run_1v1_fair returns aggregated, we need to parse
        # Actually run_1v1_fair does position swapping internally
        total_fights = outcome["total_fights"]
        wins = outcome["ai1_wins"]
        losses = outcome["ai2_wins"]
        draws = outcome["draws"]

        results["W"] = wins
        results["L"] = losses
        results["D"] = draws

    return results


def run_fair_matchup(sim: Simulator, ai1: str, ai2: str, n_rounds: int, level: int) -> dict:
    """Run fair matchup with position swapping."""
    return sim.run_1v1_fair(ai1, ai2, level=level, n_rounds=n_rounds)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test v11 vs archetypes")
    parser.add_argument("-n", "--num-rounds", type=int, default=100,
                        help="Rounds per matchup (each round = 2 fights with position swap)")
    parser.add_argument("--level", type=int, default=36,
                        help="Leek level")
    args = parser.parse_args()

    print("=" * 70)
    print(f"V11 HYDRa vs ARCHETYPES - {args.num_rounds} rounds each at L{args.level}")
    print("=" * 70)

    sim = Simulator()
    n_fights = args.num_rounds * 2  # Each round = 2 fights

    matchups = {}

    # Test v11 vs each archetype
    print(f"\nRunning {args.num_rounds} rounds ({n_fights} total fights) per matchup...\n")

    for name, ai_file in ARCHETYPES.items():
        print(f"Testing v11 vs {name}...", end=" ", flush=True)

        results = run_fair_matchup(sim, OUR_AI, ai_file, args.num_rounds, args.level)
        matchups[name] = results

        total = results["ai1_wins"] + results["ai2_wins"]
        wr = results["ai1_win_rate"] * 100 if total > 0 else 0
        print(f"{results['ai1_wins']}W-{results['ai2_wins']}L-{results['draws']}D = {wr:.1f}% WR")

    # Summary table
    print("\n" + "=" * 70)
    print("V11 PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"{'Matchup':20} | {'W':4} | {'L':4} | {'D':4} | {'WR':7} | {'Assessment'}")
    print("-" * 70)

    assessments = []
    for name, r in matchups.items():
        total = r["ai1_wins"] + r["ai2_wins"]
        wr = r["ai1_win_rate"] * 100 if total > 0 else 0

        if wr >= 60:
            assessment = "GOOD"
        elif wr >= 50:
            assessment = "OK"
        elif wr >= 40:
            assessment = "WEAK"
        else:
            assessment = "BAD"

        print(f"v11 vs {name:14} | {r['ai1_wins']:4} | {r['ai2_wins']:4} | {r['draws']:4} | {wr:6.1f}% | {assessment}")
        assessments.append((name, wr, assessment))

    # Overall stats
    total_w = sum(r["ai1_wins"] for r in matchups.values())
    total_l = sum(r["ai2_wins"] for r in matchups.values())
    total_d = sum(r["draws"] for r in matchups.values())
    overall_wr = total_w / (total_w + total_l) * 100 if (total_w + total_l) > 0 else 0

    print("-" * 70)
    print(f"{'OVERALL':20} | {total_w:4} | {total_l:4} | {total_d:4} | {overall_wr:6.1f}% |")

    # Recommendations
    print("\n" + "=" * 70)
    print("OPTIMIZATION PRIORITIES")
    print("=" * 70)

    weak_matchups = [(n, wr) for n, wr, a in assessments if wr < 50]
    if weak_matchups:
        print("\nMatchups needing improvement:")
        for name, wr in sorted(weak_matchups, key=lambda x: x[1]):
            print(f"  - {name}: {wr:.1f}% WR")

        print("\nRecommended focus areas:")
        for name, wr in sorted(weak_matchups, key=lambda x: x[1]):
            if name == "kiter":
                print("  - KITER: Need better MP management to close gaps faster")
            elif name == "rusher":
                print("  - RUSHER: Need to win damage race or use terrain")
            elif name == "balanced":
                print("  - BALANCED: Should dominate, check for errors")
            elif name == "tank":
                print("  - TANK: Need faster kill or chip damage")
            elif name == "burst":
                print("  - BURST: Need to survive initial burst, heal if low")
    else:
        print("\nAll matchups >= 50% - good overall performance!")

    return matchups


if __name__ == "__main__":
    main()