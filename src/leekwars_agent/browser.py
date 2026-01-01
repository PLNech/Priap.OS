"""LeekWars browser automation with Playwright."""

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from typing import Any
import json


class LeekWarsBrowser:
    """Headful browser automation for LeekWars."""

    BASE_URL = "https://leekwars.com"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def start(self) -> "LeekWarsBrowser":
        """Start the browser."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self._page = self._context.new_page()
        return self

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    def goto(self, path: str = "/") -> None:
        """Navigate to a page."""
        self.page.goto(f"{self.BASE_URL}{path}")
        self.page.wait_for_load_state("networkidle")

    def login(self, username: str, password: str) -> bool:
        """Login via browser UI."""
        self.goto("/")

        # Wait for the page to load and look for login
        self.page.wait_for_timeout(2000)

        # Click on login button/link
        login_btn = self.page.locator("text=Connexion").first
        if login_btn.is_visible():
            login_btn.click()
            self.page.wait_for_timeout(1000)

        # Fill login form
        self.page.fill('input[name="login"], input[placeholder*="login"], input[type="text"]', username)
        self.page.fill('input[name="password"], input[type="password"]', password)

        # Submit
        self.page.click('button[type="submit"], input[type="submit"], .login-button, button:has-text("Connexion")')
        self.page.wait_for_timeout(3000)
        self.page.wait_for_load_state("networkidle")

        # Check if logged in
        return self.is_logged_in()

    def is_logged_in(self) -> bool:
        """Check if currently logged in."""
        # Look for logout option or user menu
        return (
            self.page.locator(".farmer-menu").is_visible()
            or self.page.locator("[href='/settings']").is_visible()
            or "Déconnexion" in self.page.content()
        )

    def get_local_storage(self) -> dict[str, Any]:
        """Get localStorage data including token."""
        return self.page.evaluate("() => Object.fromEntries(Object.entries(localStorage))")

    def get_token(self) -> str | None:
        """Extract JWT token from localStorage."""
        storage = self.get_local_storage()
        return storage.get("token")

    def screenshot(self, path: str = "screenshot.png") -> None:
        """Take a screenshot."""
        self.page.screenshot(path=path)

    def get_page_data(self) -> dict[str, Any]:
        """Extract __FARMER__ data from page."""
        try:
            return self.page.evaluate("() => window.__FARMER__")
        except Exception:
            return {}

    def navigate_to_garden(self) -> None:
        """Navigate to the garden/arena."""
        self.goto("/garden")

    def navigate_to_editor(self) -> None:
        """Navigate to the AI editor."""
        self.goto("/editor")

    def navigate_to_leek(self, leek_id: int) -> None:
        """Navigate to a leek page."""
        self.goto(f"/leek/{leek_id}")

    def close(self) -> None:
        """Close browser."""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.close()
