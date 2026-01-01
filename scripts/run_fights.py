#!/usr/bin/env python3
"""Run multiple fights and analyze results."""

import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import httpx
from leekwars_agent.fight_parser import parse_fight, summarize_fight, ActionType

USERNAME = "leek@nech.pl"
PASSWORD = "REDACTED_PASSWORD"
BASE = "https://leekwars.com/api"


def main():
    client = httpx.Client(timeout=30.0)

    # Login
    print("=== LOGIN ===")
    r = client.post(
        f"{BASE}/farmer/login",
        data={"login": USERNAME, "password": PASSWORD, "keep_connected": "true"},
    )
    data = r.json()
    farmer = data["farmer"]
    token = None
    for cookie in r.cookies.jar:
        if cookie.name == "token":
            token = cookie.value
            break

    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in as: {farmer['name']}")
    print(f"Fights available: {farmer.get('fights', 'N/A')}")
    print(f"Habs: {farmer.get('habs', 'N/A')}")

    # Get leek
    leeks = farmer["leeks"]
    leek_id = list(leeks.keys())[0]
    leek = leeks[leek_id]
    print(f"\nLeek: {leek['name']} L{leek['level']}")

    # Get opponents
    print("\n=== OPPONENTS ===")
    r = client.get(f"{BASE}/garden/get-leek-opponents/{leek_id}", headers=headers)
    opps = r.json().get("opponents", [])
    print(f"Found {len(opps)} opponents")

    # Run fights
    num_fights = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print(f"\n=== RUNNING {num_fights} FIGHTS ===")

    results = []
    for i in range(min(num_fights, len(opps))):
        target = opps[i]
        print(f"\n[{i+1}/{num_fights}] Fighting {target['name']} L{target['level']}...")

        r = client.post(
            f"{BASE}/garden/start-solo-fight",
            headers=headers,
            data={"leek_id": leek_id, "target_id": target["id"]},
        )
        result = r.json()

        if isinstance(result, dict) and "fight" in result:
            fight_id = result["fight"]
            print(f"  Fight ID: {fight_id}")

            # Wait for fight to complete
            time.sleep(2)

            # Get fight result
            r = client.get(f"{BASE}/fight/get/{fight_id}")
            fight_data = r.json()

            # Parse and summarize
            winner = fight_data.get("winner", 0)
            outcome = "WIN" if winner == 1 else "LOSS" if winner == 2 else "DRAW"
            print(f"  Result: {outcome}")

            # Parse fight
            parsed = parse_fight(fight_data)
            print(f"  Turns: {parsed['summary']['turns']}")
            print(f"  Actions: {parsed['summary']['total_actions']}")

            results.append({
                "fight_id": fight_id,
                "opponent": target["name"],
                "outcome": outcome,
                "turns": parsed["summary"]["turns"],
                "parsed": parsed,
            })
        else:
            print(f"  ERROR: {result}")
            if isinstance(result, dict) and result.get("error") == "not_enough_fights":
                print("  No more fights available today!")
                break

        # Small delay between fights
        time.sleep(1)

    # Summary
    print("\n=== SUMMARY ===")
    wins = sum(1 for r in results if r["outcome"] == "WIN")
    losses = sum(1 for r in results if r["outcome"] == "LOSS")
    print(f"Record: {wins}W - {losses}L")

    # Refresh farmer data
    r = client.get(f"{BASE}/garden/get", headers=headers)
    # Get updated farmer
    r = client.post(
        f"{BASE}/farmer/login",
        data={"login": USERNAME, "password": PASSWORD, "keep_connected": "true"},
    )
    farmer = r.json().get("farmer", {})
    print(f"Updated stats:")
    print(f"  Fights remaining: {farmer.get('fights', 'N/A')}")
    print(f"  Habs: {farmer.get('habs', 'N/A')}")

    leek = farmer.get("leeks", {}).get(leek_id, {})
    print(f"  Leek {leek.get('name')}: L{leek.get('level')}")

    # Save detailed results
    os.makedirs("data", exist_ok=True)
    with open("data/fight_results.json", "w") as f:
        # Convert to serializable format
        for r in results:
            r["parsed"]["summary"]["damage_dealt"] = dict(r["parsed"]["summary"]["damage_dealt"])
            r["parsed"]["summary"]["healing_done"] = dict(r["parsed"]["summary"]["healing_done"])
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to data/fight_results.json")

    client.close()


if __name__ == "__main__":
    main()
