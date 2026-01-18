#!/usr/bin/env python3
"""Investigate online fight mechanics via test fights.

Goal: Understand why online has 58% first-mover advantage while simulator has 0%.

Strategy:
1. Create mirror match test scenarios (identical leeks, same AI)
2. Run multiple test fights
3. Analyze starting positions, turn order, and outcomes
4. Compare with simulator behavior
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.api import LeekWarsAPI
from leekwars_agent.auth import login_api


class TestFightInvestigator:
    def __init__(self):
        self.api = login_api()
        print(f"Logged in as farmer {self.api.farmer_id}")

    def get_test_data(self) -> dict:
        """Get all test scenarios, leeks, and maps."""
        response = self.api._client.get(
            "/test-scenario/get-all",
            headers=self.api._headers()
        )
        response.raise_for_status()
        return response.json()

    def create_test_leek(self, name: str, level: int = 10, **stats) -> dict:
        """Create a test leek with custom stats."""
        # First create with just name
        response = self.api._client.post(
            "/test-leek/new",
            headers=self.api._headers(),
            data={"name": name}
        )
        response.raise_for_status()
        result = response.json()
        leek_id = result.get("id")

        time.sleep(0.5)  # Rate limit protection

        # Then update with stats
        defaults = {
            "level": level,
            "life": 127,
            "strength": 100,
            "wisdom": 0,
            "agility": 0,
            "resistance": 0,
            "frequency": 100,
            "science": 0,
            "magic": 0,
            "tp": 10,
            "mp": 3,
            "cores": 1,
            "ram": 100,
        }
        defaults.update(stats)

        update_resp = self.api._client.post(
            "/test-leek/update",
            headers=self.api._headers(),
            data={
                "id": leek_id,
                **defaults,
                "weapons": json.dumps([37]),
                "chips": json.dumps([]),
            }
        )
        update_resp.raise_for_status()
        return {"id": leek_id, "updated": update_resp.json()}

    def update_test_leek(self, leek_id: int, **stats) -> dict:
        """Update a test leek's stats."""
        response = self.api._client.post(
            "/test-leek/update",
            headers=self.api._headers(),
            data={"id": leek_id, **stats}
        )
        response.raise_for_status()
        return response.json()

    def delete_test_leek(self, leek_id: int) -> dict:
        """Delete a test leek."""
        response = self.api._client.delete(
            f"/test-leek/delete/{leek_id}",
            headers=self.api._headers()
        )
        response.raise_for_status()
        return response.json()

    def create_scenario(self, name: str) -> dict:
        """Create a new test scenario."""
        response = self.api._client.post(
            "/test-scenario/new",
            headers=self.api._headers(),
            data={"name": name}
        )
        response.raise_for_status()
        return response.json()

    def add_leek_to_scenario(self, scenario_id: int, leek_id: int, team: int, ai_id: int | None = None) -> dict:
        """Add a leek to a scenario team.

        Note: team is 0-based (0=team1, 1=team2)
        """
        headers = self.api._headers()
        headers["Content-Type"] = "application/json"
        response = self.api._client.post(
            "/test-scenario/add-leek",
            headers=headers,
            json={
                "scenario_id": scenario_id,
                "leek": leek_id,  # Not leek_id!
                "team": team,     # 0=team1, 1=team2
                "ai": ai_id,
            }
        )
        response.raise_for_status()
        return response.json()

    def delete_scenario(self, scenario_id: int) -> dict:
        """Delete a test scenario."""
        response = self.api._client.delete(
            f"/test-scenario/delete/{scenario_id}",
            headers=self.api._headers()
        )
        response.raise_for_status()
        return response.json()

    def run_test_fight(self, scenario_id: int, ai_id: int) -> dict:
        """Run a test fight and return the fight ID."""
        headers = self.api._headers()
        headers["Content-Type"] = "application/json"
        response = self.api._client.post(
            "/ai/test-scenario",
            headers=headers,
            json={
                "scenario_id": scenario_id,
                "ai_id": ai_id,
            }
        )
        response.raise_for_status()
        return response.json()

    def get_farmer_ais(self) -> list:
        """Get farmer's AIs."""
        return self.api.get_farmer_ais().get("ais", [])

    def analyze_fight(self, fight_id: int) -> dict:
        """Analyze a fight's starting conditions and outcome."""
        fight = self.api.get_fight(fight_id)

        # Extract key data
        data = fight.get("data", {})
        leeks = data.get("leeks", [])

        analysis = {
            "fight_id": fight_id,
            "winner": fight.get("winner"),
            "seed": fight.get("seed"),
            "starter": fight.get("starter"),  # Who attacked (farmer ID)
            "leeks": [],
        }

        for leek in leeks:
            analysis["leeks"].append({
                "id": leek.get("id"),
                "name": leek.get("name"),
                "team": leek.get("team"),
                "cellPos": leek.get("cellPos"),
                "frequency": leek.get("frequency"),
                "strength": leek.get("strength"),
            })

        # Determine who went first from actions
        actions = data.get("actions", [])
        first_turn_entity = None
        for action in actions:
            if action[0] == 7:  # LEEK_TURN
                first_turn_entity = action[1]
                break

        analysis["first_turn_entity"] = first_turn_entity

        return analysis

    def close(self):
        self.api.close()


