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
    # AI1 stats
    strength1: int = 0,
    agility1: int = 0,
    frequency1: int = 0,
    wisdom1: int = 0,
    resistance1: int = 0,
    science1: int = 0,
    magic1: int = 0,
    life1: int = 100,
    tp1: int = 10,
    mp1: int = 3,
    # AI2 stats
    strength2: int = 0,
    agility2: int = 0,
    frequency2: int = 0,
    wisdom2: int = 0,
    resistance2: int = 0,
    science2: int = 0,
    magic2: int = 0,
    life2: int = 100,
    tp2: int = 10,
    mp2: int = 3,
    # Equipment
    chips1: list[int] | None = None,
    chips2: list[int] | None = None,
    # First-mover control
    attacker: int = 0,  # 0=random, 1=AI1 always first, 2=AI2 always first
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

    chips1 = chips1 or []
    chips2 = chips2 or []

    print(f"AI 1: {ai1_path.name}")
    print(f"  Stats: STR={strength1} AGI={agility1} FREQ={frequency1} WIS={wisdom1} RES={resistance1} SCI={science1} MAG={magic1}")
    print(f"  Base:  LIFE={life1} TP={tp1} MP={mp1} chips={chips1}")
    print(f"AI 2: {ai2_path.name}")
    print(f"  Stats: STR={strength2} AGI={agility2} FREQ={frequency2} WIS={wisdom2} RES={resistance2} SCI={science2} MAG={magic2}")
    print(f"  Base:  LIFE={life2} TP={tp2} MP={mp2} chips={chips2}")
    attacker_str = {0: "random", 1: "AI1", 2: "AI2"}.get(attacker, "random")
    print(f"First mover: {attacker_str}")
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
                life=life1,
                tp=tp1,
                mp=mp1,
                strength=strength1,
                agility=agility1,
                frequency=frequency1,
                wisdom=wisdom1,
                resistance=resistance1,
                science=science1,
                magic=magic1,
                team=1,
                weapons=[37],
                chips=chips1,
            )
            entity2 = EntityConfig(
                id=1,
                name="AI2",
                ai=ai2_name,
                level=level,
                life=life2,
                tp=tp2,
                mp=mp2,
                strength=strength2,
                agility=agility2,
                frequency=frequency2,
                wisdom=wisdom2,
                resistance=resistance2,
                science=science2,
                magic=magic2,
                team=2,
                weapons=[37],
                chips=chips2,
            )
        else:
            # AI2 as team1, AI1 as team2 (swapped)
            entity1 = EntityConfig(
                id=0,
                name="AI2",
                ai=ai2_name,
                level=level,
                life=life2,
                tp=tp2,
                mp=mp2,
                strength=strength2,
                agility=agility2,
                frequency=frequency2,
                wisdom=wisdom2,
                resistance=resistance2,
                science=science2,
                magic=magic2,
                team=1,
                weapons=[37],
                chips=chips2,
            )
            entity2 = EntityConfig(
                id=1,
                name="AI1",
                ai=ai1_name,
                level=level,
                life=life1,
                tp=tp1,
                mp=mp1,
                strength=strength1,
                agility=agility1,
                frequency=frequency1,
                wisdom=wisdom1,
                resistance=resistance1,
                science=science1,
                magic=magic1,
                team=2,
                weapons=[37],
                chips=chips1,
            )

        # Compute starter_team based on attacker setting
        # attacker=0: random, attacker=1: AI1 first, attacker=2: AI2 first
        if attacker == 0:
            starter_team = 0
        elif attacker == 1:
            # AI1 goes first: when AI1=team1 (no swap), starter=1; when AI1=team2 (swap), starter=2
            starter_team = 1 if not swap else 2
        else:  # attacker == 2
            # AI2 goes first: when AI2=team2 (no swap), starter=2; when AI2=team1 (swap), starter=1
            starter_team = 2 if not swap else 1

        # Create scenario
        scenario = ScenarioConfig(
            team1=[entity1],
            team2=[entity2],
            seed=seed,
            starter_team=starter_team,
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
    # AI1 stats
    parser.add_argument("--str1", type=int, default=0, help="AI1 strength")
    parser.add_argument("--agi1", type=int, default=0, help="AI1 agility")
    parser.add_argument("--freq1", type=int, default=0, help="AI1 frequency")
    parser.add_argument("--wis1", type=int, default=0, help="AI1 wisdom")
    parser.add_argument("--res1", type=int, default=0, help="AI1 resistance")
    parser.add_argument("--sci1", type=int, default=0, help="AI1 science")
    parser.add_argument("--mag1", type=int, default=0, help="AI1 magic")
    parser.add_argument("--life1", type=int, default=100, help="AI1 base life")
    parser.add_argument("--tp1", type=int, default=10, help="AI1 turn points")
    parser.add_argument("--mp1", type=int, default=3, help="AI1 move points")
    # AI2 stats
    parser.add_argument("--str2", type=int, default=0, help="AI2 strength")
    parser.add_argument("--agi2", type=int, default=0, help="AI2 agility")
    parser.add_argument("--freq2", type=int, default=0, help="AI2 frequency")
    parser.add_argument("--wis2", type=int, default=0, help="AI2 wisdom")
    parser.add_argument("--res2", type=int, default=0, help="AI2 resistance")
    parser.add_argument("--sci2", type=int, default=0, help="AI2 science")
    parser.add_argument("--mag2", type=int, default=0, help="AI2 magic")
    parser.add_argument("--life2", type=int, default=100, help="AI2 base life")
    parser.add_argument("--tp2", type=int, default=10, help="AI2 turn points")
    parser.add_argument("--mp2", type=int, default=3, help="AI2 move points")
    # Equipment
    parser.add_argument("--chips1", type=str, default="", help="AI1 chips (comma-separated IDs)")
    parser.add_argument("--chips2", type=str, default="", help="AI2 chips (comma-separated IDs)")
    # First-mover control
    parser.add_argument("--attacker", type=int, default=0, choices=[0, 1, 2],
                        help="Who attacks first: 0=random, 1=AI1, 2=AI2")

    args = parser.parse_args()

    # Parse chips
    chips1 = [int(c) for c in args.chips1.split(",") if c.strip()] if args.chips1 else []
    chips2 = [int(c) for c in args.chips2.split(",") if c.strip()] if args.chips2 else []

    compare_ais(
        args.ai1,
        args.ai2,
        n_fights=args.num_fights,
        level=args.level,
        # AI1 stats
        strength1=args.str1,
        agility1=args.agi1,
        frequency1=args.freq1,
        wisdom1=args.wis1,
        resistance1=args.res1,
        science1=args.sci1,
        magic1=args.mag1,
        life1=args.life1,
        tp1=args.tp1,
        mp1=args.mp1,
        # AI2 stats
        strength2=args.str2,
        agility2=args.agi2,
        frequency2=args.freq2,
        wisdom2=args.wis2,
        resistance2=args.res2,
        science2=args.sci2,
        magic2=args.mag2,
        life2=args.life2,
        tp2=args.tp2,
        mp2=args.mp2,
        # Equipment
        chips1=chips1,
        chips2=chips2,
        # First-mover
        attacker=args.attacker,
    )


if __name__ == "__main__":
    main()
