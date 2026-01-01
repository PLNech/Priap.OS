"""Test suite for the fight visualizer."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.simulator import Simulator
from leekwars_agent.visualizer import (
    FightReplayer,
    FightReport,
    EntityStats,
    generate_fight_report,
    analyze_fight,
    replay_fight,
    ACTION_START_FIGHT,
    ACTION_DAMAGE,
    ACTION_USE_WEAPON,
    ACTION_PLAYER_DEAD,
)


class TestFightReplayer:
    """Tests for the FightReplayer class."""

    @pytest.fixture
    def fight_data(self):
        """Run a fight and return raw output."""
        sim = Simulator()
        outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=42)
        return outcome.raw_output

    def test_replayer_init_with_generator_format(self, fight_data):
        """Replayer should handle generator output format (fight key)."""
        replayer = FightReplayer(fight_data)
        assert replayer.data is not None
        assert len(replayer.initial_states) == 2

    def test_replayer_init_with_api_format(self):
        """Replayer should handle API format (data key)."""
        api_format = {
            "data": {
                "leeks": [
                    {"id": 0, "name": "L1", "team": 1, "life": 100, "tp": 10, "mp": 3, "cellPos": 100},
                    {"id": 1, "name": "L2", "team": 2, "life": 100, "tp": 10, "mp": 3, "cellPos": 400},
                ],
                "actions": [[0]],
                "map": {"width": 18, "height": 18},
            },
            "winner": 1,
        }
        replayer = FightReplayer(api_format)
        assert len(replayer.initial_states) == 2

    def test_initial_states_have_correct_data(self, fight_data):
        """Initial states should reflect fight start data."""
        replayer = FightReplayer(fight_data)

        for entity_id, state in replayer.initial_states.items():
            assert state.life > 0
            assert state.tp > 0
            assert state.mp > 0
            assert state.team in [1, 2]

    def test_replay_text_returns_lines(self, fight_data):
        """replay_text should return list of log lines."""
        replayer = FightReplayer(fight_data)
        lines = replayer.replay_text()

        assert isinstance(lines, list)
        assert len(lines) > 0
        assert any("FIGHT START" in line for line in lines)
        assert any("FIGHT END" in line for line in lines)


class TestFightReport:
    """Tests for detailed fight reports."""

    @pytest.fixture
    def report(self):
        """Generate a report from a fight."""
        sim = Simulator()
        outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=42)
        return generate_fight_report(outcome.raw_output)

    def test_report_has_entity_stats(self, report):
        """Report should have stats for all entities."""
        assert len(report.entity_stats) == 2

    def test_report_tracks_turns(self, report):
        """Report should track turn count."""
        assert report.turns > 0

    def test_report_has_action_log(self, report):
        """Report should have action log."""
        assert len(report.action_log) > 0

    def test_entity_stats_track_damage(self, report):
        """Entity stats should track damage inflicted/received."""
        total_inflicted = sum(s.damage_inflicted for s in report.entity_stats.values())
        total_received = sum(s.damage_received for s in report.entity_stats.values())

        # Damage inflicted should equal damage received
        assert total_inflicted == total_received

    def test_entity_stats_track_shoots(self, report):
        """Entity stats should track number of shoots."""
        total_shoots = sum(s.shoots for s in report.entity_stats.values())
        assert total_shoots > 0

    def test_entity_stats_track_movement(self, report):
        """Entity stats should track MP used."""
        total_mp = sum(s.mp_used for s in report.entity_stats.values())
        assert total_mp > 0

    def test_entity_stats_track_kills(self, report):
        """Entity stats should track kills."""
        total_kills = sum(s.kills for s in report.entity_stats.values())
        # In a 1v1, should be 0 or 1 kill
        assert total_kills in [0, 1]

    def test_life_history_tracked(self, report):
        """Entity stats should track life history."""
        for stats in report.entity_stats.values():
            assert len(stats.life_history) > 0


class TestAnalyzeFight:
    """Tests for the analyze_fight function."""

    @pytest.fixture
    def fight_data(self):
        sim = Simulator()
        outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=42)
        return outcome.raw_output

    def test_returns_dict(self, fight_data):
        """analyze_fight should return a dict."""
        stats = analyze_fight(fight_data)
        assert isinstance(stats, dict)

    def test_has_required_keys(self, fight_data):
        """Stats dict should have required keys."""
        stats = analyze_fight(fight_data)
        assert "turns" in stats
        assert "total_damage" in stats
        assert "total_attacks" in stats
        assert "total_moves" in stats
        assert "winner" in stats


class TestActionConstants:
    """Tests for action type constants."""

    def test_action_constants_defined(self):
        """Action constants should be defined correctly."""
        assert ACTION_START_FIGHT == 0
        assert ACTION_DAMAGE == 101
        assert ACTION_USE_WEAPON == 16
        assert ACTION_PLAYER_DEAD == 5


class TestReportAccuracy:
    """Tests that report data matches actual fight actions."""

    @pytest.fixture
    def fight_and_report(self):
        """Run fight and generate report."""
        sim = Simulator()
        outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=42)
        report = generate_fight_report(outcome.raw_output)
        return outcome.raw_output, report

    def test_damage_matches_actions(self, fight_and_report):
        """Report damage should match DAMAGE actions."""
        fight_data, report = fight_and_report
        actions = fight_data["fight"]["actions"]

        # Count damage from actions
        action_damage = {}
        for action in actions:
            if action[0] == 101:  # DAMAGE
                target_id = action[1]
                damage = action[2]
                action_damage[target_id] = action_damage.get(target_id, 0) + damage

        # Compare with report
        for name, stats in report.entity_stats.items():
            # Find matching entity
            for leek in fight_data["fight"]["leeks"]:
                if leek["name"] == name:
                    entity_id = leek["id"]
                    expected_damage = action_damage.get(entity_id, 0)
                    assert stats.damage_received == expected_damage, \
                        f"{name} received {stats.damage_received} but actions show {expected_damage}"

    def test_shoots_match_use_weapon_actions(self, fight_and_report):
        """Report shoots should match USE_WEAPON actions."""
        fight_data, report = fight_and_report
        actions = fight_data["fight"]["actions"]

        # Count USE_WEAPON actions per entity
        current_entity = -1
        shoots_by_entity = {}

        for action in actions:
            if action[0] == 7:  # ENTITY_TURN
                current_entity = action[1]
            elif action[0] == 16:  # USE_WEAPON
                shoots_by_entity[current_entity] = shoots_by_entity.get(current_entity, 0) + 1

        # Map entity ID to name
        id_to_name = {leek["id"]: leek["name"] for leek in fight_data["fight"]["leeks"]}

        for entity_id, count in shoots_by_entity.items():
            name = id_to_name.get(entity_id)
            if name and name in report.entity_stats:
                assert report.entity_stats[name].shoots == count, \
                    f"{name} has {report.entity_stats[name].shoots} shoots but actions show {count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
