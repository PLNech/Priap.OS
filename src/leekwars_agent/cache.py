"""Local cache for LeekWars API responses.

Avoids rate limits by caching fight data locally.
Cache-first pattern: always check local before network.
"""

import json
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"
FIGHTS_DIR = CACHE_DIR / "fights"


def ensure_dirs():
    """Ensure cache directories exist."""
    FIGHTS_DIR.mkdir(parents=True, exist_ok=True)


def get_fight(fight_id: int) -> dict | None:
    """Get fight from cache. Returns None if not cached."""
    ensure_dirs()
    cache_file = FIGHTS_DIR / f"{fight_id}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None


def save_fight(fight_id: int, data: dict) -> None:
    """Save fight to cache."""
    ensure_dirs()
    cache_file = FIGHTS_DIR / f"{fight_id}.json"
    cache_file.write_text(json.dumps(data))


def get_cached_fight_ids() -> list[int]:
    """Get list of all cached fight IDs."""
    ensure_dirs()
    return [int(f.stem) for f in FIGHTS_DIR.glob("*.json")]


def cache_stats() -> dict:
    """Get cache statistics."""
    ensure_dirs()
    files = list(FIGHTS_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    return {
        "fights_cached": len(files),
        "total_size_kb": total_size / 1024,
    }
