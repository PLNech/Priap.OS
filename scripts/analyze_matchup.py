#!/usr/bin/env python3
"""Analyze a matchup with detailed fight metrics.

Usage:
    poetry run python scripts/analyze_matchup.py ais/fighter_v5.leek ais/fighter_v6.leek -n 100
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.py4j_simulator import Py4JSimulator
from leekwars_agent.fight_analyzer import analyze_raw_fight, format_fight_metrics, FightMetrics


def copy_ai_with_hash(source: Path, generator_path: Path) -> str:
    """Copy AI to generator with content hash for cache busting."""
    import hashlib
    content = source.read_text()
    content_hash = hashlib.md5(content.encode()).hexdigest()[:6]
    dest_name = f"{source.stem}_{content_hash}.leek"
    (generator_path / dest_name).write_text(content)
    return dest_name


def analyze_matchup(ai1_path: str, ai2_path: str, n_fights: int = 100, level: int = 1,
                    verbose: bool = False):
    """Run fights and analyze with detailed metrics.

    Note: Uses default stats for level. For custom stats, use compare_ais.py.
    """

    ai1_path = Path(ai1_path)
    ai2_path = Path(ai2_path)
    if not ai1_path.is_absolute():
        ai1_path = Path.cwd() / ai1_path
    if not ai2_path.is_absolute():
        ai2_path = Path.cwd() / ai2_path

    sim = Py4JSimulator()
    generator_path = Path(__file__).parent.parent / "tools" / "leek-wars-generator"

    # Copy AIs with cache busting
    ai1_name = copy_ai_with_hash(ai1_path, generator_path)
    ai2_name = copy_ai_with_hash(ai2_path, generator_path)

    print(f"Analyzing: {ai1_path.name} vs {ai2_path.name}")
    print(f"Fights: {n_fights} | Level: {level} (default stats)")
    print("=" * 60)

    # Collect metrics
    ai1_wins = 0
    ai2_wins = 0
    draws = 0
    all_metrics: list[FightMetrics] = []

    # Per-AI aggregates
    ai1_first_damage = 0
    ai2_first_damage = 0
    ai1_first_damage_wins = 0
    ai2_first_damage_wins = 0
    ai1_total_damage = 0
    ai2_total_damage = 0
    ai1_total_shots = 0
    ai2_total_shots = 0
    ai1_total_cells = 0
    ai2_total_cells = 0
    total_turns = 0
    total_first_damage_turn = 0

    for i in range(n_fights):
        seed = i
        swap = (i % 2 == 1)  # Alternate teams

        if not swap:
            result = sim.run_1v1(ai1_name, ai2_name, level=level, seed=seed)
            ai1_team, ai2_team = 1, 2
        else:
            result = sim.run_1v1(ai2_name, ai1_name, level=level, seed=seed)
            ai1_team, ai2_team = 2, 1

        # Parse winner
        winner = result.winner
        if winner == ai1_team:
            ai1_wins += 1
        elif winner == ai2_team:
            ai2_wins += 1
        else:
            draws += 1

        # Analyze fight
        metrics = analyze_raw_fight(result.raw_output)
        all_metrics.append(metrics)

        # Aggregate by AI (not by team)
        for eid, entity in metrics.entities.items():
            is_ai1 = (entity.team == ai1_team)
            if is_ai1:
                ai1_total_damage += entity.damage_dealt
                ai1_total_shots += entity.shots_fired
                ai1_total_cells += entity.cells_moved
            else:
                ai2_total_damage += entity.damage_dealt
                ai2_total_shots += entity.shots_fired
                ai2_total_cells += entity.cells_moved

        # First damage tracking
        if metrics.first_damage_dealer is not None:
            dealer_entity = metrics.entities.get(metrics.first_damage_dealer)
            if dealer_entity:
                if dealer_entity.team == ai1_team:
                    ai1_first_damage += 1
                    if winner == ai1_team:
                        ai1_first_damage_wins += 1
                else:
                    ai2_first_damage += 1
                    if winner == ai2_team:
                        ai2_first_damage_wins += 1

        total_turns += metrics.total_turns
        if metrics.first_damage_turn > 0:
            total_first_damage_turn += metrics.first_damage_turn

        if verbose and i < 5:
            print(f"\n--- Fight {i+1} ---")
            print(format_fight_metrics(metrics))

        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{n_fights}")

    # Results
    total = ai1_wins + ai2_wins + draws
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"{ai1_path.name}: {ai1_wins}W ({ai1_wins/total*100:.1f}%)")
    print(f"{ai2_path.name}: {ai2_wins}W ({ai2_wins/total*100:.1f}%)")
    print(f"Draws: {draws}")

    print("\n--- TIMING ---")
    print(f"Avg turns per fight: {total_turns/n_fights:.1f}")
    fights_with_damage = ai1_first_damage + ai2_first_damage
    if fights_with_damage > 0:
        print(f"Avg first damage turn: {total_first_damage_turn/fights_with_damage:.1f}")

    print("\n--- FIRST BLOOD ANALYSIS ---")
    print(f"{ai1_path.name} gets first blood: {ai1_first_damage}/{n_fights} ({ai1_first_damage/n_fights*100:.1f}%)")
    print(f"{ai2_path.name} gets first blood: {ai2_first_damage}/{n_fights} ({ai2_first_damage/n_fights*100:.1f}%)")
    if ai1_first_damage > 0:
        print(f"  {ai1_path.name} first blood -> win: {ai1_first_damage_wins}/{ai1_first_damage} ({ai1_first_damage_wins/ai1_first_damage*100:.1f}%)")
    if ai2_first_damage > 0:
        print(f"  {ai2_path.name} first blood -> win: {ai2_first_damage_wins}/{ai2_first_damage} ({ai2_first_damage_wins/ai2_first_damage*100:.1f}%)")

    print("\n--- DAMAGE EFFICIENCY ---")
    print(f"{ai1_path.name}: {ai1_total_damage} total dmg | {ai1_total_shots} shots | {ai1_total_damage/max(1,ai1_total_shots):.1f} dmg/shot")
    print(f"{ai2_path.name}: {ai2_total_damage} total dmg | {ai2_total_shots} shots | {ai2_total_damage/max(1,ai2_total_shots):.1f} dmg/shot")

    print("\n--- MOVEMENT ---")
    print(f"{ai1_path.name}: {ai1_total_cells} total cells | {ai1_total_cells/n_fights:.1f} cells/fight")
    print(f"{ai2_path.name}: {ai2_total_cells} total cells | {ai2_total_cells/n_fights:.1f} cells/fight")

    # Cleanup
    (generator_path / ai1_name).unlink(missing_ok=True)
    (generator_path / ai2_name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Analyze AI matchup with detailed metrics")
    parser.add_argument("ai1", help="First AI file")
    parser.add_argument("ai2", help="Second AI file")
    parser.add_argument("-n", "--num-fights", type=int, default=100)
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    analyze_matchup(args.ai1, args.ai2, args.num_fights, args.level, args.verbose)


if __name__ == "__main__":
    main()
