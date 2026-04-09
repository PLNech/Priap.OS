"""PySim Round-Robin Tournament with ELO Ratings.

Runs all pairs of AIs against each other (FIGHTS_PER_SIDE fights per side).
Parallelized with ProcessPoolExecutor for ~10-15x speedup on multi-core.
Results written to docs/research/pysim_elo_tournament.md.
"""

import math
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ── Tournament participants ─────────────────────────────────────────

PARTICIPANTS = [
    # Our AI
    ("v14", "ais/fighter_v14_flat.leek"),
    # External opponents (from GitHub)
    ("pbondoer", "ais/opponents/pbondoer_silly_lemon.leek"),
    ("shup1_main", "ais/opponents/shup1_main.leek"),
    ("shup1_pata", "ais/opponents/shup1_pata.leek"),
    # cktang88 — weapon-specialized AIs
    ("ck_magnum1", "ais/opponents/cktang88_magnum1.leek"),
    ("ck_magnum12", "ais/opponents/cktang88_magnum-12.leek"),
    ("ck_magnum_sword", "ais/opponents/cktang88_magnum-sword.leek"),
    ("ck_pistol1", "ais/opponents/cktang88_pistol1.leek"),
    ("ck_pistol_sg", "ais/opponents/cktang88_pistol-shotgun.leek"),
    ("ck_flamethrower", "ais/opponents/cktang88_flamethrower-destroyer.leek"),
    ("ck_venom_sg", "ais/opponents/cktang88_venom-shotgun.leek"),
    # galiroe — French modular AIs
    ("galiroe_main", "ais/opponents/galiroe_Main.leek"),
    # yaelMagnier — DamageMap AI (modular, 13 files)
    ("yaelmagnier", "ais/opponents/yaelmagnier/main/MAIN.lk"),
    # tankyx_v8 — Beam search AI with OOP (32 files, includes)
    ("tankyx", "ais/opponents/tankyx_v8/main.lk"),
    # chinafred — OOP AI with classes, sets, danger maps (26 files)
    ("chinafred", "ais/opponents/chinafred/Main/Kassbi_Class.leek"),
    # fauconv — Deep OOP AI with typed engine, strategies (29 files)
    ("fauconv", "ais/opponents/fauconv/main.leek"),
    # Archetypes (calibration)
    ("arch_balanced", "ais/archetype_balanced.leek"),
    ("arch_burst", "ais/archetype_burst.leek"),
    ("arch_kiter", "ais/archetype_kiter.leek"),
    ("arch_rusher", "ais/archetype_rusher.leek"),
    ("arch_tank", "ais/archetype_tank.leek"),
]