def main():
    inv = TestFightInvestigator()

    try:
        # Get current test data
        print("\n=== Current Test Data ===")
        data = inv.get_test_data()
        print(f"Scenarios: {len(data.get('scenarios', {}))}")
        print(f"Test Leeks: {len(data.get('leeks', []))}")
        print(f"Maps: {len(data.get('maps', {}))}")

        # Get AIs
        ais = inv.get_farmer_ais()
        if not ais:
            print("ERROR: No AIs found. Create an AI first.")
            return

        ai_id = ais[0]["id"]
        print(f"\nUsing AI: {ais[0]['name']} (ID: {ai_id})")

        # Check if we have test leeks
        test_leeks = data.get("leeks", [])
        print(f"\nTest leeks available: {[l['name'] for l in test_leeks]}")

        # We need at least 2 test leeks
        if len(test_leeks) < 2:
            print("\n=== Creating Test Leeks ===")
            needed = 2 - len(test_leeks)
            for i in range(needed):
                time.sleep(1)  # Rate limit
                leek = inv.create_test_leek(
                    f"TestLeek{len(test_leeks) + i + 1}",
                    level=10,
                    strength=100,
                    frequency=100,
                )
                print(f"Created test leek: {leek}")

            # Refresh test data
            time.sleep(1)
            data = inv.get_test_data()
            test_leeks = data.get("leeks", [])
            print(f"Updated test leeks: {[l['name'] for l in test_leeks]}")

        # Check for existing scenarios
        scenarios = data.get("scenarios", {})
        scenario_id = None

        if not scenarios:
            print("\n=== Creating Test Scenario ===")
            time.sleep(1)
            scenario = inv.create_scenario("MirrorMatch")
            print(f"Created scenario: {scenario}")
            scenario_id = scenario.get("id")
        else:
            # Use existing scenario
            scenario_id = int(list(scenarios.keys())[0])
            scenario = scenarios[str(scenario_id)]
            print(f"\nUsing existing scenario: {scenario_id}")

        # Check if scenario needs leeks
        if scenario_id and len(test_leeks) >= 2:
            scenario_info = scenarios.get(str(scenario_id), {})
            team1 = scenario_info.get("team1", [])
            team2 = scenario_info.get("team2", [])

            if not team1 or not team2:
                print("\n=== Adding leeks to scenario ===")
                if not team1:
                    time.sleep(1)
                    # team=0 for team1, pass AI ID
                    inv.add_leek_to_scenario(scenario_id, test_leeks[0]["id"], 0, ai_id)
                    print(f"Added {test_leeks[0]['name']} to team 1")
                if not team2:
                    time.sleep(1)
                    # team=1 for team2, pass AI ID
                    inv.add_leek_to_scenario(scenario_id, test_leeks[1]["id"], 1, ai_id)
                    print(f"Added {test_leeks[1]['name']} to team 2")

                # Refresh
                time.sleep(1)
                data = inv.get_test_data()
                scenarios = data.get("scenarios", {})

        print(f"\nScenarios: {json.dumps(scenarios, indent=2)}")

        # Run test fights if we have a scenario
        if scenarios:
            scenario_id = list(scenarios.keys())[0]
            print(f"\n=== Running Test Fights (Scenario {scenario_id}) ===")

            results = []
            n_fights = 20
            for i in range(n_fights):
                print(f"Fight {i+1}/{n_fights}...", end=" ", flush=True)
                time.sleep(1)  # Rate limit
                result = inv.run_test_fight(int(scenario_id), ai_id)
                fight_id = result.get("fight")
                print(f"ID: {fight_id}")

                # Wait for fight to complete
                time.sleep(3)

                # Analyze
                analysis = inv.analyze_fight(fight_id)
                results.append(analysis)

                print(f"  Winner: Team {analysis['winner']}, First turn: Entity {analysis['first_turn_entity']}")
                for leek in analysis['leeks']:
                    print(f"    {leek['name']} (Team {leek['team']}): cell={leek['cellPos']}")

            # Summary
            print("\n=== Summary ===")
            team1_wins = sum(1 for r in results if r["winner"] == 1)
            team2_wins = sum(1 for r in results if r["winner"] == 2)
            draws = sum(1 for r in results if r["winner"] == 0)
            print(f"Team 1 wins: {team1_wins}/{len(results)}")
            print(f"Team 2 wins: {team2_wins}/{len(results)}")
            print(f"Draws: {draws}/{len(results)}")

            # Analyze first-mover advantage (excluding draws)
            first_mover_wins = 0
            decisive_fights = [r for r in results if r["winner"] in (1, 2)]
            for r in decisive_fights:
                first_entity = r["first_turn_entity"]
                winner = r["winner"]
                # Find which team the first mover is on
                for leek in r["leeks"]:
                    if leek["id"] == first_entity:
                        first_mover_team = leek["team"]
                        if first_mover_team == winner:
                            first_mover_wins += 1
                        break

            print(f"First mover wins: {first_mover_wins}/{len(decisive_fights)} decisive fights")

            # Analyze by who went first
            t1_first_wins = 0
            t1_first_total = 0
            t2_first_wins = 0
            t2_first_total = 0

            for r in decisive_fights:
                first_entity = r["first_turn_entity"]
                winner = r["winner"]
                for leek in r["leeks"]:
                    if leek["id"] == first_entity:
                        if leek["team"] == 1:
                            t1_first_total += 1
                            if winner == 1:
                                t1_first_wins += 1
                        else:
                            t2_first_total += 1
                            if winner == 2:
                                t2_first_wins += 1
                        break

            print(f"\nWhen Team 1 goes first: T1 wins {t1_first_wins}/{t1_first_total}")
            print(f"When Team 2 goes first: T2 wins {t2_first_wins}/{t2_first_total}")

            # Save results for offline analysis
            with open("data/test_fight_results.json", "w") as f:
                json.dump(results, f, indent=2)
            print("\nResults saved to data/test_fight_results.json")

    finally:
        inv.close()


if __name__ == "__main__":
    main()
