#!/usr/bin/env python3
"""Debug a single fight between two AIs with full action log.

Defaults to our leek's current build (from sim_defaults.py).

Usage:
    # Single debug fight at our build (no stat args needed!)
    poetry run python scripts/debug_fight.py ais/fighter_v11.leek ais/fighter_v14.leek

    # With custom stats
    poetry run python scripts/debug_fight.py v1.leek v2.leek --str1 200

    # Bare-bones (level 1, no stats)
    poetry run python scripts/debug_fight.py v1.leek v2.leek --bare
"""

import sys
import os
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import (
    Simulator, EntityConfig, ScenarioConfig,
    GENERATOR_PATH, copy_ai_to_generator,
)
from sim_defaults import *  # noqa: F403 F401

# Action type constants (from Java generator)
ACTION_TYPES = {
    0: "START_FIGHT", 1: "USE_WEAPON", 2: "USE_CHIP", 3: "SET_WEAPON",
    4: "MOVE", 5: "KILL", 6: "NEW_TURN", 7: "ENTITY_TURN", 8: "END_TURN",
    9: "SUMMON", 10: "RESURRECTION", 11: "ADD_EFFECT", 12: "REMOVE_EFFECT",
    13: "UPDATE_EFFECT", 14: "SAY", 15: "LAMA", 16: "SHOW_CELL",
    17: "VITALITY", 18: "ENTITY_DIE", 100: "DAMAGE", 101: "HEAL",
}


def parse_actions(actions: list, leeks: dict) -> list[dict]:
    """Parse raw action arrays into structured events."""
    parsed = []
    current_entity = None

    for action in actions:
        if not action:
            continue
        action_type = action[0] if action else None
        action_name = ACTION_TYPES.get(action_type, f"UNKNOWN_{action_type}")
        event = {"type": action_name, "raw": action}

        if action_type == 6:  # NEW_TURN
            event["turn"] = action[1] if len(action) > 1 else 0
        elif action_type == 7:  # ENTITY_TURN
            eid = action[1] if len(action) > 1 else None
            current_entity = eid
            event["entity_id"] = eid
            event["entity_name"] = leeks.get(str(eid), {}).get("name", f"E{eid}")
        elif action_type == 4:  # MOVE
            eid = action[1] if len(action) > 1 else None
            path = action[2] if len(action) > 2 else []
            event["entity_name"] = leeks.get(str(eid), {}).get("name", f"E{eid}")
            event["cells_moved"] = len(path) if path else 0
        elif action_type == 1:  # USE_WEAPON
            eid = action[1] if len(action) > 1 else None
            event["entity_name"] = leeks.get(str(eid), {}).get("name", f"E{eid}")
            event["target_cell"] = action[2] if len(action) > 2 else None
            event["weapon_id"] = action[3] if len(action) > 3 else None
        elif action_type == 100:  # DAMAGE
            tid = action[1] if len(action) > 1 else None
            event["target_name"] = leeks.get(str(tid), {}).get("name", f"E{tid}")
            event["damage"] = action[2] if len(action) > 2 else 0
        elif action_type == 3:  # SET_WEAPON
            eid = action[1] if len(action) > 1 else None
            event["entity_name"] = leeks.get(str(eid), {}).get("name", f"E{eid}")
            event["weapon_id"] = action[2] if len(action) > 2 else None
        elif action_type == 18:  # ENTITY_DIE
            eid = action[1] if len(action) > 1 else None
            kid = action[2] if len(action) > 2 else None
            event["entity_name"] = leeks.get(str(eid), {}).get("name", f"E{eid}")
            event["killer_name"] = leeks.get(str(kid), {}).get("name", f"E{kid}")

        parsed.append(event)
    return parsed


def format_action_log(parsed_actions: list) -> str:
    """Format parsed actions as readable log."""
    lines = []
    for event in parsed_actions:
        t = event["type"]
        if t == "NEW_TURN":
            lines.append(f"\n{'='*50}\nTURN {event.get('turn', '?')}\n{'='*50}")
        elif t == "ENTITY_TURN":
            lines.append(f"\n--- {event.get('entity_name', '?')}'s turn ---")
        elif t == "MOVE" and event.get("cells_moved", 0) > 0:
            lines.append(f"  MOVE: {event['entity_name']} moves {event['cells_moved']} cells")
        elif t == "SET_WEAPON":
            lines.append(f"  EQUIP: {event['entity_name']} equips weapon {event.get('weapon_id')}")
        elif t == "USE_WEAPON":
            lines.append(f"  ATTACK: {event['entity_name']} fires at cell {event.get('target_cell')}")
        elif t == "DAMAGE":
            lines.append(f"    -> {event['target_name']} takes {event.get('damage')} damage")
        elif t == "ENTITY_DIE":
            lines.append(f"  DEATH: {event['entity_name']} killed by {event.get('killer_name')}")
    return "\n".join(lines)


