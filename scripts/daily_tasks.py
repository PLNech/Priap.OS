#!/usr/bin/env python3
"""Daily tasks script - run opportunistically.

Tasks:
- Buy 50-fight pack from market (once per day when affordable)
- Could add: collect daily rewards, run garden fights, etc.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api

# State file to track what we've done today
STATE_FILE = Path(__file__).parent.parent / "data" / "daily_state.json"


def load_state() -> dict:
    """Load daily state from file."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    """Save daily state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def should_run_today(task_name: str, state: dict) -> bool:
    """Check if task should run today."""
    today = date.today().isoformat()
    last_run = state.get(task_name, {}).get("last_date")
    return last_run != today


def mark_done(task_name: str, state: dict, result: str = "success"):
    """Mark task as done for today."""
    today = date.today().isoformat()
    state[task_name] = {
        "last_date": today,
        "result": result,
        "timestamp": datetime.now().isoformat(),
    }
    save_state(state)


def buy_fights(api: LeekWarsAPI, state: dict) -> bool:
    """Buy 50-fight pack if not done today and affordable."""
    task = "buy_fights"

    if not should_run_today(task, state):
        print(f"[{task}] Already done today, skipping")
        return False

    try:
        result = api.buy_fights(quantity=1)
        print(f"[{task}] Success: {result}")
        mark_done(task, state, "success")
        return True
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "not enough" in error_msg.lower():
            print(f"[{task}] Not enough habs, will retry later")
            # Don't mark as done - retry later
            return False
        elif "400" in error_msg:
            print(f"[{task}] Already have max fights or other limit")
            mark_done(task, state, "limit_reached")
            return False
        else:
            print(f"[{task}] Error: {e}")
            return False


def run_garden_fights(api: LeekWarsAPI, state: dict, max_fights: int = 10) -> int:
    """Run garden fights until done or max reached."""
    task = "garden_fights"
    fights_done = 0

    try:
        garden = api.get_garden()
        fights_left = garden.get("garden", {}).get("fights", 0)
        print(f"[{task}] Fights available: {fights_left}")

        if fights_left == 0:
            print(f"[{task}] No fights available")
            return 0

        # Get our leek
        farmer = api.get_farmer(api.farmer_id)
        leeks = farmer.get("farmer", {}).get("leeks", {})
        if not leeks:
            print(f"[{task}] No leeks found")
            return 0

        leek_id = list(leeks.keys())[0]
        print(f"[{task}] Using leek {leek_id}")

        # Get opponents
        opponents = api.get_leek_opponents(int(leek_id))
        opponent_list = opponents.get("opponents", [])

        if not opponent_list:
            print(f"[{task}] No opponents found")
            return 0

        # Fight!
        for i, opponent in enumerate(opponent_list[:max_fights]):
            if fights_done >= max_fights:
                break
            if fights_left <= 0:
                break

            target_id = opponent.get("id")
            print(f"[{task}] Fighting opponent {target_id}...")

            try:
                result = api.start_solo_fight(int(leek_id), target_id)
                fight_id = result.get("fight", {}).get("id")
                print(f"[{task}] Fight {fight_id} started")
                fights_done += 1
                fights_left -= 1
            except Exception as e:
                print(f"[{task}] Fight failed: {e}")
                break

        print(f"[{task}] Completed {fights_done} fights")
        return fights_done

    except Exception as e:
        print(f"[{task}] Error: {e}")
        return fights_done


def main():
    """Run all daily tasks."""
    print(f"=== Daily Tasks - {datetime.now().isoformat()} ===\n")

    state = load_state()

    api = login_api()
    try:
        print("Logging in...")
        print(f"Logged in as farmer {api.farmer_id}\n")

        # Task 1: Buy fights
        buy_fights(api, state)

        # Task 2: Run garden fights (optional, comment out if not wanted)
        # run_garden_fights(api, state, max_fights=5)

        print("\n=== Done ===")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    finally:
        api.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
