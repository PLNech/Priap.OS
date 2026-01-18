#!/usr/bin/env python3
"""Test stat build strategies against realistic opponents.

Simulates our actual matchup problem:
- Us: ~130 HP, 96 STR
- Typical enemy: ~250 HP, ~80 STR

Tests different ways to spend 20 capital points.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator, EntityConfig, ScenarioConfig, GENERATOR_PATH


def copy_ai_to_generator(source: Path, name: str) -> str:
    """Copy AI file to generator directory."""
    dest = GENERATOR_PATH / name
    dest.write_text(source.read_text())
    return name


def test_builds():
    """Test different stat allocation strategies."""

    # Copy AI
    ai_path = Path("ais/fighter_v1.leek")
    ai_name = copy_ai_to_generator(ai_path, "test_build.leek")

    # Our base stats (current)
    OUR_LEVEL = 12
    OUR_LIFE = 130
    OUR_STR = 96
    OUR_AGI = 10
    CAPITAL = 20  # Points to spend

    # Typical enemy stats (from analysis)
    ENEMY_LIFE = 250
    ENEMY_STR = 80
    ENEMY_AGI = 10

    # Define build variants
    # Capital costs: STR=2/pt, LIFE=1/pt (approx), AGI=1/pt
    builds = [
        {
            "name": "A: All STR (+10)",
            "life": OUR_LIFE,
            "strength": OUR_STR + 10,  # 20 capital / 2 = 10 points
            "agility": OUR_AGI,
        },
        {
            "name": "B: All LIFE (+20)",
            "life": OUR_LIFE + 20,  # 20 capital / 1 = 20 points
            "strength": OUR_STR,
            "agility": OUR_AGI,
        },
        {
            "name": "C: All AGI (+20)",
            "life": OUR_LIFE,
            "strength": OUR_STR,
            "agility": OUR_AGI + 20,  # 20 capital / 1 = 20 points
        },
        {
            "name": "D: Balanced (STR+5, LIFE+10)",
            "life": OUR_LIFE + 10,
            "strength": OUR_STR + 5,
            "agility": OUR_AGI,
        },
        {
            "name": "Baseline (no change)",
            "life": OUR_LIFE,
            "strength": OUR_STR,
            "agility": OUR_AGI,
        },
    ]

    sim = Simulator()
    n_fights = 200  # Per build
    results = []

    print("=" * 60)
    print("STAT BUILD COMPARISON")
    print("=" * 60)
    print(f"Our base: {OUR_LIFE}hp, {OUR_STR}str, {OUR_AGI}agi")
    print(f"Enemy: {ENEMY_LIFE}hp, {ENEMY_STR}str")
    print(f"Capital to spend: {CAPITAL}")
    print(f"Fights per build: {n_fights}")
    print()

    for build in builds:
        print(f"Testing: {build['name']}...")

        wins = 0
        losses = 0
        draws = 0

        for i in range(n_fights):
            # Alternate who is team 1 to neutralize position bias
            swap = (i % 2 == 1)

            us = EntityConfig(
                id=0 if not swap else 1,
                name="IAdonis",
                ai=ai_name,
                level=OUR_LEVEL,
                life=build["life"],
                strength=build["strength"],
                agility=build["agility"],
                team=1 if not swap else 2,
                weapons=[37],
            )

            enemy = EntityConfig(
                id=1 if not swap else 0,
                name="Enemy",
                ai=ai_name,  # Same AI for fair comparison
                level=OUR_LEVEL + 1,
                life=ENEMY_LIFE,
                strength=ENEMY_STR,
                agility=ENEMY_AGI,
                team=2 if not swap else 1,
                weapons=[37],
            )

            if not swap:
                scenario = ScenarioConfig(team1=[us], team2=[enemy], seed=i)
            else:
                scenario = ScenarioConfig(team1=[enemy], team2=[us], seed=i)

            try:
                outcome = sim.run_scenario(scenario)

                # Track OUR wins
                if not swap:
                    if outcome.team1_won:
                        wins += 1
                    elif outcome.team2_won:
                        losses += 1
                    else:
                        draws += 1
                else:
                    if outcome.team2_won:
                        wins += 1
                    elif outcome.team1_won:
                        losses += 1
                    else:
                        draws += 1

            except Exception as e:
                print(f"  Error: {e}")
                continue

        total = wins + losses + draws
        win_rate = (wins / total * 100) if total > 0 else 0

        results.append({
            "build": build["name"],
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": win_rate,
            "stats": f"{build['life']}hp/{build['strength']}str/{build['agility']}agi",
        })

        print(f"  {wins}W-{losses}L-{draws}D ({win_rate:.1f}%)")

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS (sorted by win rate)")
    print("=" * 60)

    results.sort(key=lambda x: x["win_rate"], reverse=True)

    for i, r in enumerate(results):
        marker = ">>>" if i == 0 else "   "
        print(f"{marker} {r['build']}: {r['win_rate']:.1f}% ({r['stats']})")

    best = results[0]
    baseline = next(r for r in results if "Baseline" in r["build"])
    improvement = best["win_rate"] - baseline["win_rate"]

    print(f"\nBest: {best['build']}")
    print(f"Improvement over baseline: {improvement:+.1f}%")

    # Cleanup
    (GENERATOR_PATH / ai_name).unlink(missing_ok=True)

    return results


if __name__ == "__main__":
    test_builds()
