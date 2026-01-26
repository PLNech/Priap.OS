#!/usr/bin/env python3
"""Quick v12 verification."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator

sim = Simulator()

print("V12 vs KITER (10 rounds)")
result = sim.run_1v1_fair("ais/fighter_v12.leek", "ais/archetype_kiter.leek", level=36, n_rounds=10)

print(f"Results: {result['ai1_wins']}W-{result['ai2_wins']}L-{result['draws']}D")
print(f"Win rate: {result['ai1_win_rate']*100:.0f}%")