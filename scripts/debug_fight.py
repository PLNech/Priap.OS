#!/usr/bin/env python3
"""Debug a single fight between two AIs with full action log output.

Usage:
    poetry run python scripts/debug_fight.py ais/fighter_v1.leek ais/fighter_v3.leek
"""

import sys
import os
import re
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator, ScenarioConfig, EntityConfig

GENERATOR_PATH = Path(__file__).parent.parent / "tools" / "leek-wars-generator"

# Default chips matching our leek (from GROUND_TRUTH.md)
# CURE=4, FLAME=5, FLASH=6, PROTEIN=8, BOOTS=14, MOTIVATION=15
DEFAULT_CHIPS = [4, 5, 6, 8, 14, 15]


def extract_includes(source: Path) -> list[Path]:
    """Extract include() statements from a LeekScript file."""
    includes = []
    content = source.read_text()

    # Match: include("filename") or include('filename')
    pattern = r'include\s*\(\s*["\']([^"\']+)["\']\s*\)'

    for match in re.finditer(pattern, content):
        include_name = match.group(1)

        # Resolve relative to source file's directory
        include_path = source.parent / include_name
        if include_path.exists():
            includes.append(include_path)
            # Recursively check for nested includes
            includes.extend(extract_includes(include_path))

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for p in includes:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    return unique

# Action type constants (from Java generator)
ACTION_TYPES = {
    0: "START_FIGHT",
    1: "USE_WEAPON",
    2: "USE_CHIP",
    3: "SET_WEAPON",
    4: "MOVE",
    5: "KILL",
    6: "NEW_TURN",
    7: "ENTITY_TURN",
    8: "END_TURN",
    9: "SUMMON",
    10: "RESURRECTION",
    11: "ADD_EFFECT",
    12: "REMOVE_EFFECT",
    13: "UPDATE_EFFECT",
    14: "SAY",
    15: "LAMA",
    16: "SHOW_CELL",
    17: "VITALITY",
    18: "ENTITY_DIE",
    100: "DAMAGE",
    101: "HEAL",
}


def copy_ai_to_generator(source: Path, name: str) -> tuple[str, list[str]]:
    """Copy AI file and its includes to generator directory.

    Returns tuple of (main_name, list_of_copied_files).
    """
    copied_files = []

    # Copy main file
    dest = GENERATOR_PATH / name
    dest.write_text(source.read_text())
    copied_files.append(name)

    # Copy included files
    for include_path in extract_includes(source):
        include_dest = GENERATOR_PATH / include_path.name
        include_dest.write_text(include_path.read_text())
        copied_files.append(include_path.name)

    return name, copied_files


def parse_actions(actions: list, leeks: dict) -> list[dict]:
    """Parse raw action arrays into structured events."""
    parsed = []
    current_turn = 0
    current_entity = None

    for action in actions:
        if not action:
            continue

        action_type = action[0] if action else None
        action_name = ACTION_TYPES.get(action_type, f"UNKNOWN_{action_type}")

        event = {"type": action_name, "raw": action}

        if action_type == 6:  # NEW_TURN
            current_turn = action[1] if len(action) > 1 else current_turn + 1
            event["turn"] = current_turn

        elif action_type == 7:  # ENTITY_TURN
            entity_id = action[1] if len(action) > 1 else None
            current_entity = entity_id
            entity_name = leeks.get(str(entity_id), {}).get("name", f"Entity_{entity_id}")
            event["entity_id"] = entity_id
            event["entity_name"] = entity_name

        elif action_type == 4:  # MOVE
            entity_id = action[1] if len(action) > 1 else None
            path = action[2] if len(action) > 2 else []
            entity_name = leeks.get(str(entity_id), {}).get("name", f"Entity_{entity_id}")
            event["entity_name"] = entity_name
            event["path"] = path
            event["cells_moved"] = len(path) if path else 0

        elif action_type == 1:  # USE_WEAPON
            entity_id = action[1] if len(action) > 1 else None
            target_cell = action[2] if len(action) > 2 else None
            weapon_id = action[3] if len(action) > 3 else None
            entity_name = leeks.get(str(entity_id), {}).get("name", f"Entity_{entity_id}")
            event["entity_name"] = entity_name
            event["target_cell"] = target_cell
            event["weapon_id"] = weapon_id

        elif action_type == 100:  # DAMAGE
            target_id = action[1] if len(action) > 1 else None
            damage = action[2] if len(action) > 2 else 0
            target_name = leeks.get(str(target_id), {}).get("name", f"Entity_{target_id}")
            event["target_name"] = target_name
            event["damage"] = damage

        elif action_type == 3:  # SET_WEAPON
            entity_id = action[1] if len(action) > 1 else None
            weapon_id = action[2] if len(action) > 2 else None
            entity_name = leeks.get(str(entity_id), {}).get("name", f"Entity_{entity_id}")
            event["entity_name"] = entity_name
            event["weapon_id"] = weapon_id

        elif action_type == 18:  # ENTITY_DIE
            entity_id = action[1] if len(action) > 1 else None
            killer_id = action[2] if len(action) > 2 else None
            entity_name = leeks.get(str(entity_id), {}).get("name", f"Entity_{entity_id}")
            killer_name = leeks.get(str(killer_id), {}).get("name", f"Entity_{killer_id}")
            event["entity_name"] = entity_name
            event["killer_name"] = killer_name

        parsed.append(event)

    return parsed