def compute_stats(parsed_actions: list, leeks: dict) -> dict:
    """Compute fight statistics from actions."""
    stats = {}
    for lid, ldata in leeks.items():
        stats[lid] = {
            "name": ldata.get("name", f"E{lid}"), "team": ldata.get("team", 0),
            "damage_dealt": 0, "damage_received": 0,
            "shots_fired": 0, "cells_moved": 0, "turns_played": 0,
        }
    current_entity = None
    for event in parsed_actions:
        if event["type"] == "ENTITY_TURN":
            current_entity = str(event.get("entity_id"))
            if current_entity in stats:
                stats[current_entity]["turns_played"] += 1
        elif event["type"] == "MOVE":
            eid = None
            for v in event.get("raw", []):
                if isinstance(v, int) and str(v) in stats:
                    eid = str(v)
                    break
            if eid and eid in stats:
                stats[eid]["cells_moved"] += event.get("cells_moved", 0)
        elif event["type"] == "USE_WEAPON":
            if current_entity and current_entity in stats:
                stats[current_entity]["shots_fired"] += 1
        elif event["type"] == "DAMAGE":
            tid = str(event.get("raw", [None, None])[1])
            dmg = event.get("damage", 0)
            if tid in stats:
                stats[tid]["damage_received"] += dmg
            if current_entity and current_entity in stats:
                stats[current_entity]["damage_dealt"] += dmg
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Debug single fight with full action log (defaults to our L73 build)")
    parser.add_argument("ai1", help="Path to first AI file")
    parser.add_argument("ai2", help="Path to second AI file")
    parser.add_argument("--level", type=int, default=LEEK_LEVEL)
    parser.add_argument("--bare", action="store_true",
                        help="Use bare defaults (L1, no stats)")
    # Stats (default=our build)
    parser.add_argument("--str1", type=int, default=LEEK_STR)
    parser.add_argument("--str2", type=int, default=LEEK_STR)
    parser.add_argument("--agi1", type=int, default=LEEK_AGI)
    parser.add_argument("--agi2", type=int, default=LEEK_AGI)
    parser.add_argument("--life1", type=int, default=LEEK_LIFE)
    parser.add_argument("--life2", type=int, default=LEEK_LIFE)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    if args.bare:
        args.level = 1
        args.str1 = args.str2 = 0
        args.agi1 = args.agi2 = 0
        args.life1 = args.life2 = 100

    ai1_path = Path(args.ai1)
    ai2_path = Path(args.ai2)
    if not ai1_path.exists() or not ai2_path.exists():
        print("Error: AI file not found")
        sys.exit(1)

    # Copy AIs (and includes) to generator
    ai1_name, ai1_files = copy_ai_to_generator(ai1_path, ai1_path.name)
    ai2_name, ai2_files = copy_ai_to_generator(ai2_path, ai2_path.name)
    all_copied_files = ai1_files + ai2_files

    print(f"AI 1: {ai1_path.name} (L{args.level} STR={args.str1} LIFE={args.life1})")
    print(f"AI 2: {ai2_path.name} (L{args.level} STR={args.str2} LIFE={args.life2})")
    print(f"Weapons: {DEFAULT_WEAPONS} | Chips: {DEFAULT_CHIPS}")
    print()

    entity1 = EntityConfig(
        id=0, name=ai1_path.stem, ai=ai1_name,
        level=args.level, life=args.life1, strength=args.str1, agility=args.agi1,
        team=1, weapons=DEFAULT_WEAPONS, chips=DEFAULT_CHIPS,
    )
    entity2 = EntityConfig(
        id=1, name=ai2_path.stem, ai=ai2_name,
        level=args.level, life=args.life2, strength=args.str2, agility=args.agi2,
        team=2, farmer=2, weapons=DEFAULT_WEAPONS, chips=DEFAULT_CHIPS,
    )

    scenario = ScenarioConfig(team1=[entity1], team2=[entity2], seed=args.seed)
    sim = Simulator()
    outcome = sim.run_scenario(scenario)

    # Parse fight data
    fight_data = outcome.raw_output.get("fight", {})
    leeks_list = fight_data.get("leeks", [])
    leeks = {str(l["id"]): l for l in leeks_list}
    parsed = parse_actions(outcome.actions, leeks)

    # Show debug logs
    if "logs" in outcome.raw_output:
        logs = outcome.raw_output["logs"]
        print("DEBUG LOGS:")
        print("-" * 60)
        for turn_key in sorted(logs.keys(), key=int):
            for entry in logs[turn_key]:
                # entry format: [entity_id, type, message, ...]
                msg = entry[2] if len(entry) > 2 else str(entry)
                eid = entry[0] if entry else "?"
                name = leeks.get(str(eid), {}).get("name", f"E{eid}")
                print(f"  [{name}] {msg}")
        print()

    # Result
    print("=" * 60)
    print("FIGHT RESULT")
    print("=" * 60)
    winner_str = "Team 1" if outcome.winner == 1 else "Team 2" if outcome.winner == 2 else "Draw"
    print(f"Winner: {winner_str}")
    print(f"Turns: {outcome.turns}")
    print(f"Duration: {outcome.duration_ms:.1f}ms")
    print()

    # Stats
    stats = compute_stats(parsed, leeks)
    print("STATISTICS:")
    print("-" * 60)
    for lid, s in sorted(stats.items(), key=lambda x: x[1]["team"]):
        print(f"{s['name']} (Team {s['team']}):")
        print(f"  Damage dealt: {s['damage_dealt']} | Received: {s['damage_received']}")
        print(f"  Shots: {s['shots_fired']} | Moved: {s['cells_moved']} cells | Turns: {s['turns_played']}")
        print()

    # Action log
    print("ACTION LOG:")
    print("-" * 60)
    print(format_action_log(parsed))

    # Save raw data
    debug_file = Path("data/debug_fight.json")
    debug_file.parent.mkdir(parents=True, exist_ok=True)
    debug_file.write_text(json.dumps({
        "winner": outcome.winner, "turns": outcome.turns,
        "actions": outcome.actions, "leeks": leeks, "stats": stats,
    }, indent=2))
    print(f"\nFull data saved to: {debug_file}")

    # Cleanup
    for f in all_copied_files:
        (GENERATOR_PATH / f).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
