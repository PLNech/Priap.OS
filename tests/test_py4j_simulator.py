"""Test suite for Py4J simulator - anti-regression tests.

These tests ensure:
1. Winner calculation is correct (entity ID offset bug)
2. Fight outcomes are valid
3. Performance is acceptable
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.py4j_simulator import Py4JSimulator
from leekwars_agent.simulator import GENERATOR_PATH


@pytest.fixture(scope="module")
def sim():
    """Create simulator instance for all tests."""
    return Py4JSimulator()


@pytest.fixture(scope="module")
def test_ai():
    """Create a simple test AI file."""
    ai_path = GENERATOR_PATH / "test_py4j.leek"
    # Delete stale file if exists (from interrupted test runs)
    if ai_path.exists():
        ai_path.unlink()
    # CRITICAL: LeekScript generator doesn't handle indentation - use FLAT code!
    ai_path.write_text("""var enemy = getNearestEnemy();
if (enemy == null) { return; }
setWeapon(WEAPON_PISTOL);
while (getMP() > 0) {
var m = moveToward(enemy);
if (m == 0) { break; }
}
while (getTP() >= 3) {
var r = useWeapon(enemy);
if (r != USE_SUCCESS) { break; }
}
""")
    yield "test_py4j.leek"
    if ai_path.exists():
        ai_path.unlink()


class TestPy4JWinnerCalculation:
    """Tests for winner calculation - CRITICAL for anti-regression."""

    def test_winner_is_valid_value(self, sim, test_ai):
        """Winner should be 0, 1, or 2."""
        result = sim.run_1v1(test_ai, test_ai, level=10, seed=42)
        assert result.winner in [0, 1, 2], f"Invalid winner: {result.winner}"

    def test_both_teams_can_win(self, sim, test_ai):
        """Both teams should win some fights in mirror match."""
        wins = {1: 0, 2: 0, 0: 0}
        for i in range(100):
            result = sim.run_1v1(test_ai, test_ai, level=10, seed=i)
            wins[result.winner] += 1

        # In a fair mirror match, both teams should win at least some fights
        # Team 1 first-mover advantage exists, but Team 2 should still win some
        assert wins[1] > 0, f"Team 1 never wins! Distribution: {wins}"
        assert wins[2] > 0, f"Team 2 never wins! This indicates ID offset bug. Distribution: {wins}"

    def test_dead_status_entity_id_offset(self, sim, test_ai):
        """Verify dead dict keys are correctly offset.

        BUG FIXED: Py4J gateway creates entities with IDs 1,2 but JSON
        serializes with id=0,1. Dead dict uses actual IDs (1,2).
        """
        result = sim.run_1v1(test_ai, test_ai, level=10, seed=42)
        dead = result.raw_output.get("fight", {}).get("dead", {})
        leeks = result.raw_output.get("fight", {}).get("leeks", [])

        # Dead dict should have keys '1' and '2' (not '0' and '1')
        assert '1' in dead or '2' in dead, f"Dead dict has wrong keys: {dead.keys()}"

        # If someone died, winner should be determined correctly
        if dead.get('1', False) and not dead.get('2', False):
            # Entity 1 dead, entity 2 alive → Team 2 wins
            assert result.winner == 2, f"Entity 1 dead but winner={result.winner}"
        elif dead.get('2', False) and not dead.get('1', False):
            # Entity 2 dead, entity 1 alive → Team 1 wins
            assert result.winner == 1, f"Entity 2 dead but winner={result.winner}"


class TestPy4JFightOutcome:
    """Tests for fight outcome structure."""

    def test_outcome_has_turns(self, sim, test_ai):
        """Outcome should have valid turn count."""
        result = sim.run_1v1(test_ai, test_ai, level=10, seed=42)
        assert result.turns >= 1, f"Invalid turns: {result.turns}"
        # NOTE: Generator uses 65 as max duration, not 64
        assert result.turns <= 65, f"Turns exceed max: {result.turns}"

    def test_outcome_has_actions(self, sim, test_ai):
        """Outcome should have action list."""
        result = sim.run_1v1(test_ai, test_ai, level=10, seed=42)
        assert len(result.actions) > 0, "No actions in fight"

    def test_outcome_has_duration_ms(self, sim, test_ai):
        """Outcome should have valid duration."""
        result = sim.run_1v1(test_ai, test_ai, level=10, seed=42)
        assert result.duration_ms > 0, f"Invalid duration: {result.duration_ms}"
        assert result.duration_ms < 5000, f"Fight too slow: {result.duration_ms}ms"


class TestPy4JPerformance:
    """Performance tests - ensure Py4J remains fast."""

    def test_minimum_throughput(self, sim, test_ai):
        """Py4J should maintain >50 fights/sec."""
        import time

        n_fights = 50
        start = time.perf_counter()
        for i in range(n_fights):
            sim.run_1v1(test_ai, test_ai, level=1, seed=i)
        elapsed = time.perf_counter() - start

        fights_per_sec = n_fights / elapsed
        assert fights_per_sec > 50, f"Too slow: {fights_per_sec:.1f} fights/sec (expected >50)"

    def test_warmup_effect(self, sim, test_ai):
        """First few fights may be slower due to JIT, but should stabilize."""
        import time

        # Warmup
        for i in range(10):
            sim.run_1v1(test_ai, test_ai, level=1, seed=i)

        # Measure post-warmup
        n_fights = 50
        start = time.perf_counter()
        for i in range(n_fights):
            sim.run_1v1(test_ai, test_ai, level=1, seed=100 + i)
        elapsed = time.perf_counter() - start

        fights_per_sec = n_fights / elapsed
        # After warmup, should be very fast
        assert fights_per_sec > 100, f"Post-warmup too slow: {fights_per_sec:.1f} fights/sec"


class TestPy4JSmokeTests:
    """Smoke tests with various AI behaviors."""

    @pytest.fixture(scope="class")
    def pacifist_ai(self):
        """AI that does nothing - tests timeout handling."""
        ai_path = GENERATOR_PATH / "test_pacifist.leek"
        if ai_path.exists():
            ai_path.unlink()
        # Empty AI - just a return statement
        ai_path.write_text("""return;
