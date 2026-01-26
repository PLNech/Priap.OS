#!/usr/bin/env python3
"""Fast v11 vs v12 comparison."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator

sim = Simulator()

print("=" * 60)
print("V11 vs V12 FAST COMPARISON - 5 rounds (10 fights) each")
print("=" * 60)

matchups = [
    ("rusher", "ais/archetype_rusher.leek"),
    ("kiter", "ais/archetype_kiter.leek"),
]

for name, ai_file in matchups:
    print(f"\n{name.upper()}:")
    
    print("  v11...", end=" ", flush=True)
    r11 = sim.run_1v1_fair("ais/fighter_v11.leek", ai_file, level=36, n_rounds=5)
    v11_wr = r11["ai1_win_rate"] * 100
    print(f"{r11['ai1_wins']}W-{r11['ai2_wins']}L = {v11_wr:.0f}%")
    
    print("  v12...", end=" ", flush=True)
    r12 = sim.run_1v1_fair("ais/fighter_v12.leek", ai_file, level=36, n_rounds=5)
    v12_wr = r12["ai1_win_rate"] * 100
    print(f"{r12['ai1_wins']}W-{r12['ai2_wins']}L = {v12_wr:.0f}%")
    
    delta = v12_wr - v11_wr
    if delta > 5:
        print(f"  → v12 is {delta:.0f}% better")
    elif delta < -5:
        print(f"  → v11 is {abs(delta):.0f}% better")
    else:
        print(f"  → Similar (~{delta:.0f}% delta)")

print("\n" + "=" * 60)