FIGHTS_PER_SIDE = 20  # 20 per side = 40 per matchup
MAX_WORKERS = max(1, (os.cpu_count() or 4) // 2)  # 50% of cores — keep machine responsive


# ── Worker function (runs in subprocess) ───────────────────────────

def run_matchup(i: int, j: int, matchup_idx: int) -> dict:
    """Run all fights for one matchup (i vs j). Returns results dict.
    This function runs in a worker process — creates its own PySimRunner."""
    from src.leekwars_agent.pysim.runner import PySimRunner

    runner = PySimRunner()
    name_i, path_i = PARTICIPANTS[i]
    name_j, path_j = PARTICIPANTS[j]

    w_i, w_j, d = 0, 0, 0
    matchup_errors = defaultdict(set)

    for side in [0, 1]:
        if side == 0:
            p1_name, p1_path = name_i, path_i
            p2_name, p2_path = name_j, path_j
        else:
            p1_name, p1_path = name_j, path_j
            p2_name, p2_path = name_i, path_i

        for fight_idx in range(FIGHTS_PER_SIDE):
            seed = matchup_idx * 1000 + side * 500 + fight_idx
            try:
                result = runner.run_1v1(p1_path, p2_path, seed=seed)
                winner = result["winner"]

                if side == 0:
                    if winner == 1:
                        w_i += 1
                    elif winner == 2:
                        w_j += 1
                    else:
                        d += 1
                else:
                    if winner == 1:
                        w_j += 1
                    elif winner == 2:
                        w_i += 1
                    else:
                        d += 1

                # Collect errors
                for eid in [1, 2]:
                    ai_name = p1_name if eid == 1 else p2_name
                    for log in result["debug_logs"].get(eid, []):
                        if "ERROR" in log:
                            matchup_errors[ai_name].add(log[:100])

            except Exception as exc:
                d += 1
                matchup_errors[name_i if side == 0 else name_j].add(f"CRASH: {exc}")

    return {
        "i": i, "j": j,
        "w_i": w_i, "w_j": w_j, "d": d,
        "name_i": name_i, "name_j": name_j,
        "errors": {k: list(v) for k, v in matchup_errors.items()},
    }


# ── ELO computation ─────────────────────────────────────────────────

def expected_score(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def update_elo(elo_a: float, elo_b: float, score_a: float, k: float = 32) -> tuple[float, float]:
    """Update ELO ratings for a single game. score_a: 1=win, 0.5=draw, 0=loss."""
    ea = expected_score(elo_a, elo_b)
    eb = 1.0 - ea
    new_a = elo_a + k * (score_a - ea)
    new_b = elo_b + k * ((1 - score_a) - eb)
    return new_a, new_b


def run_tournament():
    n = len(PARTICIPANTS)

    # Results matrix
    wins = [[0] * n for _ in range(n)]
    draws = [[0] * n for _ in range(n)]
    errors = defaultdict(set)

    # Build matchup list
    matchups = []
    matchup_idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            matchup_idx += 1
            matchups.append((i, j, matchup_idx))

    total_matchups = len(matchups)
    total_fights = total_matchups * FIGHTS_PER_SIDE * 2

    print(f"Round-robin tournament: {n} participants, {total_matchups} matchups, "
          f"{FIGHTS_PER_SIDE*2} fights each = {total_fights} total")
    print(f"Workers: {MAX_WORKERS} processes")
    print(flush=True)

    start_time = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(run_matchup, i, j, idx): (i, j)
            for i, j, idx in matchups
        }

        for future in as_completed(futures):
            completed += 1
            result = future.result()
            i, j = result["i"], result["j"]
            w_i, w_j, d = result["w_i"], result["w_j"], result["d"]

            wins[i][j] = w_i
            wins[j][i] = w_j
            draws[i][j] = draws[j][i] = d

            for name, errs in result["errors"].items():
                errors[name].update(errs)

            elapsed = time.time() - start_time
            fights_done = completed * FIGHTS_PER_SIDE * 2
            rate = fights_done / elapsed
            eta = (total_fights - fights_done) / rate if rate > 0 else 0

            print(f"  [{completed}/{total_matchups}] {result['name_i']} vs {result['name_j']}: "
                  f"{w_i}-{d}-{w_j}  ({rate:.0f} fights/sec, ETA {eta:.0f}s)",
                  flush=True)

    elapsed = time.time() - start_time
    print(f"\nAll {total_fights} fights completed in {elapsed:.1f}s "
          f"({total_fights/elapsed:.0f} fights/sec)", flush=True)

    # ── Compute ELO ─────────────────────────────────────────────────

    elo = {name: 1500.0 for name, _ in PARTICIPANTS}

    for i in range(n):
        for j in range(i + 1, n):
            name_i = PARTICIPANTS[i][0]
            name_j = PARTICIPANTS[j][0]

            total = wins[i][j] + wins[j][i] + draws[i][j]
            if total == 0:
                continue

            for _ in range(wins[i][j]):
                elo[name_i], elo[name_j] = update_elo(elo[name_i], elo[name_j], 1.0)
            for _ in range(wins[j][i]):
                elo[name_i], elo[name_j] = update_elo(elo[name_i], elo[name_j], 0.0)
            for _ in range(draws[i][j]):
                elo[name_i], elo[name_j] = update_elo(elo[name_i], elo[name_j], 0.5)

    # ── Sort by ELO ─────────────────────────────────────────────────

    ranking = sorted(elo.items(), key=lambda x: -x[1])

    print()
    print("=" * 60)
    print("  FINAL ELO RANKINGS")
    print("=" * 60)
    for rank, (name, rating) in enumerate(ranking, 1):
        idx = next(k for k, (nm, _) in enumerate(PARTICIPANTS) if nm == name)
        total_w = sum(wins[idx][j] for j in range(n) if j != idx)
        total_l = sum(wins[j][idx] for j in range(n) if j != idx)
        total_d = sum(draws[idx][j] for j in range(n) if j != idx)
        total = total_w + total_l + total_d
        wr = total_w / total * 100 if total else 0
        print(f"  #{rank} {name:20s} ELO {rating:7.1f}  WR {wr:5.1f}%  ({total_w}W-{total_l}L-{total_d}D)")

    # ── Write results ───────────────────────────────────────────────

    output_path = Path("docs/research/pysim_elo_tournament.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("# PySim ELO Tournament Results\n\n")
        f.write(f"**Date**: {date.today().isoformat()} (S45)\n")
        f.write(f"**Participants**: {n}\n")
        f.write(f"**Fights per matchup**: {FIGHTS_PER_SIDE * 2} ({FIGHTS_PER_SIDE}/side)\n")
        f.write(f"**Total fights**: {total_fights}\n")
        f.write(f"**Duration**: {elapsed:.1f}s ({total_fights/elapsed:.0f} fights/sec, {MAX_WORKERS} workers)\n\n")

        f.write("## ELO Rankings\n\n")
        f.write("| Rank | AI | ELO | WR% | W | L | D |\n")
        f.write("|------|-----|-----|-----|---|---|---|\n")

        for rank, (name, rating) in enumerate(ranking, 1):
            idx = next(k for k, (nm, _) in enumerate(PARTICIPANTS) if nm == name)
            total_w = sum(wins[idx][j] for j in range(n) if j != idx)
            total_l = sum(wins[j][idx] for j in range(n) if j != idx)
            total_d = sum(draws[idx][j] for j in range(n) if j != idx)
            total = total_w + total_l + total_d
            wr = total_w / total * 100 if total else 0
            f.write(f"| {rank} | {name} | {rating:.0f} | {wr:.1f} | {total_w} | {total_l} | {total_d} |\n")

        f.write("\n## Head-to-Head Matrix (wins)\n\n")
        f.write("| | " + " | ".join(nm for nm, _ in PARTICIPANTS) + " |\n")
        f.write("|" + "---|" * (n + 1) + "\n")
        for i in range(n):
            row = f"| **{PARTICIPANTS[i][0]}** |"
            for j in range(n):
                if i == j:
                    row += " - |"
                else:
                    row += f" {wins[i][j]}-{draws[i][j]}-{wins[j][i]} |"
            f.write(row + "\n")

        if errors:
            f.write("\n## Runtime Errors\n\n")
            for name in sorted(errors.keys()):
                f.write(f"### {name}\n")
                for err in sorted(errors[name]):
                    f.write(f"- `{err}`\n")
                f.write("\n")

    print(f"\nResults written to {output_path}")

    if errors:
        print("\nRuntime errors by AI:")
        for name in sorted(errors.keys()):
            print(f"  {name}: {len(errors[name])} unique errors")


if __name__ == "__main__":
    run_tournament()
