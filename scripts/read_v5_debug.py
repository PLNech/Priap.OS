#!/usr/bin/env python3
"""Read fighter_v5 debug registry data after online fights.

Usage:
    poetry run python scripts/read_v5_debug.py         # Read all v5 registers
    poetry run python scripts/read_v5_debug.py --clear # Clear after reading
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api

# Constants
LEEK_ID = 131321  # IAdonis


def parse_v5_state(value: str) -> dict:
    """Parse v5 registry format.

    v5.0: turn|myHP|enemyHP|myTTK|enemyTTK|kite|dist (7 fields)
    v5.1: turn|myHP|enemyHP|dmgDealt|dmgTaken|shots|startDist|endDist|kite (9 fields)
    v5.2: turn|myHP|enemyHP|dmgDealt|dmgTaken|shots|startDist|endDist|kite|shotResult (10 fields)
    """
    parts = value.split("|")

    if len(parts) == 10:
        # v5.2 format with shot result tracking
        shot_result = int(parts[9])
        result_names = {
            -1: "NO_ATTEMPT",
            0: "SUCCESS",
            1: "FAILED",
            2: "INVALID_POS",
            3: "NO_TP",
            4: "OUT_RANGE",
            5: "NO_LOS",  # Line of sight
            6: "DEAD",
        }
        return {
            "turn": int(parts[0]),
            "my_hp": int(parts[1]),
            "enemy_hp": int(parts[2]),
            "dmg_dealt": int(parts[3]),
            "dmg_taken": int(parts[4]),
            "shots": int(parts[5]),
            "start_dist": int(parts[6]),
            "end_dist": int(parts[7]),
            "kiting": parts[8] == "true",
            "shot_result": shot_result,
            "shot_result_name": result_names.get(shot_result, f"UNKNOWN_{shot_result}"),
            "version": "5.2",
        }
    elif len(parts) == 9:
        # v5.1 format with per-turn metrics
        return {
            "turn": int(parts[0]),
            "my_hp": int(parts[1]),
            "enemy_hp": int(parts[2]),
            "dmg_dealt": int(parts[3]),
            "dmg_taken": int(parts[4]),
            "shots": int(parts[5]),
            "start_dist": int(parts[6]),
            "end_dist": int(parts[7]),
            "kiting": parts[8] == "true",
            "version": "5.1",
        }
    elif len(parts) == 7:
        # v5.0 format (legacy)
        return {
            "turn": int(parts[0]),
            "my_hp": int(parts[1]),
            "enemy_hp": int(parts[2]),
            "my_ttk": int(parts[3]) if parts[3] != "999" else "∞",
            "enemy_ttk": int(parts[4]) if parts[4] != "999" else "∞",
            "kiting": parts[5] == "true",
            "distance": int(parts[6]),
            "version": "5.0",
        }
    else:
        return {"raw": value}


def main():
    parser = argparse.ArgumentParser(description="Read v5 debug registry")
    parser.add_argument("--clear", action="store_true", help="Clear registers after reading")
    args = parser.parse_args()

    # Login via centralized auth
    api = login_api()
    print(f"✓ Logged in as {api.farmer['name']}\n")

    # Fetch registers
    result = api.get_leek_registers(LEEK_ID)
    # API returns {"registers": [{key, value}, ...]}
    reg_list = result.get("registers", [])

    if not reg_list:
        print("No registers found. Run some online fights with v5 first!")
        return

    # Display v5 registers
    print("=== Fighter v5 Debug Registry ===\n")

    # Convert list to dict for easier access
    reg_dict = {r["key"]: r["value"] for r in reg_list}

    # Sort by key (v5_t1, v5_t2, ... v5_last)
    v5_keys = sorted([k for k in reg_dict.keys() if k.startswith("v5_")])

    for key in v5_keys:
        value = reg_dict[key]
        if key == "v5_last":
            print(f"📌 {key}: (FINAL STATE)")
        else:
            turn_num = key.replace("v5_t", "")
            print(f"Turn {turn_num}:")

        state = parse_v5_state(value)
        if "raw" in state:
            print(f"   Raw: {state['raw']}")
        elif state.get("version") == "5.2":
            # v5.2 format with shot result tracking
            kite_emoji = "🏃" if state["kiting"] else "⚔️"
            dmg_delta = state["dmg_dealt"] - state["dmg_taken"]
            delta_sign = "+" if dmg_delta >= 0 else ""
            result_str = state["shot_result_name"]
            if state["shot_result"] != 0 and state["shot_result"] != -1:
                result_str = f"⚠️{result_str}"  # Highlight failures
            print(f"   HP: {state['my_hp']} vs {state['enemy_hp']} | "
                  f"Dmg: {state['dmg_dealt']}→ {state['dmg_taken']}← ({delta_sign}{dmg_delta}) | "
                  f"Shots: {state['shots']} [{result_str}] | "
                  f"Dist: {state['start_dist']}→{state['end_dist']} | "
                  f"{kite_emoji}")
        elif state.get("version") == "5.1":
            # v5.1 format with per-turn metrics
            kite_emoji = "🏃" if state["kiting"] else "⚔️"
            dmg_delta = state["dmg_dealt"] - state["dmg_taken"]
            delta_sign = "+" if dmg_delta >= 0 else ""
            print(f"   HP: {state['my_hp']} vs {state['enemy_hp']} | "
                  f"Dmg: {state['dmg_dealt']}→ {state['dmg_taken']}← ({delta_sign}{dmg_delta}) | "
                  f"Shots: {state['shots']} | "
                  f"Dist: {state['start_dist']}→{state['end_dist']} | "
                  f"{kite_emoji}")
        else:
            # v5.0 format (legacy)
            kite_emoji = "🏃" if state["kiting"] else "⚔️"
            print(f"   HP: {state['my_hp']} vs {state['enemy_hp']} | "
                  f"TTK: {state['my_ttk']} vs {state['enemy_ttk']} | "
                  f"Dist: {state['distance']} | "
                  f"{kite_emoji} {'KITING' if state['kiting'] else 'AGGRESSIVE'}")
        print()

    # Clear if requested
    if args.clear:
        print("Clearing v5 registers...")
        for key in v5_keys:
            api.delete_leek_register(LEEK_ID, key)
            print(f"  ✓ Deleted {key}")
        print("\n✓ Registers cleared")

    api.close()


if __name__ == "__main__":
    main()
