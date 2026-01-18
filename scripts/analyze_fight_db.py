#!/usr/bin/env python3
"""Analyze fights_light.db to extract AI heuristics.

Extracts patterns from 10,000 fights to inform AI development.

Usage:
    poetry run python scripts/analyze_fight_db.py
    poetry run python scripts/analyze_fight_db.py --level 10-15
    poetry run python scripts/analyze_fight_db.py --fight 50529694
"""

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent / "fights_light.db"

# Action codes from action_log.py
ACTION_START_FIGHT = 0
ACTION_NEW_TURN = 6
ACTION_LEEK_TURN = 7
ACTION_END_TURN = 8
ACTION_MOVE_TO = 10
ACTION_USE_CHIP = 12
ACTION_SET_WEAPON = 13
ACTION_USE_WEAPON = 16
ACTION_LOST_LIFE = 101


@dataclass
class FightStats:
    """Statistics extracted from a single fight."""
    fight_id: int
    winner: int  # 1 or 2
    duration: int
    team1_level: int
    team2_level: int

    # Per-team stats
    team1_damage: int = 0
    team2_damage: int = 0
    team1_moves: int = 0
    team2_moves: int = 0
    team1_shots: int = 0
    team2_shots: int = 0
    team1_ops: int = 0
    team2_ops: int = 0

    # First action stats
    first_action_team1: str = ""
    first_action_team2: str = ""


def parse_fight_actions(fight_data: dict) -> FightStats:
    """Parse a fight's action log to extract statistics."""
    data = fight_data.get("data") or fight_data

    stats = FightStats(
        fight_id=fight_data.get("id", 0),
        winner=fight_data.get("winner", 0),
        duration=len([a for a in data.get("actions", []) if a[0] == ACTION_NEW_TURN]),
        team1_level=sum(l.get("level", 1) for l in fight_data.get("leeks1", [])),
        team2_level=sum(l.get("level", 1) for l in fight_data.get("leeks2", []))
    )

    # Build leek -> team mapping
    leek_team = {}
    leeks_data = data.get("leeks", [])
    # Handle both list and dict formats
    if isinstance(leeks_data, dict):
        leeks_list = list(leeks_data.values())
    else:
        leeks_list = leeks_data

    for leek in leeks_list:
        leek_id = leek.get("id")
        team = leek.get("team")
        # Team in data uses 1/2, normalize to 0/1 for internal use
        leek_team[leek_id] = 0 if team in (1, "1") else 1

    # Track ops per team
    ops_data = data.get("ops", {})
    for leek_id_str, ops in ops_data.items():
        team = leek_team.get(int(leek_id_str), 0)
        if team == 0:
            stats.team1_ops += ops
        else:
            stats.team2_ops += ops

    # Parse actions
    current_entity = None
    first_action_found = {0: False, 1: False}

    for action in data.get("actions", []):
        action_type = action[0]

        # Track current turn
        if action_type == ACTION_LEEK_TURN:
            current_entity = action[1] if len(action) > 1 else None
            continue

        # Extract damage from LOST_LIFE actions: [101, target_id, damage, source_id]
        if action_type == ACTION_LOST_LIFE and len(action) >= 3:
            target_id = action[1]
            damage = action[2]
            target_team = leek_team.get(target_id, 0)
            # Damage dealt TO team 1 = damage BY team 2
            if target_team == 0:
                stats.team2_damage += damage
            else:
                stats.team1_damage += damage
            continue

        if current_entity is None:
            continue

        team = leek_team.get(current_entity, 0)

        # Track first meaningful action per team
        if not first_action_found[team] and action_type in [ACTION_MOVE_TO, ACTION_USE_WEAPON, ACTION_USE_CHIP]:
            first_action_found[team] = True
            action_name = {ACTION_MOVE_TO: "move", ACTION_USE_WEAPON: "weapon", ACTION_USE_CHIP: "chip"}[action_type]
            if team == 0:
                stats.first_action_team1 = action_name
            else:
                stats.first_action_team2 = action_name

        # Count actions
        if action_type == ACTION_MOVE_TO:
            if team == 0:
                stats.team1_moves += 1
            else:
                stats.team2_moves += 1
        elif action_type == ACTION_USE_WEAPON:
            if team == 0:
                stats.team1_shots += 1
            else:
                stats.team2_shots += 1

    return stats


