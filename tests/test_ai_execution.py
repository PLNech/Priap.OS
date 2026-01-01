"""Tests to investigate AI execution issues.

This file contains diagnostic tests for the Leek2 AI bug where
Entity 1 doesn't execute any actions despite having the same AI.

CONFIRMED BUG: The `global` keyword in LeekScript causes entity 1 to fail
when the same AI file is used for both entities. This is likely a bug in
the LeekScript compiler or the generator where global variable state is
shared incorrectly between entities using the same compiled AI.

WORKAROUND: Use different AI files for each entity, or avoid `global` keyword.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.simulator import Simulator, EntityConfig, ScenarioConfig, GENERATOR_PATH


class TestAIExecution:
    """Diagnostic tests for AI execution."""

    @pytest.fixture
    def simulator(self):
        return Simulator()

    def test_entity_ids_in_output(self, simulator):
        """Check how entity IDs are assigned in output vs config."""
        leek1 = EntityConfig(
            id=100, name="ConfigLeek1", ai="fighter_v1.leek",
            level=1, life=103, tp=10, mp=3,
            farmer=1, team=1, cell=100, weapons=[37]
        )
        leek2 = EntityConfig(
            id=200, name="ConfigLeek2", ai="fighter_v1.leek",
            level=1, life=103, tp=10, mp=3,
            farmer=2, team=2, cell=450, weapons=[37]
        )
        scenario = ScenarioConfig(team1=[leek1], team2=[leek2], seed=42)
        outcome = simulator.run_scenario(scenario)

        fight = outcome.raw_output["fight"]
        leeks = fight["leeks"]

        # Check if config IDs are preserved or remapped
        output_ids = [l["id"] for l in leeks]
        output_names = [l["name"] for l in leeks]

        print(f"Config IDs: 100, 200")
        print(f"Output IDs: {output_ids}")
        print(f"Output names: {output_names}")

        # Document the ID mapping behavior
        assert len(leeks) == 2

    def test_ai_paths_in_scenario(self, simulator):
        """Verify AI paths are correctly set in scenario."""
        scenario_dict = ScenarioConfig(
            team1=[EntityConfig(id=1, name="L1", ai="fighter_v1.leek", farmer=1, team=1, weapons=[37])],
            team2=[EntityConfig(id=2, name="L2", ai="fighter_v1.leek", farmer=2, team=2, weapons=[37])],
        ).to_dict()

        # Both entities should have same AI path
        assert scenario_dict["entities"][0][0]["ai"] == "fighter_v1.leek"
        assert scenario_dict["entities"][1][0]["ai"] == "fighter_v1.leek"

    def test_actions_per_entity(self, simulator):
        """Count actions taken by each entity."""
        outcome = simulator.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=42)
        actions = outcome.raw_output["fight"]["actions"]

        # Track actions by entity
        current_entity = -1
        actions_by_entity = {}

        for action in actions:
            if action[0] == 7:  # ENTITY_TURN
                current_entity = action[1]
                if current_entity not in actions_by_entity:
                    actions_by_entity[current_entity] = {"turns": 0, "moves": 0, "attacks": 0, "set_weapon": 0}
                actions_by_entity[current_entity]["turns"] += 1
            elif action[0] == 10:  # MOVE
                if current_entity in actions_by_entity:
                    actions_by_entity[current_entity]["moves"] += 1
            elif action[0] == 16:  # USE_WEAPON
                if current_entity in actions_by_entity:
                    actions_by_entity[current_entity]["attacks"] += 1
            elif action[0] == 13:  # SET_WEAPON
                if current_entity in actions_by_entity:
                    actions_by_entity[current_entity]["set_weapon"] += 1

        print("\nActions by entity:")
        for eid, stats in actions_by_entity.items():
            print(f"  Entity {eid}: {stats}")

        # Document the bug
        assert 0 in actions_by_entity, "Entity 0 should exist"
        assert actions_by_entity[0]["moves"] > 0 or actions_by_entity[0]["attacks"] > 0, \
            "Entity 0 should have actions"

        # This is the bug - Entity 1 has no actions
        if 1 in actions_by_entity:
            e1_total = actions_by_entity[1]["moves"] + actions_by_entity[1]["attacks"]
            if e1_total == 0:
                pytest.xfail("Known bug: Entity 1 doesn't take any actions")

    def test_entity_starting_positions(self, simulator):
        """Verify both entities start at expected positions."""
        outcome = simulator.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=42)
        leeks = outcome.raw_output["fight"]["leeks"]

        positions = {l["name"]: l["cellPos"] for l in leeks}
        teams = {l["name"]: l["team"] for l in leeks}

        print(f"Starting positions: {positions}")
        print(f"Teams: {teams}")

        # Both should have valid positions
        assert all(pos >= 0 for pos in positions.values())
        # Different teams
        assert len(set(teams.values())) == 2

    def test_debug_ai_output(self, simulator):
        """Use debug AI to see what each entity perceives."""
        # Create debug AI
        debug_ai_path = GENERATOR_PATH / "debug_ai.leek"
        debug_ai_path.write_text("""
