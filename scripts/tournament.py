#!/usr/bin/env python3
"""Run a round-robin tournament between N AI variants.

Usage:
    poetry run python scripts/tournament.py ais/v1a.leek ais/v1b.leek ais/v1c.leek -k 50
    poetry run python scripts/tournament.py ais/*.leek -k 100 --level 6 --strength 96
    poetry run python scripts/tournament.py ais/*.leek -k 50 --workers 4  # Parallel!
"""

import sys
import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator, EntityConfig, ScenarioConfig, GENERATOR_PATH


@dataclass
class AIStats:
    """Track stats for a single AI."""
    name: str
    path: Path
    wins: int = 0
    losses: int = 0
    draws: int = 0
    elo: float = 1500.0
    matchups: dict = field(default_factory=dict)  # opponent -> {wins, losses, draws}

    @property
    def total_fights(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.wins / self.total_fights * 100


def validate_ai(ai_path: Path) -> tuple[bool, str]:
    """Validate AI syntax using LeekScript compiler."""
    jar_path = GENERATOR_PATH / "leekscript" / "leekscript.jar"
    if not jar_path.exists():
        return True, "validator not found, skipping"

    try:
        result = subprocess.run(
            ["java", "-jar", str(jar_path), str(ai_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, result.stderr or result.stdout
        return True, "OK"
    except Exception as e:
        return True, f"validation skipped: {e}"


def copy_ai_to_generator(source: Path, name: str) -> str:
    """Copy AI file to generator directory and return relative name."""
    dest = GENERATOR_PATH / name
    dest.write_text(source.read_text())
    return name


def update_elo(winner_elo: float, loser_elo: float, k: float = 32) -> tuple[float, float]:
    """Update ELO ratings after a match."""
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_elo - loser_elo) / 400))

    new_winner_elo = winner_elo + k * (1 - expected_winner)
    new_loser_elo = loser_elo + k * (0 - expected_loser)

    return new_winner_elo, new_loser_elo


# Worker function for parallel execution (must be top-level for pickling)
def _run_single_fight(args: tuple) -> tuple[str, str, int, int]:
    """Run a single fight and return (ai1_name, ai2_name, fight_idx, winner).

    Winner: 1 = ai1 won, 2 = ai2 won, 0 = draw
    """
    ai1_name, ai2_name, ai1_temp, ai2_temp, fight_idx, level, strength, agility = args

    sim = Simulator()
    seed = hash((ai1_name, ai2_name, fight_idx)) % 2**31
    swap = (fight_idx % 2 == 1)

    if not swap:
        entity1 = EntityConfig(
            id=0, name="AI1", ai=ai1_temp,
            level=level, strength=strength, agility=agility,
            team=1, weapons=[37],
        )
        entity2 = EntityConfig(
            id=1, name="AI2", ai=ai2_temp,
            level=level, strength=strength, agility=agility,
            team=2, weapons=[37],
        )
    else:
        entity1 = EntityConfig(
            id=0, name="AI2", ai=ai2_temp,
            level=level, strength=strength, agility=agility,
            team=1, weapons=[37],
        )
        entity2 = EntityConfig(
            id=1, name="AI1", ai=ai1_temp,
            level=level, strength=strength, agility=agility,
            team=2, weapons=[37],
        )

    scenario = ScenarioConfig(team1=[entity1], team2=[entity2], seed=seed)

    try:
        outcome = sim.run_scenario(scenario)

        # Determine winner accounting for swap
        if not swap:
            if outcome.team1_won:
                return (ai1_name, ai2_name, fight_idx, 1)
            elif outcome.team2_won:
                return (ai1_name, ai2_name, fight_idx, 2)
            else:
                return (ai1_name, ai2_name, fight_idx, 0)
        else:
            if outcome.team1_won:
                return (ai1_name, ai2_name, fight_idx, 2)
            elif outcome.team2_won:
                return (ai1_name, ai2_name, fight_idx, 1)
            else:
                return (ai1_name, ai2_name, fight_idx, 0)
    except Exception:
        return (ai1_name, ai2_name, fight_idx, -1)  # Error


def run_tournament(
    ai_paths: list[Path],
    fights_per_pair: int = 50,
    level: int = 1,
    strength: int = 0,
    agility: int = 0,
    verbose: bool = False,
    workers: int = 0,  # 0 = auto-detect (use nproc - 4)
) -> list[AIStats]:
    """Run round-robin tournament between all AIs."""
    import time

    # Auto-detect workers
    if workers <= 0:
        import os
        workers = max(1, os.cpu_count() - 4)  # Leave 4 cores for system

    # Validate all AIs first
    print("Validating AI files...")
    ai_names = {}
    path_by_name = {}
    for path in ai_paths:
        valid, msg = validate_ai(path)
        if not valid:
            print(f"  INVALID: {path.name} - {msg}")
            return []
        # Copy to generator directory
        temp_name = f"tourney_{path.stem}.leek"
        ai_names[path] = copy_ai_to_generator(path, temp_name)
        path_by_name[path.name] = path
        print(f"  OK: {path.name}")

    print()

    # Initialize stats for each AI
    stats = {path: AIStats(name=path.name, path=path) for path in ai_paths}

    # Generate all pairs
    pairs = list(combinations(ai_paths, 2))
    total_fights = len(pairs) * fights_per_pair

    print(f"Tournament: {len(ai_paths)} AIs, {len(pairs)} matchups, {fights_per_pair} fights each")
    print(f"Total fights: {total_fights} (using {workers} workers)")
    print()

    # Build all fight tasks
    fight_tasks = []
    for ai1_path, ai2_path in pairs:
        ai1_temp = ai_names[ai1_path]
        ai2_temp = ai_names[ai2_path]
        for i in range(fights_per_pair):
            fight_tasks.append((
                ai1_path.name, ai2_path.name,
                ai1_temp, ai2_temp,
                i, level, strength, agility
            ))

    # Run fights in parallel
    start_time = time.perf_counter()
    results = []

    if workers == 1:
        # Sequential mode
        for i, task in enumerate(fight_tasks):
            results.append(_run_single_fight(task))
            if (i + 1) % 100 == 0:
                elapsed = time.perf_counter() - start_time
                rate = (i + 1) / elapsed
                print(f"  Progress: {i+1}/{len(fight_tasks)} ({rate:.1f} fights/sec)")
    else:
        # Parallel mode
        completed = 0
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_run_single_fight, task): task for task in fight_tasks}
            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                if completed % 100 == 0:
                    elapsed = time.perf_counter() - start_time
                    rate = completed / elapsed
                    eta = (len(fight_tasks) - completed) / rate if rate > 0 else 0
                    print(f"  Progress: {completed}/{len(fight_tasks)} ({rate:.1f} f/s, ETA {eta:.0f}s)")

    elapsed = time.perf_counter() - start_time
    print(f"\nCompleted {len(results)} fights in {elapsed:.1f}s ({len(results)/elapsed:.1f} fights/sec)")

    # Aggregate results by matchup
    matchup_results = {}  # (ai1, ai2) -> {wins1, wins2, draws}
    for ai1_name, ai2_name, fight_idx, winner in results:
        key = (ai1_name, ai2_name)
        if key not in matchup_results:
            matchup_results[key] = {"wins1": 0, "wins2": 0, "draws": 0}

        if winner == 1:
            matchup_results[key]["wins1"] += 1
        elif winner == 2:
            matchup_results[key]["wins2"] += 1
        elif winner == 0:
            matchup_results[key]["draws"] += 1
        # winner == -1 is error, skip

    # Update stats and ELO from aggregated results
    for (ai1_name, ai2_name), res in matchup_results.items():
        ai1_path = path_by_name[ai1_name]
        ai2_path = path_by_name[ai2_name]

        pair_wins1 = res["wins1"]
        pair_wins2 = res["wins2"]
        pair_draws = res["draws"]

        # Update ELO based on overall matchup result
        if pair_wins1 > pair_wins2:
            stats[ai1_path].elo, stats[ai2_path].elo = update_elo(
                stats[ai1_path].elo, stats[ai2_path].elo
            )
        elif pair_wins2 > pair_wins1:
            stats[ai2_path].elo, stats[ai1_path].elo = update_elo(
                stats[ai2_path].elo, stats[ai1_path].elo
            )

        # Update win/loss records
        stats[ai1_path].wins += pair_wins1
        stats[ai1_path].losses += pair_wins2
        stats[ai1_path].draws += pair_draws
        stats[ai1_path].matchups[ai2_name] = {
            "wins": pair_wins1, "losses": pair_wins2, "draws": pair_draws
        }

        stats[ai2_path].wins += pair_wins2
        stats[ai2_path].losses += pair_wins1
        stats[ai2_path].draws += pair_draws
        stats[ai2_path].matchups[ai1_name] = {
            "wins": pair_wins2, "losses": pair_wins1, "draws": pair_draws
        }

        # Progress per matchup
        print(f"  {ai1_name} vs {ai2_name}: {pair_wins1}-{pair_wins2}-{pair_draws}")

    # Cleanup temp files
    for temp_name in ai_names.values():
        (GENERATOR_PATH / temp_name).unlink(missing_ok=True)

    # Sort by ELO (descending)
    ranked = sorted(stats.values(), key=lambda s: s.elo, reverse=True)

    return ranked


