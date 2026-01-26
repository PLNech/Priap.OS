#!/usr/bin/env python3
"""Validate archetype dynamics in the simulator.

Tests if our real-world findings (aggro > balanced > kiter dynamics)
hold true in offline simulation.

Usage:
    poetry run python scripts/validate_archetypes.py
    poetry run python scripts/validate_archetypes.py -n 200  # More fights
"""

import sys
import os
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator


# Archetype AIs to test
ARCHETYPES = {
    "aggro": "archetype_rusher.leek",
    "kiter": "archetype_kiter.leek",
    "balanced": "archetype_balanced.leek",
}


def copy_ai_to_generator(src_path: str):
    """Copy a single AI to generator directory."""
    src = Path(src_path)
    dst = Path("tools/leek-wars-generator") / src.name
    if src.exists():
        dst.write_text(src.read_text())
        print(f"  Copied {src.name}")
        return True
    else:
        print(f"  WARNING: {src_path} not found!")
        return False


def copy_ais_to_generator():
    """Copy archetype AIs to generator directory."""
    src_dir = Path("ais")
    dst_dir = Path("tools/leek-wars-generator")

    for name, ai_file in ARCHETYPES.items():
        src = src_dir / ai_file
        dst = dst_dir / ai_file
        if src.exists():
            dst.write_text(src.read_text())
            print(f"  Copied {ai_file}")


def run_matchup(sim: Simulator, ai1: str, ai2: str, n_fights: int, level: int = 34) -> dict:
    """Run matchup between two AIs and return results."""
    results = {"W": 0, "L": 0, "D": 0, "turns": []}

    for seed in range(n_fights):
        outcome = sim.run_1v1(ai1, ai2, level=level, seed=seed)
        results["turns"].append(outcome.turns)

        if outcome.winner == 1:
            results["W"] += 1
        elif outcome.winner == 2:
            results["L"] += 1
        else:
            results["D"] += 1

    return results


