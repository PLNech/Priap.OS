#!/usr/bin/env python3
"""Exploration script for API and browser introspection."""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent import LeekWarsAPI, LeekWarsBrowser
from leekwars_agent.auth import get_credentials, login_api





def explore_api():
    """Explore API endpoints."""
    print("\n" + "=" * 60)
    print("API EXPLORATION")
    print("=" * 60)

    with LeekWarsAPI() as api:
        # Login
        print("\n[1] Login...")
        username, password = get_credentials()
        login_data = api.login(username, password)
        print(f"    Token: {api.token[:50]}..." if api.token else "    No token!")
        print(f"    Farmer ID: {api.farmer_id}")
        print(f"    Farmer: {api.farmer.get('name')}")

        # Get leek info
        leeks = api.farmer.get("leeks", {})
        for leek_id, leek in leeks.items():
            print(f"\n[2] Leek: {leek.get('name')} (ID: {leek_id})")
            print(f"    Level: {leek.get('level')}")
            print(f"    Capital: {leek.get('capital')}")
            print(f"    Stats: L{leek.get('life')} S{leek.get('strength')} A{leek.get('agility')}")

        # Test garden endpoint
        print("\n[3] Testing garden endpoint...")
        try:
            garden = api.get_garden()
            print(f"    Response keys: {list(garden.keys())}")
            if "garden" in garden:
                g = garden["garden"]
                print(f"    Solo fights: {g.get('solo_fights', 'N/A')}")
                print(f"    Farmer fights: {g.get('farmer_fights', 'N/A')}")
                print(f"    Leeks in garden: {g.get('leeks', [])}")
        except Exception as e:
            print(f"    ERROR: {e}")

        # Test opponents endpoint
        print("\n[4] Testing get-leek-opponents...")
        leek_id = list(leeks.keys())[0] if leeks else None
        if leek_id:
            try:
                opps = api.get_leek_opponents(int(leek_id))
                print(f"    Response keys: {list(opps.keys())}")
                if "opponents" in opps:
                    print(f"    Found {len(opps['opponents'])} opponents")
                    for opp in opps["opponents"][:3]:
                        print(f"      - {opp.get('name')} (L{opp.get('level')}, T{opp.get('talent')})")
            except Exception as e:
                print(f"    ERROR: {e}")

        # Test static data
        print("\n[5] Testing static data endpoints...")
        try:
            weapons = api.get_weapons()
            print(f"    Weapons: {len(weapons.get('weapons', {}))} types")
        except Exception as e:
            print(f"    Weapons ERROR: {e}")

        try:
            chips = api.get_chips()
            print(f"    Chips: {len(chips.get('chips', {}))} types")
        except Exception as e:
            print(f"    Chips ERROR: {e}")

        try:
            funcs = api.get_functions()
            print(f"    Functions: {len(funcs.get('functions', {}))} available")
        except Exception as e:
            print(f"    Functions ERROR: {e}")

        return api.token, api.farmer


def explore_browser(token: str = None):
    """Browser introspection."""
    print("\n" + "=" * 60)
    print("BROWSER INTROSPECTION")
    print("=" * 60)

    os.makedirs("screenshots", exist_ok=True)

    with LeekWarsBrowser(headless=False) as browser:
        # Go to home
        print("\n[1] Loading homepage...")
        browser.goto("/")
        browser.page.wait_for_timeout(2000)
        browser.screenshot("screenshots/01_home.png")

        # Check page state
        print("\n[2] Page introspection...")
        print(f"    URL: {browser.page.url}")
        print(f"    Title: {browser.page.title()}")

        # Get localStorage
        storage = browser.get_local_storage()
        print(f"    localStorage keys: {list(storage.keys())}")

        # Try login via UI
        print("\n[3] Attempting UI login...")

        # Look for login elements
        page = browser.page

        # Find clickable login link/button
        login_triggers = page.locator("a, button").filter(has_text="Connexion")
        count = login_triggers.count()
        print(f"    Found {count} 'Connexion' elements")

        if count > 0:
            login_triggers.first.click()
            page.wait_for_timeout(1500)
            browser.screenshot("screenshots/02_login_dialog.png")

        # Find input fields
        inputs = page.locator("input")
        print(f"    Found {inputs.count()} input elements")

        for i in range(min(inputs.count(), 10)):
            inp = inputs.nth(i)
            try:
                inp_type = inp.get_attribute("type") or "text"
                inp_name = inp.get_attribute("name") or ""
                inp_placeholder = inp.get_attribute("placeholder") or ""
                print(f"      [{i}] type={inp_type} name={inp_name} placeholder={inp_placeholder}")
            except:
                pass

        # Fill login form
        print("\n[4] Filling login form...")
        try:
            # Try various selectors
            login_input = page.locator("input[type='text'], input[name='login'], input[placeholder*='ogin']").first
            pass_input = page.locator("input[type='password']").first

            if login_input.is_visible() and pass_input.is_visible():
                username, password = get_credentials()
                login_input.fill(username)
                pass_input.fill(password)
                browser.screenshot("screenshots/03_filled_form.png")

                # Find submit button
                submit = page.locator("button[type='submit'], .login-button, button:has-text('Connexion')").first
                if submit.is_visible():
                    submit.click()
                    page.wait_for_timeout(3000)
                    page.wait_for_load_state("networkidle")
                    browser.screenshot("screenshots/04_after_login.png")
                    print(f"    Login submitted!")
                    print(f"    URL after: {page.url}")
        except Exception as e:
            print(f"    Form fill ERROR: {e}")

        # Check if logged in
        print("\n[5] Post-login state...")
        storage = browser.get_local_storage()
        print(f"    localStorage keys: {list(storage.keys())}")

        token = browser.get_token()
        print(f"    Token: {token[:50] if token else 'None'}...")

        farmer = browser.get_page_data()
        print(f"    __FARMER__: {bool(farmer)}")

        # Navigate to garden
        print("\n[6] Navigating to garden...")
        browser.navigate_to_garden()
        page.wait_for_timeout(2000)
        browser.screenshot("screenshots/05_garden.png")
        print(f"    URL: {page.url}")

        # Introspect garden UI
        print("\n[7] Garden UI introspection...")

        # Look for fight buttons
        fight_btns = page.locator("button, .fight, [class*='fight']")
        print(f"    Fight-related elements: {fight_btns.count()}")

        # Look for leek cards
        leek_cards = page.locator("[class*='leek'], [class*='opponent']")
        print(f"    Leek/opponent elements: {leek_cards.count()}")

        # Dump some class names for analysis
        print("\n[8] DOM class analysis...")
        classes = page.evaluate("""() => {
            const all = document.querySelectorAll('*');
            const classSet = new Set();
            all.forEach(el => {
                el.classList.forEach(c => classSet.add(c));
            });
            return Array.from(classSet).filter(c =>
                c.includes('fight') || c.includes('leek') ||
                c.includes('opponent') || c.includes('garden') ||
                c.includes('button') || c.includes('solo')
            ).slice(0, 30);
        }""")
        print(f"    Relevant classes: {classes}")

        # Keep browser open for manual inspection
        print("\n[9] Browser open for inspection. Press Enter to close...")
        input()


if __name__ == "__main__":
    token, farmer = explore_api()

    if "--browser" in sys.argv or "-b" in sys.argv:
        explore_browser(token)
    else:
        print("\n[INFO] Run with --browser or -b to open browser for introspection")