// Debug AI - minimal actions with debug output
debug("=== DEBUG AI START ===")
debug("Entity ID: " + getEntity())
debug("Team: " + getTeam())
debug("Cell: " + getCell())

var enemy = getNearestEnemy()
if (enemy) {
    debug("Enemy found: " + enemy)
    debug("Enemy cell: " + getCell(enemy))
    debug("Distance: " + getCellDistance(getCell(), getCell(enemy)))

    // Try one action
    if (getWeapon() != WEAPON_PISTOL) {
        var result = setWeapon(WEAPON_PISTOL)
        debug("setWeapon result: " + result)
    }
    moveToward(enemy)
} else {
    debug("NO ENEMY - this is the bug!")
}
debug("=== DEBUG AI END ===")
""")

        outcome = simulator.run_1v1("debug_ai.leek", "debug_ai.leek", seed=42)

        # Check logs for both entities
        logs = outcome.raw_output.get("logs", {})
        print(f"\nLog keys (entity IDs): {list(logs.keys())}")

        for entity_id, entity_logs in logs.items():
            print(f"\nEntity {entity_id} logs ({len(entity_logs)} turns):")
            for turn, entries in list(entity_logs.items())[:3]:
                print(f"  Turn {turn}: {len(entries)} entries")
                for entry in entries[:2]:
                    print(f"    {entry}")

        # Clean up
        debug_ai_path.unlink()

    def test_different_ai_files(self, simulator):
        """Test with two different AI files (same content)."""
        ai_content = """
var enemy = getNearestEnemy()
if (!enemy) return
moveToward(enemy)
if (getWeapon() != WEAPON_PISTOL) setWeapon(WEAPON_PISTOL)
useWeapon(enemy)
"""
        ai1_path = GENERATOR_PATH / "test_ai_1.leek"
        ai2_path = GENERATOR_PATH / "test_ai_2.leek"
        ai1_path.write_text(ai_content)
        ai2_path.write_text(ai_content)

        try:
            outcome = simulator.run_1v1("test_ai_1.leek", "test_ai_2.leek", seed=42)
            actions = outcome.raw_output["fight"]["actions"]

            # Count actions per entity
            current_entity = -1
            moves = {0: 0, 1: 0}

            for action in actions:
                if action[0] == 7:
                    current_entity = action[1]
                elif action[0] == 10 and current_entity in moves:
                    moves[current_entity] += 1

            print(f"Moves per entity: {moves}")

            # Check if using different files fixes it
            if moves[1] == 0:
                pytest.xfail("Bug persists with different AI files")

        finally:
            ai1_path.unlink()
            ai2_path.unlink()


    def test_same_ai_file_causes_bug(self, simulator):
        """Confirm the bug is related to using the same AI file for both entities."""
        ai_content = """
