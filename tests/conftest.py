"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.simulator import Simulator, GENERATOR_PATH


@pytest.fixture(scope="session")
def ensure_test_ai():
    """Ensure test AI file exists in generator directory."""
    ai_path = GENERATOR_PATH / "fighter_v1.leek"
    if not ai_path.exists():
        ai_path.write_text("""
// Test fighter AI
var enemy = getNearestEnemy()
if (!enemy) return
moveToward(enemy)
if (getWeapon() != WEAPON_PISTOL) setWeapon(WEAPON_PISTOL)
useWeapon(enemy)
""")
    return "fighter_v1.leek"


@pytest.fixture(scope="session")
def simulator():
    """Shared simulator instance."""
    return Simulator()


@pytest.fixture
def sample_fight(simulator, ensure_test_ai):
    """Run a sample fight and return the outcome."""
    return simulator.run_1v1(ensure_test_ai, ensure_test_ai, seed=42)
