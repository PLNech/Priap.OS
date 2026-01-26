#!/usr/bin/env python3
"""Quick test for v14 opening burst."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator

# Paths relative to PROJECT_ROOT (which is the repo root)
V14_AI = "tools/leek-wars-generator/fighter_v14.leek"
V11_AI = "tools/leek-wars-generator/fighter_v11.leek"
RUSHER_AI = "tools/leek-wars-generator/archetype_rusher.leek"
KITER_AI = "tools/leek-wars-generator/archetype_kiter.leek"

def test_v14_vs_rusher(n_rounds=10):
    """Test v14 vs rusher archetype (runs n_rounds*2 fights)."""
    sim = Simulator()

    print(f"Running {n_rounds*2} fights: v14 vs archetype_rusher")
    results = sim.run_1v1_fair(
        ai1=V14_AI,
        ai2=RUSHER_AI,
        level=38,
        n_rounds=n_rounds
    )

    print(f"\n=== RESULTS ===")
    print(f"v14 wins: {results['ai1_wins']}")
    print(f"rusher wins: {results['ai2_wins']}")
    print(f"draws: {results['draws']}")
    print(f"v14 WR: {results['ai1_win_rate']*100:.1f}%")

    return results

def test_v14_vs_kiter(n_rounds=10):
    """Test v14 vs kiter archetype (runs n_rounds*2 fights)."""
    sim = Simulator()

    print(f"\nRunning {n_rounds*2} fights: v14 vs archetype_kiter")
    results = sim.run_1v1_fair(
        ai1=V14_AI,
        ai2=KITER_AI,
        level=38,
        n_rounds=n_rounds
    )

    print(f"\n=== RESULTS ===")
    print(f"v14 wins: {results['ai1_wins']}")
    print(f"kiter wins: {results['ai2_wins']}")
    print(f"draws: {results['draws']}")
    print(f"v14 WR: {results['ai1_win_rate']*100:.1f}%")

    return results

def test_v14_vs_v11(n_rounds=10):
    """Test v14 vs v11 baseline (runs n_rounds*2 fights)."""
    sim = Simulator()

    print(f"\nRunning {n_rounds*2} fights: v14 vs v11 (baseline)")
    results = sim.run_1v1_fair(
        ai1=V14_AI,
        ai2=V11_AI,
        level=38,
        n_rounds=n_rounds
    )

    print(f"\n=== RESULTS ===")
    print(f"v14 wins: {results['ai1_wins']}")
    print(f"v11 wins: {results['ai2_wins']}")
    print(f"draws: {results['draws']}")
    print(f"v14 WR: {results['ai1_win_rate']*100:.1f}%")

    return results

if __name__ == "__main__":
    print("=== v14 OPENING BURST TEST ===\n")

    # Run tests
    rusher_results = test_v14_vs_rusher(10)
    kiter_results = test_v14_vs_kiter(10)
    v11_results = test_v14_vs_v11(10)

    print("\n=== SUMMARY ===")
    print(f"v14 vs Rusher: {rusher_results['ai1_win_rate']*100:.0f}% WR ({rusher_results['ai1_wins']}/{rusher_results['total_fights']})")
    print(f"v14 vs Kiter:  {kiter_results['ai1_win_rate']*100:.0f}% WR ({kiter_results['ai1_wins']}/{kiter_results['total_fights']})")
    print(f"v14 vs v11:    {v11_results['ai1_win_rate']*100:.0f}% WR ({v11_results['ai1_wins']}/{v11_results['total_fights']})")