var enemy = getNearestEnemy()
if (!enemy) return
moveToward(enemy)
if (getWeapon() != WEAPON_PISTOL) setWeapon(WEAPON_PISTOL)
useWeapon(enemy)
"""
        ai_path = GENERATOR_PATH / "shared_ai.leek"
        ai_path.write_text(ai_content)

        try:
            # Test 1: Same file for both - expect bug
            outcome1 = simulator.run_1v1("shared_ai.leek", "shared_ai.leek", seed=42)
            actions1 = outcome1.raw_output["fight"]["actions"]

            current_entity = -1
            actions_same = {0: 0, 1: 0}
            for action in actions1:
                if action[0] == 7:
                    current_entity = action[1]
                elif action[0] in [10, 16] and current_entity in actions_same:
                    actions_same[current_entity] += 1

            print(f"Same AI file - actions: {actions_same}")

            # Test 2: Make a copy with different name
            ai_copy_path = GENERATOR_PATH / "shared_ai_copy.leek"
            ai_copy_path.write_text(ai_content)

            outcome2 = simulator.run_1v1("shared_ai.leek", "shared_ai_copy.leek", seed=42)
            actions2 = outcome2.raw_output["fight"]["actions"]

            actions_diff = {0: 0, 1: 0}
            for action in actions2:
                if action[0] == 7:
                    current_entity = action[1]
                elif action[0] in [10, 16] and current_entity in actions_diff:
                    actions_diff[current_entity] += 1

            print(f"Different AI files - actions: {actions_diff}")

            # Document the bug: same file = entity 1 inactive
            # different file = both active
            same_file_bug = actions_same[1] == 0
            diff_file_works = actions_diff[0] > 0 and actions_diff[1] > 0

            if same_file_bug and diff_file_works:
                pytest.xfail("Confirmed: Using same AI file causes entity 1 to be inactive")

            ai_copy_path.unlink()

        finally:
            ai_path.unlink()


    def test_identify_problematic_ai_feature(self, simulator):
        """Identify which AI feature causes the entity 1 bug."""
        results = {}

        # Test different AI variations
        ai_variations = {
            "minimal": """
var enemy = getNearestEnemy()
if (!enemy) return
moveToward(enemy)
""",
            "with_setWeapon": """
var enemy = getNearestEnemy()
if (!enemy) return
setWeapon(WEAPON_PISTOL)
moveToward(enemy)
""",
            "with_global": """
global dist
var enemy = getNearestEnemy()
if (!enemy) return
dist = 1
moveToward(enemy)
""",
            "with_while": """
var enemy = getNearestEnemy()
if (!enemy) return
while (getMP() > 0) {
    moveToward(enemy)
}
""",
            "full_fighter_v1": """
global dist
var enemy = getNearestEnemy()
if (!enemy) return
dist = getCellDistance(getCell(), getCell(enemy))
var PISTOL_MIN = 1
var PISTOL_MAX = 7
var PISTOL_COST = 3
if (getWeapon() != WEAPON_PISTOL) {
    setWeapon(WEAPON_PISTOL)
}
while (dist > PISTOL_MAX && getMP() > 0) {
    var moved = moveToward(enemy)
    if (moved == 0) break
    dist = getCellDistance(getCell(), getCell(enemy))
}
while (dist < PISTOL_MIN && getMP() > 0) {
    var moved = moveAwayFrom(enemy)
    if (moved == 0) break
    dist = getCellDistance(getCell(), getCell(enemy))
}
while (getTP() >= PISTOL_COST && dist >= PISTOL_MIN && dist <= PISTOL_MAX) {
    var result = useWeapon(enemy)
    if (result != USE_SUCCESS) break
    dist = getCellDistance(getCell(), getCell(enemy))
}
if (getMP() > 0 && dist > PISTOL_MIN) {
    moveToward(enemy)
}
""",
        }

        for name, ai_code in ai_variations.items():
            ai_path = GENERATOR_PATH / f"test_{name}.leek"
            ai_path.write_text(ai_code)

            try:
                outcome = simulator.run_1v1(f"test_{name}.leek", f"test_{name}.leek", seed=42)
                actions = outcome.raw_output["fight"]["actions"]

                current_entity = -1
                entity_actions = {0: 0, 1: 0}
                for action in actions:
                    if action[0] == 7:
                        current_entity = action[1]
                    elif action[0] in [10, 13, 16] and current_entity in entity_actions:
                        entity_actions[current_entity] += 1

                results[name] = entity_actions
                bug = entity_actions[1] == 0
                status = "BUG" if bug else "OK"
                print(f"{name}: {entity_actions} [{status}]")

            finally:
                ai_path.unlink()

        # Check which variations trigger the bug
        bugged = [name for name, actions in results.items() if actions[1] == 0]
        print(f"\nVariations with bug: {bugged}")

        # The test passes if we can identify the problematic feature
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