def run_direct_matchup(sim: Simulator, ai1_name: str, ai2_name: str, n_fights: int, level: int = 34) -> dict:
    """Run matchup with pre-copied AI files (skip copy, assume files exist in generator dir)."""
    results = {"W": 0, "L": 0, "D": 0, "turns": []}

    # Manually construct scenario to bypass AI file copying
    from leekwars_agent.simulator import MapConfig

    map_config = MapConfig.symmetric_empty(18, 18)

    for seed in range(n_fights):
        # Build scenario dict directly
        scenario = {
            "seed": seed,
            "map": map_config.to_dict(),
            "entities": [
                {"id": 0, "level": level, "skin": 0, "cell": map_config.team1_spawns[0], "team": 1, "ai": ai1_name},
                {"id": 1, "level": level, "skin": 0, "cell": map_config.team2_spawns[0], "team": 2, "ai": ai2_name},
            ],
            "constants": {},
        }

        outcome = sim._run_fight_direct(scenario)
        results["turns"].append(outcome.turns)

        if outcome.winner == 1:
            results["W"] += 1
        elif outcome.winner == 2:
            results["L"] += 1
        else:
            results["D"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="Validate archetype dynamics")
    parser.add_argument("-n", "--num-fights", type=int, default=100,
                        help="Fights per matchup (default: 100)")
    parser.add_argument("--level", type=int, default=34,
                        help="Leek level (default: 34)")
    parser.add_argument("--ai", type=str, default=None,
                        help="Custom AI file to test (e.g., ais/fighter_v11.leek)")
    parser.add_argument("--opponent", type=str, default=None,
                        help="Custom opponent AI file (e.g., ais/archetype_balanced.leek)")
    args = parser.parse_args()

    print("=" * 60)
    if args.ai and args.opponent:
        print(f"CUSTOM MATCHUP: {args.ai} vs {args.opponent}")
    else:
        print("ARCHETYPE VALIDATION - Simulator vs Real-World")
    print("=" * 60)

    # Copy custom AIs to generator
    if args.ai:
        print("\nSetting up custom AI...")
        copy_ai_to_generator(args.ai)
        copy_ai_to_generator(args.opponent) if args.opponent else None
    else:
        # Copy archetype AIs to generator
        print("\nSetting up archetype AIs...")
        copy_ais_to_generator()

    # Initialize simulator
    sim = Simulator()

    # Results matrix for archetype testing
    matchups = {}

    # Custom matchup test
    if args.ai and args.opponent:
        print("\n" + "=" * 60)
        print("CUSTOM MATCHUP RESULTS")
        print("=" * 60)

        ai1_name = Path(args.ai).stem
        ai2_name = Path(args.opponent).stem

        key = f"{ai1_name} vs {ai2_name}"
        print(f"\n  Testing {key} at L{args.level}...", end=" ", flush=True)

        # Pass ABSOLUTE paths to bypass PROJECT_ROOT resolution
        ai1_path = str(Path(args.ai).resolve())
        ai2_path = str(Path(args.opponent).resolve())

        results = run_matchup(sim, ai1_path, ai2_path, args.num_fights, args.level)

        wr = results["W"] / (results["W"] + results["L"]) * 100 if (results["W"] + results["L"]) > 0 else 0
        avg_turns = sum(results["turns"]) / len(results["turns"]) if results["turns"] else 0
        print(f"\n  {results['W']}W-{results['L']}L-{results['D']}D = {wr:.1f}% WR (avg {avg_turns:.1f}t)")

        # Mid-game stats
        mid_game_turns = [t for t in results["turns"] if t >= 4]
        mid_game_wins = sum(1 for t, w in zip(results["turns"], ["W"] * results["W"]) if t >= 4)
        # This is approximate - need actual fight data for precise mid-game WR

        print(f"\n  Fights reaching turn 4+: {len(mid_game_turns)}/{args.num_fights}")
        print(f"  Avg duration: {avg_turns:.1f} turns")

        return  # Skip archetype testing if custom matchup

    print(f"\nRunning {args.num_fights} fights per matchup at L{args.level}...\n")

    for ai1_name in archetype_names:
        for ai2_name in archetype_names:
            ai1_file = ARCHETYPES[ai1_name]
            ai2_file = ARCHETYPES[ai2_name]

            key = f"{ai1_name} vs {ai2_name}"
            print(f"  Testing {key}...", end=" ", flush=True)

            results = run_matchup(sim, ai1_file, ai2_file, args.num_fights, args.level)
            matchups[key] = results

            wr = results["W"] / (results["W"] + results["L"]) * 100 if (results["W"] + results["L"]) > 0 else 0
            avg_turns = sum(results["turns"]) / len(results["turns"]) if results["turns"] else 0
            print(f"{results['W']}W-{results['L']}L-{results['D']}D = {wr:.1f}% WR (avg {avg_turns:.1f}t)")

    # Summary table
    print("\n" + "=" * 60)
    print("RESULTS MATRIX (T1 = row, T2 = column)")
    print("=" * 60)

    # Header
    header = f"{'T1 vs T2':15}"
    for name in archetype_names:
        header += f" | {name:8}"
    print(header)
    print("-" * len(header))

    # Rows
    for ai1_name in archetype_names:
        row = f"{ai1_name:15}"
        for ai2_name in archetype_names:
            key = f"{ai1_name} vs {ai2_name}"
            r = matchups[key]
            wr = r["W"] / (r["W"] + r["L"]) * 100 if (r["W"] + r["L"]) > 0 else 0
            row += f" | {wr:6.1f}%"
        print(row)

    # Compare to real-world expectations
    print("\n" + "=" * 60)
    print("VALIDATION vs REAL-WORLD DATA")
    print("=" * 60)

    expectations = [
        ("aggro vs balanced", ">80%", 80),  # Real: 89.9%
        ("aggro vs kiter", ">60%", 60),      # Real: 68.9%
        ("kiter vs balanced", ">80%", 80),   # Real: 86.3%
        ("kiter vs aggro", "<50%", -50),     # Real: 56.9% (expectation: aggro wins)
    ]

    passed = 0
    for key, expected, threshold in expectations:
        r = matchups.get(key, {"W": 0, "L": 0})
        wr = r["W"] / (r["W"] + r["L"]) * 100 if (r["W"] + r["L"]) > 0 else 0

        if threshold > 0:
            check = wr >= threshold
        else:
            check = wr < abs(threshold)

        status = "✓ PASS" if check else "✗ FAIL"
        passed += 1 if check else 0
        print(f"  {key:25} Expected {expected:6} | Got {wr:5.1f}% | {status}")

    print(f"\nValidation: {passed}/{len(expectations)} checks passed")

    # Overall archetype strength
    print("\n" + "=" * 60)
    print("OVERALL ARCHETYPE STRENGTH")
    print("=" * 60)

    for name in archetype_names:
        total_w, total_l, total_d = 0, 0, 0
        for key, r in matchups.items():
            if key.startswith(f"{name} vs"):
                total_w += r["W"]
                total_l += r["L"]
                total_d += r["D"]

        wr = total_w / (total_w + total_l) * 100 if (total_w + total_l) > 0 else 0
        print(f"  {name:12} | Total: {total_w}W-{total_l}L-{total_d}D = {wr:.1f}% WR")


if __name__ == "__main__":
    main()
