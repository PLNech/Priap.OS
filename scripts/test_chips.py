#!/usr/bin/env python3
"""Diagnostic script to test chip loading in the simulator.

This verifies that getChips() returns non-empty arrays in offline simulation.

Usage:
    poetry run python scripts/test_chips.py
    poetry run python scripts/test_chips.py --verbose
"""

import sys
import os
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.simulator import Simulator, EntityConfig, ScenarioConfig, GENERATOR_PATH

# Our standard chips (from GROUND_TRUTH.md)
OUR_CHIPS = [4, 5, 6, 8, 14, 15]  # CURE, FLAME, FLASH, PROTEIN, BOOTS, MOTIVATION
CHIP_NAMES = {4: "CURE", 5: "FLAME", 6: "FLASH", 8: "PROTEIN", 14: "BOOTS", 15: "MOTIVATION"}


def create_chip_test_ai() -> Path:
    """Create a test AI that reports its chips via debug()."""
    ai_path = GENERATOR_PATH / "chip_test.leek"
    ai_path.write_text('''// Chip detection test AI
var myChips = getChips();
var chipCount = count(myChips);

debug("=== CHIP TEST ===");
debug("getChips() returned " + chipCount + " chips");

if (chipCount == 0) {
    debug("ERROR: No chips loaded!");
    debug("getChips() = []");
} else {
    debug("SUCCESS: Chips detected!");
    for (var chip in myChips) {
        debug("  - Chip ID: " + chip);
    }
}

// Also test a chip if we have FLAME (ID 5)
if (chipCount > 0) {
    var enemy = getNearestEnemy();
    if (enemy) {
        moveToward(enemy);
        // Try using FLAME if available
        var result = useChip(CHIP_FLAME, enemy);
        debug("useChip(CHIP_FLAME) = " + result);
    }
}
''')
    return ai_path


def run_chip_test(verbose: bool = False) -> dict:
    """Run the chip test and return results."""
    ai_path = create_chip_test_ai()

    try:
        sim = Simulator()

        # Create entity with chips
        entity1 = EntityConfig(
            id=0,
            name="ChipTest",
            ai="chip_test.leek",
            level=34,
            life=300,
            tp=10,
            mp=3,
            strength=234,
            magic=50,  # For chip damage
            team=1,
            farmer=1,
            weapons=[37],  # Pistol
            chips=OUR_CHIPS,
        )

        # Opponent with same chips
        entity2 = EntityConfig(
            id=1,
            name="Opponent",
            ai="chip_test.leek",
            level=34,
            life=300,
            tp=10,
            mp=3,
            strength=234,
            magic=50,
            team=2,
            farmer=2,
            weapons=[37],
            chips=OUR_CHIPS,
        )

        scenario = ScenarioConfig(
            team1=[entity1],
            team2=[entity2],
            seed=42,
        )

        if verbose:
            print("Scenario JSON (chips section):")
            scenario_dict = scenario.to_dict()
            for i, team in enumerate(scenario_dict.get("entities", [])):
                for e in team:
                    print(f"  Entity '{e['name']}': chips={e.get('chips', [])}")
            print()

        # Run the fight
        outcome = sim.run_scenario(scenario)

        # Check for chip-related debug output in logs
        logs = outcome.raw_output.get("logs", {})
        fight = outcome.raw_output.get("fight", {})

        # Parse logs to check if getChips() returned chips
        # Log structure: {entity_id: {turn: [[entity, type, message, ...], ...]}}
        chips_detected = {"ChipTest": False, "Opponent": False}
        chip_counts = {"ChipTest": 0, "Opponent": 0}

        for entity_id_str, entity_logs in logs.items():
            if isinstance(entity_logs, dict):
                for turn, turn_logs in entity_logs.items():
                    if isinstance(turn_logs, list):
                        for log_entry in turn_logs:
                            if len(log_entry) >= 3:
                                entity_id = log_entry[0]
                                message = str(log_entry[2])
                                entity_name = "ChipTest" if entity_id == 0 else "Opponent"

                                if "SUCCESS: Chips detected!" in message:
                                    chips_detected[entity_name] = True
                                if "getChips() returned" in message:
                                    # Extract count from "getChips() returned N chips"
                                    try:
                                        count = int(message.split("returned")[1].split("chips")[0].strip())
                                        chip_counts[entity_name] = count
                                    except (ValueError, IndexError):
                                        pass

        results = {
            "chips_requested": OUR_CHIPS,
            "chips_detected": chips_detected,
            "chip_counts": chip_counts,
            "success": all(chips_detected.values()) and all(c == len(OUR_CHIPS) for c in chip_counts.values()),
        }

        if verbose:
            print("Chips detected from getChips() logs:")
            for name, detected in chips_detected.items():
                count = chip_counts.get(name, 0)
                print(f"  {name}: {count} chips (detected={detected})")
            print()

        return results

    finally:
        ai_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Test chip loading in simulator")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print("=== Chip Loading Diagnostic ===\n")
    print(f"Testing chips: {[CHIP_NAMES[c] for c in OUR_CHIPS]}")
    print(f"Chip IDs: {OUR_CHIPS}\n")

    try:
        results = run_chip_test(verbose=args.verbose)

        print("=" * 50)
        if results["success"]:
            print("✅ SUCCESS: Chips loaded correctly!")
            for name, count in results["chip_counts"].items():
                print(f"   {name}: {count} chips via getChips()")
            print("\n💡 Chips work! The issue may be scripts not passing chips.")
            print("   Use: compare_ais.py --chips1=4,5,6,8,14,15 --chips2=4,5,6,8,14,15")
        else:
            print("❌ FAILURE: Chips NOT loaded!")
            print("\nChip detection from logs:")
            for name, detected in results["chips_detected"].items():
                count = results["chip_counts"].get(name, 0)
                status = "✓" if detected else "✗ NOT DETECTED"
                print(f"   {name}: {count} chips {status}")

            print("\nPossible causes:")
            print("  1. Generator not loading data/chips.json")
            print("  2. Working directory mismatch")
            print("  3. Chip IDs not in chips.json")
            print("\nTry running with --verbose to see detailed output")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0 if results["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
