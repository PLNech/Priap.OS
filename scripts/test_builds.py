#!/usr/bin/env python3
"""Test different build configurations to find optimal capital allocation.

Usage:
    poetry run python scripts/test_builds.py --ai ais/fighter_v2.leek --level 4 --capital 17
    poetry run python scripts/test_builds.py --stat strength --range 90-110 -n 500
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator, EntityConfig, ScenarioConfig, GENERATOR_PATH
from leekwars_agent.models import capital_for_characteristic


def copy_ai_to_generator(source: Path, name: str) -> str:
    """Copy AI file to generator directory and return relative name."""
    dest = GENERATOR_PATH / name
    dest.write_text(source.read_text())
    return name


def test_build_variants(
    ai_path: str,
    base_level: int = 4,
    base_str: int = 96,
    base_agi: int = 10,
    available_capital: int = 17,
    n_fights_per_variant: int = 100,
) -> dict:
    """Test different ways to spend available capital."""

    ai_path = Path(ai_path)
    if not ai_path.is_absolute():
        ai_path = Path.cwd() / ai_path

    # Copy AI to generator directory once
    ai_name = copy_ai_to_generator(ai_path, f"test_build_{ai_path.name}")

    print(f"Testing build variants with {available_capital} capital to spend")
    print(f"Base: Level {base_level}, STR={base_str}, AGI={base_agi}")
    print(f"AI: {ai_path.name}")
    print(f"Fights per variant: {n_fights_per_variant}\n")

    # Define build variants
    variants = [
        {
            "name": "Baseline (no change)",
            "strength": base_str,
            "agility": base_agi,
        },
        {
            "name": "+8 STR (16 cap)",
            "strength": base_str + 8,  # Costs 2 cap/pt at this level
            "agility": base_agi,
        },
        {
            "name": "+17 AGI (17 cap)",
            "strength": base_str,
            "agility": base_agi + 17,  # Costs 1 cap/pt
        },
        {
            "name": "+17 Frequency (17 cap)",
            "strength": base_str,
            "agility": base_agi,
            "frequency": 17,  # Test turn order impact
        },
    ]

    sim = Simulator()
    results = []

    # Test each variant against baseline
    baseline = variants[0]

    for variant in variants[1:]:  # Skip baseline vs itself
        print(f"\nTesting: {variant['name']} vs Baseline")
        print("=" * 50)

        wins = 0
        losses = 0
        draws = 0

        for i in range(n_fights_per_variant):
            swap = (i % 2 == 1)

            if not swap:
                # Variant as team1, baseline as team2
                entity1 = EntityConfig(
                    id=0,
                    name="Variant",
                    ai=ai_name,
                    level=base_level,
                    strength=variant.get("strength", 0),
                    agility=variant.get("agility", 0),
                    frequency=variant.get("frequency", 100),
                    team=1,
                    weapons=[37],
                )
                entity2 = EntityConfig(
                    id=1,
                    name="Baseline",
                    ai=ai_name,
                    level=base_level,
                    strength=baseline["strength"],
                    agility=baseline["agility"],
                    team=2,
                    weapons=[37],
                )
            else:
                # Baseline as team1, variant as team2 (swapped)
                entity1 = EntityConfig(
                    id=0,
                    name="Baseline",
                    ai=ai_name,
                    level=base_level,
                    strength=baseline["strength"],
                    agility=baseline["agility"],
                    team=1,
                    weapons=[37],
                )
                entity2 = EntityConfig(
                    id=1,
                    name="Variant",
                    ai=ai_name,
                    level=base_level,
                    strength=variant.get("strength", 0),
                    agility=variant.get("agility", 0),
                    frequency=variant.get("frequency", 100),
                    team=2,
                    weapons=[37],
                )

            scenario = ScenarioConfig(
                team1=[entity1],
                team2=[entity2],
                seed=i,
            )

            try:
                outcome = sim.run_scenario(scenario)

                # Track wins for variant (accounting for swap)
                if not swap:
                    if outcome.team1_won:
                        wins += 1
                    elif outcome.team2_won:
                        losses += 1
                    else:
                        draws += 1
                else:
                    # Teams swapped
                    if outcome.team1_won:
                        losses += 1
                    elif outcome.team2_won:
                        wins += 1
                    else:
                        draws += 1

                if (i + 1) % 50 == 0:
                    print(f"  Progress: {i+1}/{n_fights_per_variant}")

            except Exception as e:
                print(f"  Fight {i+1} error: {e}")
                continue

        total = wins + losses + draws
        win_rate = (wins / total * 100) if total > 0 else 0

        result = {
            "variant": variant["name"],
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": win_rate,
        }
        results.append(result)

        print(f"  Result: {wins}W-{losses}L-{draws}D ({win_rate:.1f}%)")

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    results.sort(key=lambda x: x["win_rate"], reverse=True)

    for i, result in enumerate(results):
        marker = "★" if i == 0 else " "
        print(f"{marker} {result['variant']}: {result['win_rate']:.1f}% ({result['wins']}W-{result['losses']}L)")

    best = results[0]
    print(f"\n✓ Best choice: {best['variant']} (+{best['win_rate']-50:.1f}% vs baseline)")

    # Cleanup copied file
    (GENERATOR_PATH / ai_name).unlink(missing_ok=True)

    return results


def main():
    parser = argparse.ArgumentParser(description="Test build capital allocation")
    parser.add_argument("--ai", default="ais/fighter_v2.leek", help="AI file to test")
    parser.add_argument("--level", type=int, default=4, help="Leek level")
    parser.add_argument("--str", type=int, default=96, help="Base strength")
    parser.add_argument("--agi", type=int, default=10, help="Base agility")
    parser.add_argument("--capital", type=int, default=17, help="Available capital")
    parser.add_argument("-n", "--num-fights", type=int, default=100, help="Fights per variant")

    args = parser.parse_args()

    test_build_variants(
        args.ai,
        base_level=args.level,
        base_str=args.str,
        base_agi=args.agi,
        available_capital=args.capital,
        n_fights_per_variant=args.num_fights,
    )


if __name__ == "__main__":
    main()