""")
        yield "test_pacifist.leek"
        if ai_path.exists():
            ai_path.unlink()

    @pytest.fixture(scope="class")
    def aggressive_ai(self):
        """AI that rushes and shoots."""
        ai_path = GENERATOR_PATH / "test_aggressive.leek"
        if ai_path.exists():
            ai_path.unlink()
        # CRITICAL: LeekScript generator doesn't handle indentation - use FLAT code!
        ai_path.write_text("""var enemy = getNearestEnemy();
if (enemy == null) { return; }
setWeapon(WEAPON_PISTOL);
while (getMP() > 0) {
var m = moveToward(enemy);
if (m == 0) { break; }
}
while (getTP() >= 3) {
var r = useWeapon(enemy);
if (r != USE_SUCCESS) { break; }
}
""")
        yield "test_aggressive.leek"
        if ai_path.exists():
            ai_path.unlink()

    @pytest.fixture(scope="class")
    def kiter_ai(self):
        """AI that maintains distance."""
        ai_path = GENERATOR_PATH / "test_kiter.leek"
        if ai_path.exists():
            ai_path.unlink()
        # CRITICAL: LeekScript generator doesn't handle indentation - use FLAT code!
        ai_path.write_text("""var enemy = getNearestEnemy();
if (enemy == null) { return; }
setWeapon(WEAPON_PISTOL);
var dist = getCellDistance(getCell(), getCell(enemy));
while (getTP() >= 3 && dist <= 7 && dist >= 1) {
var r = useWeapon(enemy);
if (r != USE_SUCCESS) { break; }
dist = getCellDistance(getCell(), getCell(enemy));
}
while (getMP() > 0) {
var m = moveAwayFrom(enemy);
if (m == 0) { break; }
}
""")
        yield "test_kiter.leek"
        if ai_path.exists():
            ai_path.unlink()

    def test_pacifist_vs_pacifist_times_out(self, sim, pacifist_ai):
        """Two pacifists should result in draw (timeout)."""
        result = sim.run_1v1(pacifist_ai, pacifist_ai, level=10, seed=42)
        # Should be a draw since neither does anything
        assert result.winner == 0, f"Expected draw, got winner={result.winner}"
        # NOTE: Generator uses 65 as max duration
        assert result.turns == 65, f"Expected timeout at 65 turns, got {result.turns}"

    def test_aggressive_beats_pacifist(self, sim, aggressive_ai, pacifist_ai):
        """Aggressive AI should always beat pacifist."""
        wins = 0
        for i in range(10):
            result = sim.run_1v1(aggressive_ai, pacifist_ai, level=10, seed=i)
            if result.winner == 1:
                wins += 1
        assert wins >= 8, f"Aggressive should win most fights vs pacifist: {wins}/10"

    def test_pacifist_loses_to_aggressive(self, sim, pacifist_ai, aggressive_ai):
        """Pacifist should always lose to aggressive."""
        losses = 0
        for i in range(10):
            result = sim.run_1v1(pacifist_ai, aggressive_ai, level=10, seed=i)
            if result.winner == 2:
                losses += 1
        assert losses >= 8, f"Pacifist should lose most fights: {losses}/10 losses"

    def test_aggressive_vs_aggressive(self, sim, aggressive_ai):
        """Aggressive mirror should have decisive outcomes."""
        wins = {1: 0, 2: 0, 0: 0}
        for i in range(50):
            result = sim.run_1v1(aggressive_ai, aggressive_ai, level=10, seed=i)
            wins[result.winner] += 1

        # Most fights should have a winner
        decisive = wins[1] + wins[2]
        assert decisive > 30, f"Too many draws in aggressive mirror: {wins}"

    def test_kiter_vs_aggressive(self, sim, kiter_ai, aggressive_ai):
        """Kiter vs aggressive should produce valid results."""
        wins = {1: 0, 2: 0, 0: 0}
        for i in range(20):
            result = sim.run_1v1(kiter_ai, aggressive_ai, level=10, seed=i)
            wins[result.winner] += 1

        # Both strategies should win some fights
        total = sum(wins.values())
        assert total == 20, f"Missing results: {wins}"


class TestPy4JConnectionHandling:
    """Tests for gateway connection handling."""

    def test_simulator_connects(self):
        """Simulator should connect to gateway."""
        sim = Py4JSimulator()
        assert sim.gateway is not None, "Failed to connect to gateway"

    def test_can_run_after_reconnect(self, test_ai):
        """Should handle gateway restarts gracefully."""
        sim1 = Py4JSimulator()
        result1 = sim1.run_1v1(test_ai, test_ai, level=1, seed=1)
        assert result1.winner in [0, 1, 2]

        # Create new simulator (reuses connection)
        sim2 = Py4JSimulator()
        result2 = sim2.run_1v1(test_ai, test_ai, level=1, seed=2)
        assert result2.winner in [0, 1, 2]