def print_leaderboard(ranked: list[AIStats]) -> None:
    """Print tournament leaderboard."""
    print("\n" + "=" * 70)
    print("TOURNAMENT RESULTS")
    print("=" * 70)
    print(f"{'Rank':<5} {'AI':<25} {'W-L-D':<15} {'Win%':<8} {'ELO':<8}")
    print("-" * 70)

    for i, s in enumerate(ranked, 1):
        record = f"{s.wins}-{s.losses}-{s.draws}"
        print(f"{i:<5} {s.name:<25} {record:<15} {s.win_rate:>5.1f}%   {s.elo:>7.0f}")

    print("=" * 70)
    print(f"Winner: {ranked[0].name}")


def get_top_fighter(ai_paths: list[Path], **kwargs) -> Optional[Path]:
    """Run tournament and return path to best performing AI."""
    ranked = run_tournament(ai_paths, **kwargs)
    if ranked:
        return ranked[0].path
    return None


def save_results(ranked: list[AIStats], output_path: Path) -> None:
    """Save tournament results to JSON."""
    data = {
        "ranking": [
            {
                "rank": i + 1,
                "name": s.name,
                "path": str(s.path),
                "wins": s.wins,
                "losses": s.losses,
                "draws": s.draws,
                "win_rate": s.win_rate,
                "elo": s.elo,
                "matchups": s.matchups,
            }
            for i, s in enumerate(ranked)
        ]
    }
    output_path.write_text(json.dumps(data, indent=2))
    print(f"\nResults saved to: {output_path}")


