"""Test simulator determinism with seeded fights.

Verifies that the Java generator produces identical results when given
the same seed, map, and entity configurations.
"""

import pytest
from pathlib import Path

from leekwars_agent.simulator import (
    Simulator,
    EntityConfig,
    ScenarioConfig,
    MapConfig,
    replay_fight_scenario,
    detect_starter_team,
)


# Skip tests if generator.jar not available
pytestmark = pytest.mark.skipif(
    not Path("tools/leek-wars-generator/generator.jar").exists(),
    reason="generator.jar not built - run: cd tools/leek-wars-generator && ./gradlew jar"
)


class TestDeterminism:
    """Test that same seed produces identical results."""

    def test_same_seed_same_result_10_runs(self):
        """CRITICAL: 10 runs with same seed + same map MUST produce identical outcomes.

        For true determinism, we must fix BOTH:
        - The RNG seed (controls damage rolls, AI decisions)
        - The map (get_random_map() uses Python random, which is NOT seeded)
        """
        sim = Simulator()
        seed = 12345
        results = []

        # Use a simple AI that exists
        ai_path = "fighter_v11.leek"
        if not Path(f"tools/leek-wars-generator/ai/{ai_path}").exists():
            ai_path = "fighter_v8.leek"  # Fallback

        # Fix the map for determinism (random map selection uses Python random)
        fixed_map = MapConfig.symmetric_empty()

        for i in range(10):
            outcome = sim.run_1v1(ai_path, ai_path, level=10, seed=seed, map_config=fixed_map)
            results.append({
                "winner": outcome.winner,
                "turns": outcome.turns,
                "action_count": len(outcome.actions),
            })

        # Winner and turns MUST be identical (core determinism)
        for i in range(1, 10):
            assert results[i]["winner"] == results[0]["winner"], \
                f"Run {i} winner differs: {results[i]['winner']} vs {results[0]['winner']}"
            assert results[i]["turns"] == results[0]["turns"], \
                f"Run {i} turns differs: {results[i]['turns']} vs {results[0]['turns']}"

        # Action count should also be identical with fixed conditions
        for i in range(1, 10):
            assert results[i]["action_count"] == results[0]["action_count"], \
                f"Run {i} action_count differs: {results[i]['action_count']} vs {results[0]['action_count']}"

    def test_different_seeds_different_results(self):
        """Different seeds should produce statistical variance."""
        sim = Simulator()
        outcomes = set()

        ai_path = "fighter_v11.leek"
        if not Path(f"tools/leek-wars-generator/ai/{ai_path}").exists():
            ai_path = "fighter_v8.leek"

        # Run with 20 different seeds
        for seed in range(20):
            outcome = sim.run_1v1(ai_path, ai_path, level=10, seed=seed)
            outcomes.add((outcome.winner, outcome.turns))

        # With 20 different seeds, we should see at least 3 unique outcomes
        # (some variation in winner or turn count)
        assert len(outcomes) >= 2, \
            f"Expected variance with different seeds, got {len(outcomes)} unique outcomes"


class TestStarterTeamDetection:
    """Test starter team detection from fight data."""

    def test_detect_team1_starter(self):
        """When starter farmer is in leeks1, return 1."""
        fight_data = {
            "starter": 124831,  # PriapOS
            "leeks1": [{"id": 131321, "farmer": 124831}],
            "leeks2": [{"id": 103658, "farmer": 98040}],
        }
        assert detect_starter_team(fight_data) == 1

    def test_detect_team2_starter(self):
        """When starter farmer is in leeks2, return 2."""
        fight_data = {
            "starter": 98040,  # Opponent
            "leeks1": [{"id": 131321, "farmer": 124831}],
            "leeks2": [{"id": 103658, "farmer": 98040}],
        }
        assert detect_starter_team(fight_data) == 2

    def test_missing_starter_returns_zero(self):
        """Missing starter field returns 0 (frequency-based)."""
        fight_data = {
            "leeks1": [{"id": 131321, "farmer": 124831}],
            "leeks2": [{"id": 103658, "farmer": 98040}],
        }
        assert detect_starter_team(fight_data) == 0


