#!/usr/bin/env python3
"""
LeekWars Fight & Map Scraper

Comprehensive Playwright-based scraper for collecting fight data, map layouts,
and building a simulation-ready map library.

Usage:
    # Build map library from existing cache
    poetry run python scripts/scrape_maps.py

    # Scrape new fights (requires Playwright browsers installed)
    poetry run python scripts/scrape_maps.py --scrape --count=100

    # Scrape specific fight IDs
    poetry run python scripts/scrape_maps.py --fights 50900000 50900001 50900002

    # Scrape recent fights from a farmer
    poetry run python scripts/scrape_maps.py --farmer 124831 --count=50
"""

import argparse
import asyncio
import json
import random
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

try:
    from playwright.async_api import async_playwright, Page, Response
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache" / "fights"
MAP_LIBRARY_FILE = DATA_DIR / "map_library.json"

# LeekWars URLs
LEEKWARS_BASE = "https://leekwars.com"
LEEKWARS_API = f"{LEEKWARS_BASE}/api"


@dataclass
class FightData:
    """Complete fight data structure matching LeekWars API format."""
    id: int
    date: int = 0
    year: int = 0
    type: int = 0  # 0=solo, 1=farmer, 2=team
    context: int = 0  # 1=garden, 2=test, 3=tournament
    status: int = 0  # 0=processing, 1=finished
    winner: int = 0  # 1=team1, 2=team2, 0=draw
    leeks1: list = field(default_factory=list)
    leeks2: list = field(default_factory=list)
    farmers1: list = field(default_factory=list)
    farmers2: list = field(default_factory=list)
    report: Any = None
    comments: list = field(default_factory=list)
    tournament: Any = None
    views: int = 0
    starter: int = 0  # Which team started
    trophies: list = field(default_factory=list)
    seed: int | None = None
    team1_name: str = ""
    team2_name: str = ""
    data: dict = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, resp: dict) -> "FightData":
        """Parse API response into FightData."""
        return cls(
            id=resp.get("id", 0),
            date=resp.get("date", 0),
            year=resp.get("year", 0),
            type=resp.get("type", 0),
            context=resp.get("context", 0),
            status=resp.get("status", 0),
            winner=resp.get("winner", 0),
            leeks1=resp.get("leeks1", []),
            leeks2=resp.get("leeks2", []),
            farmers1=resp.get("farmers1", []),
            farmers2=resp.get("farmers2", []),
            report=resp.get("report"),
            comments=resp.get("comments", []),
            tournament=resp.get("tournament"),
            views=resp.get("views", 0),
            starter=resp.get("starter", 0),
            trophies=resp.get("trophies", []),
            seed=resp.get("seed"),
            team1_name=resp.get("team1_name", ""),
            team2_name=resp.get("team2_name", ""),
            data=resp.get("data", {}),
        )


