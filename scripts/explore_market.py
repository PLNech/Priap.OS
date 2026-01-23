#!/usr/bin/env python3
"""Explore LeekWars market UI to understand DOM structure for crafting automation.

Usage:
    poetry run python scripts/explore_market.py

Output:
    - Screenshots in data/screenshots/
    - DOM dumps for analysis
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent.browser import LeekWarsBrowser
from leekwars_agent.auth import get_credentials

# Output directories
PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOT_DIR = PROJECT_ROOT / "data" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def explore_market():
    """Explore market UI and capture structure."""
    username, password = get_credentials()

    print("=" * 60)
    print("  Market Explorer - Empirical Discovery")
    print("=" * 60)

    # Use headful mode so we can see what's happening
    with LeekWarsBrowser(headless=False) as browser:
        print("\n[1] Logging in...")
        if not browser.login(username, password):
            print("    Login failed!")
            return
        print("    Logged in!")

        # Screenshot after login
        ss_path = SCREENSHOT_DIR / f"{timestamp()}_01_logged_in.png"
        browser.screenshot(str(ss_path))
        print(f"    Screenshot: {ss_path}")

        print("\n[2] Navigating to /market...")
        browser.goto("/market")
        browser.page.wait_for_timeout(3000)  # Let Vue render

        ss_path = SCREENSHOT_DIR / f"{timestamp()}_02_market.png"
        browser.screenshot(str(ss_path))
        print(f"    Screenshot: {ss_path}")

        print("\n[3] Looking for tabs/navigation...")
        # Try to find inventory tab
        page = browser.page

        # Dump all clickable elements for analysis
        tabs = page.locator("role=tab, .tab, [class*='tab'], .v-tab").all()
        print(f"    Found {len(tabs)} potential tabs")
        for i, tab in enumerate(tabs[:10]):
            try:
                text = tab.text_content()
                print(f"      [{i}] {text[:50] if text else '(no text)'}")
            except:
                pass

        # Look for "Inventaire" or "Inventory"
        inventory_btn = page.locator("text=Inventaire, text=Inventory, text=inventaire").first
        if inventory_btn.is_visible():
            print("\n[4] Found Inventory button, clicking...")
            inventory_btn.click()
            page.wait_for_timeout(2000)

            ss_path = SCREENSHOT_DIR / f"{timestamp()}_03_inventory.png"
            browser.screenshot(str(ss_path))
            print(f"    Screenshot: {ss_path}")
        else:
            print("\n[4] No 'Inventaire' button found, trying to discover...")
            # Try clicking various elements
            for selector in [".inventory", "[href*='inventory']", "a:has-text('Inv')"]:
                try:
                    el = page.locator(selector).first
                    if el.is_visible():
                        print(f"    Found: {selector}")
                        el.click()
                        page.wait_for_timeout(2000)
                        break
                except:
                    pass

        print("\n[5] Dumping page structure...")

        # Get all items that look like inventory/craftable
        items = page.locator("[class*='item'], [class*='chip'], [class*='resource'], .card").all()
        print(f"    Found {len(items)} potential item elements")

        # Try to extract item data from Vue/page
        try:
            # LeekWars often stores data in window.__LW__ or similar
            page_data = page.evaluate("""() => {
                const data = {};
                // Try common Vue data stores
                if (window.__FARMER__) data.farmer = window.__FARMER__;
                if (window.__LEEK__) data.leek = window.__LEEK__;
                if (window.$store) {
                    try {
                        data.store_state = JSON.parse(JSON.stringify(window.$store.state));
                    } catch(e) {}
                }
                // Try to find Vue instance data
                const app = document.querySelector('#app');
                if (app && app.__vue__) {
                    try {
                        data.vue_data = JSON.parse(JSON.stringify(app.__vue__.$data));
                    } catch(e) {}
                }
                return data;
            }""")

            if page_data:
                dump_path = SCREENSHOT_DIR / f"{timestamp()}_page_data.json"
                dump_path.write_text(json.dumps(page_data, indent=2, default=str))
                print(f"    Page data dumped: {dump_path}")

                # Quick summary
                if "farmer" in page_data:
                    farmer = page_data["farmer"]
                    print(f"    Farmer: {farmer.get('name')} (L{farmer.get('level')})")
        except Exception as e:
            print(f"    Could not extract page data: {e}")

        # Dump HTML for offline analysis
        html_path = SCREENSHOT_DIR / f"{timestamp()}_market.html"
        html_path.write_text(page.content())
        print(f"    HTML dumped: {html_path}")

        print("\n[6] Interactive pause - browser stays open...")
        print("    Explore manually, then press Enter to close.")
        input("    > ")

    print("\nDone! Check data/screenshots/ for outputs.")


if __name__ == "__main__":
    explore_market()