def analyze_database(db_path: Path, level_range: tuple[int, int] | None = None) -> dict[str, Any]:
    """Analyze all fights in database."""
    conn = sqlite3.connect(db_path)

    # Build query
    query = "SELECT json_data, winner, team1_levels, team2_levels, duration FROM fights"
    params = []

    if level_range:
        query += " WHERE team1_levels BETWEEN ? AND ?"
        params = [level_range[0], level_range[1]]

    cursor = conn.execute(query, params)

    # Aggregate stats
    results = {
        "total_fights": 0,
        "team1_wins": 0,
        "team2_wins": 0,
        "draws": 0,
        "avg_duration": 0,
        "first_action_wins": {"move": 0, "weapon": 0, "chip": 0},
        "first_action_total": {"move": 0, "weapon": 0, "chip": 0},
        "ops_winner_avg": 0,
        "ops_loser_avg": 0,
        "damage_per_turn_winner": 0,
        "damage_per_turn_loser": 0,
        "by_duration": defaultdict(lambda: {"total": 0, "team1_wins": 0}),
        "by_first_action": defaultdict(lambda: {"total": 0, "wins": 0}),
    }

    all_stats: list[FightStats] = []

    for row in cursor:
        json_data, winner, t1_lvl, t2_lvl, duration = row
        try:
            fight_data = json.loads(json_data)
            stats = parse_fight_actions(fight_data)
            all_stats.append(stats)

            results["total_fights"] += 1
            if winner == 1:
                results["team1_wins"] += 1
            elif winner == 2:
                results["team2_wins"] += 1
            else:
                results["draws"] += 1

            results["avg_duration"] += duration
            results["by_duration"][duration]["total"] += 1
            if winner == 1:
                results["by_duration"][duration]["team1_wins"] += 1

            # First action analysis
            if stats.first_action_team1:
                results["first_action_total"][stats.first_action_team1] += 1
                if winner == 1:
                    results["first_action_wins"][stats.first_action_team1] += 1

            # Track first action -> win correlation
            key = f"t1_{stats.first_action_team1}_t2_{stats.first_action_team2}"
            results["by_first_action"][key]["total"] += 1
            if winner == 1:
                results["by_first_action"][key]["wins"] += 1

        except (json.JSONDecodeError, KeyError) as e:
            continue

    conn.close()

    # Calculate averages
    if results["total_fights"] > 0:
        results["avg_duration"] /= results["total_fights"]
        results["team1_wr"] = 100 * results["team1_wins"] / results["total_fights"]

    # Ops and damage analysis
    winner_ops = []
    loser_ops = []
    winner_dpt = []
    loser_dpt = []

    for s in all_stats:
        if s.winner == 1:
            winner_ops.append(s.team1_ops)
            loser_ops.append(s.team2_ops)
            if s.duration > 0:
                winner_dpt.append(s.team1_damage / s.duration)
                loser_dpt.append(s.team2_damage / s.duration)
        elif s.winner == 2:
            winner_ops.append(s.team2_ops)
            loser_ops.append(s.team1_ops)
            if s.duration > 0:
                winner_dpt.append(s.team2_damage / s.duration)
                loser_dpt.append(s.team1_damage / s.duration)

    if winner_ops:
        results["ops_winner_avg"] = sum(winner_ops) / len(winner_ops)
        results["ops_loser_avg"] = sum(loser_ops) / len(loser_ops)
    if winner_dpt:
        results["damage_per_turn_winner"] = sum(winner_dpt) / len(winner_dpt)
        results["damage_per_turn_loser"] = sum(loser_dpt) / len(loser_dpt)

    return results


