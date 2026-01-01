"""Baseline agents for LeekWars fights.

These are LeekScript AI files + Python evaluation utilities.
"""

from pathlib import Path

AGENTS_DIR = Path(__file__).parent
AI_DIR = AGENTS_DIR / "ai"

# AI file paths
RANDOM_AI = "agents/ai/random.leek"
HEURISTIC_AI = "agents/ai/heuristic.leek"
FIGHTER_V1_AI = "fighter_v1.leek"  # In generator dir


def get_ai_path(name: str) -> str:
    """Get AI path by name."""
    ais = {
        "random": RANDOM_AI,
        "heuristic": HEURISTIC_AI,
        "fighter_v1": FIGHTER_V1_AI,
    }
    return ais.get(name, name)
