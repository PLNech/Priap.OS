#!/usr/bin/env python3
"""Test login via both API and browser."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from leekwars_agent import LeekWarsAPI, LeekWarsBrowser


def test_api_login(username: str, password: str):
    """Test API login."""
    print("\n=== Testing API Login ===")

    with LeekWarsAPI() as api:
        result = api.login(username, password)

        if result.get("success"):
            print(f"[OK] API login successful!")
            print(f"    Token: {api.token[:50]}..." if api.token else "    No token")

            farmer = result.get("farmer", {})
            print(f"    Farmer ID: {farmer.get('id')}")
            print(f"    Name: {farmer.get('name')}")
            print(f"    Level: {farmer.get('total_level')}")

            # Get garden info
            try:
                garden = api.get_garden()
                if garden.get("success"):
                    print(f"\n    Garden info:")
                    print(f"    Solo fights: {garden.get('garden', {}).get('solo_fights', 'N/A')}")
                    print(f"    Farmer fights: {garden.get('garden', {}).get('farmer_fights', 'N/A')}")
            except Exception as e:
                print(f"    Could not fetch garden: {e}")

            return True, result
        else:
            print(f"[FAIL] API login failed: {result.get('error')}")
            return False, result


def test_browser_login(username: str, password: str, headless: bool = False):
    """Test browser login."""
    print("\n=== Testing Browser Login ===")

    with LeekWarsBrowser(headless=headless) as browser:
        browser.goto("/")
        print(f"    Navigated to LeekWars")
        browser.screenshot("screenshots/01_home.png")

        success = browser.login(username, password)

        if success:
            print(f"[OK] Browser login successful!")
            browser.screenshot("screenshots/02_logged_in.png")

            token = browser.get_token()
            print(f"    Token from localStorage: {token[:50] if token else 'None'}...")

            farmer_data = browser.get_page_data()
            if farmer_data:
                print(f"    Farmer data found: {bool(farmer_data)}")

            return True
        else:
            print(f"[FAIL] Browser login failed")
            browser.screenshot("screenshots/02_login_failed.png")
            return False


if __name__ == "__main__":
    # Credentials
    from leekwars_agent.auth import get_credentials
    USERNAME, PASSWORD = get_credentials()

    # Create screenshots dir
    os.makedirs("screenshots", exist_ok=True)

    # Test API
    api_success, api_result = test_api_login(USERNAME, PASSWORD)

    # Test browser (headful)
    if "--browser" in sys.argv:
        browser_success = test_browser_login(USERNAME, PASSWORD, headless=False)
    elif "--headless" in sys.argv:
        browser_success = test_browser_login(USERNAME, PASSWORD, headless=True)
    else:
        print("\n[INFO] Skipping browser test. Use --browser or --headless to enable.")
        browser_success = None

    print("\n=== Summary ===")
    print(f"API Login: {'OK' if api_success else 'FAILED'}")
    if browser_success is not None:
        print(f"Browser Login: {'OK' if browser_success else 'FAILED'}")