def format_action_log(parsed_actions: list) -> str:
    """Format parsed actions as readable log."""
    lines = []
    current_turn = 0

    for event in parsed_actions:
        action_type = event["type"]

        if action_type == "NEW_TURN":
            current_turn = event.get("turn", current_turn + 1)
            lines.append(f"\n{'='*50}")
            lines.append(f"TURN {current_turn}")
            lines.append('='*50)

        elif action_type == "ENTITY_TURN":
            lines.append(f"\n--- {event.get('entity_name', '?')}'s turn ---")

        elif action_type == "MOVE":
            cells = event.get("cells_moved", 0)
            if cells > 0:
                lines.append(f"  MOVE: {event.get('entity_name')} moves {cells} cells")

        elif action_type == "SET_WEAPON":
            lines.append(f"  EQUIP: {event.get('entity_name')} equips weapon {event.get('weapon_id')}")

        elif action_type == "USE_WEAPON":
            lines.append(f"  ATTACK: {event.get('entity_name')} fires at cell {event.get('target_cell')}")

        elif action_type == "DAMAGE":
            lines.append(f"    -> {event.get('target_name')} takes {event.get('damage')} damage")

        elif action_type == "ENTITY_DIE":
            lines.append(f"  DEATH: {event.get('entity_name')} killed by {event.get('killer_name')}")

        elif action_type == "END_TURN":
            pass  # Skip, too verbose

    return "\n".join(lines)


def compute_stats(parsed_actions: list, leeks: dict) -> dict:
    """Compute fight statistics from actions."""
    stats = {}
    for leek_id, leek_data in leeks.items():
        stats[leek_id] = {
            "name": leek_data.get("name", f"Entity_{leek_id}"),
            "team": leek_data.get("team", 0),
            "damage_dealt": 0,
            "damage_received": 0,
            "shots_fired": 0,
            "cells_moved": 0,
            "turns_played": 0,
        }

    current_entity = None
    for event in parsed_actions:
        if event["type"] == "ENTITY_TURN":
            current_entity = str(event.get("entity_id"))
            if current_entity in stats:
                stats[current_entity]["turns_played"] += 1

        elif event["type"] == "MOVE":
            entity_id = None
            for raw_val in event.get("raw", []):
                if isinstance(raw_val, int) and str(raw_val) in stats:
                    entity_id = str(raw_val)
                    break
            if entity_id and entity_id in stats:
                stats[entity_id]["cells_moved"] += event.get("cells_moved", 0)

        elif event["type"] == "USE_WEAPON":
            if current_entity and current_entity in stats:
                stats[current_entity]["shots_fired"] += 1

        elif event["type"] == "DAMAGE":
            target_id = str(event.get("raw", [None, None])[1])
            damage = event.get("damage", 0)
            if target_id in stats:
                stats[target_id]["damage_received"] += damage
            if current_entity and current_entity in stats:
                stats[current_entity]["damage_dealt"] += damage

    return stats


