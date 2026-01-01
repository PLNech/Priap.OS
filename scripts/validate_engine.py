"""Validate local fight engine against real site data."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.py4j_simulator import Py4JSimulator
from leekwars_agent.simulator import Simulator, EntityConfig, ScenarioConfig
from leekwars_agent.api import LeekWarsAPI


def run_configurable_fight():
    """Run a fight with full control over entity configuration."""
    print("=" * 60)
    print("CONFIGURABLE FIGHT TEST")
    print("=" * 60)

    sim = Simulator()

    # Create custom entities with full stat control
    tank = EntityConfig(
        id=1,
        name="TankLeek",
        ai="fighter_v1.leek",
        level=100,
        life=500,          # High HP
        tp=15,             # High TP
        mp=5,              # Good mobility
        strength=200,      # Physical damage
        agility=50,
        wisdom=100,
        resistance=150,    # Damage reduction
        science=0,
        magic=0,
        frequency=50,
        cores=4,
        ram=400,
        farmer=1,
        team=1,
        cell=100,
        weapons=[1, 37],   # Pistol + B-Laser
        chips=[6, 20],     # Shield + Cure
    )

    glasscanon = EntityConfig(
        id=2,
        name="GlassCanon",
        ai="fighter_v1.leek",
        level=100,
        life=200,          # Low HP
        tp=20,             # Max TP for attacks
        mp=3,
        strength=400,      # Max damage
        agility=100,
        wisdom=0,
        resistance=0,      # No defense
        science=0,
        magic=0,
        frequency=100,
        cores=4,
        ram=400,
        farmer=2,
        team=2,
        cell=450,
        weapons=[47],      # Magnum (high damage)
        chips=[],
    )

    scenario = ScenarioConfig(
        team1=[tank],
        team2=[glasscanon],
        seed=42,
        max_turns=64,
    )

    print("\nFight: Tank vs Glass Canon")
    print(f"Tank: HP={tank.life}, STR={tank.strength}, RES={tank.resistance}")
    print(f"Glass: HP={glasscanon.life}, STR={glasscanon.strength}, RES={glasscanon.resistance}")

    outcome = sim.run_scenario(scenario)

    print(f"\nResult: {'Tank wins!' if outcome.team1_won else 'Glass Canon wins!' if outcome.team2_won else 'Draw'}")
    print(f"Turns: {outcome.turns}")

    return outcome


def run_local_fight():
    """Run a local fight and examine the output."""
    print("\n" + "=" * 60)
    print("BASIC LOCAL FIGHT TEST")
    print("=" * 60)

    sim = Py4JSimulator()

    # Run fight with fixed seed for reproducibility
    outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", level=1, seed=42)

    print(f"\nOutcome summary:")
    print(f"  Winner: {outcome.winner}")
    print(f"  Turns: {outcome.turns}")
    print(f"  Duration: {outcome.duration_ms:.1f}ms")
    print(f"  Actions count: {len(outcome.actions)}")

    # Examine raw output structure
    raw = outcome.raw_output
    print(f"\nRaw output keys: {list(raw.keys())}")

    # Look at fight structure if present
    if "fight" in raw:
        fight = raw["fight"]
        print(f"\nFight keys: {list(fight.keys())}")

        if "data" in fight:
            data = fight["data"]
            print(f"Fight data keys: {list(data.keys())}")

            # Map info
            if "map" in data:
                map_data = data["map"]
                print(f"\nMap: {map_data.get('width')}x{map_data.get('height')}")
                if "obstacles" in map_data:
                    print(f"Obstacles: {len(map_data['obstacles'])} cells")

            # Leeks
            if "leeks" in data:
                print(f"\nLeeks ({len(data['leeks'])}):")
                for lid, leek in data["leeks"].items():
                    print(f"  [{lid}] {leek.get('name')}: HP={leek.get('life')}, TP={leek.get('tp')}, MP={leek.get('mp')}")
                    print(f"        Cell={leek.get('cell')}, Team={leek.get('team')}")

        # Actions per turn
        if "actions" in fight:
            actions = fight["actions"]
            print(f"\nActions by turn ({len(actions)} turns):")
            for turn_idx, turn_actions in enumerate(actions[:5]):  # First 5 turns
                print(f"  Turn {turn_idx}: {len(turn_actions)} actions")
                for action in turn_actions[:3]:  # First 3 actions per turn
                    print(f"    {action}")
                if len(turn_actions) > 3:
                    print(f"    ... ({len(turn_actions) - 3} more)")
            if len(actions) > 5:
                print(f"  ... ({len(actions) - 5} more turns)")

    sim.close()
    return raw


def fetch_real_fight(fight_id: int = None):
    """Fetch a real fight from the API for comparison."""
    print("\n" + "=" * 60)
    print("REAL FIGHT FROM API")
    print("=" * 60)

    api = LeekWarsAPI()
    api.login()

    # Get recent fight if no ID provided
    if fight_id is None:
        # Get farmer's fights
        farmer_id = 111397  # PriapOS farmer ID
        resp = api.session.get(f"{api.BASE_URL}/history/farmer/{farmer_id}/5")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("fights"):
                fight_id = data["fights"][0]["id"]
                print(f"Using most recent fight: {fight_id}")

    if not fight_id:
        print("No fight ID available")
        return None

    # Fetch fight details
    resp = api.session.get(f"{api.BASE_URL}/fight/get/{fight_id}")
    if resp.status_code != 200:
        print(f"Failed to fetch fight: {resp.status_code}")
        return None

    fight_data = resp.json()
    print(f"\nReal fight keys: {list(fight_data.keys())}")

    if "fight" in fight_data:
        fight = fight_data["fight"]
        print(f"Fight structure keys: {list(fight.keys())}")

        # Basic info
        print(f"\nFight ID: {fight.get('id')}")
        print(f"Type: {fight.get('type')}")
        print(f"Winner: {fight.get('winner')}")

        if "data" in fight:
            data = fight["data"]
            print(f"\nFight data keys: {list(data.keys())}")

            # Map
            if "map" in data:
                map_data = data["map"]
                print(f"Map: {map_data.get('width')}x{map_data.get('height')}")

            # Leeks
            if "leeks" in data:
                print(f"\nLeeks ({len(data['leeks'])}):")
                for lid, leek in data["leeks"].items():
                    print(f"  [{lid}] {leek.get('name')}: level={leek.get('level')}")

        # Actions
        if "actions" in fight:
            actions = fight["actions"]
            print(f"\nActions: {len(actions)} turns")
            if actions:
                print(f"First turn sample: {actions[0][:3] if len(actions[0]) > 0 else 'empty'}")

    return fight_data


def compare_structures(local_raw, real_data):
    """Compare local and real fight data structures."""
    print("\n" + "=" * 60)
    print("STRUCTURE COMPARISON")
    print("=" * 60)

    if not local_raw or not real_data:
        print("Missing data for comparison")
        return

    local_fight = local_raw.get("fight", {})
    real_fight = real_data.get("fight", {})

    local_keys = set(local_fight.keys())
    real_keys = set(real_fight.keys())

    print(f"\nLocal-only keys: {local_keys - real_keys}")
    print(f"Real-only keys: {real_keys - local_keys}")
    print(f"Common keys: {local_keys & real_keys}")

    # Compare data substructure
    local_data = local_fight.get("data", {})
    real_data_inner = real_fight.get("data", {})

    local_data_keys = set(local_data.keys())
    real_data_keys = set(real_data_inner.keys())

    print(f"\nData - Local-only: {local_data_keys - real_data_keys}")
    print(f"Data - Real-only: {real_data_keys - local_data_keys}")
    print(f"Data - Common: {local_data_keys & real_data_keys}")

    # Compare action format
    print("\nAction format comparison:")
    local_actions = local_fight.get("actions", [[]])
    real_actions = real_fight.get("actions", [[]])

    if local_actions and local_actions[0]:
        print(f"Local action sample: {local_actions[0][0]}")
    if real_actions and real_actions[0]:
        print(f"Real action sample: {real_actions[0][0]}")


def save_fight_data(local_raw, real_data):
    """Save fight data for inspection."""
    output_dir = Path(__file__).parent.parent / "data" / "fights"
    output_dir.mkdir(parents=True, exist_ok=True)

    if local_raw:
        with open(output_dir / "local_fight_sample.json", "w") as f:
            json.dump(local_raw, f, indent=2)
        print(f"\nSaved local fight to {output_dir / 'local_fight_sample.json'}")

    if real_data:
        with open(output_dir / "real_fight_sample.json", "w") as f:
            json.dump(real_data, f, indent=2)
        print(f"Saved real fight to {output_dir / 'real_fight_sample.json'}")


if __name__ == "__main__":
    # First: demonstrate configurable fights with custom stats
    run_configurable_fight()

    # Run basic local fight
    local_raw = run_local_fight()

    # Fetch real fight
    real_data = fetch_real_fight()

    # Compare
    compare_structures(local_raw, real_data)

    # Save for inspection
    save_fight_data(local_raw, real_data)
