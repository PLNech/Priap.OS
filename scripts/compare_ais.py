#!/usr/bin/env python3
"""Compare two AI versions by running simulated fights.

Usage:
    poetry run python scripts/compare_ais.py ais/fighter_v1.leek ais/fighter_v2.leek
    poetry run python scripts/compare_ais.py v1.leek v2.leek -n 1000
    poetry run python scripts/compare_ais.py v1.leek v2.leek --level 4 --str1 96 --agi1 10
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator, EntityConfig, ScenarioConfig, GENERATOR_PATH


def copy_ai_to_generator(source: Path, name: str) -> str:
    """Copy AI file to generator directory and return relative name."""
    dest = GENERATOR_PATH / name
    dest.write_text(source.read_text())
    return name


def compare_ais(
    ai1_path: str,
    ai2_path: str,
    n_fights: int = 100,
    level: int = 1,
    strength1: int = 0,
    agility1: int = 0,
    strength2: int = 0,
    agility2: int = 0,
) -> dict:
    """Run N fights between two AIs and return stats."""

    # Resolve paths
    ai1_path = Path(ai1_path)
    ai2_path = Path(ai2_path)

    if not ai1_path.is_absolute():
        ai1_path = Path.cwd() / ai1_path
    if not ai2_path.is_absolute():
        ai2_path = Path.cwd() / ai2_path

    # Copy AI files to generator directory
    ai1_name = copy_ai_to_generator(ai1_path, f"test_ai1_{ai1_path.name}")
    ai2_name = copy_ai_to_generator(ai2_path, f"test_ai2_{ai2_path.name}")

    print(f"AI 1: {ai1_path.name} (STR={strength1}, AGI={agility1})")
    print(f"AI 2: {ai2_path.name} (STR={strength2}, AGI={agility2})")
    print(f"Running {n_fights} fights at level {level}...\n")

    sim = Simulator()

    wins1 = 0
    wins2 = 0
    draws = 0

    for i in range(n_fights):
        seed = i
        # Swap teams every other fight to eliminate map bias
        swap = (i % 2 == 1)

        if not swap:
            # AI1 as team1, AI2 as team2
            entity1 = EntityConfig(
                id=0,
                name="AI1",
                ai=ai1_name,
                level=level,
                strength=strength1,
                agility=agility1,
                team=1,
                weapons=[37],
            )
            entity2 = EntityConfig(
                id=1,
                name="AI2",
                ai=ai2_name,
                level=level,
                strength=strength2,
                agility=agility2,
                team=2,
                weapons=[37],
            )
        else:
            # AI2 as team1, AI1 as team2 (swapped)
            entity1 = EntityConfig(
                id=0,
                name="AI2",
                ai=ai2_name,
                level=level,
                strength=strength2,
                agility=agility2,
                team=1,
                weapons=[37],
            )
            entity2 = EntityConfig(
                id=1,
                name="AI1",
                ai=ai1_name,
                level=level,
                strength=strength1,
                agility=agility1,
                team=2,
                weapons=[37],
            )

        # Create scenario
        scenario = ScenarioConfig(
            team1=[entity1],
            team2=[entity2],
            seed=seed,
        )

        # Run fight
        try:
            outcome = sim.run_scenario(scenario)

            # Track wins for the correct AI (accounting for swap)
            if not swap:
                if outcome.team1_won:
                    wins1 += 1
                elif outcome.team2_won:
                    wins2 += 1
                else:
                    draws += 1
            else:
                # Teams swapped, so reverse the win tracking
                if outcome.team1_won:
                    wins2 += 1
                elif outcome.team2_won:
                    wins1 += 1
                else:
                    draws += 1

            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"Progress: {i+1}/{n_fights} fights ({wins1}W-{wins2}L-{draws}D)")

        except Exception as e:
            print(f"Fight {i+1} error: {e}")
            continue

    # Results
    total = wins1 + wins2 + draws
    win_rate1 = (wins1 / total * 100) if total > 0 else 0
    win_rate2 = (wins2 / total * 100) if total > 0 else 0

    print(f"\n=== Results ({total} fights) ===")
    print(f"{ai1_path.name}: {wins1}W ({win_rate1:.1f}%)")
    print(f"{ai2_path.name}: {wins2}W ({win_rate2:.1f}%)")
    print(f"Draws: {draws}")

    if wins1 > wins2:
        delta = win_rate1 - win_rate2
        print(f"\n✓ {ai1_path.name} wins by {delta:.1f}%")
    elif wins2 > wins1:
        delta = win_rate2 - win_rate1
        print(f"\n✓ {ai2_path.name} wins by {delta:.1f}%")
    else:
        print(f"\n= Tie!")

    # Cleanup copied files
    (GENERATOR_PATH / ai1_name).unlink(missing_ok=True)
    (GENERATOR_PATH / ai2_name).unlink(missing_ok=True)

    return {
        "ai1": ai1_path.name,
        "ai2": ai2_path.name,
        "wins1": wins1,
        "wins2": wins2,
        "draws": draws,
        "win_rate1": win_rate1,
        "win_rate2": win_rate2,
    }


def main():
    parser = argparse.ArgumentParser(description="Compare two LeekScript AIs")
    parser.add_argument("ai1", help="Path to first AI file")
    parser.add_argument("ai2", help="Path to second AI file")
    parser.add_argument("-n", "--num-fights", type=int, default=100, help="Number of fights")
    parser.add_argument("--level", type=int, default=1, help="Leek level")
    parser.add_argument("--str1", type=int, default=0, help="AI1 strength")
    parser.add_argument("--agi1", type=int, default=0, help="AI1 agility")
    parser.add_argument("--str2", type=int, default=0, help="AI2 strength")
    parser.add_argument("--agi2", type=int, default=0, help="AI2 agility")

    args = parser.parse_args()

    compare_ais(
        args.ai1,
        args.ai2,
        n_fights=args.num_fights,
        level=args.level,
        strength1=args.str1,
        agility1=args.agi1,
        strength2=args.str2,
        agility2=args.agi2,
    )


if __name__ == "__main__":
    main()
