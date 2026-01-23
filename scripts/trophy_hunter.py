#!/usr/bin/env python3
"""Trophy Hunter - Unlock secret trophies and enigmas via browser automation.

Known enigmas from frontend source analysis:
1. Trophy 113 "Konami" (40,000 habs) - Enter: ↑↑↓↓←→←→BA
2. Trophy 234 "On me voit on me voit plus" (2,500 habs) - Toggle SFW mode
3. Trophy 325 "Eagle" (varies) - Click 100 clovers when they appear
4. Trophy 92 "Lucky" (90,000 habs) - Clover-related

Usage:
    python scripts/trophy_hunter.py --check     # Check trophy status
    python scripts/trophy_hunter.py --hunt      # Hunt trophies interactively
"""

import argparse
import time
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from leekwars_agent.api import LeekWarsAPI


# Known secret/enigma trophy IDs and their rewards
ENIGMA_TROPHIES = {
    # === EASY (UI actions) ===
    113: {"code": "konami", "habs": 40000, "hint": "✅ Konami code: ↑↑↓↓←→←→BA (anywhere on site)"},
    234: {"code": "you_can_see_me", "habs": 2500, "hint": "✅ Toggle SFW mode in settings"},

    # === MEDIUM (gameplay) ===
    92: {"code": "lucky", "habs": 90000, "hint": "Click clovers when they randomly appear on site"},
    325: {"code": "eagle", "habs": 0, "hint": "Click 100 clovers total"},
    87: {"code": "mathematician", "habs": 250000, "hint": "Walk on 50 PRIME cells (2,3,5,7,11...) in fights"},

    # === HARD (secrets) ===
    323: {"code": "lost", "habs": 810000, "hint": "??? (LOST numbers: 4 8 15 16 23 42? Only 37 people have it!)"},
    188: {"code": "xii", "habs": 810000, "hint": "'Consume 12 12 12 12 12 operations in one fight' (73 players!)"},
    231: {"code": "9_34", "habs": 360000, "hint": "??? Platform 9¾ (209 players)"},
    187: {"code": "shhh", "habs": 250000, "hint": "??? Secret... maybe type 'shhh'?"},

    # === MISC ===
    51: {"code": "serge", "habs": 40000, "hint": "Who is Serge? (creator?)"},
    112: {"code": "fish", "habs": 0, "hint": "April Fools? (April 1st)"},
    324: {"code": "joker", "habs": 0, "hint": "Click the joker trophy image (fake clover)"},
}


def check_trophy_status():
    """Check which enigma trophies we have unlocked."""
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    username = os.getenv("LEEKWARS_USER") or os.getenv("LEEKWARS_USERNAME") or os.getenv("LEEKWARS_LOGIN") or "leek@nech.pl"
    password = os.getenv("LEEKWARS_PASS") or os.getenv("LEEKWARS_PASSWORD")
    if not password:
        print("❌ LEEKWARS_PASSWORD not found in .env")
        return

    api = LeekWarsAPI()
    api.login(username, password)

    farmer_id = api.farmer_id
    print(f"\n🏆 Trophy Status for Farmer {farmer_id}")
    print("=" * 60)

    # Get trophy status
    resp = api.session.get(
        f"{api.BASE_URL}/trophy/get-farmer-trophies/{farmer_id}/fr"
    )
    data = resp.json()

    total_potential = 0
    already_earned = 0
    available_habs = 0

    print("\n📋 Enigma Trophies:\n")
    for trophy_id, info in sorted(ENIGMA_TROPHIES.items()):
        # Find this trophy in the list
        trophy = None
        for t in data.get("trophies", []):
            if t.get("id") == trophy_id:
                trophy = t
                break

        status = "✅" if trophy and trophy.get("unlocked") else "❌"
        habs = info["habs"]
        total_potential += habs

        if trophy and trophy.get("unlocked"):
            already_earned += habs
            print(f"  {status} {info['code']:25} {habs:>8} habs - UNLOCKED!")
        else:
            available_habs += habs
            print(f"  {status} {info['code']:25} {habs:>8} habs - {info['hint']}")

    print("\n" + "=" * 60)
    print(f"💰 Already earned:   {already_earned:>10} habs")
    print(f"💰 Still available:  {available_habs:>10} habs")
    print(f"💰 Total potential:  {total_potential:>10} habs")
    print("=" * 60)

    # Current habs
    farmer = api.farmer  # From login response
    print(f"\n💵 Current balance: {farmer.get('habs', 0):,} habs")

    return data