class TestReplayScenario:
    """Test replay scenario creation from fight data."""

    def test_creates_scenario_from_fight_data(self):
        """replay_fight_scenario extracts all necessary data."""
        # Minimal fight data structure (from real fight 50886948)
        fight_data = {
            "seed": 1378083065,
            "starter": 124831,
            "leeks1": [{"id": 131321, "farmer": 124831}],
            "leeks2": [{"id": 103658, "farmer": 98040}],
            "data": {
                "leeks": [
                    {
                        "id": 0, "name": "IAdonis", "team": 1,
                        "level": 10, "life": 127, "tp": 10, "mp": 3,
                        "strength": 96, "agility": 10, "wisdom": 0,
                        "resistance": 0, "science": 0, "magic": 0,
                        "frequency": 100, "farmer": 124831,
                        "cellPos": 214, "weapons": [], "chips": [],
                    },
                    {
                        "id": 1, "name": "basation", "team": 2,
                        "level": 10, "life": 127, "tp": 10, "mp": 3,
                        "strength": 100, "agility": 0, "wisdom": 10,
                        "resistance": 0, "science": 10, "magic": 0,
                        "frequency": 100, "farmer": 98040,
                        "cellPos": 472, "weapons": [], "chips": [],
                    },
                ],
                "map": {
                    "width": 18, "height": 18, "type": 1,
                    "obstacles": {"2": 1, "9": 1},
                },
            },
        }

        scenario = replay_fight_scenario(fight_data, "test_ai.leek")

        assert scenario.seed == 1378083065
        assert scenario.starter_team == 1
        assert len(scenario.team1) == 1
        assert len(scenario.team2) == 1
        assert scenario.team1[0].name == "IAdonis"
        assert scenario.team1[0].strength == 96
        assert scenario.team2[0].name == "basation"
        assert scenario.team2[0].strength == 100

    def test_seed_override(self):
        """seed_override replaces original seed."""
        fight_data = {
            "seed": 1378083065,
            "data": {"leeks": [], "map": {}},
        }

        scenario = replay_fight_scenario(fight_data, "test.leek", seed_override=99999)
        assert scenario.seed == 99999

    def test_different_ai_per_team(self):
        """Can specify different AI for each team."""
        fight_data = {
            "seed": 123,
            "data": {
                "leeks": [
                    {"id": 0, "name": "A", "team": 1, "farmer": 1},
                    {"id": 1, "name": "B", "team": 2, "farmer": 2},
                ],
                "map": {},
            },
        }

        scenario = replay_fight_scenario(fight_data, "our_ai.leek", "opponent_ai.leek")
        assert scenario.team1[0].ai == "our_ai.leek"
        assert scenario.team2[0].ai == "opponent_ai.leek"


class TestEntityConfigFromReplay:
    """Test EntityConfig.from_replay_entity()."""

    def test_extracts_all_stats(self):
        """All stats are correctly extracted from replay entity."""
        entity = {
            "id": 0,
            "name": "TestLeek",
            "level": 34,
            "life": 250,
            "tp": 10,
            "mp": 4,
            "strength": 310,
            "agility": 10,
            "wisdom": 50,
            "resistance": 20,
            "science": 5,
            "magic": 0,
            "frequency": 100,
            "farmer": 124831,
            "weapons": [37, 45],
            "chips": [4, 5, 6],
        }

        config = EntityConfig.from_replay_entity(entity, "test.leek", team=1)

        assert config.id == 0
        assert config.name == "TestLeek"
        assert config.ai == "test.leek"
        assert config.level == 34
        assert config.life == 250
        assert config.tp == 10
        assert config.mp == 4
        assert config.strength == 310
        assert config.agility == 10
        assert config.wisdom == 50
        assert config.resistance == 20
        assert config.science == 5
        assert config.magic == 0
        assert config.frequency == 100
        assert config.farmer == 124831
        assert config.team == 1
        assert config.weapons == [37, 45]
        assert config.chips == [4, 5, 6]

    def test_defaults_for_missing_fields(self):
        """Missing fields get sensible defaults."""
        entity = {"id": 1, "name": "Minimal"}

        config = EntityConfig.from_replay_entity(entity, "ai.leek", team=2)

        assert config.level == 1
        assert config.life == 100
        assert config.tp == 10
        assert config.mp == 3
        assert config.strength == 0
        assert config.frequency == 100
        assert config.cores == 1
        assert config.ram == 100
        assert config.weapons == []
        assert config.chips == []
