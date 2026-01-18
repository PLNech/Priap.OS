#!/usr/bin/env python3
"""Probe the test fight API to understand online fight mechanics.

This script explores the test-scenario API to understand:
1. How test leeks work (custom stats)
2. How test scenarios work (maps, positions)
3. What data is returned from test fights
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api


def probe_test_fights():
    """Explore the test fight API."""
    print("Logging in...")
    api = login_api()
    print(f"Logged in as farmer {api.farmer_id}")

    # Get all test scenarios
    print("\n=== Getting test scenarios ===")
    response = api._client.get("/test-scenario/get-all", headers=api._headers())
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

    # Get farmer AIs to find an AI to test with
    print("\n=== Getting farmer AIs ===")
    ais = api.get_farmer_ais()
    if "ais" in ais:
        for ai in ais["ais"][:5]:  # First 5 AIs
            print(f"  AI {ai['id']}: {ai['name']}")

    api.close()


if __name__ == "__main__":
    probe_test_fights()