def hunt_with_browser():
    """Launch browser and hunt for trophies interactively."""
    from playwright.sync_api import sync_playwright

    print("\n🎮 Launching Trophy Hunter Browser...")
    print("=" * 60)

    # Load credentials
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    username = os.getenv("LEEKWARS_USER") or os.getenv("LEEKWARS_USERNAME") or os.getenv("LEEKWARS_LOGIN") or "leek@nech.pl"
    password = os.getenv("LEEKWARS_PASS") or os.getenv("LEEKWARS_PASSWORD")
    if not password:
        print("❌ LEEKWARS_PASSWORD not found in .env")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Headful for interactive
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()

        print("📡 Navigating to LeekWars...")
        page.goto("https://leekwars.com/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Check if already logged in
        if "Connexion" in page.content():
            print("🔐 Logging in...")
            # Click login button/link
            login_btn = page.locator("text=Connexion").first
            if login_btn.is_visible():
                login_btn.click()
                time.sleep(1)

            # Fill credentials
            page.fill('input[type="text"]', username)
            page.fill('input[type="password"]', password)
            page.click('button:has-text("Connexion")')
            time.sleep(3)
            page.wait_for_load_state("networkidle")

        print("✅ Logged in!")

        # === TROPHY 113: KONAMI CODE ===
        print("\n🎮 Attempting Konami Code (Trophy 113 - 40,000 habs)...")
        print("   Entering: ↑ ↑ ↓ ↓ ← → ← → B A")

        # Wait a moment for the page to be ready
        time.sleep(1)

        # Enter the Konami code
        konami_sequence = [
            "ArrowUp", "ArrowUp",
            "ArrowDown", "ArrowDown",
            "ArrowLeft", "ArrowRight",
            "ArrowLeft", "ArrowRight",
            "KeyB", "KeyA"
        ]

        for key in konami_sequence:
            page.keyboard.press(key)
            time.sleep(0.1)

        time.sleep(2)
        print("   ✅ Konami code entered!")

        # === TROPHY 234: SFW MODE ===
        print("\n⚙️ Attempting SFW Mode (Trophy 234 - 2,500 habs)...")
        page.goto("https://leekwars.com/settings")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Look for SFW toggle
        try:
            sfw_toggle = page.locator('text="Safe for work"').first
            if sfw_toggle.is_visible():
                # Find the switch next to it and toggle
                switch = page.locator('.v-input--switch').filter(
                    has=page.locator('text="Safe for work"')
                ).first
                if switch.is_visible():
                    switch.click()
                    time.sleep(1)
                    print("   ✅ SFW mode toggled!")
                    # Toggle back
                    switch.click()
                    time.sleep(1)
        except Exception as e:
            print(f"   ⚠️ Could not find SFW toggle: {e}")

        print("\n" + "=" * 60)
        print("🎯 Interactive mode - browser stays open for manual exploration")
        print("   Try these:")
        print("   • Look for clovers (4-leaf) that appear randomly - click them!")
        print("   • Visit /trophy/lost and see if there's a hint")
        print("   • Visit /trophy/9_34 for Platform 9¾ clues")
        print("=" * 60)

        # Keep browser open for manual exploration
        input("\n⏸️  Press Enter to close browser...")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="LeekWars Trophy Hunter")
    parser.add_argument("--check", action="store_true", help="Check trophy status")
    parser.add_argument("--hunt", action="store_true", help="Hunt trophies with browser")
    args = parser.parse_args()

    if args.check:
        check_trophy_status()
    elif args.hunt:
        hunt_with_browser()
    else:
        # Default: check then hunt
        check_trophy_status()
        print("\n")
        response = input("🎯 Launch trophy hunter browser? [y/N]: ")
        if response.lower() == "y":
            hunt_with_browser()


if __name__ == "__main__":
    main()