def analyze_single_fight(db_path: Path, fight_id: int) -> None:
    """Deep-dive analysis of a single fight."""
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT json_data FROM fights WHERE fight_id = ?", [fight_id]).fetchone()
    conn.close()

    if not row:
        print(f"Fight {fight_id} not found")
        return

    fight_data = json.loads(row[0])
    data = fight_data.get("data") or fight_data

    print(f"\n=== Fight {fight_id} Analysis ===")
    print(f"Winner: Team {fight_data.get('winner')}")
    print(f"Team 1: {[l.get('name') for l in fight_data.get('leeks1', [])]}")
    print(f"Team 2: {[l.get('name') for l in fight_data.get('leeks2', [])]}")

    # Leek details
    leeks_data = data.get("leeks", [])
    if isinstance(leeks_data, dict):
        leeks_list = list(leeks_data.values())
    else:
        leeks_list = leeks_data

    print("\nLeek Stats:")
    for leek in leeks_list:
        print(f"  {leek.get('name')}: L{leek.get('level')} HP={leek.get('life')} STR={leek.get('strength')} "
              f"AGI={leek.get('agility')} TP={leek.get('tp')} MP={leek.get('mp')}")

    # Ops usage
    print("\nOperations:")
    leek_by_id = {str(l.get("id")): l for l in leeks_list}
    for leek_id, ops in data.get("ops", {}).items():
        leek = leek_by_id.get(str(leek_id), {})
        print(f"  {leek.get('name', leek_id)}: {ops:,} ops")

    # Action summary
    print("\nAction Log (first 30 actions):")
    current_entity = None
    leek_names = {str(l.get("id")): l.get("name") for l in leeks_list}

    for i, action in enumerate(data.get("actions", [])[:30]):
        action_type = action[0]

        if action_type == ACTION_LEEK_TURN:
            current_entity = action[1] if len(action) > 1 else None
            entity_name = leek_names.get(str(current_entity), f"E{current_entity}")
            print(f"\n  Turn: {entity_name}'s turn")
        elif action_type == ACTION_MOVE_TO:
            # Format: [10, entity_id, dest_cell, path]
            dest = action[2] if len(action) > 2 else action[1]
            path_len = len(action[3]) if len(action) > 3 and isinstance(action[3], list) else 0
            print(f"    MOVE to cell {dest} ({path_len} steps)")
        elif action_type == ACTION_USE_WEAPON:
            # Format: [16, target_cell, weapon_id]
            target_cell = action[1] if len(action) > 1 else "?"
            weapon_id = action[2] if len(action) > 2 else "?"
            print(f"    WEAPON -> cell {target_cell} (weapon {weapon_id})")
        elif action_type == ACTION_USE_CHIP:
            target = leek_names.get(str(action[1]), f"E{action[1]}")
            print(f"    CHIP -> {target}")
        elif action_type == ACTION_LOST_LIFE:
            target = leek_names.get(str(action[1]), f"E{action[1]}")
            dmg = action[2] if len(action) > 2 else "?"
            print(f"    DMG: {target} takes {dmg}")
        elif action_type == ACTION_NEW_TURN:
            print(f"\n  --- Turn {action[1] if len(action) > 1 else '?'} ---")


def print_results(results: dict[str, Any]) -> None:
    """Pretty print analysis results."""
    print("\n" + "="*60)
    print("FIGHT DATABASE ANALYSIS")
    print("="*60)

    print(f"\nTotal fights analyzed: {results['total_fights']:,}")
    print(f"Team 1 wins: {results['team1_wins']:,} ({results.get('team1_wr', 0):.1f}%)")
    print(f"Team 2 wins: {results['team2_wins']:,}")
    print(f"Draws: {results['draws']:,}")
    print(f"Average duration: {results['avg_duration']:.1f} turns")

    print("\n--- First-Mover Advantage by Duration ---")
    for dur in sorted(results["by_duration"].keys()):
        data = results["by_duration"][dur]
        if data["total"] >= 10:  # Only show if enough samples
            wr = 100 * data["team1_wins"] / data["total"]
            print(f"  {dur} turns: {data['total']:,} fights, Team 1 WR: {wr:.1f}%")

    print("\n--- First Action Correlation ---")
    print("(Does moving first vs shooting first affect win rate?)")
    for fa, data in sorted(results["first_action_total"].items()):
        if data > 0:
            wr = 100 * results["first_action_wins"][fa] / data
            print(f"  Team 1 opens with {fa}: {data:,} times, WR: {wr:.1f}%")

    print("\n--- Operations Usage ---")
    print(f"  Winners average: {results['ops_winner_avg']:,.0f} ops")
    print(f"  Losers average: {results['ops_loser_avg']:,.0f} ops")
    if results['ops_loser_avg'] > 0:
        ratio = results['ops_winner_avg'] / results['ops_loser_avg']
        print(f"  Ratio: {ratio:.2f}x")

    print("\n--- Damage Per Turn ---")
    print(f"  Winners: {results['damage_per_turn_winner']:.1f} dmg/turn")
    print(f"  Losers: {results['damage_per_turn_loser']:.1f} dmg/turn")

    print("\n--- First Action Matchup Analysis ---")
    print("(What happens when Team 1 does X and Team 2 does Y?)")
    matchups = [(k, v) for k, v in results["by_first_action"].items() if v["total"] >= 50]
    matchups.sort(key=lambda x: x[1]["total"], reverse=True)
    for matchup, data in matchups[:10]:
        wr = 100 * data["wins"] / data["total"]
        print(f"  {matchup}: {data['total']:,} fights, T1 WR: {wr:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Analyze fight database for heuristics")
    parser.add_argument("--level", type=str, help="Level range (e.g., 10-15)")
    parser.add_argument("--fight", type=int, help="Analyze specific fight ID")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    if args.fight:
        analyze_single_fight(DB_PATH, args.fight)
        return

    level_range = None
    if args.level:
        parts = args.level.split("-")
        level_range = (int(parts[0]), int(parts[1]))
        print(f"Analyzing fights at levels {level_range[0]}-{level_range[1]}...")

    results = analyze_database(DB_PATH, level_range)
    print_results(results)


if __name__ == "__main__":
    main()