def main():
    import os
    default_workers = max(1, os.cpu_count() - 4)

    parser = argparse.ArgumentParser(description="Run round-robin tournament between AIs")
    parser.add_argument("ais", nargs="+", help="Paths to AI files")
    parser.add_argument("-k", "--fights-per-pair", type=int, default=50, help="Fights per matchup")
    parser.add_argument("-w", "--workers", type=int, default=default_workers, help=f"Parallel workers (default: {default_workers})")
    parser.add_argument("--level", type=int, default=1, help="Leek level")
    parser.add_argument("--strength", type=int, default=0, help="Strength stat")
    parser.add_argument("--agility", type=int, default=0, help="Agility stat")
    parser.add_argument("-o", "--output", type=Path, help="Save results to JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Resolve paths
    ai_paths = []
    for ai in args.ais:
        path = Path(ai)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            print(f"Error: {ai} not found")
            return
        ai_paths.append(path)

    if len(ai_paths) < 2:
        print("Error: Need at least 2 AIs for tournament")
        return

    ranked = run_tournament(
        ai_paths,
        fights_per_pair=args.fights_per_pair,
        level=args.level,
        strength=args.strength,
        agility=args.agility,
        verbose=args.verbose,
        workers=args.workers,
    )

    if ranked:
        print_leaderboard(ranked)

        if args.output:
            save_results(ranked, args.output)


if __name__ == "__main__":
    main()