def main():
    if len(sys.argv) < 3:
        print("Usage: poetry run python scripts/debug_fight.py <ai1.leek> <ai2.leek>")
        sys.exit(1)

    ai1_path = Path(sys.argv[1])
    ai2_path = Path(sys.argv[2])

    if not ai1_path.exists() or not ai2_path.exists():
        print(f"Error: AI file not found")
        sys.exit(1)

    # Copy AIs (and includes) to generator
    ai1_name, ai1_files = copy_ai_to_generator(ai1_path, ai1_path.name)
    ai2_name, ai2_files = copy_ai_to_generator(ai2_path, ai2_path.name)
    all_copied_files = ai1_files + ai2_files

    print(f"AI 1: {ai1_path.name}")
    print(f"AI 2: {ai2_path.name}")
    print()

    # Create entities
    entity1 = EntityConfig(
        id=0,
        name=ai1_path.stem,
        level=1,
        ai=ai1_name,
        farmer=1,
        team=1,
        weapons=[37],  # Pistol
        chips=DEFAULT_CHIPS,
    )
    entity2 = EntityConfig(
        id=1,
        name=ai2_path.stem,
        level=1,
        ai=ai2_name,
        farmer=2,
        team=2,
        weapons=[37],
        chips=DEFAULT_CHIPS,
    )

    scenario = ScenarioConfig(
        team1=[entity1],
        team2=[entity2],
    )

    sim = Simulator()
    outcome = sim.run_scenario(scenario)

    # Debug: Show raw output structure
    print("RAW OUTPUT KEYS:", list(outcome.raw_output.keys()))
    if "logs" in outcome.raw_output:
        logs = outcome.raw_output["logs"]
        print(f"LOGS: {type(logs)} = {logs}")
    if "fight" in outcome.raw_output:
        fight = outcome.raw_output["fight"]
        print("FIGHT KEYS:", list(fight.keys()))
        if "actions" in fight:
            actions = fight["actions"]
            print(f"FIGHT ACTIONS: {len(actions)} entries")
            if actions:
                print(f"  First action: {actions[0][:5] if len(actions[0]) > 5 else actions[0]}")
        if "dead" in fight:
            print(f"DEAD STATUS: {fight['dead']}")
    print()

    # Get leek data from raw output
    fight_data = outcome.raw_output.get("fight", {})
    leeks_list = fight_data.get("leeks", [])
    leeks = {str(l["id"]): l for l in leeks_list}

    # Parse and display actions
    parsed = parse_actions(outcome.actions, leeks)

    print("="*60)
    print("FIGHT RESULT")
    print("="*60)
    winner_str = "Team 1" if outcome.winner == 1 else "Team 2" if outcome.winner == 2 else "Draw"
    print(f"Winner: {winner_str}")
    print(f"Turns: {outcome.turns}")
    print(f"Duration: {outcome.duration_ms:.1f}ms")
    print()

    # Show stats
    stats = compute_stats(parsed, leeks)
    print("STATISTICS:")
    print("-"*60)
    for leek_id, s in sorted(stats.items(), key=lambda x: x[1]["team"]):
        print(f"{s['name']} (Team {s['team']}):")
        print(f"  Damage dealt:    {s['damage_dealt']}")
        print(f"  Damage received: {s['damage_received']}")
        print(f"  Shots fired:     {s['shots_fired']}")
        print(f"  Cells moved:     {s['cells_moved']}")
        print(f"  Turns played:    {s['turns_played']}")
        print()

    # Show action log
    print("\nACTION LOG:")
    print("-"*60)
    action_log = format_action_log(parsed)
    print(action_log)

    # Also save full raw output for deeper analysis
    debug_file = Path("data/debug_fight.json")
    debug_file.parent.mkdir(parents=True, exist_ok=True)
    debug_file.write_text(json.dumps({
        "winner": outcome.winner,
        "turns": outcome.turns,
        "actions": outcome.actions,
        "leeks": leeks,
        "stats": stats,
    }, indent=2))
    print(f"\nFull data saved to: {debug_file}")

    # Cleanup all copied files (including includes)
    for f in all_copied_files:
        (GENERATOR_PATH / f).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
