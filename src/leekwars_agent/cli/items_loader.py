"""Dynamic item loader - API first, file fallback.

Priority:
1. Fetch from LeekWars API (always fresh)
2. Parse tools/leek-wars/src/model/items.ts (offline fallback)
3. Minimal hardcoded set (emergency fallback)

No more hardcoding = no more "weapon_destroyer incidents"!
"""

import re
import json
from pathlib import Path
from functools import lru_cache
from typing import TypedDict
import httpx


class ItemData(TypedDict):
    name: str
    type: int  # 1=weapon, 2=chip
    level: int
    price: int


# Type constants
ITEM_TYPE_WEAPON = 1
ITEM_TYPE_CHIP = 2

# Cache file for offline use
CACHE_FILE = Path(__file__).parent / ".items_cache.json"


def fetch_items_from_api() -> dict[int, ItemData] | None:
    """Fetch items from LeekWars API.

    Returns None if API unavailable.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://leekwars.com/api/item/get-templates")
            response.raise_for_status()
            data = response.json()

        items: dict[int, ItemData] = {}
        templates = data.get("templates", data)

        if isinstance(templates, dict):
            for item_id_str, item in templates.items():
                item_id = int(item_id_str)
                # Only include weapons and chips
                item_type = item.get("type", 0)
                if item_type not in (ITEM_TYPE_WEAPON, ITEM_TYPE_CHIP):
                    continue

                items[item_id] = {
                    "name": item.get("name", f"item_{item_id}"),
                    "type": item_type,
                    "level": item.get("level", 1),
                    "price": item.get("price", 0),
                }

        # Cache for offline use
        if items:
            _save_cache(items)

        return items

    except (httpx.HTTPError, KeyError, ValueError):
        return None


def _save_cache(items: dict[int, ItemData]) -> None:
    """Save items to cache file."""
    try:
        # Convert int keys to strings for JSON
        data = {str(k): v for k, v in items.items()}
        CACHE_FILE.write_text(json.dumps(data, indent=2))
    except OSError:
        pass  # Cache is optional


def _load_cache() -> dict[int, ItemData] | None:
    """Load items from cache file."""
    try:
        if CACHE_FILE.exists():
            data = json.loads(CACHE_FILE.read_text())
            return {int(k): v for k, v in data.items()}
    except (OSError, json.JSONDecodeError):
        pass
    return None


def find_items_ts() -> Path | None:
    """Find items.ts in the project."""
    base = Path(__file__).parent.parent.parent.parent
    candidates = [
        base / "tools/leek-wars/src/model/items.ts",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def load_items_from_file() -> dict[int, ItemData] | None:
    """Parse items.ts to get all items."""
    items_path = find_items_ts()
    if not items_path:
        return None

    content = items_path.read_text()
    pattern = r"'(\d+)':\s*\{\s*id:\s*(\d+),\s*name:\s*'(\w+)',\s*type:\s*(\d+),\s*price:\s*(\d+),\s*level:\s*(\d+)"

    items: dict[int, ItemData] = {}
    for match in re.finditer(pattern, content):
        item_id = int(match.group(1))
        item_type = int(match.group(4))
        if item_type not in (ITEM_TYPE_WEAPON, ITEM_TYPE_CHIP):
            continue
        items[item_id] = {
            "name": match.group(3),
            "type": item_type,
            "level": int(match.group(6)),
            "price": int(match.group(5)),
        }

    return items if items else None


@lru_cache(maxsize=1)
def load_items() -> dict[int, ItemData]:
    """Load items with fallback chain: API -> cache -> file -> hardcoded."""
    # Try API first (freshest data)
    items = fetch_items_from_api()
    if items:
        return items

    # Try cache (recent API data)
    items = _load_cache()
    if items:
        return items

    # Try file (items.ts)
    items = load_items_from_file()
    if items:
        return items

    # Emergency fallback
    return _get_fallback_items()


def get_market_items(max_level: int | None = None, item_type: int | None = None) -> dict[int, ItemData]:
    """Get market items, optionally filtered."""
    items = load_items()

    result = {}
    for item_id, item in items.items():
        if item_type is not None and item["type"] != item_type:
            continue
        if max_level is not None and item["level"] > max_level:
            continue
        result[item_id] = item

    return result


def get_chips(max_level: int | None = None) -> dict[int, ItemData]:
    """Get all chips up to max_level."""
    return get_market_items(max_level=max_level, item_type=ITEM_TYPE_CHIP)


def get_weapons(max_level: int | None = None) -> dict[int, ItemData]:
    """Get all weapons up to max_level."""
    return get_market_items(max_level=max_level, item_type=ITEM_TYPE_WEAPON)


def get_item(item_id: int) -> ItemData | None:
    """Get a specific item by ID."""
    return load_items().get(item_id)


def _get_fallback_items() -> dict[int, ItemData]:
    """Minimal fallback - only verified essentials."""
    return {
        37: {"name": "weapon_pistol", "type": 1, "level": 1, "price": 900},
        45: {"name": "weapon_magnum", "type": 1, "level": 27, "price": 7510},
        6: {"name": "chip_flash", "type": 2, "level": 24, "price": 4890},
        4: {"name": "chip_cure", "type": 2, "level": 20, "price": 3710},
    }
