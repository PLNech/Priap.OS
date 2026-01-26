#!/usr/bin/env python3
"""Test kiter counter fix - v11 before/after comparison."""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator


def main():
    sim = Simulator()
    
    print("V11 KITER COUNTER TEST")
    print("=" * 50)
    print("Testing 25 rounds (50 fights) vs kiter")
    print("Expected: >50% win rate")
    print()
    
    result = sim.run_1v1_fair("ais/fighter_v11.leek", "ais/archetype_kiter.leek", 
                              level=36, n_rounds=25)
    
    wr = result['ai1_win_rate'] * 100
    
    print(f"Results:")
    print(f"  v11 wins: {result['ai1_wins']}")
    print(f"  v11 losses: {result['ai2_wins']}")
    print(f"  Draws: {result['draws']}")
    print(f"  Win rate: {wr:.1f}%")
    print(f"  Total fights: {result['total_fights']}")
    print()
    
    if wr >= 55:
        print("SUCCESS: Win rate >= 55% - fix is effective!")
    elif wr >= 50:
        print("MARGINAL: Win rate 50-55% - may need more tuning")
    else:
        print("FAILED: Win rate < 50% - fix didn't help or made it worse")


if __name__ == "__main__":
    main()