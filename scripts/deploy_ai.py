#!/usr/bin/env python3
"""Deploy AI to LeekWars and optionally test it."""

import sys
import os
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent import LeekWarsAPI

USERNAME = "leek@nech.pl"
PASSWORD = "REDACTED_PASSWORD"
AI_ID = 453627  # Our main AI
LEEK_ID = 131321  # IAdonis


def load_ai_file(path: str) -> str:
    """Load AI code from file."""
    with open(path, "r") as f:
        return f.read()


def deploy(api: LeekWarsAPI, code: str, name: str = None):
    """Deploy AI code."""
    print(f"Deploying AI ({len(code)} chars)...")

    # Save code
    result = api.save_ai(AI_ID, code)
    print(f"  Save result: {result}")

    # Rename if specified (may fail due to API quirks)
    if name:
        try:
            api.rename_ai(AI_ID, name)
            print(f"  Renamed to: {name}")
        except Exception as e:
            print(f"  Rename failed (non-fatal): {e}")

    # Verify
    ai = api.get_ai(AI_ID)["ai"]
    print(f"  Verified: {ai['name']}, valid={ai['valid']}, {len(ai['code'])} chars")

    return ai["valid"]


def test_fight(api: LeekWarsAPI, num_fights: int = 1):
    """Run test fights with the deployed AI."""
    print(f"\nRunning {num_fights} test fight(s)...")

    # Get opponents
    opps = api.get_leek_opponents(LEEK_ID).get("opponents", [])
    if not opps:
        print("  No opponents available!")
        return []

    results = []
    for i in range(min(num_fights, len(opps))):
        target = opps[i]
        print(f"\n  [{i+1}] vs {target['name']} L{target['level']}...")

        result = api.start_solo_fight(LEEK_ID, target["id"])

        if isinstance(result, dict) and "fight" in result:
            fight_id = result["fight"]
            print(f"      Fight ID: {fight_id}")

            time.sleep(2)

            fight = api.get_fight(fight_id)
            winner = fight.get("winner", 0)
            outcome = "WIN" if winner == 1 else "LOSS" if winner == 2 else "DRAW"
            print(f"      Result: {outcome}")

            results.append({
                "fight_id": fight_id,
                "opponent": target["name"],
                "outcome": outcome,
            })
        else:
            print(f"      ERROR: {result}")
            break

        time.sleep(1)

    # Summary
    wins = sum(1 for r in results if r["outcome"] == "WIN")
    losses = sum(1 for r in results if r["outcome"] == "LOSS")
    print(f"\n  Record: {wins}W - {losses}L")

    return results


def main():
    parser = argparse.ArgumentParser(description="Deploy AI to LeekWars")
    parser.add_argument("ai_file", nargs="?", default="ais/fighter_v1.leek",
                       help="Path to AI file")
    parser.add_argument("-n", "--name", help="AI name")
    parser.add_argument("-t", "--test", type=int, default=0,
                       help="Number of test fights to run")
    parser.add_argument("--show", action="store_true",
                       help="Show current AI code")
    args = parser.parse_args()

    api = LeekWarsAPI()
    try:
        # Login
        print("Logging in...")
        api.login(USERNAME, PASSWORD)
        print(f"  Logged in as {api.farmer['name']}")

        if args.show:
            # Just show current AI
            ai = api.get_ai(AI_ID)["ai"]
            print(f"\n=== {ai['name']} (ID: {ai['id']}) ===")
            print(ai["code"])
            return

        # Load and deploy
        if os.path.exists(args.ai_file):
            code = load_ai_file(args.ai_file)
            name = args.name or os.path.basename(args.ai_file).replace(".leek", "")
        else:
            print(f"File not found: {args.ai_file}")
            return

        valid = deploy(api, code, name)

        if not valid:
            print("\nWARNING: AI has errors! Check the code.")
            return

        # Test if requested
        if args.test > 0:
            test_fight(api, args.test)

    finally:
        api.close()


if __name__ == "__main__":
    main()
