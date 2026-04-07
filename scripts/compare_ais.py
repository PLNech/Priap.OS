#!/usr/bin/env python3
"""Compare two AI versions by running simulated fights.

Defaults to our leek's current build (from sim_defaults.py).
Mirror match: both AIs get identical stats unless overridden.

Usage:
    # Mirror match at our build (no stat args needed!)
    poetry run python scripts/compare_ais.py ais/fighter_v11.leek ais/fighter_v14.leek -n 500

    # Override stats for one side
    poetry run python scripts/compare_ais.py v1.leek v2.leek --str2 200

    # Bare-bones (level 1, no stats)
    poetry run python scripts/compare_ais.py v1.leek v2.leek --bare
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import (
    Simulator, EntityConfig, ScenarioConfig, MapConfig,
    GENERATOR_PATH, copy_ai_to_generator,
)
from sim_defaults import *  # noqa: F403 F401


def compare_ais(
    ai1_path: str,
    ai2_path: str,
    n_fights: int = 100,
    level: int = LEEK_LEVEL,
    # AI1 stats (default = our build)
    strength1: int = LEEK_STR,
    agility1: int = LEEK_AGI,
    frequency1: int = LEEK_FREQ,
    wisdom1: int = LEEK_WIS,
    resistance1: int = LEEK_RES,
    science1: int = LEEK_SCI,
    magic1: int = LEEK_MAG,
    life1: int = LEEK_LIFE,
    tp1: int = LEEK_TP,
    mp1: int = LEEK_MP,
    # AI2 stats (default = our build, mirror match)
    strength2: int = LEEK_STR,
    agility2: int = LEEK_AGI,
    frequency2: int = LEEK_FREQ,
    wisdom2: int = LEEK_WIS,
    resistance2: int = LEEK_RES,
    science2: int = LEEK_SCI,
    magic2: int = LEEK_MAG,
    life2: int = LEEK_LIFE,
    tp2: int = LEEK_TP,
    mp2: int = LEEK_MP,
    # Equipment
    weapons1: list[int] | None = None,
    weapons2: list[int] | None = None,
    chips1: list[int] | None = None,
    chips2: list[int] | None = None,
    # First-mover control
    attacker: int = 0,  # 0=random, 1=AI1 always first, 2=AI2 always first
    verbose: bool = False,
    engine: str = "java",  # "java" or "pysim"
) -> dict:
    """Run N fights between two AIs and return stats."""

    # Resolve paths
    ai1_path = Path(ai1_path)
    ai2_path = Path(ai2_path)
    if not ai1_path.is_absolute():
        ai1_path = Path.cwd() / ai1_path
    if not ai2_path.is_absolute():
        ai2_path = Path.cwd() / ai2_path

    # Default equipment
    weapons1 = weapons1 if weapons1 is not None else DEFAULT_WEAPONS
    weapons2 = weapons2 if weapons2 is not None else DEFAULT_WEAPONS
    chips1 = chips1 if chips1 is not None else DEFAULT_CHIPS
    chips2 = chips2 if chips2 is not None else DEFAULT_CHIPS

    # Print config
    print(f"AI 1: {ai1_path.name}")
    print(f"  Stats: L{level} STR={strength1} AGI={agility1} LIFE={life1} TP={tp1} MP={mp1}")
    print(f"  Weapons={weapons1} Chips={chips1}")
    print(f"AI 2: {ai2_path.name}")
    print(f"  Stats: L{level} STR={strength2} AGI={agility2} LIFE={life2} TP={tp2} MP={mp2}")
    print(f"  Weapons={weapons2} Chips={chips2}")
    attacker_str = {0: "random", 1: "AI1", 2: "AI2"}.get(attacker, "random")
    print(f"Engine: {engine} | First mover: {attacker_str} | Fights: {n_fights}")
    print()

    if engine == "pysim":
        return _run_pysim(
            ai1_path, ai2_path, n_fights,
            level=level, life=life1, tp=tp1, mp=mp1,
            strength=strength1, agility=agility1, frequency=frequency1,
            wisdom=wisdom1, resistance=resistance1, magic=magic1,
            weapons1=weapons1, weapons2=weapons2,
            chips1=chips1, chips2=chips2,
        )

    # ── Java engine path ───────────────────────────────────────────
    ai1_name, ai1_files = copy_ai_to_generator(ai1_path, f"test_ai1_{ai1_path.name}")
    ai2_name, ai2_files = copy_ai_to_generator(ai2_path, f"test_ai2_{ai2_path.name}")
    all_copied_files = ai1_files + ai2_files
    sim = Simulator()
    wins1 = 0
    wins2 = 0
    draws = 0

    import random as _random

    for i in range(n_fights):
        seed = i
        swap = (i % 2 == 1)  # Swap teams every other fight to eliminate map bias

        # Use real maps from library (167 maps with obstacles, realistic LOS)
        # Falls back to symmetric empty if library unavailable
        from leekwars_agent.simulator import get_map_library
        map_lib = get_map_library()
        if map_lib.count > 0:
            fight_map = map_lib.get_map_by_index(seed)
        else:
            map_rng = _random.Random(seed * 7919 + 42)
            fight_map = MapConfig.symmetric_empty(rng=map_rng)

        # Build entity configs (swap positions to eliminate map bias)
        configs = [
            (ai1_name, level, life1, tp1, mp1, strength1, agility1, frequency1,
             wisdom1, resistance1, science1, magic1, weapons1, chips1),
            (ai2_name, level, life2, tp2, mp2, strength2, agility2, frequency2,
             wisdom2, resistance2, science2, magic2, weapons2, chips2),
        ]
        if swap:
            configs = configs[::-1]

        t1, t2 = configs
        entity1 = EntityConfig(
            id=0, name="AI2" if swap else "AI1", ai=t1[0],
            level=t1[1], life=t1[2], tp=t1[3], mp=t1[4],
            strength=t1[5], agility=t1[6], frequency=t1[7],
            wisdom=t1[8], resistance=t1[9], science=t1[10], magic=t1[11],
            team=1, weapons=t1[12], chips=t1[13],
        )
        entity2 = EntityConfig(
            id=1, name="AI1" if swap else "AI2", ai=t2[0],
            level=t2[1], life=t2[2], tp=t2[3], mp=t2[4],
            strength=t2[5], agility=t2[6], frequency=t2[7],
            wisdom=t2[8], resistance=t2[9], science=t2[10], magic=t2[11],
            team=2, weapons=t2[12], chips=t2[13],
        )

        # First-mover control
        if attacker == 0:
            starter_team = 0
        elif attacker == 1:
            starter_team = 1 if not swap else 2
        else:
            starter_team = 2 if not swap else 1

        scenario = ScenarioConfig(
            team1=[entity1], team2=[entity2],
            map_config=fight_map,
            seed=seed, starter_team=starter_team,
        )

        try:
            outcome = sim.run_scenario(scenario)
            if not swap:
                if outcome.team1_won:
                    wins1 += 1
                elif outcome.team2_won:
                    wins2 += 1
                else:
                    draws += 1
            else:
                if outcome.team1_won:
                    wins2 += 1
                elif outcome.team2_won:
                    wins1 += 1
                else:
                    draws += 1

            if (i + 1) % 100 == 0:
                print(f"Progress: {i+1}/{n_fights} ({wins1}W-{wins2}L-{draws}D)")

        except Exception as e:
            print(f"Fight {i+1} error: {e}")
            continue

    # Results
    total = wins1 + wins2 + draws
    wr1 = (wins1 / total * 100) if total > 0 else 0
    wr2 = (wins2 / total * 100) if total > 0 else 0

    print(f"\n=== Results ({total} fights) ===")
    print(f"{ai1_path.name}: {wins1}W ({wr1:.1f}%)")
    print(f"{ai2_path.name}: {wins2}W ({wr2:.1f}%)")
    print(f"Draws: {draws}")

    if wins1 > wins2:
        print(f"\n> {ai1_path.name} wins by {wr1 - wr2:.1f}%")
    elif wins2 > wins1:
        print(f"\n> {ai2_path.name} wins by {wr2 - wr1:.1f}%")
    else:
        print(f"\n= Tie!")

    # Cleanup
    for f in all_copied_files:
        (GENERATOR_PATH / f).unlink(missing_ok=True)

    return {
        "ai1": ai1_path.name, "ai2": ai2_path.name,
        "wins1": wins1, "wins2": wins2, "draws": draws,
        "win_rate1": wr1, "win_rate2": wr2,
    }


def _run_pysim(
    ai1_path: Path, ai2_path: Path, n_fights: int, *,
    level, life, tp, mp, strength, agility, frequency, wisdom, resistance, magic,
    weapons1, weapons2, chips1, chips2,
) -> dict:
    """Run fights using PySim (Python LeekScript interpreter)."""
    import time
    from leekwars_agent.pysim.runner import PySimRunner

    runner = PySimRunner()
    wins1 = wins2 = draws = 0
    t0 = time.time()

    for i in range(n_fights):
        seed = i
        swap = (i % 2 == 1)

        a1, a2 = (ai2_path, ai1_path) if swap else (ai1_path, ai2_path)
        w1, w2 = (weapons2, weapons1) if swap else (weapons1, weapons2)
        c1, c2 = (chips2, chips1) if swap else (chips1, chips2)

        result = runner.run_1v1(
            str(a1), str(a2), seed=seed,
            level=level, life=life, tp=tp, mp=mp,
            strength=strength, agility=agility, frequency=frequency,
            wisdom=wisdom, resistance=resistance, magic=magic,
            weapon_ids=w1, chip_ids=c1,
            weapon_ids_2=w2, chip_ids_2=c2,
        )

        winner = result["winner"]
        if winner == 0:
            draws += 1
        elif (winner == 1 and not swap) or (winner == 2 and swap):
            wins1 += 1
        else:
            wins2 += 1

        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            print(f"Progress: {i+1}/{n_fights} ({wins1}W-{wins2}L-{draws}D) "
                  f"[{(i+1)/elapsed:.1f} fights/sec]")

    elapsed = time.time() - t0
    total = wins1 + wins2 + draws
    wr1 = (wins1 / total * 100) if total > 0 else 0
    wr2 = (wins2 / total * 100) if total > 0 else 0

    print(f"\n=== Results ({total} fights, {elapsed:.1f}s, {total/elapsed:.1f} fights/sec) ===")
    print(f"{ai1_path.name}: {wins1}W ({wr1:.1f}%)")
    print(f"{ai2_path.name}: {wins2}W ({wr2:.1f}%)")
    print(f"Draws: {draws}")

    if wins1 > wins2:
        print(f"\n> {ai1_path.name} wins by {wr1 - wr2:.1f}%")
    elif wins2 > wins1:
        print(f"\n> {ai2_path.name} wins by {wr2 - wr1:.1f}%")
    else:
        print(f"\n= Tie!")

    return {
        "ai1": ai1_path.name, "ai2": ai2_path.name,
        "wins1": wins1, "wins2": wins2, "draws": draws,
        "win_rate1": wr1, "win_rate2": wr2,
    }


def _parse_id_list(arg: str | None, default: list[int]) -> list[int] | None:
    """Parse comma-separated int list. None=use default, 'none'=empty."""
    if arg is None:
        return None
    if arg.lower() == 'none' or arg.strip() == '':
        return []
    return [int(c) for c in arg.split(",") if c.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Compare two LeekScript AIs (defaults to our L73 build)")
    parser.add_argument("ai1", help="Path to first AI file")
    parser.add_argument("ai2", help="Path to second AI file")
    parser.add_argument("-n", "--num-fights", type=int, default=100)
    parser.add_argument("--level", type=int, default=LEEK_LEVEL)
    parser.add_argument("--bare", action="store_true",
                        help="Use bare defaults (L1, no stats) instead of our build")
    # AI1 stats (default=our build from sim_defaults)
    parser.add_argument("--str1", type=int, default=LEEK_STR)
    parser.add_argument("--agi1", type=int, default=LEEK_AGI)
    parser.add_argument("--freq1", type=int, default=LEEK_FREQ)
    parser.add_argument("--wis1", type=int, default=LEEK_WIS)
    parser.add_argument("--res1", type=int, default=LEEK_RES)
    parser.add_argument("--sci1", type=int, default=LEEK_SCI)
    parser.add_argument("--mag1", type=int, default=LEEK_MAG)
    parser.add_argument("--life1", type=int, default=LEEK_LIFE)
    parser.add_argument("--tp1", type=int, default=LEEK_TP)
    parser.add_argument("--mp1", type=int, default=LEEK_MP)
    # AI2 stats (same defaults = mirror match)
    parser.add_argument("--str2", type=int, default=LEEK_STR)
    parser.add_argument("--agi2", type=int, default=LEEK_AGI)
    parser.add_argument("--freq2", type=int, default=LEEK_FREQ)
    parser.add_argument("--wis2", type=int, default=LEEK_WIS)
    parser.add_argument("--res2", type=int, default=LEEK_RES)
    parser.add_argument("--sci2", type=int, default=LEEK_SCI)
    parser.add_argument("--mag2", type=int, default=LEEK_MAG)
    parser.add_argument("--life2", type=int, default=LEEK_LIFE)
    parser.add_argument("--tp2", type=int, default=LEEK_TP)
    parser.add_argument("--mp2", type=int, default=LEEK_MP)
    # Equipment
    parser.add_argument("--weapons1", type=str, default=None,
                        help=f"AI1 weapons (comma-separated IDs). Default: {DEFAULT_WEAPONS}")
    parser.add_argument("--weapons2", type=str, default=None,
                        help=f"AI2 weapons (comma-separated IDs). Default: {DEFAULT_WEAPONS}")
    parser.add_argument("--chips1", type=str, default=None,
                        help=f"AI1 chips (comma-separated IDs). Default: {DEFAULT_CHIPS}")
    parser.add_argument("--chips2", type=str, default=None,
                        help=f"AI2 chips (comma-separated IDs). Default: {DEFAULT_CHIPS}")
    # First-mover
    parser.add_argument("--attacker", type=int, default=0, choices=[0, 1, 2])
    parser.add_argument("-v", "--verbose", action="store_true")
    # Engine
    parser.add_argument("--engine", choices=["java", "pysim"], default="java",
                        help="Fight engine: java (generator) or pysim (Python interpreter)")

    args = parser.parse_args()

    # --bare: reset to minimal defaults
    if args.bare:
        args.level = 1
        for attr in ['str1', 'agi1', 'freq1', 'wis1', 'res1', 'sci1', 'mag1',
                      'str2', 'agi2', 'freq2', 'wis2', 'res2', 'sci2', 'mag2']:
            setattr(args, attr, 0)
        args.life1 = args.life2 = 100

    compare_ais(
        args.ai1, args.ai2,
        n_fights=args.num_fights, level=args.level,
        strength1=args.str1, agility1=args.agi1, frequency1=args.freq1,
        wisdom1=args.wis1, resistance1=args.res1, science1=args.sci1, magic1=args.mag1,
        life1=args.life1, tp1=args.tp1, mp1=args.mp1,
        strength2=args.str2, agility2=args.agi2, frequency2=args.freq2,
        wisdom2=args.wis2, resistance2=args.res2, science2=args.sci2, magic2=args.mag2,
        life2=args.life2, tp2=args.tp2, mp2=args.mp2,
        weapons1=_parse_id_list(args.weapons1, DEFAULT_WEAPONS),
        weapons2=_parse_id_list(args.weapons2, DEFAULT_WEAPONS),
        chips1=_parse_id_list(args.chips1, DEFAULT_CHIPS),
        chips2=_parse_id_list(args.chips2, DEFAULT_CHIPS),
        attacker=args.attacker, verbose=args.verbose,
        engine=args.engine,
    )


if __name__ == "__main__":
    main()
