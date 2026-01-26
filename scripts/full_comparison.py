#!/usr/bin/env python3
"""Full archetype comparison - v11 vs v12."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator


def run_matchup(ai_name, ai_path, opponent_path, n_rounds=25, level=36):
    """Run fair matchup."""
    sim = Simulator()
    return sim.run_1v1_fair(ai_path, opponent_path, level=level, n_rounds=n_rounds)


def main():
    print("=" * 70)
    print("V11 vs V12 - FULL ARCHETYPE COMPARISON")
    print("=" * 70)
    print("Testing 25 rounds (50 fights) per matchup at L36")
    print()
    
    archetypes = {
        "rusher": "ais/archetype_rusher.leek",
        "kiter": "ais/archetype_kiter.leek",
        "balanced": "ais/archetype_balanced.leek",
    }
    
    results = {
        "v11": {},
        "v12": {},
    }
    
    for name, ai_file in archetypes.items():
        print(f"\nTesting {name}...")
        
        print("  v11...", end=" ", flush=True)
        r11 = run_matchup("v11", "ais/fighter_v11.leek", ai_file)
        results["v11"][name] = r11
        print(f"{r11['ai1_wins']}W-{r11['ai2_wins']}L ({r11['ai1_win_rate']*100:.0f}%)")
        
        print("  v12...", end=" ", flush=True)
        r12 = run_matchup("v12", "ais/fighter_v12.leek", ai_file)
        results["v12"][name] = r12
        print(f"{r12['ai1_wins']}W-{r12['ai2_wins']}L ({r12['ai1_win_rate']*100:.0f}%)")
    
    # Summary table
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Matchup':15} | {'v11 WR':10} | {'v12 WR':10} | {'Delta':8} | {'Winner'}")
    print("-" * 70)
    
    improvements = 0
    total_v11_w = 0
    total_v11_l = 0
    total_v12_w = 0
    total_v12_l = 0
    
    for name in archetypes.keys():
        v11_wr = results["v11"][name]["ai1_win_rate"] * 100
        v12_wr = results["v12"][name]["ai1_win_rate"] * 100
        delta = v12_wr - v11_wr
        
        if delta > 0:
            improvements += 1
            winner = "v12"
        elif delta < 0:
            winner = "v11"
        else:
            winner = "="
        
        print(f"v11/v12 vs {name:8} | {v11_wr:8.0f}% | {v12_wr:8.0f}% | {delta:+7.0f}% | {winner}")
        
        total_v11_w += results["v11"][name]["ai1_wins"]
        total_v11_l += results["v11"][name]["ai2_wins"]
        total_v12_w += results["v12"][name]["ai1_wins"]
        total_v12_l += results["v12"][name]["ai2_wins"]
    
    # Overall
    v11_overall = total_v11_w / (total_v11_w + total_v11_l) * 100 if (total_v11_w + total_v11_l) > 0 else 0
    v12_overall = total_v12_w / (total_v12_w + total_v12_l) * 100 if (total_v12_w + total_v12_l) > 0 else 0
    
    print("-" * 70)
    print(f"{'OVERALL':15} | {v11_overall:8.0f}% | {v12_overall:8.0f}% | {v12_overall-v11_overall:+7.0f}% | {'v12' if v12_overall > v11_overall else 'v11'}")
    
    print("\n" + "=" * 70)
    if improvements >= 2:
        print("RECOMMENDATION: Deploy v12 - improvement in", improvements, "matchups")
    else:
        print("RECOMMENDATION: Keep v11 - not enough improvement")


if __name__ == "__main__":
    main()