@dataclass
class MapData:
    """Extracted map data for simulation."""
    fight_id: int
    width: int
    height: int
    type: int
    obstacles: dict[str, int]
    pattern: list[int] | None
    team1_spawns: list[int]
    team2_spawns: list[int]
    # Computed symmetric spawns for fair 1v1
    symmetric_spawns: dict[str, list[int]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.symmetric_spawns:
            self.symmetric_spawns = self._compute_symmetric_spawns()

    def _compute_symmetric_spawns(self) -> dict[str, list[int]]:
        """Compute fair symmetric spawn positions.

        Places teams on opposite sides of the map with meaningful distance.
        For 18x18 map: stride=35, center=306, we want ~4-5 rows apart.
        """
        # Diamond grid properties
        stride = self.width * 2 - 1
        total_cells = stride * self.height - (self.width - 1)
        center = total_cells // 2

        # Find valid cells (not obstacles)
        obstacle_cells = set(int(k) for k in self.obstacles.keys())

        # Minimum offset: ~3 rows = stride * 1.5 ≈ 50 cells for 18x18
        # Maximum offset: ~6 rows = stride * 3 ≈ 100 cells
        min_offset = stride + stride // 2  # ~1.5 rows
        max_offset = stride * 4  # ~4 rows

        # Search for symmetric pair with meaningful distance
        for offset in range(min_offset, max_offset):
            t1_cell = center - offset
            t2_cell = center + offset

            if (t1_cell > 0 and t2_cell < total_cells and
                t1_cell not in obstacle_cells and
                t2_cell not in obstacle_cells):
                return {"team1": [t1_cell], "team2": [t2_cell]}

        # Fallback: try smaller offset if no valid large offset found
        for offset in range(stride // 2, min_offset):
            t1_cell = center - offset
            t2_cell = center + offset

            if (t1_cell > 0 and t2_cell < total_cells and
                t1_cell not in obstacle_cells and
                t2_cell not in obstacle_cells):
                return {"team1": [t1_cell], "team2": [t2_cell]}

        # Last fallback to actual spawns
        return {"team1": self.team1_spawns[:1], "team2": self.team2_spawns[:1]}


class LeekWarsScraper:
    """Playwright-based LeekWars scraper."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self._intercepted_data: dict[str, Any] = {}

    async def __aenter__(self):
        if not HAS_PLAYWRIGHT:
            raise RuntimeError("Playwright not installed. Run: poetry add playwright && playwright install chromium")
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        return self

    async def __aexit__(self, *args):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()

    async def _intercept_response(self, response: Response):
        """Intercept API responses."""
        url = response.url

        # Capture fight data
        if "/api/fight/get/" in url:
            try:
                data = await response.json()
                fight_id = data.get("id") or url.split("/")[-1].split("?")[0]
                self._intercepted_data[f"fight_{fight_id}"] = data
            except:
                pass

        # Capture farmer data (for fight history)
        elif "/api/farmer/get/" in url or "/api/leek/get/" in url:
            try:
                data = await response.json()
                entity_id = url.split("/")[-1].split("?")[0]
                self._intercepted_data[f"entity_{entity_id}"] = data
            except:
                pass

        # Capture garden fights
        elif "/api/garden/get" in url:
            try:
                data = await response.json()
                self._intercepted_data["garden"] = data
            except:
                pass

    async def scrape_fight(self, fight_id: int, include_logs: bool = False) -> FightData | None:
        """Scrape a single fight by ID."""
        self._intercepted_data.clear()

        page = await self.context.new_page()
        page.on("response", self._intercept_response)

        try:
            # Try fight page first
            url = f"{LEEKWARS_BASE}/fight/{fight_id}"
            await page.goto(url, timeout=30000, wait_until="networkidle")

            # Wait for data to load
            await page.wait_for_timeout(2000)

            # Check if we intercepted the fight data
            fight_key = f"fight_{fight_id}"
            if fight_key in self._intercepted_data:
                return FightData.from_api_response(self._intercepted_data[fight_key])

            # Fallback: try report page
            url = f"{LEEKWARS_BASE}/report/{fight_id}"
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            if fight_key in self._intercepted_data:
                return FightData.from_api_response(self._intercepted_data[fight_key])

            return None

        except Exception as e:
            print(f"    Error scraping fight {fight_id}: {e}")
            return None
        finally:
            await page.close()

    async def scrape_farmer_fights(self, farmer_id: int, count: int = 50) -> list[int]:
        """Get recent fight IDs for a farmer."""
        self._intercepted_data.clear()

        page = await self.context.new_page()
        page.on("response", self._intercept_response)

        fight_ids = []
        try:
            url = f"{LEEKWARS_BASE}/farmer/{farmer_id}"
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Extract fight IDs from intercepted data
            for key, data in self._intercepted_data.items():
                if "fights" in data:
                    for fight in data["fights"][:count]:
                        if isinstance(fight, dict) and "id" in fight:
                            fight_ids.append(fight["id"])
                        elif isinstance(fight, int):
                            fight_ids.append(fight)

            # Also try to find fight links on page
            if not fight_ids:
                links = await page.query_selector_all('a[href*="/fight/"]')
                for link in links[:count]:
                    href = await link.get_attribute("href")
                    if href:
                        try:
                            fid = int(href.split("/fight/")[-1].split("/")[0])
                            if fid not in fight_ids:
                                fight_ids.append(fid)
                        except:
                            pass

        except Exception as e:
            print(f"    Error getting farmer fights: {e}")
        finally:
            await page.close()

        return fight_ids[:count]

    async def scrape_random_fights(
        self,
        count: int = 50,
        base_id: int = 50900000,
        range_size: int = 200000
    ) -> list[FightData]:
        """Scrape random recent fights."""
        fights = []
        attempts = 0
        max_attempts = count * 5

        while len(fights) < count and attempts < max_attempts:
            fight_id = base_id + random.randint(-range_size // 2, range_size // 2)
            attempts += 1

            # Skip already cached
            if is_cached(fight_id):
                cached = load_cached(fight_id)
                if cached and cached.data:
                    fights.append(cached)
                    print(f"  [cache] Fight {fight_id} ✓")
                continue

            print(f"  [{len(fights)+1}/{count}] Scraping fight {fight_id}...", end=" ", flush=True)

            fight = await self.scrape_fight(fight_id)
            if fight and fight.data:
                save_to_cache(fight)
                fights.append(fight)
                print(f"✓ (winner={fight.winner}, {len(fight.data.get('map', {}).get('obstacles', {}))} obstacles)")
            else:
                print("✗")

            # Rate limit
            await asyncio.sleep(0.5 + random.random())

        return fights


# Cache utilities
def is_cached(fight_id: int) -> bool:
    return (CACHE_DIR / f"{fight_id}.json").exists()


def load_cached(fight_id: int) -> FightData | None:
    path = CACHE_DIR / f"{fight_id}.json"
    if path.exists():
        try:
            return FightData.from_api_response(json.loads(path.read_text()))
        except:
            return None
    return None


def save_to_cache(fight: FightData):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{fight.id}.json"
    path.write_text(json.dumps(asdict(fight), indent=2))


def load_all_cached() -> list[FightData]:
    """Load all fights from cache."""
    fights = []
    for path in CACHE_DIR.glob("*.json"):
        try:
            fights.append(FightData.from_api_response(json.loads(path.read_text())))
        except:
            continue
    return fights


def extract_map_data(fight: FightData) -> MapData | None:
    """Extract map data from a fight."""
    if not fight.data:
        return None

    map_info = fight.data.get("map", {})
    leeks = fight.data.get("leeks", [])

    if not map_info.get("obstacles"):
        return None

    return MapData(
        fight_id=fight.id,
        width=map_info.get("width", 18),
        height=map_info.get("height", 18),
        type=map_info.get("type", 0),
        obstacles=map_info.get("obstacles", {}),
        pattern=map_info.get("pattern"),
        team1_spawns=[l["cellPos"] for l in leeks if l.get("team") == 1],
        team2_spawns=[l["cellPos"] for l in leeks if l.get("team") == 2],
    )


def build_map_library(fights: list[FightData]) -> list[MapData]:
    """Build unique map library from fights."""
    maps = []
    seen_layouts = set()

    for fight in fights:
        map_data = extract_map_data(fight)
        if not map_data:
            continue

        # Dedupe by obstacle layout
        obs_sig = tuple(sorted(map_data.obstacles.items()))
        layout_sig = (map_data.width, map_data.height, obs_sig)

        if layout_sig not in seen_layouts:
            seen_layouts.add(layout_sig)
            maps.append(map_data)

    return maps


def save_map_library(maps: list[MapData]):
    """Save map library to JSON."""
    library = {
        "version": 2,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(maps),
        "maps": [asdict(m) for m in maps],
    }
    MAP_LIBRARY_FILE.write_text(json.dumps(library, indent=2))
    print(f"\n✓ Saved {len(maps)} maps to {MAP_LIBRARY_FILE}")


async def main():
    parser = argparse.ArgumentParser(description="LeekWars Fight & Map Scraper")
    parser.add_argument("--scrape", action="store_true", help="Scrape new fights")
    parser.add_argument("--count", type=int, default=50, help="Number of fights to scrape")
    parser.add_argument("--fights", nargs="+", type=int, help="Specific fight IDs to scrape")
    parser.add_argument("--farmer", type=int, help="Scrape recent fights from farmer ID")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser headless")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    args = parser.parse_args()

    print("=" * 60)
    print("  LeekWars Fight & Map Scraper")
    print("=" * 60)

    # Load existing cache
    print("\n[1] Loading cached fights...")
    cached_fights = load_all_cached()
    print(f"    Found {len(cached_fights)} fights in cache")

    # Scrape new fights if requested
    new_fights = []
    if args.scrape or args.fights or args.farmer:
        if not HAS_PLAYWRIGHT:
            print("\n⚠ Playwright not installed. Run:")
            print("    poetry add playwright")
            print("    playwright install chromium")
            sys.exit(1)

        headless = not args.visible

        async with LeekWarsScraper(headless=headless) as scraper:
            if args.fights:
                print(f"\n[2] Scraping {len(args.fights)} specific fights...")
                for fid in args.fights:
                    if is_cached(fid):
                        print(f"    Fight {fid} already cached")
                        continue
                    print(f"    Scraping {fid}...", end=" ", flush=True)
                    fight = await scraper.scrape_fight(fid)
                    if fight and fight.data:
                        save_to_cache(fight)
                        new_fights.append(fight)
                        print("✓")
                    else:
                        print("✗")
                    await asyncio.sleep(1)

            elif args.farmer:
                print(f"\n[2] Getting fights for farmer {args.farmer}...")
                fight_ids = await scraper.scrape_farmer_fights(args.farmer, args.count)
                print(f"    Found {len(fight_ids)} fight IDs")

                for fid in fight_ids:
                    if is_cached(fid):
                        continue
                    print(f"    Scraping {fid}...", end=" ", flush=True)
                    fight = await scraper.scrape_fight(fid)
                    if fight and fight.data:
                        save_to_cache(fight)
                        new_fights.append(fight)
                        print("✓")
                    else:
                        print("✗")
                    await asyncio.sleep(1)

            else:
                print(f"\n[2] Scraping {args.count} random fights...")
                new_fights = await scraper.scrape_random_fights(count=args.count)

        print(f"    Scraped {len(new_fights)} new fights")

    # Combine all fights
    all_fights = cached_fights + new_fights

    # Build map library
    print("\n[3] Building map library...")
    maps = build_map_library(all_fights)
    print(f"    Found {len(maps)} unique map layouts")

    # Save
    print("\n[4] Saving map library...")
    save_map_library(maps)

    # Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  Total fights in cache: {len(cached_fights) + len(new_fights)}")
    print(f"  Unique map layouts:    {len(maps)}")
    print(f"  Map library:           {MAP_LIBRARY_FILE}")

    # Sample maps
    print("\n  Sample maps:")
    for m in maps[:3]:
        print(f"    • Fight {m.fight_id}: {m.width}x{m.height}, {len(m.obstacles)} obstacles")
        print(f"      Actual:    T1={m.team1_spawns[:2]} T2={m.team2_spawns[:2]}")
        print(f"      Symmetric: T1={m.symmetric_spawns['team1']} T2={m.symmetric_spawns['team2']}")


if __name__ == "__main__":
    asyncio.run(main())
